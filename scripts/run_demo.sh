#!/usr/bin/env bash
# Local demo — no Docker. From repo root: ./scripts/run_demo.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

API_PORT="${API_PORT:-8000}"
WEB_PORT="${WEB_PORT:-8080}"
API_PID=""
WEB_PID=""
STARTED_API=0
STARTED_WEB=0
LOCAL_CONFIG="$ROOT/web/config.local.js"

if ! python3 -c "import fastapi, uvicorn, FlightRadar24" 2>/dev/null; then
  echo "Installing Python dependencies (first run only)..."
  "$ROOT/scripts/install_deps.sh"
fi

port_in_use() {
  lsof -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1
}

api_healthy() {
  curl -sf "http://127.0.0.1:$1/health" >/dev/null 2>&1
}

find_free_port() {
  local port="$1"
  while port_in_use "$port"; do
    port=$((port + 1))
  done
  echo "$port"
}

write_local_config() {
  cat >"$LOCAL_CONFIG" <<EOF
window.APP_CONFIG = {
  apiBaseUrl: "http://127.0.0.1:${API_PORT}",
};
EOF
}

cleanup() {
  if [[ "$STARTED_API" -eq 1 && -n "${API_PID:-}" ]]; then
    kill "$API_PID" 2>/dev/null || true
  fi
  if [[ "$STARTED_WEB" -eq 1 && -n "${WEB_PID:-}" ]]; then
    kill "$WEB_PID" 2>/dev/null || true
  fi
  if [[ -f "$LOCAL_CONFIG" && "${LOCAL_CONFIG_CREATED:-0}" -eq 1 ]]; then
    rm -f "$LOCAL_CONFIG"
  fi
}
trap cleanup EXIT INT TERM

# --- API ---
if api_healthy "$API_PORT"; then
  echo "API  → http://127.0.0.1:${API_PORT}  (already running, reusing)"
elif ! port_in_use "$API_PORT"; then
  echo "API  → http://127.0.0.1:${API_PORT}  (docs: /docs)"
  python3 -m uvicorn api.main:app --host 127.0.0.1 --port "$API_PORT" &
  API_PID=$!
  STARTED_API=1
  for _ in $(seq 1 20); do
    if api_healthy "$API_PORT"; then
      break
    fi
    sleep 0.25
  done
  if ! api_healthy "$API_PORT"; then
    echo "ERROR: API failed to start on port ${API_PORT}."
    exit 1
  fi
else
  if api_healthy 8000; then
    API_PORT=8000
    echo "API  → http://127.0.0.1:8000  (already running, reusing)"
  else
    NEW_PORT="$(find_free_port "$((API_PORT + 1))")"
    echo "Port ${API_PORT} is busy (Docker or old server?). Starting API on ${NEW_PORT} ..."
    echo "Tip: free ports with  docker compose down  or  lsof -i :8000"
    API_PORT="$NEW_PORT"
    python3 -m uvicorn api.main:app --host 127.0.0.1 --port "$API_PORT" &
    API_PID=$!
    STARTED_API=1
    for _ in $(seq 1 20); do
      if api_healthy "$API_PORT"; then
        break
      fi
      sleep 0.25
    done
    if ! api_healthy "$API_PORT"; then
      echo "ERROR: API failed to start on port ${API_PORT}."
      exit 1
    fi
    write_local_config
    LOCAL_CONFIG_CREATED=1
    echo "API  → http://127.0.0.1:${API_PORT}"
  fi
fi

if [[ "$API_PORT" != "8000" ]]; then
  write_local_config
  LOCAL_CONFIG_CREATED=1
fi

# --- Web ---
if port_in_use "$WEB_PORT"; then
  OLD_WEB="$WEB_PORT"
  WEB_PORT="$(find_free_port "$((WEB_PORT + 1))")"
  echo "Port ${OLD_WEB} is busy — web UI on http://127.0.0.1:${WEB_PORT}"
else
  echo "Web  → http://127.0.0.1:${WEB_PORT}"
fi

python3 -m http.server "$WEB_PORT" --directory web &
WEB_PID=$!
STARTED_WEB=1
sleep 0.5

if ! port_in_use "$WEB_PORT"; then
  echo "ERROR: Web server failed to start on port ${WEB_PORT}."
  exit 1
fi

echo ""
echo "Open http://127.0.0.1:${WEB_PORT} and search PVD / JFK / LAX"
echo "Press Ctrl+C to stop"
wait
