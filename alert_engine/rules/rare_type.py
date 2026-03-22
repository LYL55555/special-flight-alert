from __future__ import annotations

from typing import Any, Dict

from config import EngineConfig
from models.flight import Flight


def check_rare_type(flight: Flight, config: EngineConfig) -> Dict[str, Any]:
    code = (flight.aircraft_type or "").strip().upper()
    if not code:
        return {"matched": False, "score": 0, "reason": None}
    if code in config.rare_aircraft_codes:
        return {
            "matched": True,
            "score": config.score_rare_type,
            "reason": f"Rare aircraft type: {code}",
        }
    return {"matched": False, "score": 0, "reason": None}
