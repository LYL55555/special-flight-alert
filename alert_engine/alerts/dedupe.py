from __future__ import annotations

import time
from typing import Iterable, List

from models.flight import Flight


class Deduper:
    """Suppress repeat alerts for the same *leg* + reason set within TTL.

    Departure and arrival rows for the same tail are different legs (leg_signature).
    """

    def __init__(self, ttl_seconds: float) -> None:
        self.ttl_seconds = ttl_seconds
        self._last: dict[str, float] = {}

    @staticmethod
    def fingerprint(flight: Flight, reasons: Iterable[str]) -> str:
        leg = flight.leg_signature()
        r = "|".join(sorted(reasons))
        return f"{leg}::{r}"

    def should_emit(self, flight: Flight, reasons: List[str]) -> bool:
        key = self.fingerprint(flight, reasons)
        now = time.time()
        prev = self._last.get(key)
        if prev is not None and (now - prev) < self.ttl_seconds:
            return False
        self._last[key] = now
        return True
