# AppleOS Web PWA Design

Date: 2026-08-28
Branch: `appleos-web-pwa`

## Goal

Build AppleOS as a normal deployable web project instead of a single giant embedded HTML file. Desktop remains based on the real ThanasOS source, Mobile remains the real PearisticOS build, and the project gains PWA install/offline support, selective WebAssembly acceleration, and a WebGPU renderer with WebGL2 fallback.

A local elementary OS companion is optional but supported. It lets AppleOS show applications installed on the device and launch them, so AppleOS can occupy one dedicated workspace like a shell-style desktop while elementary OS/Pantheon remains the actual host operating system.

## Non-goals

- Do not rewrite the complete React/DOM desktop in WebAssembly.
- Do not replace elementary OS, Pantheon, Gala, systemd, or the Linux kernel.
- Do not give the browser unrestricted command execution.
- Do not merge this branch into main without explicit approval.
- Do not embed the full PearisticOS/ThanasOS application into one enormous HTML file.

## Deliverable

A ZIP/folder project with a production web build and development source:

```text
AppleOS-Web/
├── index.html
├── manifest.webmanifest
├── service-worker.js
├── assets/
│   ├── js/
│   ├── css/
│   ├── icons/
│   ├── wallpapers/
│   └── wasm/
├── desktop/
│   └── ThanasOS-generated chunks/assets
├── mobile/
│   └── PearisticOS web build
├── bridge/
│   ├── appleos-bridge.py
│   ├── appleos-bridge.desktop
│   └── install-bridge.sh
└── scripts/
    ├── dev.sh
    ├── build.sh
    └── run-elementary-workspace.sh
```

The exact generated Vite chunk names are build outputs rather than API contracts.

## Architecture

### 1. Web shell

`index.html` is intentionally small. It loads the AppleOS boot/mode chooser and core runtime only.

Desktop selection lazy-loads the ThanasOS desktop bundle. Mobile selection lazy-loads the PearisticOS bundle/page. Heavy optional renderers and WASM are loaded only when the selected mode uses them.

### 2. Desktop mode: real ThanasOS base

The real ThanasOS React/TypeScript source remains the desktop implementation, including its windows, Dock, apps, menus, Control Center, Spotlight, Launchpad, settings, and related behavior.

AppleOS patches are limited to branding/integration requirements such as:

- user-provided Apple icon in the top-left menu position;
- AppleOS account/device wording;
- AppleOS mode switching;
- optional native-app launcher integration;
- PWA/service-worker integration;
- animation tuning inspired by `macos.vercel.app` while preserving ThanasOS behavior;
- selected AppleOS-provided assets/emoji artwork where the shell owns the rendering.

### 3. Mobile mode: real PearisticOS

PearisticOS is not injected with `srcDoc` and not converted into a base64 payload. It is emitted as a normal web resource under `mobile/` and loaded by URL when Mobile mode is selected.

This avoids loading the entire mobile OS payload during Desktop startup.

## PWA

The project includes:

- `manifest.webmanifest` with AppleOS name, icons, display mode, theme/background colors, and start URL;
- service worker registration from the shell;
- offline app-shell caching;
- versioned caches so updates can replace old assets safely;
- lazy/runtime caching for Desktop and Mobile assets after first use.

Cache policy:

- core boot shell: precache;
- icons/fonts/critical CSS: precache;
- Desktop chunks: cache on first Desktop launch, with immutable fingerprinted assets;
- Mobile assets: cache on first Mobile launch;
- network pages used by browser-like apps are not blindly cached.

## WebAssembly

WASM is selective, not mandatory for every UI action.

Initial WASM module responsibilities:

- Dock cosine magnification calculations;
- spring/inertial interpolation helpers;
- reusable numeric animation helpers where profiling shows repeated CPU-side work.

JavaScript/TypeScript remains responsible for DOM manipulation, React state, app/window management, accessibility, browser APIs, and orchestration.

