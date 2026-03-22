#!/usr/bin/env python3
"""
Rare flight alert engine — poll FlightRadar24 near configured airports, score, notify.
Run from this directory:

  pip install -r requirements.txt
  python main.py              # single poll (default: next 24h schedule boards)
  python main.py --live       # live traffic in radius around airport
  python main.py --loop       # repeat every poll_interval_seconds (override: --poll-seconds 14400)

  Default outputs: alert data/{AIRPORT}/alerts_{AP}_{timestamp}.csv and snapshot_{AP}_{timestamp}.xlsx
  Legacy single-file mode: pass --output path.csv (disables per-airport layout)
  Telegram: TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID in .env; optional TELEGRAM_EACH_ALERT=1
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from dataclasses import replace
from datetime import timezone
from pathlib import Path
from typing import List, NamedTuple, Optional, Tuple

from dotenv import load_dotenv
from FlightRadar24 import FlightRadar24API

from alerts.dedupe import Deduper
from alerts.notifier import send_alert
from alerts.scorer import AlertExtras, score_flight
from alerts.run_paths import AlertRunPaths
from alerts.snapshot_report import (
    format_digest_line,
    qualifying_rows,
    sort_row_dicts_for_display,
    update_single_snapshot,
    update_snapshots_by_airport,
)
from alerts.telegram_notifier import TelegramNotifier, format_special_livery_alert
from config import DEFAULT_CONFIG, EngineConfig
from data_sources.details import enrich_flight_from_fr24_details
from data_sources.flights_api import load_live_flights
from data_sources.schedule_api import load_schedules_multi_airport
from models.flight import Flight
from rules.special_livery import load_livery_db


def _root() -> Path:
    return Path(__file__).resolve().parent


class CycleOutcome(NamedTuple):
    """emitted = passed dedupe and written to CSV; qualifying = all score ≥ threshold."""

    emitted_count: int
    qualifying: List[Tuple[Flight, int, List[str], AlertExtras]]
    emitted: List[Tuple[Flight, int, List[str], AlertExtras]]


def _load_flights(
    fr_api: FlightRadar24API,
    config: EngineConfig,
    airport_filter: Optional[Tuple[str, ...]],
    *,
    live_fetch_details: bool = False,
) -> List[Flight]:
    if config.scan_mode == "live":
        # Optional: one clickhandler per aircraft — fills airline full name for operator "(…)" livery.
        # FR24 may return 402 without a suitable data subscription; default off so --live still runs.
        return load_live_flights(
            fr_api,
            config=config,
            airport_filter=airport_filter,
            fetch_details=live_fetch_details,
        )
    return load_schedules_multi_airport(
        fr_api,
        config=config,
        airport_filter=airport_filter,
        hours=config.schedule_horizon_hours,
    )


def _spot_sort_key(f: Flight) -> tuple:
    """Departure → dep time; arrival → arr time; missing time sorts last."""
    t = f.spot_time_for_sort()
    if t is None:
        return (1, float("inf"), f.monitored_airport or "", f.leg_signature())
    if t.tzinfo is None:
        t = t.replace(tzinfo=timezone.utc)
    return (0, t.timestamp(), f.monitored_airport or "", f.leg_signature())


def run_cycle(
    fr_api: FlightRadar24API,
    config: EngineConfig,
    livery_db: dict,
    deduper: Deduper,
    *,
    airport_filter: Optional[Tuple[str, ...]] = None,
    live_fetch_details: bool = False,
    run_paths: Optional[AlertRunPaths] = None,
) -> CycleOutcome:
    flights = _load_flights(
        fr_api, config, airport_filter, live_fetch_details=live_fetch_details
    )
    qualifying: List[tuple[Flight, int, List[str], AlertExtras]] = []
    for flight in flights:
        total, reasons, extras = score_flight(flight, config, livery_db)
        if total < config.alert_min_score:
            continue
        qualifying.append((flight, total, reasons, extras))

    pending: List[tuple[Flight, int, List[str], AlertExtras]] = []
    for flight, total, reasons, extras in qualifying:
        if not deduper.should_emit(flight, reasons):
            continue
        if config.fetch_details_on_alert and flight.fr24_id:
            try:
                enrich_flight_from_fr24_details(fr_api, flight)
            except Exception:
                pass
        pending.append((flight, total, reasons, extras))
    pending.sort(key=lambda row: _spot_sort_key(row[0]))
    for flight, total, reasons, extras in pending:
        send_alert(flight, total, reasons, config, extras, run_paths=run_paths)
    return CycleOutcome(len(pending), qualifying, pending)


_EN_MONTH = (
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
)


def _digest_send_stamp() -> str:
    """e.g. 2026Mar22-00:00EST — English month, local wall + TZ abbr."""
    from datetime import datetime

    dt = datetime.now().astimezone()
    mon = _EN_MONTH[dt.month - 1]
    tz = dt.tzname() or dt.strftime("%Z")
    return f"{dt.year}{mon}{dt.day}-{dt.strftime('%H:%M')}{tz}"


def _airports_display_label(
    airport_filter: Optional[Tuple[str, ...]],
    qualifying: List[Tuple[Flight, int, List[str], AlertExtras]],
) -> str:
    if airport_filter:
        return ", ".join(airport_filter)
    codes = sorted(
        {(f.monitored_airport or "UNK").strip().upper() for f, _, _, _ in qualifying}
    )
    return ", ".join(codes) if codes else "UNK"


def _format_digest_text(
    config: EngineConfig,
    airports_label: str,
    send_stamp: str,
    n_expired: int,
    n_new: int,
    expired_lines: List[str],
    new_lines: List[str],
    current_lines: List[str],
    qualifying_n: int,
) -> str:
    def section(title: str, count: int, lines: List[str]) -> str:
        if not lines:
            body = "- (none)"
        else:
            body = "\n".join(f"- {x}" for x in lines)
        return f"{title} ({count}):\n{body}"

    return (
        f"📊 {airports_label} Special Flights - {send_stamp}\n"
        f"Horizon: ~{config.schedule_horizon_hours}h | mode: {config.scan_mode}\n"
        f"Current qualifying flights: {qualifying_n}\n\n"
        f"{section('expired', n_expired, expired_lines)}\n\n"
        f"{section('new', n_new, new_lines)}\n\n"
        f"{section('current', qualifying_n, current_lines)}"
    )


def _run_telegram_post_cycle(
    notifier: TelegramNotifier,
    config: EngineConfig,
    outcome: CycleOutcome,
    n_exp: int,
    n_new: int,
    expired_lines: List[str],
    new_lines: List[str],
    qualifying_n: int,
    *,
    airports_label: str,
    current_lines: List[str],
    written_snapshots: List[Path],
) -> None:
    digest = _format_digest_text(
        config,
        airports_label,
        _digest_send_stamp(),
        n_exp,
        n_new,
        expired_lines,
        new_lines,
        current_lines,
        qualifying_n,
    )
    if not notifier.send_long_text(digest):
        print("Telegram sendMessage failed (check TELEGRAM_* env).", file=sys.stderr)
    for p in written_snapshots:
        if not notifier.send_document(p, caption=""):
            print(f"Telegram sendDocument failed: {p}", file=sys.stderr)

    if os.environ.get("TELEGRAM_EACH_ALERT", "").strip() in ("1", "true", "yes"):
        for flight, total, reasons, extras in outcome.emitted:
            if total < config.alert_min_score:
                continue
            msg = format_special_livery_alert(flight, total, reasons, extras)
            notifier.send(msg)


def _post_run_snapshots(
    config: EngineConfig,
    qualifying: List[Tuple[Flight, int, List[str], AlertExtras]],
    run_paths: Optional[AlertRunPaths],
) -> Tuple[int, int, List[str], List[str], int, List[Path]]:
    if run_paths is not None:
        return update_snapshots_by_airport(qualifying, config, run_paths)
    n_exp, n_new, el, nl, qn = update_single_snapshot(config, qualifying)
    return n_exp, n_new, el, nl, qn, [Path(config.schedule_snapshot_xlsx_path)]


def main() -> None:
    load_dotenv(_root() / ".env")
    load_dotenv()

    parser = argparse.ArgumentParser(description="Rare flight alerts (FlightRadar24)")
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Keep polling (interval from config.poll_interval_seconds)",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Use live traffic in radius (default: schedule boards for next 24h)",
    )
    parser.add_argument(
        "--live-details",
        action="store_true",
        help="With --live: fetch FR24 clickhandler per aircraft (operator/Livery text; slower; may require paid data access)",
    )
    parser.add_argument(
        "--hours",
        type=float,
        default=None,
        help="Schedule lookahead hours (default from config.schedule_horizon_hours)",
    )
    parser.add_argument(
        "--livery-csv",
        type=Path,
        default=None,
        help="Path to special_liveries.csv (default: ./db/special_liveries.csv)",
    )
    parser.add_argument(
        "--airports",
        type=str,
        default=None,
        help="Comma-separated IATA/ICAO codes, overrides config.airports (e.g. BOS or BOS,PVD)",
    )
    parser.add_argument(
        "--movement",
        type=str,
        default=None,
        choices=("all", "airport_linked", "arrival", "departure"),
        help="Override config.movement_filter",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Alert CSV path (default: ~/Downloads/rare_flight_alerts_local.csv)",
    )
    parser.add_argument(
        "--no-details",
        action="store_true",
        help="Do not call FR24 per-flight details (faster; flight number/times may be thinner)",
    )
    parser.add_argument(
        "--poll-seconds",
        type=int,
        default=None,
        help="With --loop: sleep interval in seconds (e.g. 14400 = every 4 hours)",
    )
    parser.add_argument(
        "--snapshot-xlsx",
        type=Path,
        default=None,
        help="Single-file snapshot path (only with --output legacy mode)",
    )
    args = parser.parse_args()
    config: EngineConfig = DEFAULT_CONFIG
    if args.live:
        config = replace(config, scan_mode="live")
    if args.hours is not None:
        config = replace(config, schedule_horizon_hours=args.hours)
    if args.movement:
        config = replace(config, movement_filter=args.movement)
    if args.output:
        config = replace(config, alerts_csv_path=str(args.output.expanduser().resolve()))
    if args.no_details:
        config = replace(config, fetch_details_on_alert=False)
    if args.snapshot_xlsx is not None:
        config = replace(
            config,
            schedule_snapshot_xlsx_path=str(args.snapshot_xlsx.expanduser().resolve()),
        )

    poll_seconds = (
        args.poll_seconds
        if args.poll_seconds is not None
        else config.poll_interval_seconds
    )

    airport_filter: Optional[Tuple[str, ...]] = None
    if args.airports:
        airport_filter = tuple(
            x.strip().upper() for x in args.airports.split(",") if x.strip()
        )
    csv_path = args.livery_csv or (_root() / "db" / "special_liveries.csv")
    livery_db = load_livery_db(csv_path)

    fr_api = FlightRadar24API()
    deduper = Deduper(config.dedupe_ttl_seconds)
    telegram = TelegramNotifier.from_env()

    def _one_cycle() -> None:
        run_ts = time.strftime("%Y-%m-%d_%H%M%S")
        run_paths: Optional[AlertRunPaths] = None
        if args.output is None:
            run_paths = AlertRunPaths(run_ts, _root() / "alert data")
        outcome = run_cycle(
            fr_api,
            config,
            livery_db,
            deduper,
            airport_filter=airport_filter,
            live_fetch_details=args.live_details,
            run_paths=run_paths,
        )
        n_exp, n_new, el, nl, qn, written = _post_run_snapshots(
            config, outcome.qualifying, run_paths
        )
        rows = qualifying_rows(
            outcome.qualifying, config, run_paths=run_paths
        )
        current_lines = [
            format_digest_line(r) for r in sort_row_dicts_for_display(rows)
        ]
        ap_label = _airports_display_label(airport_filter, outcome.qualifying)
        dest = (
            str(run_paths.root)
            if run_paths is not None
            else config.alerts_csv_path
        )
        print(
            f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] "
            f"emitted={outcome.emitted_count} qualifying={qn} -> {dest} | run={run_ts}",
            file=sys.stderr,
        )
        if telegram and telegram.enabled():
            _run_telegram_post_cycle(
                telegram,
                config,
                outcome,
                n_exp,
                n_new,
                el,
                nl,
                qn,
                airports_label=ap_label,
                current_lines=current_lines,
                written_snapshots=written,
            )
        elif os.environ.get("CI"):
            print(
                "Telegram: not configured (set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID "
                "in repo Settings → Secrets and variables → Actions).",
                file=sys.stderr,
            )

    if args.loop:
        while True:
            try:
                _one_cycle()
            except Exception as e:
                print(f"Poll error: {e}", file=sys.stderr)
            time.sleep(poll_seconds)
    else:
        _one_cycle()


if __name__ == "__main__":
    main()
