#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/appleos"
TOKEN_FILE="$CONFIG_DIR/bridge-token"
APP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
DESKTOP_FILE="$APP_DIR/appleos.desktop"

mkdir -p "$CONFIG_DIR" "$APP_DIR"
chmod 700 "$CONFIG_DIR"

if [[ ! -s "$TOKEN_FILE" ]]; then
  python3 - "$TOKEN_FILE" <<'PY'
from pathlib import Path
import secrets
import sys
p = Path(sys.argv[1])
p.write_text(secrets.token_urlsafe(32) + "\n", encoding="utf-8")
PY
  chmod 600 "$TOKEN_FILE"
fi

python3 - "$ROOT" "$DESKTOP_FILE" <<'PY'
from pathlib import Path
import shlex
import sys
root = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2])
template = (root / "bridge/appleos.desktop.in").read_text(encoding="utf-8")
runner = root / "scripts/run-elementary-workspace.sh"
icon = root / "assets/icons/apple-logo-192.png"
text = template.replace("@APPLEOS_RUNNER@", shlex.quote(str(runner))).replace("@APPLEOS_ICON@", str(icon))
out.write_text(text, encoding="utf-8")
PY

chmod +x "$ROOT/scripts/run-elementary-workspace.sh" "$ROOT/bridge/install-bridge.sh"
command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$APP_DIR" >/dev/null 2>&1 || true

echo "AppleOS elementary integration installed."
echo "Launcher: $DESKTOP_FILE"
echo "Bridge token: $TOKEN_FILE"
