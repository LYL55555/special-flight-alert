"""Classify arrival / departure vs overflight relative to a monitored airport."""

from __future__ import annotations

from typing import TYPE_CHECKING, Set

if TYPE_CHECKING:
    from FlightRadar24.entities.airport import Airport


def airport_match_codes(airport: "Airport") -> Set[str]:
    codes: Set[str] = set()
    for attr in ("iata", "icao"):
        v = getattr(airport, attr, None)
        if v is None or v == "N/A":
            continue
        s = str(v).strip().upper()
        if s:
            codes.add(s)
    return codes


def classify_movement(
    origin: str | None,
    destination: str | None,
    codes: Set[str],
) -> str:
    o = (origin or "").strip().upper()
    d = (destination or "").strip().upper()
    dep_here = o in codes and o != ""
    arr_here = d in codes and d != ""
    if arr_here and dep_here:
        return "both"
    if arr_here:
        return "arrival"
    if dep_here:
        return "departure"
    return "overflight"


def movement_passes_filter(movement: str, movement_filter: str) -> bool:
    """
    movement_filter:
      - all: any traffic inside the geographic radius (including overflights)
      - airport_linked: arrival, departure, or both (exclude pure overflights)
      - arrival: destination is this airport (includes "both")
      - departure: origin is this airport (includes "both")
    """
    mf = movement_filter.strip().lower()
    if mf == "all":
        return True
    if mf == "airport_linked":
        return movement in ("arrival", "departure", "both")
    if mf == "arrival":
        return movement in ("arrival", "both")
    if mf == "departure":
        return movement in ("departure", "both")
    return True
