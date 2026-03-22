"""Minimal Telegram sender (token + chat_id from environment)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import requests

from alerts.scorer import AlertExtras
from models.flight import Flight


def _env(name: str) -> str:
    return (os.environ.get(name) or "").strip()


class TelegramNotifier:
    def __init__(self, token: Optional[str] = None, chat_id: Optional[str] = None) -> None:
        self.token = token or _env("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or _env("TELEGRAM_CHAT_ID")

    @classmethod
    def from_env(cls) -> Optional["TelegramNotifier"]:
        t, c = _env("TELEGRAM_BOT_TOKEN"), _env("TELEGRAM_CHAT_ID")
        if not t or not c:
            return None
        return cls(token=t, chat_id=c)

    def enabled(self) -> bool:
        return bool(self.token and self.chat_id)

    def send(self, message: str) -> bool:
        if not self.enabled():
            return False
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        try:
            r = requests.post(
                url,
                data={"chat_id": self.chat_id, "text": message},
                timeout=30,
            )
            r.raise_for_status()
            return True
        except requests.RequestException:
            return False

    def send_document(self, path: str | Path, caption: str = "") -> bool:
        if not self.enabled():
            return False
        p = Path(path)
        if not p.is_file():
            return False
        url = f"https://api.telegram.org/bot{self.token}/sendDocument"
        try:
            with p.open("rb") as f:
                files = {"document": (p.name, f)}
                data: dict = {"chat_id": self.chat_id}
                if caption:
                    data["caption"] = caption[:1024]
                r = requests.post(url, data=data, files=files, timeout=120)
            r.raise_for_status()
            return True
        except (OSError, requests.RequestException):
            return False

    def send_long_text(self, message: str, max_len: int = 4096) -> bool:
        """Split on newlines so each Telegram message stays under the API limit (no omission)."""
        if not self.enabled():
            return False
        if not message:
            return True
        chunks: list[str] = []
        buf: list[str] = []
        size = 0
        for line in message.split("\n"):
            if len(line) > max_len:
                if buf:
                    chunks.append("\n".join(buf))
                    buf = []
                    size = 0
                for i in range(0, len(line), max_len):
                    chunks.append(line[i : i + max_len])
                continue
            extra = len(line) + (1 if buf else 0)
            if size + extra > max_len and buf:
                chunks.append("\n".join(buf))
                buf = [line]
                size = len(line)
            else:
                buf.append(line)
                size += extra
        if buf:
            chunks.append("\n".join(buf))
        for c in chunks:
            if not self.send(c):
                return False
        return True


def format_special_livery_alert(
    flight: Flight,
    score: int,
    reasons: list[str],
    extras: AlertExtras,
) -> str:
    """Readable single-flight block (spec §5)."""
    spot = flight.spot_time_local_display() or "—"
    mv = (flight.movement or "—").strip()
    reg = flight.registration or "?"
    ac = flight.aircraft_type or "?"
    orig = flight.origin or "?"
    dest = flight.destination or "?"
    liv = (extras.livery_name or "").strip()
    if not liv:
        for r in reasons:
            if r.startswith("Special livery:"):
                liv = r.replace("Special livery:", "").strip()
                break
    liv = liv or "—"
    lines = [
        "🚨 SPECIAL LIVERY ALERT",
        f"Spot time：{spot}",
        f"Movement：{mv}",
        f"Aircraft: {reg} ({ac})",
        f"Livery description：{liv}",
        f"Route: {orig} → {dest}",
        f"Score: {score}",
        "Reason:",
    ]
    for r in reasons:
        lines.append(f"- {r}")
    return "\n".join(lines)