There must always be a JavaScript fallback if WASM initialization fails.

## WebGPU / WebGL2 renderer

A small graphics backend is used only for effects that benefit from GPU rendering, such as premium animated wallpaper/glass-light fields or particles.

Backend selection:

```text
WebGPU available -> WebGPU backend
else WebGL2 available -> WebGL2 backend
else -> CSS/static fallback
```

The renderer is a visual layer behind the DOM shell. Windows, text, menus, buttons, Dock icons, and accessibility semantics remain DOM elements.

This prevents GPU rendering from turning the desktop into a canvas-only application.

## Animation system

Animation feel should be heavily inspired by the smooth spring/scale/fade behavior demonstrated by `macos.vercel.app`, without copying its source.

Animation priorities:

- window open: opacity + slight scale + short positional settle;
- window close: reverse with shorter duration;
- minimize/restore: spring-like transformation toward/from Dock geometry when practical;
- Control Center/menus: scale + fade + small directional offset;
- Dock: retain ThanasOS-style magnification behavior;
- respect reduced-motion settings.

WASM can compute spring curves, but DOM transforms remain driven with `requestAnimationFrame`, Web Animations API, or the existing animation framework depending on the component.

## Device-installed application integration

### Browser-only limitation

A normal PWA must not attempt to enumerate all applications installed on the computer. The browser sandbox does not provide a general-purpose API for listing arbitrary Linux desktop applications or running arbitrary local commands.

Therefore installed-app integration is an optional local companion feature.

### AppleOS local bridge

On elementary OS, `appleos-bridge.py` runs only on loopback and exposes a deliberately small API to the locally running AppleOS UI.

It scans desktop-entry metadata from:

- `/usr/share/applications/*.desktop`
- `/usr/local/share/applications/*.desktop`
- `~/.local/share/applications/*.desktop`

It returns sanitized app metadata:

```json
{
  "id": "org.kde.konsole.desktop",
  "name": "Konsole",
  "icon": "utilities-terminal",
  "categories": ["System", "TerminalEmulator"]
}
```

It does not send raw `Exec=` command strings to the browser.

### Launch API

The browser requests launch by desktop-file ID only. The bridge resolves that ID against its own freshly scanned allowlist and launches it using desktop-entry semantics (`gtk-launch`, `gio launch`, or another host-appropriate method chosen during implementation).

The UI cannot supply arbitrary shell commands, paths, or arguments to the bridge.

Expected endpoints:

```text
GET  /v1/status
GET  /v1/apps
POST /v1/apps/{desktop-id}/launch
```

The server binds to `127.0.0.1` only and requires an installation-generated bearer token stored outside the web project. CORS is restricted to the configured AppleOS local origin.

### UI behavior

When the bridge is detected, AppleOS adds a `Device Apps`/`Applications` source to Launchpad/Finder-style app browsing. Device applications get their desktop-entry icon where resolvable and can be launched by clicking them.

When the bridge is unavailable, AppleOS works normally and simply hides/disables device-app integration.

## elementary OS dedicated-workspace mode

AppleOS does not replace Pantheon. Instead a launcher script starts the locally served/installed PWA in app/fullscreen mode so the user can keep it on a dedicated workspace.

The first implementation should avoid fragile window-manager hacks. It will:

1. start the optional local bridge;
2. start a local static server for the AppleOS build, unless installed PWA mode is being used;
3. launch Chromium/Chrome in app/fullscreen mode when available;
4. leave workspace assignment to Pantheon/Gala or the user's existing workspace shortcut workflow unless a stable supported mechanism is confirmed.

The browser process should be easy to leave/close and must not intercept global workspace shortcuts intentionally.

## Assets and branding

