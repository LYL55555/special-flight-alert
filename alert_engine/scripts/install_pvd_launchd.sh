#!/usr/bin/env bash
# Installs a LaunchAgent: PVD scan at local 00:00, 06:00, 12:00, 18:00 daily.
set -euo pipefail
ALERT_ENGINE_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LABEL="com.flightradar.alertengine.pvd"
PLIST_DEST="${HOME}/Library/LaunchAgents/${LABEL}.plist"
RUNNER="${ALERT_ENGINE_ROOT}/scripts/run_pvd_scan.sh"
LOG_DIR="${ALERT_ENGINE_ROOT}/logs"
OUT_LOG="${LOG_DIR}/launchd-pvd.out.log"
ERR_LOG="${LOG_DIR}/launchd-pvd.err.log"

mkdir -p "$LOG_DIR"
chmod +x "${ALERT_ENGINE_ROOT}/scripts/run_pvd_scan.sh"

if [[ ! -x "${ALERT_ENGINE_ROOT}/.venv/bin/python" ]]; then
  echo "Missing venv: ${ALERT_ENGINE_ROOT}/.venv/bin/python — run: cd \"${ALERT_ENGINE_ROOT}\" && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt" >&2
  exit 1
fi

if [[ -f "$PLIST_DEST" ]]; then
  launchctl unload "$PLIST_DEST" 2>/dev/null || true
fi

cat > "$PLIST_DEST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>${LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>${RUNNER}</string>
  </array>
  <key>StartCalendarInterval</key>
  <array>
    <dict>
      <key>Hour</key><integer>0</integer>
      <key>Minute</key><integer>0</integer>
    </dict>
    <dict>
      <key>Hour</key><integer>6</integer>
      <key>Minute</key><integer>0</integer>
    </dict>
    <dict>
      <key>Hour</key><integer>12</integer>
      <key>Minute</key><integer>0</integer>
    </dict>
    <dict>
      <key>Hour</key><integer>18</integer>
      <key>Minute</key><integer>0</integer>
    </dict>
  </array>
  <key>StandardOutPath</key>
  <string>${OUT_LOG}</string>
  <key>StandardErrorPath</key>
  <string>${ERR_LOG}</string>
</dict>
</plist>
EOF

launchctl load "$PLIST_DEST"
echo "Installed ${PLIST_DEST}"
echo "Schedule: daily at 00:00, 06:00, 12:00, 18:00 (system local time)"
echo "Logs: ${OUT_LOG} / ${ERR_LOG}"
echo "Unload: launchctl unload ~/Library/LaunchAgents/${LABEL}.plist"
