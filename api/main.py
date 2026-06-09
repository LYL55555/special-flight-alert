from __future__ import annotations

import asyncio
import copy
import logging
import os
import sys
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator, Deque

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware


ROOT = Path(__file__).resolve().parents[1]
ENGINE_DIR = ROOT / "alert_engine"
SDK_DIR = ROOT / "python"
for path in (ENGINE_DIR, SDK_DIR):
    s = str(path)
    if s not in sys.path:
        sys.path.insert(0, s)

from services.airport_scan import (  # noqa: E402
    AirportScanError,
    InvalidAirportCodeError,
    load_default_livery_db,
    normalize_airport_code,
    scan_airport_once,
)


APP_NAME = "Special Flight Alert API"
logger = logging.getLogger(__name__)
FALLBACK_MESSAGE = (
    "Live FlightRadar24 data is temporarily unavailable. Please try again later."
)
SCAN_TIMEOUT_SECONDS = float(os.environ.get("SCAN_TIMEOUT_SECONDS", "30"))
CACHE_TTL_SECONDS = int(os.environ.get("SCAN_CACHE_TTL_SECONDS", "300"))
RATE_LIMIT_PER_MINUTE = int(os.environ.get("SCAN_RATE_LIMIT_PER_MINUTE", "3"))
ALLOWED_ORIGINS = [
    item.strip()
    for item in os.environ.get("ALLOWED_ORIGINS", "*").split(",")
    if item.strip()
]

_cache: dict[str, tuple[float, dict[str, Any]]] = {}
_rate_buckets: dict[str, Deque[float]] = defaultdict(deque)
_livery_db: dict | None = None


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    global _livery_db
    _livery_db = load_default_livery_db()
    yield


app = FastAPI(title=APP_NAME, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _client_key(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",", 1)[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def _check_rate_limit(key: str) -> None:
    if RATE_LIMIT_PER_MINUTE <= 0:
        return
    now = time.monotonic()
    bucket = _rate_buckets[key]
    while bucket and now - bucket[0] > 60:
        bucket.popleft()
    if len(bucket) >= RATE_LIMIT_PER_MINUTE:
        raise HTTPException(
            status_code=429,
            detail="Too many scan requests. Please wait a minute and try again.",
        )
    bucket.append(now)


def _cached_result(code: str) -> dict[str, Any] | None:
    item = _cache.get(code)
    if item is None:
        return None
    created, payload = item
    age = int(time.monotonic() - created)
    if age > CACHE_TTL_SECONDS:
        _cache.pop(code, None)
        return None
    result = copy.deepcopy(payload)
    result["cached"] = True
    result["cache_age_seconds"] = age
    return result


def _store_cache(code: str, payload: dict[str, Any]) -> None:
    _cache[code] = (time.monotonic(), copy.deepcopy(payload))


def _scan_fallback(airport: str, exc: Exception) -> dict[str, Any]:
    logger.exception("Airport scan failed for %s", airport, exc_info=exc)
    return {
        "airport": airport.upper(),
        "status": "degraded",
        "source": "fallback",
        "message": FALLBACK_MESSAGE,
        "flights": [],
        "error": str(exc),
    }


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": "Special Flight Alert API",
        "docs": "/docs",
        "health": "/health",
        "scan": "/api/scan?airport=PVD",
    }


@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}


@app.get("/api/scan")
async def scan_airport(
    request: Request,
    airport: str = Query(...),
) -> dict[str, Any]:
    try:
        code = normalize_airport_code(airport)
    except InvalidAirportCodeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    _check_rate_limit(_client_key(request))

    cached = _cached_result(code)
    if cached is not None:
        return cached

    try:
        payload = await asyncio.wait_for(
            asyncio.to_thread(scan_airport_once, code, livery_db=_livery_db),
            timeout=SCAN_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError as exc:
        return _scan_fallback(code, exc)
    except InvalidAirportCodeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except AirportScanError as exc:
        return _scan_fallback(code, exc)
    except Exception as exc:
        return _scan_fallback(code, exc)

    _store_cache(code, payload)
    return payload
