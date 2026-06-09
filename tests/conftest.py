from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "alert_engine", ROOT / "python", ROOT):
    s = str(path)
    if s not in sys.path:
        sys.path.insert(0, s)
