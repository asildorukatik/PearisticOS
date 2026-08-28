#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/appleos"
TOKEN_FILE="$CONFIG_DIR/bridge-token"
LOG_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/appleos"
mkdir -p "$LOG_DIR"

"$ROOT/bridge/install-bridge.sh" >/dev/null
TOKEN="$(tr -d '\r\n' < "$TOKEN_FILE")"

BRIDGE_PID=""
HTTP_PID=""
cleanup() {
  [[ -n "$BRIDGE_PID" ]] && kill "$BRIDGE_PID" >/dev/null 2>&1 || true
  [[ -n "$HTTP_PID" ]] && kill "$HTTP_PID" >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

APPLEOS_BRIDGE_TOKEN="$TOKEN" \
APPLEOS_ALLOWED_ORIGINS="http://127.0.0.1:4173,http://localhost:4173" \
python3 "$ROOT/bridge/appleos_bridge.py" >"$LOG_DIR/bridge.log" 2>&1 &
BRIDGE_PID=$!

(
  cd "$ROOT"
  python3 -m http.server 4173 --bind 127.0.0.1 >"$LOG_DIR/http.log" 2>&1
) &
HTTP_PID=$!

sleep 0.7
ENCODED_TOKEN="$(python3 - "$TOKEN" <<'PY'
from urllib.parse import quote
import sys
print(quote(sys.argv[1], safe=''))
PY
)"
URL="http://127.0.0.1:4173/#bridgeToken=$ENCODED_TOKEN"
PROFILE="${XDG_CACHE_HOME:-$HOME/.cache}/appleos/chromium-profile"
mkdir -p "$PROFILE"

launch_chromium() {
  local browser="$1"
  "$browser" \
    --user-data-dir="$PROFILE" \
    --app="$URL" \
    --start-fullscreen \
    --no-first-run \
    --disable-session-crashed-bubble \
    --class=AppleOS
}

for browser in chromium chromium-browser google-chrome google-chrome-stable brave-browser; do
  if command -v "$browser" >/dev/null 2>&1; then
    launch_chromium "$browser"
    exit $?
  fi
done

if command -v firefox >/dev/null 2>&1; then
  firefox --kiosk "$URL"
  exit $?
fi

if command -v xdg-open >/dev/null 2>&1; then
  echo "No Chromium/Firefox kiosk executable found; opening AppleOS in the default browser."
  xdg-open "$URL"
  echo "Keep this terminal open while AppleOS is running. Press Ctrl+C to stop the local server."
  wait "$HTTP_PID"
  exit 0
fi

echo "No supported browser launcher found." >&2
exit 1
