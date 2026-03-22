from __future__ import annotations

from typing import Iterable, List, Optional, Set, TYPE_CHECKING

from FlightRadar24 import FlightRadar24API

if TYPE_CHECKING:
    from FlightRadar24.entities.flight import Flight as SdkFlight

from models.flight import Flight

from config import EngineConfig, DEFAULT_CONFIG
from data_sources.movement import (
    airport_match_codes,
    classify_movement,
    movement_passes_filter,
)


def _dedupe_key(sdk: "SdkFlight") -> str:
    return getattr(sdk, "id", "") or str(id(sdk))


def load_live_flights(
    fr_api: Optional[FlightRadar24API] = None,
    *,
    config: EngineConfig = DEFAULT_CONFIG,
    airport_filter: Optional[Iterable[str]] = None,
    fetch_details: bool = False,
) -> List[Flight]:
    """
    Load live flights within config.radius_meters of each configured airport.
    Merges multi-airport results and de-duplicates by FR24 flight id.

    movement_filter (on config) drops traffic that only overflies the airport
    cylinder without origin/destination at that airport (when not ``all``).
    """
    api = fr_api or FlightRadar24API()
    codes = tuple(airport_filter) if airport_filter is not None else config.airports
    seen: Set[str] = set()
    out: List[Flight] = []

    for code in codes:
        airport = api.get_airport(code)
        match_codes = airport_match_codes(airport)
        query_code = code.strip().upper()
        if query_code:
            match_codes.add(query_code)

        bounds = api.get_bounds_by_point(
            airport.latitude, airport.longitude, config.radius_meters
        )
        sdk_flights = api.get_flights(bounds=bounds, details=fetch_details)
        for sdk in sdk_flights:
            key = _dedupe_key(sdk)
            if key in seen:
                continue
            dist_km = sdk.get_distance_from(airport)
            if dist_km * 1000.0 > config.radius_meters:
                continue

            fl = Flight.from_sdk_flight(sdk)
            fl.monitored_airport = query_code
            fl.movement = classify_movement(fl.origin, fl.destination, match_codes)
            if not movement_passes_filter(fl.movement, config.movement_filter):
                continue

            seen.add(key)
            if fetch_details:
                fl.enrich_from_details(sdk)
            out.append(fl)

    return out
