"""Alert engine settings. Adjust airports, radii, and scoring here."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, FrozenSet, Tuple


def _default_alerts_csv_path() -> str:
    # New schema (local times, schedule source); avoids appending onto pre-v2 CSV columns.
    return str(Path.home() / "Downloads" / "rare_flight_alerts_local.csv")


def _default_schedule_snapshot_xlsx_path() -> str:
    # Latest qualifying snapshot (score ≥ threshold) for Excel + Telegram diff; under alert_engine/data/.
    return str(Path(__file__).resolve().parent / "data" / "schedule_qualifying_snapshot.xlsx")


@dataclass(frozen=True)
class EngineConfig:
    # IATA or ICAO per airport code accepted by FlightRadar24API.get_airport
    airports: Tuple[str, ...] = ("PVD",)
    # schedule_24h: airport arrivals/departures boards, next schedule_horizon_hours
    #   (no geographic radius — every row is a scheduled arr/dep at that airport, not "overhead traffic")
    # live: aircraft currently inside radius_meters of each airport
    scan_mode: str = "schedule_24h"
    schedule_horizon_hours: float = 24.0
    schedule_max_pages: int = 12
    # Radius around each airport center (meters): used ONLY when scan_mode == "live".
    # Ignored for schedule_24h. This is NOT the same as "only arrivals" — see movement_filter.
    radius_meters: float = 80_000.0
    # Which flights to keep after geographic fetch:
    #   all — everything in the radius (including overflights)
    #   airport_linked — origin OR destination is this airport (arrival, departure, or both)
    #   arrival — destination is this airport (turnarounds count)
    #   departure — origin is this airport (turnarounds count)
    movement_filter: str = "airport_linked"
    # Minimum total score to emit an alert
    alert_min_score: int = 50
    # Poll interval when running as a daemon (--loop), e.g. 14400 = every 4 hours
    poll_interval_seconds: int = 60
    # Skip re-alerting same aircraft for this many seconds (per reason fingerprint)
    dedupe_ttl_seconds: int = 3600
    # Night penalty: local hour in [start, end) — half-open, wraps past midnight if start > end
    night_penalty: int = -15
    night_hours: Tuple[int, int] = (3, 6)  # 03:00–05:59 local
    # Append-only alert log (default: your macOS Downloads folder)
    alerts_csv_path: str = field(default_factory=_default_alerts_csv_path)
    # Overwritten each run: all flights with total score ≥ alert_min_score (before dedupe), for diff / Excel
    schedule_snapshot_xlsx_path: str = field(
        default_factory=_default_schedule_snapshot_xlsx_path
    )
    # Call FR24 flight-details once per alerting flight (fills ETA/ETD when API provides them)
    fetch_details_on_alert: bool = True
    # ICAO aircraft type codes (and common aliases) considered "rare"
    rare_aircraft_codes: FrozenSet[str] = field(
        default_factory=lambda: frozenset(
            {
                "B741",
                "B742",
                "B743",
                "B744",
                "B748",
                "B74S",
                "BLCF",
                "A342",
                "A343",
                "A345",
                "A346",
                "A388",
                "A124",
                "A225",
                "A306",
                "AN12",
                "AN22",
                "AN24",
                "AN26",
                "AN32",
                "AN72",
                "AN74",
                "A3ST",
                "C17",
                "C5M",
                "K35R",
                "K35E",
                "C30J",
                "C295",
                "A400",
                "IL76",
                "C135",
            }
        )
    )
    score_rare_type: int = 50
    score_special_livery: int = 50
    score_military: int = 50
    military_operator_icao: FrozenSet[str] = field(
        default_factory=lambda: frozenset({"RCH", "CNV", "EVAC", "NAF", "IAM", "RRR"})
    )


DEFAULT_CONFIG = EngineConfig()
