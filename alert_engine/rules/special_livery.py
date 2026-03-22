from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any, Dict, Optional

from config import EngineConfig
from models.flight import Flight

_PAREN_GROUPS = re.compile(r"\(([^)]*)\)")


def _operator_livery_fields(operator: str) -> Optional[Dict[str, str]]:
    """
    FR24 等来源常在 airline 全称后加括号备注（含特殊涂装）。
    任意非空括号内容均视为涂装/备注标签；多个括号用 \" | \" 拼接。
    """
    s = operator.strip()
    if "(" not in s or ")" not in s:
        return None
    parts = [p.strip() for p in _PAREN_GROUPS.findall(s) if p.strip()]
    if not parts:
        return None
    inner = " | ".join(parts)
    base = _PAREN_GROUPS.sub("", s)
    base = re.sub(r"\s+", " ", base).strip()
    return {"livery_label": inner, "operator_base": base or s}


def _norm_tail(t: str) -> str:
    return t.strip().upper().replace("-", "").replace(" ", "")


def load_livery_db(csv_path: str | Path) -> Dict[str, Dict[str, str]]:
    path = Path(csv_path)
    out: Dict[str, Dict[str, str]] = {}
    if not path.is_file():
        return out
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw = row.get("tail_number") or row.get("tail") or ""
            key = _norm_tail(raw)
            if not key:
                continue
            out[key] = {
                "tail_number": raw.strip(),
                "airline": (row.get("airline") or "").strip(),
                "livery_name": (row.get("livery_name") or "").strip(),
                "description": (row.get("description") or "").strip(),
            }
    return out


def check_special_livery(
    flight: Flight,
    config: EngineConfig,
    livery_db: Dict[str, Dict[str, str]],
) -> Dict[str, Any]:
    op_raw = flight.operator
    if isinstance(op_raw, str) and op_raw.strip():
        fields = _operator_livery_fields(op_raw)
        if fields:
            label = fields["livery_label"]
            return {
                "matched": True,
                "score": config.score_special_livery,
                "reason": f"Special livery: {label}",
                "livery_name": label,
                "livery_airline": fields["operator_base"],
                "livery_description": op_raw.strip(),
            }

    reg = flight.registration
    if not reg:
        return {"matched": False, "score": 0, "reason": None}
    key = _norm_tail(reg)
    row = livery_db.get(key)
    if not row:
        return {"matched": False, "score": 0, "reason": None}
    label = row.get("livery_name") or row.get("description") or key
    return {
        "matched": True,
        "score": config.score_special_livery,
        "reason": f"Special livery: {label}",
        "livery_name": row.get("livery_name") or "",
        "livery_airline": row.get("airline") or "",
        "livery_description": row.get("description") or "",
    }
