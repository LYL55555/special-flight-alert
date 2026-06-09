#!/usr/bin/env bash
# Stop local demo processes and optional Docker stack using ports 8000/8080.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "Stopping Docker stack (if any)..."
docker compose down 2>/dev/null || true

for port in 8000 8080; do
  pids=$(lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)
  if [[ -n "$pids" ]]; then
    echo "Killing process(es) on port ${port}: ${pids}"
    kill $pids 2>/dev/null || true
  fi
done

rm -f "$ROOT/web/config.local.js"
echo "Ports 8000 and 8080 should be free now."
