#!/usr/bin/env python3
from __future__ import annotations

import configparser
import hmac
import json
import os
import re
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable, Iterable
from urllib.parse import unquote, urlparse

HOST = "127.0.0.1"
PORT = int(os.environ.get("APPLEOS_BRIDGE_PORT", "8765"))
DEFAULT_APP_DIRS = [
    Path("/usr/share/applications"),
    Path("/usr/local/share/applications"),
    Path.home() / ".local/share/applications",
]
DESKTOP_ID_RE = re.compile(r"^[A-Za-z0-9._+@-]+\.desktop$")
TOKEN_FILE = Path.home() / ".config/appleos/bridge-token"
DEFAULT_ORIGINS = {"http://127.0.0.1:4173", "http://localhost:4173"}


def valid_desktop_id(value: str) -> bool:
    return bool(DESKTOP_ID_RE.fullmatch(value or ""))


def _true(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def parse_desktop_file(path: Path) -> dict | None:
    try:
        parser = configparser.RawConfigParser(interpolation=None, strict=False)
        parser.read(path, encoding="utf-8")
        if not parser.has_section("Desktop Entry"):
            return None
        entry = parser["Desktop Entry"]
        if entry.get("Type", "Application").strip() != "Application":
            return None
        if _true(entry.get("Hidden")) or _true(entry.get("NoDisplay")):
            return None
        name = entry.get("Name", "").strip()
        if not name:
            return None
        categories = [part for part in entry.get("Categories", "").split(";") if part]
        return {
            "id": path.name,
            "name": name,
            "icon": entry.get("Icon", "").strip(),
            "categories": categories,
            "_path": str(path.resolve()),
        }
    except (OSError, UnicodeError, configparser.Error):
        return None


def scan_applications(paths: Iterable[Path] | None = None) -> tuple[list[dict], dict[str, str]]:
    public_by_id: dict[str, dict] = {}
    internal: dict[str, str] = {}
    for directory in list(paths or DEFAULT_APP_DIRS):
        directory = Path(directory)
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.desktop")):
            item = parse_desktop_file(path)
            if not item or not valid_desktop_id(item["id"]):
                continue
            app_id = item["id"]
            internal[app_id] = item["_path"]
            public_by_id[app_id] = {
                "id": app_id,
                "name": item["name"],
                "icon": item["icon"],
                "categories": item["categories"],
            }
    public = sorted(public_by_id.values(), key=lambda item: item["name"].casefold())
    return public, internal


def authorized(header: str | None, token: str) -> bool:
    if not header or not header.startswith("Bearer "):
        return False
    supplied = header[7:]
    return bool(token) and hmac.compare_digest(supplied, token)


def launch_application(app_id: str, app_map: dict[str, str], runner: Callable[[list[str]], object] | None = None):
    if not valid_desktop_id(app_id):
        raise ValueError("invalid desktop id")
    path = app_map.get(app_id)
    if not path:
        raise KeyError(app_id)
    desktop_path = Path(path).resolve()
    if desktop_path.suffix != ".desktop" or not desktop_path.is_file():
        raise KeyError(app_id)

    if runner is None:
        def runner(args: list[str]):
            return subprocess.Popen(
                args,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )

    return runner(["gio", "launch", str(desktop_path)])


def load_token() -> str:
    env = os.environ.get("APPLEOS_BRIDGE_TOKEN", "").strip()
    if env:
        return env
    try:
        return TOKEN_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def allowed_origins() -> set[str]:
    raw = os.environ.get("APPLEOS_ALLOWED_ORIGINS", "").strip()
    if not raw:
        return set(DEFAULT_ORIGINS)
    return {origin.strip() for origin in raw.split(",") if origin.strip()}


class AppleOSBridgeHandler(BaseHTTPRequestHandler):
    server_version = "AppleOSBridge/1.0"
    auth_token = ""
    origins: set[str] = set(DEFAULT_ORIGINS)

    def log_message(self, fmt: str, *args) -> None:
        print(f"[AppleOS bridge] {self.address_string()} - {fmt % args}")

    def _origin(self) -> str:
        return self.headers.get("Origin", "")

    def _cors_allowed(self) -> bool:
        origin = self._origin()
        return not origin or origin in self.origins

    def _send_cors(self) -> None:
        origin = self._origin()
        if origin and origin in self.origins:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")

    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self._send_cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _authorized(self) -> bool:
        return authorized(self.headers.get("Authorization"), self.auth_token)

    def do_OPTIONS(self) -> None:
        if not self._cors_allowed():
            self.send_response(403)
            self.end_headers()
            return
        self.send_response(204)
        self._send_cors()
        self.end_headers()

    def do_GET(self) -> None:
        if not self._cors_allowed():
            self._json(403, {"error": "origin_not_allowed"})
            return
        path = urlparse(self.path).path
        if path == "/v1/status":
            self._json(200, {"ok": True, "version": "1.0", "host": HOST})
            return
        if path == "/v1/apps":
            if not self._authorized():
                self._json(401, {"error": "unauthorized"})
                return
            public, _ = scan_applications()
            self._json(200, {"apps": public})
            return
        self._json(404, {"error": "not_found"})

    def do_POST(self) -> None:
        if not self._cors_allowed():
            self._json(403, {"error": "origin_not_allowed"})
            return
        if not self._authorized():
            self._json(401, {"error": "unauthorized"})
            return
        match = re.fullmatch(r"/v1/apps/([^/]+)/launch", urlparse(self.path).path)
        if not match:
            self._json(404, {"error": "not_found"})
            return
        app_id = unquote(match.group(1))
        if not valid_desktop_id(app_id):
            self._json(400, {"error": "invalid_id"})
            return
        _, internal = scan_applications()
        try:
            launch_application(app_id, internal)
        except KeyError:
            self._json(404, {"error": "unknown_app"})
            return
        except (ValueError, OSError) as exc:
            self._json(500, {"error": "launch_failed", "detail": str(exc)})
            return
        self._json(200, {"ok": True})


def run_server() -> None:
    token = load_token()
    if not token:
        raise SystemExit(f"AppleOS bridge token missing. Run install-bridge.sh or create {TOKEN_FILE}")
    AppleOSBridgeHandler.auth_token = token
    AppleOSBridgeHandler.origins = allowed_origins()
    server = ThreadingHTTPServer((HOST, PORT), AppleOSBridgeHandler)
    print(f"AppleOS device-app bridge listening on http://{HOST}:{PORT}")
    print("Allowed browser origins:", ", ".join(sorted(AppleOSBridgeHandler.origins)))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    run_server()
