from __future__ import annotations

import re
import time
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional
from urllib.parse import quote_plus

from FlightRadar24 import FlightRadar24API

from alerts.scorer import AlertExtras, score_flight
from config import DEFAULT_CONFIG, EngineConfig
from data_sources.details import enrich_flight_from_fr24_details
from data_sources.flights_api import load_live_flights
from data_sources.photos import AircraftPhoto, fetch_planespotters_photo
from data_sources.schedule_api import load_schedules_multi_airport
from models.flight import Flight
from rules.special_livery import load_livery_db


AIRPORT_CODE_RE = re.compile(r"^[A-Za-z]{3,4}$")
PHOTO_CACHE_TTL_SECONDS = 24 * 3600
_photo_cache: dict[str, tuple[float, AircraftPhoto | None]] = {}


class AirportScanError(Exception):
    """Base error for one-shot airport scan failures."""


class InvalidAirportCodeError(AirportScanError):
    """Raised when an airport code cannot be queried safely."""


def normalize_airport_code(airport: str) -> str:
    code = (airport or "").strip().upper()
    if not AIRPORT_CODE_RE.fullmatch(code):
        raise InvalidAirportCodeError("Airport code must be 3 or 4 letters.")
    return code


def default_livery_csv_path() -> Path:
    return Path(__file__).resolve().parents[1] / "db" / "special_liveries.csv"


def load_default_livery_db() -> dict:
    return load_livery_db(default_livery_csv_path())


def _load_flights_for_api(
    fr_api: FlightRadar24API,
    config: EngineConfig,
    airport: str,
    *,
    live_fetch_details: bool = False,
) -> list[Flight]:
    if config.scan_mode == "live":
        return load_live_flights(
            fr_api,
            config=config,
            airport_filter=(airport,),
            fetch_details=live_fetch_details,
        )
    return load_schedules_multi_airport(
        fr_api,
        config=config,
        airport_filter=(airport,),
        hours=config.schedule_horizon_hours,
    )


