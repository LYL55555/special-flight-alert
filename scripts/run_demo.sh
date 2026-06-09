#!/usr/bin/env bash
# Local demo — no Docker. From repo root: ./scripts/run_demo.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! python3 -c "import fastapi, uvicorn, FlightRadar24" 2>/dev/null; then
  echo "Installing Python dependencies (first run only)..."
  "$ROOT/scripts/install_deps.sh"
fi

cleanup() {
  kill "${API_PID:-}" "${WEB_PID:-}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "API  → http://127.0.0.1:8000  (docs: /docs)"
python3 -m uvicorn api.main:app --host 127.0.0.1 --port 8000 &
API_PID=$!
sleep 1

echo "Web  → http://127.0.0.1:8080  (auto-uses local API when opened in browser)"
(cd web && python3 -m http.server 8080) &
WEB_PID=$!

echo ""
echo "Open http://127.0.0.1:8080 and search PVD / JFK / LAX"
echo "Press Ctrl+C to stop"
wait
