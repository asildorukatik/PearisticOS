# AppleOS Web PWA Implementation Plan

**Goal:** Build AppleOS as a deployable PWA folder/ZIP with real ThanasOS Desktop, real PearisticOS Mobile, selective WASM math, WebGPU/WebGL2 effects, and an optional elementary OS bridge for installed-app discovery/launch.

**Architecture:** A small root boot shell selects either `desktop/` or `mobile/`. `desktop/` is a normal Vite build of patched upstream ThanasOS; `mobile/` is the repository PearisticOS `index.html` copied as a normal resource. Root PWA assets, service worker, WASM/GPU modules, and the local elementary bridge remain separate files.

**Tech Stack:** HTML/CSS/ES modules, React 18 + TypeScript + Vite (upstream ThanasOS), Python 3 standard library bridge/build tooling, C-to-WebAssembly via clang, PWA service worker, WebGPU with WebGL2 fallback.

**Spec:** `docs/superpowers/specs/2026-08-28-appleos-web-pwa-design.md`

## Global Constraints

- Work only on branch `appleos-web-pwa`; do not merge to main.
- Desktop must remain the real ThanasOS source/build, not a recreation.
- Mobile must remain the real PearisticOS repository `index.html` and must not be embedded with `srcDoc` or base64.
- User-provided Apple icon must replace only the top-left menu icon.
- WASM failure must fall back to JavaScript; WebGPU failure must fall back to WebGL2 then CSS/static.
- Native bridge binds only to `127.0.0.1`, never exposes arbitrary command execution, and launches allowlisted desktop-entry IDs only.
- AppleOS must be usable as a fullscreen/app-style window on an elementary OS workspace without replacing Pantheon.

---

### Task 1: Build acceptance tests

**Files:**
- Create: `appleos-web/test_web_pwa.py`
- Create: `appleos-web/test_bridge.py`

**Interfaces:**
- Consumes: generated `AppleOS-Web/` directory and `bridge/appleos_bridge.py`.
- Produces: deterministic structural/security acceptance checks used in CI.

- [ ] **Step 1: Write failing structural tests** that require `index.html`, `manifest.webmanifest`, `service-worker.js`, separate `desktop/` and `mobile/`, external assets, a `.wasm` file, GPU fallback module, user Apple logo, and no embedded PearisticOS payload in root HTML.
- [ ] **Step 2: Run the structural tests before implementation** with `python3 appleos-web/test_web_pwa.py AppleOS-Web`; expected result: FAIL because `AppleOS-Web` does not exist.
- [ ] **Step 3: Write failing bridge tests** for hidden/no-display filtering, sanitized output, invalid ID rejection, loopback binding constant, and bearer-token launch requirement.
- [ ] **Step 4: Run bridge tests before implementation** with `python3 -m unittest appleos-web/test_bridge.py -v`; expected result: import/file failure because bridge implementation does not exist.

### Task 2: PWA shell, ThanasOS patcher, Mobile output

**Files:**
- Create: `appleos-web/build_web.py`
- Create: `appleos-web/templates/index.html`
- Create: `appleos-web/templates/appleos.css`
- Create: `appleos-web/templates/app-shell.js`
- Create: `appleos-web/templates/manifest.webmanifest`
- Create: `appleos-web/templates/service-worker.js`

**Interfaces:**
- Consumes: upstream ThanasOS checkout path, repository PearisticOS `index.html`, `appleos-builder/apple-logo.b64`.
- Produces: patched ThanasOS source and generated `AppleOS-Web/` root/mobile assets.

- [ ] **Step 1: Patch upstream ThanasOS** to add `appleos-apple-logo.png`, switch only the MenuBar top-left image to that asset, set Vite `base: './'`, remove automatic `MobileFallback` so the Desktop build stays desktop-only, and add AppleOS spring CSS without replacing ThanasOS Dock/window logic.
- [ ] **Step 2: Generate root PWA shell** with Desktop/Mobile cards, fullscreen request, keyboard access, reduced-motion support, and no eager import of either OS payload.
- [ ] **Step 3: Copy PearisticOS** to `AppleOS-Web/mobile/index.html` as a normal file.
- [ ] **Step 4: After `npm run build`, copy ThanasOS `dist/` to `AppleOS-Web/desktop/` and inject only the AppleOS optional integration scripts into `desktop/index.html`.

