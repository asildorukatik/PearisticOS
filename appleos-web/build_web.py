#!/usr/bin/env python3
from __future__ import annotations

import base64
import re
import shutil
import stat
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = Path(__file__).resolve().parent / "templates"
SOURCE_ROOT = Path(__file__).resolve().parent
MOTION_MARKER = "/* AppleOS PWA spring motion */"


def require_replace(text: str, old: str, new: str, label: str, count: int = 1) -> str:
    if old not in text:
        raise RuntimeError(f"Could not locate {label}")
    return text.replace(old, new, count)


def install_user_apple_logo(thanas_root: Path) -> bytes:
    encoded = (REPO_ROOT / "appleos-builder/apple-logo.b64").read_text(encoding="ascii").strip()
    payload = base64.b64decode(encoded, validate=True)
    if not payload.startswith(b"\x89PNG\r\n\x1a\n"):
        raise RuntimeError("Bundled user Apple logo is not a PNG")
    target = thanas_root / "src/assets/appleos-apple-logo.png"
    target.write_bytes(payload)
    return payload


def patch_menu_bar(thanas_root: Path) -> None:
    path = thanas_root / "src/components/macos/MenuBar.tsx"
    text = path.read_text(encoding="utf-8")
    if "appleos-apple-logo.png" not in text:
        text = require_replace(
            text,
            "import turtleLogo from '@/assets/turtle-logo.png';",
            "import turtleLogo from '@/assets/turtle-logo.png';\nimport appleOSLogo from '@/assets/appleos-apple-logo.png';",
            "ThanasOS menu logo import",
        )
    old = '<img src={turtleLogo} alt="Logo" className="h-[18px] w-auto object-contain" />'
    new = '<img src={appleOSLogo} alt="Apple" className="h-[18px] w-auto object-contain" />'
    if old in text:
        text = text.replace(old, new, 1)
    elif new not in text:
        raise RuntimeError("Could not locate ThanasOS top-left menu icon")
    path.write_text(text, encoding="utf-8")


def patch_settings_branding(thanas_root: Path) -> None:
    path = thanas_root / "src/components/apps/SettingsApp.tsx"
    text = path.read_text(encoding="utf-8")
    text = text.replace("Thanas R", "Doruk")
    text = text.replace("thanas5.rd@gmail.com", "AppleOS Account")
    text = text.replace("Thanas's", "Doruk's")
    text = text.replace("THANAS-LAPTOP", "DORUK-LAPTOP")
    path.write_text(text, encoding="utf-8")


def patch_desktop_mode(thanas_root: Path) -> None:
    path = thanas_root / "src/pages/Index.tsx"
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(r"const detectIsMobile = \(\) => \{.*?\n\};", re.S)
    if pattern.search(text):
        text = pattern.sub("const detectIsMobile = () => false; // AppleOS Desktop is explicitly selected by the outer PWA shell.", text, count=1)
    elif "const detectIsMobile = () => false;" not in text:
        raise RuntimeError("Could not locate ThanasOS mobile detector")
    path.write_text(text, encoding="utf-8")


def patch_vite(thanas_root: Path) -> None:
    path = thanas_root / "vite.config.ts"
    text = path.read_text(encoding="utf-8")
    if "base: './'" not in text and 'base: "./"' not in text:
        text = require_replace(
            text,
            "export default defineConfig(({ mode }) => ({\n  server:",
            "export default defineConfig(({ mode }) => ({\n  base: './',\n  server:",
            "Vite config entry",
        )
    path.write_text(text, encoding="utf-8")


def patch_dock_wasm(thanas_root: Path) -> None:
    path = thanas_root / "src/components/macos/Dock.tsx"
    text = path.read_text(encoding="utf-8")
    if "AppleOSMath?:" not in text:
        old = """    gsap?: {\n      to: (target: Element | null, vars: Record<string, unknown>) => void;\n    };\n"""
        new = old + """    AppleOSMath?: {\n      cosineMagnification01: (normalized: number) => number;\n      springStep: (current: number, target: number, velocity: number, stiffness: number, damping: number, dt: number) => number;\n      backend: 'wasm' | 'js';\n    };\n"""
        text = require_replace(text, old, new, "Dock Window global declaration")
    old_formula = "const scaleFactor = (1 - Math.cos(cappedTheta)) / 2;"
    new_formula = "const scaleFactor = window.AppleOSMath?.cosineMagnification01 ? window.AppleOSMath.cosineMagnification01(cappedTheta / (2 * Math.PI)) : (1 - Math.cos(cappedTheta)) / 2;"
    if old_formula in text:
        text = text.replace(old_formula, new_formula, 1)
    elif new_formula not in text:
        raise RuntimeError("Could not locate ThanasOS Dock cosine formula")
    path.write_text(text, encoding="utf-8")


