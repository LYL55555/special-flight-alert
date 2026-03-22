"""Per-run output layout: alert data/{AIRPORT}/alerts_{AP}_{ts}.csv etc."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class AlertRunPaths:
    """One polling run: timestamp slug + root ``alert data`` directory."""

    run_ts: str
    root: Path

    def airport_dir(self, airport: str) -> Path:
        ap = (airport or "UNK").strip().upper() or "UNK"
        d = self.root / ap
        d.mkdir(parents=True, exist_ok=True)
        return d

    def alerts_csv_path(self, airport: str) -> Path:
        ap = (airport or "UNK").strip().upper() or "UNK"
        return self.airport_dir(ap) / f"alerts_{ap}_{self.run_ts}.csv"

    def snapshot_latest_path(self, airport: str) -> Path:
        ap = (airport or "UNK").strip().upper() or "UNK"
        return self.airport_dir(ap) / f"snapshot_{ap}_latest.xlsx"

    def snapshot_run_path(self, airport: str) -> Path:
        ap = (airport or "UNK").strip().upper() or "UNK"
        return self.airport_dir(ap) / f"snapshot_{ap}_{self.run_ts}.xlsx"
