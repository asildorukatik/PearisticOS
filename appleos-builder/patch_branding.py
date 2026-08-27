from __future__ import annotations

import base64
import sys
from pathlib import Path


MOTION_CSS = r'''
/* AppleOS motion layer: spring-like scale/fade transitions inspired by macos.vercel.app.
   ThanasOS's own Dock/window animation system remains untouched. */
@keyframes appleosBootIn {
  from { opacity: 0; transform: translateY(18px) scale(.955); filter: blur(10px); }
  to   { opacity: 1; transform: translateY(0) scale(1); filter: blur(0); }
}
@keyframes appleosStageIn {
  from { opacity: 0; transform: scale(1.025); }
  to   { opacity: 1; transform: scale(1); }
}
.appleos-boot-stage { animation: appleosStageIn 420ms cubic-bezier(.16,1,.3,1) both; }
.appleos-boot-card {
  animation: appleosBootIn 560ms cubic-bezier(.16,1,.3,1) 35ms both;
  transform-origin: 50% 55%;
}
.appleos-mode-card {
  transition: transform 300ms cubic-bezier(.16,1,.3,1),
              background-color 220ms ease,
              border-color 220ms ease,
              box-shadow 300ms cubic-bezier(.16,1,.3,1) !important;
  will-change: transform;
}
.appleos-mode-card:hover {
  transform: translateY(-7px) scale(1.018);
  box-shadow: 0 22px 55px rgba(0,0,0,.32);
}
.appleos-mode-card:active {
  transform: translateY(-2px) scale(.985);
  transition-duration: 110ms !important;
}
@media (prefers-reduced-motion: reduce) {
  .appleos-boot-stage, .appleos-boot-card { animation: none !important; }
  .appleos-mode-card { transition: none !important; }
  .appleos-mode-card:hover, .appleos-mode-card:active { transform: none !important; }
}
'''


def patch_menu_bar(root: Path) -> None:
    path = root / "src/components/macos/MenuBar.tsx"
    text = path.read_text(encoding="utf-8")
    import_line = "import turtleLogo from '@/assets/turtle-logo.png';"
    if import_line not in text:
        raise RuntimeError("Could not locate ThanasOS menu logo import")
    text = text.replace(
        import_line,
        import_line + "\nimport appleOSLogo from '@/assets/appleos-apple-logo.png';",
        1,
    )
    old = '<img src={turtleLogo} alt="Logo" className="h-[18px] w-auto object-contain" />'
    new = '<img src={appleOSLogo} alt="Apple" className="h-[18px] w-auto object-contain" />'
    if old not in text:
        raise RuntimeError("Could not locate ThanasOS top-left menu icon")
    text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")


def patch_boot_motion(root: Path) -> None:
    boot = root / "src/components/appleos/AppleOSBoot.tsx"
    text = boot.read_text(encoding="utf-8")
    if "import './appleos-motion.css';" not in text:
        text = text.replace(
            "import { useState } from 'react';",
            "import { useState } from 'react';\nimport './appleos-motion.css';",
            1,
        )
    text = text.replace(
        'className="fixed inset-0 z-[99999] grid place-items-center',
        'className="appleos-boot-stage fixed inset-0 z-[99999] grid place-items-center',
        1,
    )
    text = text.replace(
        'className="w-[min(820px,calc(100vw-34px))] rounded-[30px]',
        'className="appleos-boot-card w-[min(820px,calc(100vw-34px))] rounded-[30px]',
        1,
    )
    text = text.replace(
        'className="flex h-52 flex-col justify-between rounded-3xl',
        'className="appleos-mode-card flex h-52 flex-col justify-between rounded-3xl',
    )
    boot.write_text(text, encoding="utf-8")
    (boot.parent / "appleos-motion.css").write_text(MOTION_CSS, encoding="utf-8")


def install_logo(root: Path) -> None:
    encoded = (Path(__file__).with_name("apple-logo.b64")).read_text(encoding="ascii").strip()
    payload = base64.b64decode(encoded, validate=True)
    if not payload.startswith(b"\x89PNG\r\n\x1a\n"):
        raise RuntimeError("Bundled Apple logo is not a PNG")
    target = root / "src/assets/appleos-apple-logo.png"
    target.write_bytes(payload)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch_branding.py <thanasos-root>")
    root = Path(sys.argv[1]).resolve()
    install_logo(root)
    patch_menu_bar(root)
    patch_boot_motion(root)
    print("Applied user Apple icon + AppleOS spring motion without replacing ThanasOS shell behavior")


if __name__ == "__main__":
    main()
