"""Format UTC datetimes as local wall time using IANA name or FR24 offset seconds."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional


def format_local(
    dt: Optional[datetime],
    tz_name: Optional[str] = None,
    offset_seconds: Optional[int] = None,
) -> str:
    if dt is None:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    if tz_name:
        try:
            from zoneinfo import ZoneInfo

            loc = dt.astimezone(ZoneInfo(tz_name))
            abbr = loc.tzname() or ""
            return loc.strftime(f"%Y-%m-%d %H:%M:%S ({abbr})")
        except Exception:
            pass
    if offset_seconds is not None:
        tz = timezone(timedelta(seconds=int(offset_seconds)))
        loc = dt.astimezone(tz)
        return loc.strftime("%Y-%m-%d %H:%M:%S %z")
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def now_local_string(tz_name: Optional[str], offset_seconds: Optional[int]) -> str:
    return format_local(datetime.now(timezone.utc), tz_name, offset_seconds)
