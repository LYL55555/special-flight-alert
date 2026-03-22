#!/usr/bin/env bash
# PVD-only schedule poll (used by launchd). Loads .env from alert_engine/.
set -euo pipefail
ALERT_ENGINE_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ALERT_ENGINE_ROOT"
exec .venv/bin/python main.py --airports PVD