def patch_motion(thanas_root: Path) -> None:
    path = thanas_root / "src/index.css"
    text = path.read_text(encoding="utf-8")
    if MOTION_MARKER in text:
        return
    text += r'''

/* AppleOS PWA spring motion */
@keyframes appleosWindowIn {
  0%   { opacity: 0; transform: translateY(12px) scale(.945); filter: blur(3px); }
  64%  { opacity: 1; transform: translateY(-2px) scale(1.006); filter: blur(0); }
  100% { opacity: 1; transform: translateY(0) scale(1); filter: blur(0); }
}

.animate-fade-in {
  animation: appleosWindowIn 460ms cubic-bezier(.16,1,.3,1) both !important;
  transform-origin: 50% 52%;
  will-change: transform, opacity;
}

[data-radix-popper-content-wrapper] {
  transition: opacity 180ms ease, transform 320ms cubic-bezier(.16,1,.3,1);
}

@media (prefers-reduced-motion: reduce) {
  .animate-fade-in { animation: none !important; }
  [data-radix-popper-content-wrapper] { transition: none !important; }
}
'''
    path.write_text(text, encoding="utf-8")


def patch_thanasos(thanas_root: Path) -> bytes:
    payload = install_user_apple_logo(thanas_root)
    patch_menu_bar(thanas_root)
    patch_settings_branding(thanas_root)
    patch_desktop_mode(thanas_root)
    patch_vite(thanas_root)
    patch_dock_wasm(thanas_root)
    patch_motion(thanas_root)
    return payload


def copy_template(name: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(TEMPLATES / name, target)


def copy_executable(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    target.chmod(target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def prepare(thanas_root: Path, pearistic_index: Path, output: Path) -> None:
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    logo = patch_thanasos(thanas_root)

    copy_template("index.html", output / "index.html")
    copy_template("appleos.css", output / "assets/css/appleos.css")
    copy_template("app-shell.js", output / "assets/js/app-shell.js")
    copy_template("manifest.webmanifest", output / "manifest.webmanifest")
    copy_template("service-worker.js", output / "service-worker.js")
    copy_template("wasm-math.js", output / "assets/js/wasm-math.js")
    copy_template("gpu-effects.js", output / "assets/js/gpu-effects.js")
    copy_template("device-apps.js", output / "assets/js/device-apps.js")

    icons = output / "assets/icons"
    icons.mkdir(parents=True, exist_ok=True)
    (icons / "apple-logo-128.png").write_bytes(logo)

    mobile = output / "mobile"
    mobile.mkdir(parents=True, exist_ok=True)
    shutil.copy2(pearistic_index, mobile / "index.html")

    bridge_out = output / "bridge"
    bridge_out.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE_ROOT / "bridge/appleos_bridge.py", bridge_out / "appleos_bridge.py")
    copy_executable(SOURCE_ROOT / "bridge/install-bridge.sh", bridge_out / "install-bridge.sh")
    shutil.copy2(SOURCE_ROOT / "bridge/appleos.desktop.in", bridge_out / "appleos.desktop.in")

    scripts_out = output / "scripts"
    scripts_out.mkdir(parents=True, exist_ok=True)
    copy_executable(SOURCE_ROOT / "scripts/run-elementary-workspace.sh", scripts_out / "run-elementary-workspace.sh")
    copy_executable(SOURCE_ROOT / "scripts/dev.sh", scripts_out / "dev.sh")
    shutil.copy2(SOURCE_ROOT / "README.md", output / "README.md")

    (output / "assets/wasm").mkdir(parents=True, exist_ok=True)
    print(f"Prepared AppleOS PWA shell at {output}")


def inject_desktop_integrations(desktop_index: Path) -> None:
    text = desktop_index.read_text(encoding="utf-8")
    snippets = [
        '<script type="module" src="../assets/js/wasm-math.js"></script>',
        '<script type="module" src="../assets/js/device-apps.js"></script>',
    ]
    for snippet in snippets:
        if snippet not in text:
            if "</body>" not in text:
                raise RuntimeError("ThanasOS dist index has no </body>")
            text = text.replace("</body>", f"  {snippet}\n</body>", 1)
    desktop_index.write_text(text, encoding="utf-8")


def finalize(thanas_root: Path, output: Path) -> None:
    dist = thanas_root / "dist"
    if not (dist / "index.html").exists():
        raise RuntimeError("ThanasOS dist has not been built")
    desktop = output / "desktop"
    if desktop.exists():
        shutil.rmtree(desktop)
    shutil.copytree(dist, desktop)
    inject_desktop_integrations(desktop / "index.html")
    print(f"Installed real ThanasOS Vite build at {desktop}")


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("usage: build_web.py prepare <thanasos> <pearistic-index> <output> | finalize <thanasos> <output>")
    mode = sys.argv[1]
    if mode == "prepare" and len(sys.argv) == 5:
        prepare(Path(sys.argv[2]).resolve(), Path(sys.argv[3]).resolve(), Path(sys.argv[4]).resolve())
    elif mode == "finalize" and len(sys.argv) == 4:
        finalize(Path(sys.argv[2]).resolve(), Path(sys.argv[3]).resolve())
    else:
        raise SystemExit("invalid arguments")


if __name__ == "__main__":
    main()
