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


def _image_score(url: str, context: tuple[str, ...]) -> int:
    lower_url = url.lower()
    lower_context = " ".join(context).lower()
    score = 0
    for token, points in (
        ("original", 90),
        ("large", 80),
        ("big", 70),
        ("medium", 45),
        ("small", 5),
        ("thumb", -25),
        ("thumbnail", -25),
        ("200", -10),
        ("400", 10),
        ("800", 30),
        ("1024", 45),
        ("1200", 55),
        ("1600", 70),
    ):
        if token in lower_url:
            score += points
        if token in lower_context:
            score += points
    return score


def _collect_image_urls(value: Any, context: tuple[str, ...] = ()) -> list[tuple[int, str]]:
    if isinstance(value, str):
        s = value.strip()
        if s.startswith(("http://", "https://")):
            return [(_image_score(s, context), s)]
        return []
    if isinstance(value, list):
        out: list[tuple[int, str]] = []
        for item in value:
            out.extend(_collect_image_urls(item, context))
        return out
    if isinstance(value, dict):
        out: list[tuple[int, str]] = []
        for key in ("src", "url", "link", "href"):
            out.extend(_collect_image_urls(value.get(key), context + (key,)))
        for key, item in value.items():
            out.extend(_collect_image_urls(item, context + (str(key),)))
        return out
    return []


def _best_image_url(value: Any) -> str | None:
    candidates = _collect_image_urls(value)
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def _apply_aircraft_image(raw: dict, flight: "Flight") -> None:
    aircraft = raw.get("aircraft") or {}
    if not isinstance(aircraft, dict):
        return
    image_url = _best_image_url(aircraft.get("images"))
    if image_url:
        setattr(flight, "image_url", image_url)


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
    _apply_aircraft_image(raw, flight)
    sdk.set_flight_details(raw)
    flight.enrich_from_details(sdk)
