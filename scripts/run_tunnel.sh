#!/usr/bin/env bash
# Free public HTTPS URL for your local API (uses your home IP for FR24).
# Requires: brew install cloudflared
# Usage: ./scripts/run_tunnel.sh
# Then paste the printed https://*.trycloudflare.com URL into web/config.js → tunnelApiBaseUrl
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! command -v cloudflared >/dev/null 2>&1; then
  echo "Install cloudflared first: brew install cloudflared"
  exit 1
fi

if ! curl -sf http://127.0.0.1:8000/health >/dev/null 2>&1; then
  echo "Starting local API on http://127.0.0.1:8000 ..."
  python3 -m uvicorn api.main:app --host 127.0.0.1 --port 8000 &
  API_PID=$!
  sleep 2
  trap 'kill "${API_PID:-}" 2>/dev/null' EXIT INT TERM
fi

echo ""
echo "Cloudflare quick tunnel (free). Copy the https URL below into:"
echo "  web/config.js  →  tunnelApiBaseUrl: \"https://....trycloudflare.com\""
echo "Then redeploy Vercel (or refresh local web) for live FR24 data on the public frontend."
echo ""

cloudflared tunnel --url http://127.0.0.1:8000
