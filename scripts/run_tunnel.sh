#!/usr/bin/env bash
# Cloudflare Named Tunnel helper (not Quick Tunnel).
# Prerequisite: create tunnel "special-flight-alert-api" in Cloudflare Zero Trust
# and route flight-api.<your-domain> -> http://localhost:8000
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! command -v cloudflared >/dev/null 2>&1; then
  echo "Install cloudflared: brew install cloudflared"
  exit 1
fi

if ! curl -sf http://127.0.0.1:8000/health >/dev/null 2>&1; then
  echo "Starting local API on http://127.0.0.1:8000 ..."
  python3 -m uvicorn api.main:app --host 127.0.0.1 --port 8000 &
  API_PID=$!
  sleep 2
  trap 'kill "${API_PID:-}" 2>/dev/null' EXIT INT TERM
fi

CONFIG="${CLOUDFLARED_CONFIG:-$HOME/.cloudflared/config.yml}"
TUNNEL_NAME="${CLOUDFLARED_TUNNEL:-special-flight-alert-api}"

if [[ ! -f "$CONFIG" ]]; then
  echo "Missing $CONFIG"
  echo ""
  echo "Set up a Named Tunnel first:"
  echo "  1. Cloudflare Zero Trust -> Networks -> Tunnels -> Create tunnel"
  echo "  2. Name: special-flight-alert-api"
  echo "  3. Public hostname: flight-api.<your-domain> -> http://localhost:8000"
  echo "  4. Install connector token / config.yml to ~/.cloudflared/"
  echo ""
  echo "Then run: cloudflared tunnel run $TUNNEL_NAME"
  exit 1
fi

echo "Running named tunnel: $TUNNEL_NAME"
echo "Fixed API URL: https://flight-api.<your-domain> (set in web/config.js)"
cloudflared tunnel run "$TUNNEL_NAME"
