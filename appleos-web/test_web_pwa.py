#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "AppleOS-Web")
    require(root.is_dir(), f"build directory missing: {root}")

    index = root / "index.html"
    manifest = root / "manifest.webmanifest"
    sw = root / "service-worker.js"
    css = root / "assets/css/appleos.css"
    shell_js = root / "assets/js/app-shell.js"
    gpu_js = root / "assets/js/gpu-effects.js"
    wasm_js = root / "assets/js/wasm-math.js"
    device_js = root / "assets/js/device-apps.js"
    wasm = root / "assets/wasm/appleos_math.wasm"
    logo = root / "assets/icons/apple-logo-128.png"
    desktop = root / "desktop/index.html"
    mobile = root / "mobile/index.html"

    for path in [index, manifest, sw, css, shell_js, gpu_js, wasm_js, device_js, wasm, logo, desktop, mobile]:
        require(path.exists(), f"missing required output: {path}")

    root_html = index.read_text(encoding="utf-8")
    require(index.stat().st_size < 180_000, "root index.html became a monolithic payload")
    require("./desktop/index.html" in root_html, "Desktop is not lazy-selected by URL")
    require("./mobile/index.html" in root_html, "Mobile is not lazy-selected by URL")
    require("manifest.webmanifest" in root_html, "PWA manifest is not linked")
    require("assets/js/app-shell.js" in root_html, "root shell JS is not external")
    require("srcDoc" not in root_html, "root shell embeds another OS with srcDoc")
    require("data:text/html" not in root_html, "root shell embeds another OS as a data URL")

    data = json.loads(manifest.read_text(encoding="utf-8"))
    require(data.get("name") == "AppleOS", "manifest name must be AppleOS")
    require(data.get("display") in {"standalone", "fullscreen"}, "manifest display must be app-like")
    icons = data.get("icons") or []
    require(any(i.get("sizes") == "192x192" for i in icons), "manifest lacks 192x192 icon")
    require(any(i.get("sizes") == "512x512" for i in icons), "manifest lacks 512x512 icon")

    sw_text = sw.read_text(encoding="utf-8")
    require("addEventListener('install'" in sw_text or 'addEventListener("install"' in sw_text, "service worker install handler missing")
    require("addEventListener('fetch'" in sw_text or 'addEventListener("fetch"' in sw_text, "service worker fetch handler missing")
    require("appleos-shell-" in sw_text, "service worker cache is not versioned")

    require(mobile.stat().st_size > 20_000_000, f"PearisticOS mobile payload unexpectedly small: {mobile.stat().st_size}")

    desktop_assets = list((root / "desktop/assets").glob("*"))
    require(len(desktop_assets) >= 2, "desktop Vite build does not contain separate generated assets")
    desktop_html = desktop.read_text(encoding="utf-8")
    require("../assets/js/device-apps.js" in desktop_html, "desktop does not load Device Apps integration")
    require("../assets/js/wasm-math.js" in desktop_html, "desktop does not load WASM math integration")

    wasm_bytes = wasm.read_bytes()
    require(wasm_bytes.startswith(b"\x00asm"), "WASM output does not have the WebAssembly magic header")
    wasm_loader = wasm_js.read_text(encoding="utf-8")
    require("cosineMagnification01" in wasm_loader, "WASM/JS math API missing cosineMagnification01")
    require("fallback" in wasm_loader.lower(), "WASM loader does not expose an explicit JS fallback")

    gpu = gpu_js.read_text(encoding="utf-8")
    require("navigator.gpu" in gpu, "WebGPU path missing")
    require("webgl2" in gpu.lower(), "WebGL2 fallback missing")
    require("css" in gpu.lower(), "CSS/static fallback missing")

    logo_bytes = logo.read_bytes()
    require(logo_bytes.startswith(b"\x89PNG\r\n\x1a\n"), "Apple logo is not a PNG")

    bridge = root / "bridge/appleos_bridge.py"
    launcher = root / "scripts/run-elementary-workspace.sh"
    require(bridge.exists(), "elementary OS bridge missing")
    require(launcher.exists(), "elementary workspace launcher missing")

    require(not re.search(r"<script[^>]+>[^<]{5_000_000,}</script>", root_html, re.S), "root HTML contains an enormous inline script")
    print("AppleOS Web PWA structural acceptance: PASS")


if __name__ == "__main__":
    main()