### Task 3: WASM math and GPU effects

**Files:**
- Create: `appleos-web/wasm/appleos_math.c`
- Create: `appleos-web/templates/wasm-math.js`
- Create: `appleos-web/templates/gpu-effects.js`

**Interfaces:**
- Produces browser global `window.AppleOSMath.cosineMagnification01(normalized)` and `window.AppleOSMath.springStep(current,target,velocity,stiffness,damping,dt)` with JS fallback.
- Produces `startAppleOSEffects(canvas)` selecting WebGPU, WebGL2, then CSS/static.

- [ ] **Step 1: Compile C to `assets/wasm/appleos_math.wasm`** with clang `--target=wasm32 -nostdlib -Wl,--no-entry` and exported math functions.
- [ ] **Step 2: Load WASM asynchronously** and expose JS fallback implementations immediately so UI startup never waits for WASM.
- [ ] **Step 3: Patch ThanasOS Dock cosine calculation** to call `window.AppleOSMath.cosineMagnification01()` when available and retain the existing `Math.cos` formula as fallback.
- [ ] **Step 4: Implement GPU boot-background renderer** with WebGPU first, WebGL2 second, CSS/static last; the DOM remains responsible for all text/windows/buttons.

### Task 4: elementary OS installed-app bridge and workspace launcher

**Files:**
- Create: `appleos-web/bridge/appleos_bridge.py`
- Create: `appleos-web/bridge/install-bridge.sh`
- Create: `appleos-web/bridge/appleos.desktop.in`
- Create: `appleos-web/templates/device-apps.js`
- Create: `appleos-web/scripts/run-elementary-workspace.sh`
- Create: `appleos-web/scripts/dev.sh`

**Interfaces:**
- `GET /v1/status` -> `{ok:true,version:string}`.
- `GET /v1/apps` with bearer token -> `{apps:[{id,name,icon,categories}]}` with no `Exec` field.
- `POST /v1/apps/<desktop-id>/launch` with bearer token -> launches only a freshly resolved allowlisted desktop entry using `gio launch`.

- [ ] **Step 1: Parse standard `.desktop` locations** and skip non-Application, Hidden, or NoDisplay entries.
- [ ] **Step 2: Enforce security boundary**: loopback bind, token auth, strict desktop-id regex, allowlisted path resolution, no shell invocation, no raw `Exec` in JSON.
- [ ] **Step 3: Add Device Apps glass launcher** to Desktop only when the bridge is reachable; clicking an app posts its desktop ID to the bridge.
- [ ] **Step 4: Add elementary launcher** that starts the bridge, starts `python3 -m http.server` on port 4173, passes the token in the URL fragment, and opens Chromium/Chrome app/fullscreen mode or Firefox kiosk fallback without altering Pantheon/Gala configuration.

### Task 5: CI build, package, verify

**Files:**
- Create: `.github/workflows/build-appleos-web-pwa.yml`
- Create: `appleos-web/README.md`

**Interfaces:**
- Produces GitHub Actions artifact `AppleOS-Web-PWA` containing `AppleOS-Web-PWA.zip` and the unpacked `AppleOS-Web/` folder.

- [ ] **Step 1: Workflow checks out PearisticOS and clones upstream ThanasOS** at build time.
- [ ] **Step 2: Run RED/GREEN source and bridge acceptance tests**, install ThanasOS dependencies, build normal Vite chunks, compile WASM, assemble PWA, and run final acceptance tests.
- [ ] **Step 3: Verify no monolithic output**: root `index.html` remains small, `mobile/index.html` remains separate and >20 MB, `desktop/assets/` contains multiple Vite assets, and the WASM binary instantiates.
- [ ] **Step 4: ZIP the finished project** preserving executable bits where possible and upload it as the Actions artifact.
- [ ] **Step 5: Download the successful artifact and inspect ZIP integrity** before reporting completion.