- The user-provided Apple icon is the Apple menu icon at the top-left of Desktop mode.
- Real ThanasOS app icons/wallpapers already approved for AppleOS may remain where appropriate.
- User-provided emoji artwork is used for AppleOS-owned emoji-like UI where practical; the web build does not alter the host OS emoji font.
- Asset files remain external resources so the browser can cache/decode them independently.

## Performance strategy

The biggest performance improvements should come from load behavior rather than moving everything to WASM:

1. remove enormous asset inlining;
2. code-split Desktop/Mobile and heavy apps;
3. lazy-load optional features;
4. fingerprint/cache static assets;
5. preload only first-screen essentials;
6. keep wallpaper/icon binaries external;
7. use GPU rendering only where it reduces DOM/CSS workload;
8. use WASM only for measured numeric hot paths.

Performance targets for the first production pass:

- boot chooser should become interactive without loading PearisticOS;
- Desktop launch should not load Mobile resources;
- Mobile launch should not load most Desktop application chunks;
- service worker should allow the previously used mode to reopen offline after assets have been cached;
- no single JavaScript bundle should intentionally contain every image and Mobile HTML payload.

## Error handling

- WebGPU init failure -> WebGL2.
- WebGL2 failure -> CSS/static renderer.
- WASM init failure -> JavaScript math fallback.
- service-worker registration failure -> online web app still works.
- native bridge unavailable -> device-app UI is hidden/disabled; web apps remain functional.
- a malformed `.desktop` file -> skip that entry, do not fail the entire app list.
- launch request for unknown app ID -> reject.

## Security boundaries

- No arbitrary command execution endpoint.
- No arbitrary filesystem-reading endpoint.
- No browser-provided `Exec=` string.
- No listening on LAN interfaces by default.
- Device-app bridge remains optional and local-only.
- External web apps remain browser-sandboxed.
- PearisticOS/ThanasOS should not automatically gain bridge privileges simply because they are rendered; bridge calls go through a narrow AppleOS integration module.

## Testing

### Build/static tests

- mode chooser bundle does not import PearisticOS eagerly;
- manifest validates;
- service worker precache paths exist;
- WASM binary can instantiate;
- JavaScript WASM fallback matches numeric results within tolerance;
- backend selection tests cover WebGPU/WebGL2/CSS paths;
- Apple top-left asset path exists;
- generated build has multiple chunks/assets rather than one inlined monolith.

### Bridge tests

- `.desktop` parser handles common entries and ignores hidden/no-display apps where appropriate;
- returned metadata contains no raw command string;
- unknown IDs cannot launch;
- invalid IDs/path traversal are rejected;
- server binds loopback only;
- token is required for launch requests;
- app-launch adapter is mocked during automated tests.

### Browser tests

- boot -> Desktop;
- boot -> Mobile;
- Desktop -> switch mode;
- installable PWA manifest/service worker;
- offline relaunch after cache warm-up;
- Control Center/menu animations;
- installed device apps appear only when local bridge is reachable.

### Manual elementary OS acceptance

- run AppleOS in a dedicated Pantheon workspace;
- switch to another workspace normally and return;
- launch a known installed application from AppleOS;
- close AppleOS without logging out/restarting the host;
- verify elementary OS remains untouched outside the optional companion/autostart files.

## Acceptance criteria

The feature is accepted when:

1. AppleOS is delivered as a normal web/PWA folder/ZIP rather than one embedded HTML file.
2. Desktop mode visibly uses the real ThanasOS desktop implementation.
3. Mobile mode visibly uses the real PearisticOS implementation.
4. user-provided Apple icon is used at top-left.
5. animation tuning follows the approved smooth macOS-like reference feel.
6. PWA installs and can reopen cached content offline.
7. WASM has a verified fallback and does not gate basic UI startup.
8. WebGPU has WebGL2 and CSS/static fallbacks.
9. optional elementary OS bridge lists sanitized installed-app metadata and launches only resolved desktop-entry IDs.
10. AppleOS can run fullscreen/app-style on one elementary OS workspace without replacing the host OS.
