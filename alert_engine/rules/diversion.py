from __future__ import annotations

from typing import Any, Dict

from config import EngineConfig
from models.flight import Flight


def check_diversion(flight: Flight, _config: EngineConfig) -> Dict[str, Any]:
    """
    Placeholder: diversion / holding detection needs status + trail from FR24 details.
    Extend here when you add enriched flight state.
    """
    return {"matched": False, "score": 0, "reason": None}
