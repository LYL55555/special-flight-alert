from __future__ import annotations

from typing import Any, Dict

from config import EngineConfig
from models.flight import Flight


def check_military_operator(flight: Flight, config: EngineConfig) -> Dict[str, Any]:
    icao = (flight.airline_icao or "").strip().upper()
    if icao and icao in config.military_operator_icao:
        return {
            "matched": True,
            "score": config.score_military,
            "reason": f"Military operator ICAO: {icao}",
        }
    return {"matched": False, "score": 0, "reason": None}
