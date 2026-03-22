from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import List, Optional, TextIO

from alerts.run_paths import AlertRunPaths
from alerts.scorer import AlertExtras
from config import EngineConfig
from models.flight import Flight
from rules.rarity import rarity_tier


def format_alert_line(
    flight: Flight,
    score: int,
    reasons: List[str],
    extras: AlertExtras,
) -> str:
    op = (flight.operator or flight.airline_icao or "").strip()
    ac = flight.aircraft_type or "?"
    reg = flight.registration or "?"
    num = flight.flight_number or "?"
    ap = flight.monitored_airport or "?"
    mv = flight.movement or "?"
    liv = extras.livery_name or ""
    if not liv:
        for r in reasons:
            if r.startswith("Special livery:"):
                liv = r.replace("Special livery:", "").strip()
                break
    tloc = flight.row_local_times()
    time_bits = []
    if mv in ("arrival", "both") and (
        tloc["estimated_arrival_local"] or tloc["scheduled_arrival_local"]
    ):
        time_bits.append(
            "arr~"
            + (
                tloc["estimated_arrival_local"]
                or tloc["scheduled_arrival_local"]
            )
        )
    if mv in ("departure", "both") and (
        tloc["estimated_departure_local"] or tloc["scheduled_departure_local"]
    ):
        time_bits.append(
            "dep~"
            + (
                tloc["estimated_departure_local"]
                or tloc["scheduled_departure_local"]
            )
        )
    time_s = " ".join(time_bits)
    rarity = rarity_tier(score)
    spot = flight.spot_time_local_display()
    lead = f"[ALERT] {spot} | " if spot else "[ALERT] "
    head = f"{lead}{ap} {mv} | {op} {ac} {reg} {num}".strip()
    paint = f'paint="{liv}"' if liv else ""
    tail = f"score={score} rarity={rarity} | " + " | ".join(reasons)
    parts = [head, paint, time_s, tail]
    return " ".join(p for p in parts if p)


def send_alert(
    flight: Flight,
    score: int,
    reasons: List[str],
    config: EngineConfig,
    extras: AlertExtras,
    *,
    stream: Optional[TextIO] = None,
    run_paths: Optional[AlertRunPaths] = None,
) -> None:
    line = format_alert_line(flight, score, reasons, extras)
    out = stream or sys.stdout
    print(line, file=out)

    if run_paths is not None:
        path = run_paths.alerts_csv_path(flight.monitored_airport or "UNK")
    else:
        path = Path(config.alerts_csv_path)
        path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.is_file()
    tloc = flight.row_local_times()
    row = {
        "spot_time_local": flight.spot_time_local_display(),
        "monitored_airport": flight.monitored_airport or "",
        "movement": flight.movement or "",
        "source": flight.source,
        "flight_number": flight.flight_number or "",
        "registration": flight.registration or "",
        "aircraft_type": flight.aircraft_type or "",
        "operator": flight.operator or "",
        "airline_icao": flight.airline_icao or "",
        "origin": flight.origin or "",
        "destination": flight.destination or "",
        "scheduled_departure_local": tloc["scheduled_departure_local"],
        "estimated_departure_local": tloc["estimated_departure_local"],
        "scheduled_arrival_local": tloc["scheduled_arrival_local"],
        "estimated_arrival_local": tloc["estimated_arrival_local"],
        "departure_tz": tloc["departure_tz_label"],
        "arrival_tz": tloc["arrival_tz_label"],
        "livery_name": extras.livery_name,
        "livery_airline": extras.livery_airline,
        "livery_description": extras.livery_description,
        "score": score,
        "reasons": " | ".join(reasons),
        "fr24_id": flight.fr24_id or "",
        "schedule_row_id": flight.schedule_row_id or "",
    }
    fieldnames = list(row.keys())
    with path.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            w.writeheader()
        w.writerow(row)
