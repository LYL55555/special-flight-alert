"""Selective FR24 flight-details fetch to fill schedule/ETA fields."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from FlightRadar24 import FlightRadar24API
from FlightRadar24.entities.flight import Flight as SdkFlight

if TYPE_CHECKING:
    from models.flight import Flight


def _apply_identification_raw(raw: dict, flight: "Flight") -> None:
    ident = raw.get("identification") or {}
    if not isinstance(ident, dict):
        return
    num = ident.get("number") or {}
    if isinstance(num, dict):
        fn = num.get("default") or num.get("alternative")
        if fn and str(fn).strip() and not flight.flight_number:
            flight.flight_number = str(fn).strip()


def enrich_flight_from_fr24_details(api: FlightRadar24API, flight: "Flight") -> None:
    if not flight.fr24_id:
        return
    lat = float(flight.latitude) if flight.latitude is not None else 0.0
    lon = float(flight.longitude) if flight.longitude is not None else 0.0
    info: list = [None] * 19
    info[1] = lat
    info[2] = lon
    info[13] = flight.flight_number or "ZZ0000"
    sdk = SdkFlight(flight.fr24_id, info)
    raw = api.get_flight_details(sdk)
    if not isinstance(raw, dict):
        return
    _apply_identification_raw(raw, flight)
    sdk.set_flight_details(raw)
    flight.enrich_from_details(sdk)
