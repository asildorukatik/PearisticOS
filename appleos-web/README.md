# AppleOS Web PWA

This build is a normal web/PWA project rather than one enormous embedded HTML file.

## Structure

- `index.html` — small AppleOS Desktop/Mobile chooser.
- `desktop/` — normal Vite production build of the real ThanasOS source, patched only for AppleOS integration/branding.
- `mobile/index.html` — the real PearisticOS file copied as a separate web resource.
- `assets/` — external CSS, JavaScript, icons and the small optional WebAssembly math module.
- `bridge/` — optional local elementary OS companion for listing and launching installed Linux desktop applications.
- `scripts/` — local preview and fullscreen elementary launcher.

## Quick test

From this folder:

```bash
./scripts/dev.sh
```

Then open `http://127.0.0.1:4173/`.

`file://` is not recommended because PWA service workers, WebAssembly fetching, and the native-app bridge require an HTTP origin. Localhost HTTP is treated as a secure context for PWA development.

## elementary OS: use AppleOS on one workspace

Run once:

```bash
./bridge/install-bridge.sh
```

Then either launch **AppleOS** from the elementary Applications menu, or run:

```bash
./scripts/run-elementary-workspace.sh
```

The launcher:

1. starts a loopback-only local bridge on `127.0.0.1:8765`;
2. serves this folder on `127.0.0.1:4173`;
3. opens Chromium/Chrome in app/fullscreen mode, with Firefox kiosk fallback;
4. does **not** replace Pantheon, modify Gala, or change your other workspaces.

Move/switch to another elementary workspace using your normal workspace gestures/shortcuts. AppleOS is just one fullscreen application window.

## Device Applications

When AppleOS is started through the elementary launcher, Desktop mode checks the optional bridge. If connected, an **Applications** glass button appears below the menu bar. It lists sanitized `.desktop` entries from standard Linux application directories and can launch them.

Security rules:

- bridge listens only on loopback;
- requests require a random bearer token;
- the browser can request only a desktop-file ID;
- raw `Exec=` commands are never returned to the browser;
- launch uses `gio launch` on a freshly scanned, allowlisted `.desktop` file;
- there is no arbitrary shell-command or arbitrary-file API.

## Performance design

- Desktop and Mobile are separate resources and load only after mode selection.
- Images and Vite assets remain external so the browser can cache/decode them independently.
- The service worker precaches only the small boot shell and runtime-caches Desktop/Mobile after use.
- `assets/wasm/appleos_math.wasm` accelerates numeric Dock/spring helpers when available; JavaScript fallback is immediate.
- The boot visual layer chooses WebGPU first, WebGL2 second, and a CSS fallback last.
- ThanasOS remains DOM/React rather than being rewritten into a canvas/WASM app.

## Branding and source

The top-left Desktop menu icon is the user-provided Apple PNG. ThanasOS remains the real upstream implementation and retains its license in the source repository used at build time. The animation tuning uses spring/scale/fade behavior inspired by the referenced macOS web demo without copying its source.