def _iso(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def build_flight_links(flight: Flight) -> dict[str, Optional[str]]:
    registration = (flight.registration or "").strip().upper()
    flight_number = (flight.flight_number or "").strip().upper()
    fr24_id = (flight.fr24_id or "").strip()

    if fr24_id:
        fr24_url = f"https://www.flightradar24.com/{quote_plus(fr24_id)}"
    elif flight_number:
        fr24_url = f"https://www.flightradar24.com/data/flights/{quote_plus(flight_number.lower())}"
    elif registration:
        fr24_url = f"https://www.flightradar24.com/data/aircraft/{quote_plus(registration.lower())}"
    else:
        fr24_url = None
    jetphotos_url = (
        f"https://www.jetphotos.com/registration/{quote_plus(registration)}"
        if registration
        else None
    )
    planespotters_url = (
        f"https://www.planespotters.net/photos/reg/{quote_plus(registration)}"
        if registration
        else None
    )
    return {
        "fr24": fr24_url,
        "jetphotos": jetphotos_url,
        "planespotters": planespotters_url,
    }


def _cached_photo_for_registration(registration: str) -> AircraftPhoto | None:
    reg = (registration or "").strip().upper()
    if not reg:
        return None
    now = time.monotonic()
    cached = _photo_cache.get(reg)
    if cached is not None:
        created, photo = cached
        if now - created <= PHOTO_CACHE_TTL_SECONDS:
            return photo
        _photo_cache.pop(reg, None)
    try:
        photo = fetch_planespotters_photo(reg)
    except Exception:
        photo = None
    _photo_cache[reg] = (now, photo)
    return photo


def _display_endpoint(flight: Flight, field: str) -> Optional[str]:
    if field == "origin":
        if flight.origin:
            return flight.origin
        if flight.movement == "departure":
            return flight.monitored_airport
        return None
    if flight.destination:
        return flight.destination
    if flight.movement == "arrival":
        return flight.monitored_airport
    return None


def _primary_time(flight: Flight, local_times: dict[str, str]) -> dict[str, Any]:
    if flight.movement == "departure":
        dt = flight.estimated_departure or flight.scheduled_departure
        display = (
            local_times["estimated_departure_local"]
            or local_times["scheduled_departure_local"]
        )
        label = "departure"
    elif flight.movement == "arrival":
        dt = flight.estimated_arrival or flight.scheduled_arrival
        display = (
            local_times["estimated_arrival_local"]
            or local_times["scheduled_arrival_local"]
        )
        label = "arrival"
    else:
        dt = flight.spot_time_for_sort()
        display = flight.spot_time_local_display()
        label = "time"
    return {
        "label": label,
        "utc": _iso(dt),
        "local": display or None,
    }


def _operator_display(operator: Optional[str]) -> Optional[str]:
    if not operator:
        return None
    name = re.sub(r"\s*\([^)]*\)\s*", " ", operator).strip()
    name = re.sub(r"\s+", " ", name)
    aliases = (
        (re.compile(r"^jet\s*blue\b", re.I), "JetBlue"),
        (re.compile(r"^american( airlines)?\b", re.I), "American Airlines"),
        (re.compile(r"^delta( air lines)?\b", re.I), "Delta Air Lines"),
        (re.compile(r"^united( airlines)?\b", re.I), "United Airlines"),
        (re.compile(r"^southwest( airlines)?\b", re.I), "Southwest Airlines"),
        (re.compile(r"^alaska( airlines)?\b", re.I), "Alaska Airlines"),
        (re.compile(r"^spirit( airlines)?\b", re.I), "Spirit Airlines"),
        (re.compile(r"^frontier( airlines)?\b", re.I), "Frontier Airlines"),
        (re.compile(r"^breeze( airways)?\b", re.I), "Breeze Airways"),
    )
    for pattern, label in aliases:
        if pattern.search(name):
            return label
    return name or None


def flight_to_api_dict(
    flight: Flight,
    score: int,
    reasons: Iterable[str],
    extras: AlertExtras,
) -> dict[str, Any]:
    local_times = flight.row_local_times()
    primary = _primary_time(flight, local_times)
    return {
        "flight_number": flight.flight_number,
        "registration": flight.registration,
        "aircraft_type": flight.aircraft_type,
        "operator": flight.operator,
        "operator_display": _operator_display(flight.operator),
        "origin": flight.origin,
        "destination": flight.destination,
        "display_origin": _display_endpoint(flight, "origin"),
        "display_destination": _display_endpoint(flight, "destination"),
        "movement": flight.movement,
        "primary_time_label": primary["label"],
        "primary_time": primary["utc"],
        "primary_time_local": primary["local"],
        "scheduled_departure": _iso(flight.scheduled_departure),
        "estimated_departure": _iso(flight.estimated_departure),
        "scheduled_arrival": _iso(flight.scheduled_arrival),
        "estimated_arrival": _iso(flight.estimated_arrival),
        "scheduled_departure_local": local_times["scheduled_departure_local"],
        "estimated_departure_local": local_times["estimated_departure_local"],
        "scheduled_arrival_local": local_times["scheduled_arrival_local"],
        "estimated_arrival_local": local_times["estimated_arrival_local"],
        "departure_tz_label": local_times["departure_tz_label"],
        "arrival_tz_label": local_times["arrival_tz_label"],
        "livery_name": extras.livery_name,
        "livery_airline": extras.livery_airline,
        "livery_description": extras.livery_description,
        "score": score,
        "reasons": list(reasons),
        "jetphotos_url": build_flight_links(flight)["jetphotos"],
        "image_url": getattr(flight, "image_url", None),
        "photo_url": getattr(flight, "photo_url", None)
        or getattr(flight, "image_url", None),
        "photo_source": getattr(flight, "photo_source", None),
        "photo_page_url": getattr(flight, "photo_page_url", None),
        "photo_credit": getattr(flight, "photo_credit", None),
        "fr24_id": flight.fr24_id,
        "source": flight.source,
        "links": build_flight_links(flight),
    }


def _sort_key(row: tuple[Flight, int, list[str], AlertExtras]) -> tuple:
    flight = row[0]
    t = flight.spot_time_for_sort()
    if t is None:
        return (1, float("inf"), flight.flight_number or "", flight.registration or "")
    if t.tzinfo is None:
        t = t.replace(tzinfo=timezone.utc)
    return (0, t.timestamp(), flight.flight_number or "", flight.registration or "")


def _share_images_by_registration(
    rows: list[tuple[Flight, int, list[str], AlertExtras]],
) -> None:
    images: dict[str, str] = {}
    for flight, _, _, _ in rows:
        reg = (flight.registration or "").strip().upper()
        image_url = getattr(flight, "image_url", None)
        if reg and image_url and reg not in images:
            images[reg] = str(image_url)
    for flight, _, _, _ in rows:
        reg = (flight.registration or "").strip().upper()
        if reg and reg in images and not getattr(flight, "image_url", None):
            setattr(flight, "image_url", images[reg])


def _fill_missing_photos(
    rows: list[tuple[Flight, int, list[str], AlertExtras]],
) -> None:
    for flight, _, _, _ in rows:
        if getattr(flight, "image_url", None):
            continue
        photo = _cached_photo_for_registration(flight.registration or "")
        if not photo:
            continue
        setattr(flight, "image_url", photo.image_url)
        setattr(flight, "photo_url", photo.image_url)
        setattr(flight, "photo_source", photo.source)
        if photo.page_url:
            setattr(flight, "photo_page_url", photo.page_url)
        if photo.photographer:
            setattr(flight, "photo_credit", photo.photographer)


def scan_airport_once(
    airport: str,
    *,
    fr_api: Optional[FlightRadar24API] = None,
    config: EngineConfig = DEFAULT_CONFIG,
    livery_db: Optional[dict] = None,
    fetch_details: Optional[bool] = None,
) -> dict[str, Any]:
    code = normalize_airport_code(airport)
    api = fr_api or FlightRadar24API()
    scan_config = replace(config, airports=(code,))
    liveries = livery_db if livery_db is not None else load_default_livery_db()
    should_fetch_details = (
        scan_config.fetch_details_on_alert if fetch_details is None else fetch_details
    )

    flights = _load_flights_for_api(api, scan_config, code)
    qualifying: list[tuple[Flight, int, list[str], AlertExtras]] = []
    for flight in flights:
        total, reasons, extras = score_flight(flight, scan_config, liveries)
        if total < scan_config.alert_min_score:
            continue
        if should_fetch_details and flight.fr24_id:
            try:
                enrich_flight_from_fr24_details(api, flight)
            except Exception:
                pass
        qualifying.append((flight, total, reasons, extras))

    qualifying.sort(key=_sort_key)
    _share_images_by_registration(qualifying)
    _fill_missing_photos(qualifying)
    _share_images_by_registration(qualifying)
    return {
        "airport": code,
        "queried_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "count": len(qualifying),
        "cached": False,
        "cache_age_seconds": None,
        "flights": [
            flight_to_api_dict(flight, total, reasons, extras)
            for flight, total, reasons, extras in qualifying
        ],
    }
