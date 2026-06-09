"""Aircraft photo lookup helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import requests


PLANESPOTTERS_API_BASE = "https://api.planespotters.net/pub/photos/reg"
PLANESPOTTERS_USER_AGENT = os.environ.get(
    "PLANESPOTTERS_USER_AGENT",
    "SpecialFlightWatch/0.1 (+https://github.com/LYL55555/special-flight-alert)",
)


@dataclass(frozen=True)
class AircraftPhoto:
    image_url: str
    page_url: str | None = None
    source: str = "planespotters"
    photographer: str | None = None


def _best_photo_image(photo: dict[str, Any]) -> str | None:
    for key in ("thumbnail_large", "thumbnail"):
        block = photo.get(key)
        if not isinstance(block, dict):
            continue
        src = block.get("src")
        if isinstance(src, str) and src.startswith(("http://", "https://")):
            return src
    return None


def fetch_planespotters_photo(
    registration: str,
    *,
    timeout_seconds: float = 6.0,
) -> AircraftPhoto | None:
    reg = (registration or "").strip().upper()
    if not reg:
        return None

    response = requests.get(
        f"{PLANESPOTTERS_API_BASE}/{reg}",
        headers={"User-Agent": PLANESPOTTERS_USER_AGENT},
        timeout=timeout_seconds,
    )
    response.raise_for_status()
    payload = response.json()
    photos = payload.get("photos") if isinstance(payload, dict) else None
    if not isinstance(photos, list):
        return None

    for photo in photos:
        if not isinstance(photo, dict):
            continue
        image_url = _best_photo_image(photo)
        if not image_url:
            continue
        link = photo.get("link")
        photographer = photo.get("photographer")
        return AircraftPhoto(
            image_url=image_url,
            page_url=link if isinstance(link, str) else None,
            photographer=photographer if isinstance(photographer, str) else None,
        )
    return None
