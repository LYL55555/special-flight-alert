from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for sub in (ROOT / "alert_engine", ROOT / "python"):
    s = str(sub)
    if s not in sys.path:
        sys.path.insert(0, s)

from mcp.server.fastmcp import FastMCP  # noqa: E402

from services.airport_scan import (  # noqa: E402
    InvalidAirportCodeError,
    load_default_livery_db,
    scan_airport_once,
)

mcp = FastMCP("special-flight-alert")
_livery_cache: dict | None = None


def _get_livery_db() -> dict:
    global _livery_cache
    if _livery_cache is None:
        _livery_cache = load_default_livery_db()
    return _livery_cache


@mcp.tool()
def health_check() -> str:
    """Return API health status."""
    return json.dumps({"ok": True})


@mcp.tool()
def scan_airport(airport: str) -> str:
    """Scan an airport for special liveries and rare aircraft.

    Args:
        airport: 3- or 4-letter IATA/ICAO code, e.g. PVD, JFK, LAX.
    """
    try:
        payload = scan_airport_once(airport, livery_db=_get_livery_db())
        return json.dumps(payload, ensure_ascii=False, indent=2)
    except InvalidAirportCodeError as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False)
    except Exception as exc:
        return json.dumps(
            {
                "airport": airport.strip().upper(),
                "status": "degraded",
                "source": "fallback",
                "message": "FlightRadar24 request failed.",
                "flights": [],
                "error": str(exc),
            },
            ensure_ascii=False,
            indent=2,
        )


if __name__ == "__main__":
    mcp.run()
