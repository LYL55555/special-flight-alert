#!/usr/bin/env bash
# Install all Python deps from repo root (API + vendored FR24 SDK).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -d python ]]; then
  echo "Missing ./python — run this from the FlightRadarAPI repo root after git clone."
  exit 1
fi

echo "Installing from $ROOT/requirements.txt ..."
pip install -r requirements.txt

if [[ -f mcp_server/requirements.txt ]]; then
  echo "Installing MCP extras ..."
  pip install -r mcp_server/requirements.txt
fi

echo "Done."
