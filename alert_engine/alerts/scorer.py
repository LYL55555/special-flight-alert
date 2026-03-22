from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from config import EngineConfig
from models.flight import Flight
from rules.diversion import check_diversion
from rules.military import check_military_operator
from rules.rare_type import check_rare_type
from rules.special_livery import check_special_livery


@dataclass
class AlertExtras:
    livery_name: str = ""
    livery_airline: str = ""
    livery_description: str = ""


def in_night_window(hour: int, start: int, end: int) -> bool:
    if start <= end:
        return start <= hour < end
    return hour >= start or hour < end


def score_flight(
    flight: Flight,
    config: EngineConfig,
    livery_db: dict,
) -> Tuple[int, List[str], AlertExtras]:
    checks: List[Dict[str, Any]] = [
        check_rare_type(flight, config),
        check_special_livery(flight, config, livery_db),
        check_military_operator(flight, config),
        check_diversion(flight, config),
    ]
    total = 0
    reasons: List[str] = []
    extras = AlertExtras()
    for r in checks:
        if r["matched"]:
            total += r["score"]
            reason = r.get("reason")
            if reason:
                reasons.append(reason)
            if r.get("livery_name"):
                extras.livery_name = str(r["livery_name"])
            if r.get("livery_airline"):
                extras.livery_airline = str(r["livery_airline"])
            if r.get("livery_description"):
                extras.livery_description = str(r["livery_description"])
    hour = time.localtime().tm_hour
    if in_night_window(hour, config.night_hours[0], config.night_hours[1]):
        total += config.night_penalty
        if config.night_penalty != 0:
            reasons.append(
                f"Local night window ({config.night_hours[0]}–{config.night_hours[1]}h): {config.night_penalty}"
            )
    return total, reasons, extras
