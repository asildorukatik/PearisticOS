from __future__ import annotations

import sys
from pathlib import Path


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: test_source.py <thanasos-root>")

    root = Path(sys.argv[1])
    index = (root / "src/pages/Index.tsx").read_text(encoding="utf-8")
    settings = (root / "src/components/apps/SettingsApp.tsx").read_text(encoding="utf-8")
    vite = (root / "vite.config.ts").read_text(encoding="utf-8")

    boot_path = root / "src/components/appleos/AppleOSBoot.tsx"
    mobile_path = root / "src/components/appleos/PearisticMobile.tsx"
    pearistic_path = root / "src/appleos/pearistic.html"
    logo_path = root / "src/assets/appleos-apple-logo.png"
    menu_path = root / "src/components/macos/MenuBar.tsx"

    require(boot_path.exists(), "AppleOSBoot.tsx is missing")
    require(mobile_path.exists(), "PearisticMobile.tsx is missing")
    require(pearistic_path.exists(), "embedded PearisticOS index.html is missing")

    boot = boot_path.read_text(encoding="utf-8")
    mobile = mobile_path.read_text(encoding="utf-8")
    menu = menu_path.read_text(encoding="utf-8")

    require("AppleOSBoot" in index, "Index.tsx does not use AppleOSBoot")
    require("PearisticMobile" in index, "Index.tsx does not use PearisticMobile")
    require("<Desktop />" in index, "real ThanasOS Desktop is no longer used")
    require("MobileFallback" not in index, "old ThanasOS MobileFallback still controls mobile mode")
    require("requestFullscreen" in boot, "boot choice does not request fullscreen")
    require("pearistic.html?raw" in mobile, "PearisticOS is not embedded from its real index.html")
    require("srcDoc={pearisticHtml}" in mobile, "PearisticOS runtime is not loaded from embedded source")

    require("Doruk" in settings, "Settings Apple Account was not changed to Doruk")
    require("Thanas R" not in settings, "Thanas R is still shown as Apple Account owner")
    require("thanas5.rd@gmail.com" not in settings, "upstream owner email is still shown")
    require("Thanas's" not in settings, "upstream owner device names remain in Apple Account")

    require(logo_path.exists(), "user-supplied Apple logo was not installed into ThanasOS")
    require(logo_path.stat().st_size > 50_000, "Apple logo payload is unexpectedly small")
    require("appleos-apple-logo.png" in menu, "menu bar does not import the user Apple logo")
    require('alt="Apple"' in menu, "top-left Apple icon markup was not patched")
    require("appleos-boot-card" in boot, "AppleOS boot motion class is missing")
    require("appleos-mode-card" in boot, "AppleOS mode-card motion class is missing")
    require("cubic-bezier" in boot, "macOS-style motion curve is missing")

    require("assetsInlineLimit" in vite, "Vite is not configured to inline binary assets")
    require("inlineDynamicImports" in vite, "Vite is not configured for a single JS bundle")
    require("base: './'" in vite or 'base: "./"' in vite, "Vite base is not file-safe")

    pearistic_size = pearistic_path.stat().st_size
    require(pearistic_size > 20_000_000, f"PearisticOS payload is unexpectedly small: {pearistic_size}")

    print("AppleOS v0.7 source acceptance checks: PASS")


if __name__ == "__main__":
    main()
