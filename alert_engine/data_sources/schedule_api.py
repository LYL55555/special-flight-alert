"""Airport schedule boards (arrivals / departures) for a rolling time window."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from FlightRadar24 import FlightRadar24API

from config import EngineConfig, DEFAULT_CONFIG
from data_sources.movement import movement_passes_filter
from models.flight import Flight


def _utc(ts: Any) -> datetime | None:
    if not isinstance(ts, int) or ts < 1_000_000_000:
        return None
    if ts > 1_000_000_000_000:
        ts //= 1000
    try:
        return datetime.fromtimestamp(ts, tz=timezone.utc)
    except (ValueError, OSError):
        return None


def _iata(airport_block: Any) -> Optional[str]:
    if not isinstance(airport_block, dict):
        return None
    code = airport_block.get("code")
    if isinstance(code, dict):
        v = (code.get("iata") or "").strip().upper()
        return v or None
    return None


def _tz_meta(airport_block: Any) -> Tuple[Optional[str], Optional[int]]:
    if not isinstance(airport_block, dict):
        return None, None
    tz = airport_block.get("timezone")
    if not isinstance(tz, dict):
        return None, None
    name = tz.get("name")
    name_s = str(name).strip() if name else None
    off = tz.get("offset")
    try:
        off_i = int(off) if off is not None else None
    except (TypeError, ValueError):
        off_i = None
    return name_s, off_i


def _flight_from_schedule_board_row(
    item: Dict[str, Any],
    *,
    movement: str,
    monitored_query_code: str,
) -> Optional[Flight]:
    f = item.get("flight")
    if not isinstance(f, dict):
        return None
    ident = f.get("identification") or {}
    if not isinstance(ident, dict):
        ident = {}
    num_block = ident.get("number") or {}
    fn = None
    if isinstance(num_block, dict):
        fn = (num_block.get("default") or num_block.get("alternative") or "").strip() or None
    frid = ident.get("id")
    fr24_id = str(frid) if frid else None
    row_id = ident.get("row")
    schedule_row_id = str(row_id) if row_id is not None else None

    ac = f.get("aircraft") or {}
    reg = None
    ac_code = None
    if isinstance(ac, dict):
        reg = (ac.get("registration") or "").strip().upper() or None
        model = ac.get("model") or {}
        if isinstance(model, dict):
            ac_code = (model.get("code") or "").strip().upper() or None

    al = f.get("airline") or {}
    icao = None
    op = None
    if isinstance(al, dict):
        codes = al.get("code") or {}
        if isinstance(codes, dict):
            icao = (codes.get("icao") or "").strip().upper() or None
        op = (al.get("name") or "").strip() or None

    ap = f.get("airport") or {}
    orig = dest = None
    otz_n = otz_o = dtz_n = dtz_o = None
    if isinstance(ap, dict):
        ob = ap.get("origin") or {}
        db = ap.get("destination") or {}
        orig = _iata(ob)
        dest = _iata(db)
        otz_n, otz_o = _tz_meta(ob)
        dtz_n, dtz_o = _tz_meta(db)

    time_block = f.get("time") if isinstance(f.get("time"), dict) else {}

    fl = Flight(
        flight_number=fn,
        registration=reg,
        aircraft_type=ac_code,
        operator=op,
        origin=orig,
        destination=dest,
        scheduled_arrival=None,
        estimated_arrival=None,
        scheduled_departure=None,
        estimated_departure=None,
        fr24_id=fr24_id,
        callsign=(ident.get("callsign") or "").strip() or None,
        airline_icao=icao,
        on_ground=None,
        monitored_airport=monitored_query_code.strip().upper(),
        movement=movement,
        origin_timezone_name=otz_n,
        destination_timezone_name=dtz_n,
        origin_timezone_offset=otz_o,
        destination_timezone_offset=dtz_o,
        schedule_row_id=schedule_row_id,
        source="schedule",
    )
    fl.apply_time_block(time_block)

    if movement == "arrival":
        fl.monitored_timezone_name = dtz_n
    else:
        fl.monitored_timezone_name = otz_n

    if not reg and not fn and not fr24_id:
        return None
    return fl


def _in_next_hours(
    flight: Flight,
    now: datetime,
    end: datetime,
) -> bool:
    if flight.movement == "arrival":
        anchor = (
            flight.scheduled_arrival
            or flight.estimated_arrival
            or flight.scheduled_departure
        )
    else:
        anchor = (
            flight.scheduled_departure
            or flight.estimated_departure
            or flight.scheduled_arrival
        )
    if anchor is None:
        return False
    return now <= anchor <= end


def load_schedule_next_hours(
    api: FlightRadar24API,
    airport_code: str,
    *,
    config: EngineConfig = DEFAULT_CONFIG,
    hours: Optional[float] = None,
) -> List[Flight]:
    horizon = hours if hours is not None else float(config.schedule_horizon_hours)
    now = datetime.now(timezone.utc)
    end = now + timedelta(hours=horizon)
    code = airport_code.strip().upper()

    r1 = api.get_airport_details(code, flight_limit=100, page=1)
    sched = (
        r1.get("airport", {})
        .get("pluginData", {})
        .get("schedule", {})
    )
    if not isinstance(sched, dict):
        return []

    arr_total = int((sched.get("arrivals") or {}).get("page", {}).get("total") or 1)
    dep_total = int((sched.get("departures") or {}).get("page", {}).get("total") or 1)
    max_pages = max(arr_total, dep_total, 1)
    max_pages = min(max_pages, config.schedule_max_pages)

    out: List[Flight] = []
    proc_arr = movement_passes_filter("arrival", config.movement_filter)
    proc_dep = movement_passes_filter("departure", config.movement_filter)

    def consume_response(resp: Dict[str, Any], p: int) -> None:
        s = (
            resp.get("airport", {})
            .get("pluginData", {})
            .get("schedule", {})
        )
        if not isinstance(s, dict):
            return
        arr = s.get("arrivals") or {}
        dep = s.get("departures") or {}

        if isinstance(arr, dict) and arr.get("page", {}).get("current") == p and proc_arr:
            for item in arr.get("data") or []:
                if not isinstance(item, dict):
                    continue
                fl = _flight_from_schedule_board_row(
                    item, movement="arrival", monitored_query_code=code
                )
                if fl is None:
                    continue
                if _in_next_hours(fl, now, end):
                    out.append(fl)

        if isinstance(dep, dict) and dep.get("page", {}).get("current") == p and proc_dep:
            for item in dep.get("data") or []:
                if not isinstance(item, dict):
                    continue
                fl = _flight_from_schedule_board_row(
                    item, movement="departure", monitored_query_code=code
                )
                if fl is None:
                    continue
                if _in_next_hours(fl, now, end):
                    out.append(fl)

    consume_response(r1, 1)

    for p in range(2, max_pages + 1):
        resp = api.get_airport_details(code, flight_limit=100, page=p)
        consume_response(resp, p)

    return out


def load_schedules_multi_airport(
    api: FlightRadar24API,
    *,
    config: EngineConfig = DEFAULT_CONFIG,
    airport_filter: Optional[Tuple[str, ...]] = None,
    hours: Optional[float] = None,
) -> List[Flight]:
    codes = airport_filter if airport_filter is not None else config.airports
    acc: List[Flight] = []
    for c in codes:
        acc.extend(load_schedule_next_hours(api, c, config=config, hours=hours))
    return acc
