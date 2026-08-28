import './wasm-math.js';
import { startAppleOSEffects } from './gpu-effects.js';

const qs = (selector) => document.querySelector(selector);
const fullscreenNote = qs('#fullscreen-note');
const gpuStatus = qs('#gpu-status');
const wasmStatus = qs('#wasm-status');
const pwaStatus = qs('#pwa-status');
const installButton = qs('#install-button');

function rememberBridgeTokenFromHash() {
  const raw = location.hash.startsWith('#') ? location.hash.slice(1) : '';
  if (!raw) return;
  const params = new URLSearchParams(raw);
  const token = params.get('bridgeToken');
  if (!token) return;
  sessionStorage.setItem('appleosBridgeToken', token);
  history.replaceState(null, '', location.pathname + location.search);
}

rememberBridgeTokenFromHash();

const canvas = qs('#appleos-effects');
if (canvas) {
  startAppleOSEffects(canvas).then((backend) => {
    if (gpuStatus) {
      gpuStatus.textContent = backend === 'webgpu' ? 'WebGPU active' : backend === 'webgl2' ? 'WebGL2 fallback' : 'CSS fallback';
      gpuStatus.classList.add('ok');
    }
  }).catch(() => {
    document.body.classList.add('appleos-css-fallback');
    if (gpuStatus) gpuStatus.textContent = 'CSS fallback';
  });
}

window.addEventListener('appleos:wasm-ready', (event) => {
  const backend = event.detail?.backend || window.AppleOSMath?.backend || 'js';
  if (wasmStatus) {
    wasmStatus.textContent = backend === 'wasm' ? 'WASM math active' : 'JS math fallback';
    wasmStatus.classList.add('ok');
  }
});
setTimeout(() => {
  if (wasmStatus && !wasmStatus.classList.contains('ok')) {
    wasmStatus.textContent = window.AppleOSMath?.backend === 'wasm' ? 'WASM math active' : 'JS math fallback';
    wasmStatus.classList.add('ok');
  }
}, 900);

if ('serviceWorker' in navigator) {
  addEventListener('load', async () => {
    try {
      await navigator.serviceWorker.register('./service-worker.js', { scope: './' });
      pwaStatus?.classList.add('ok');
      if (pwaStatus) pwaStatus.textContent = 'PWA offline shell ready';
    } catch {
      if (pwaStatus) pwaStatus.textContent = 'PWA online mode';
    }
  });
}

for (const button of document.querySelectorAll('.mode-card[data-target]')) {
  button.addEventListener('click', async () => {
    const target = button.getAttribute('data-target');
    if (!target) return;
    try {
      if (!document.fullscreenElement && document.documentElement.requestFullscreen) {
        await document.documentElement.requestFullscreen({ navigationUI: 'hide' });
      }
      if (fullscreenNote) fullscreenNote.hidden = true;
    } catch {
      if (fullscreenNote) fullscreenNote.hidden = false;
    }
    button.animate(
      [
        { transform: 'translateY(-4px) scale(1.01)', opacity: 1 },
        { transform: 'translateY(4px) scale(.965)', opacity: .2 },
      ],
      { duration: 190, easing: 'cubic-bezier(.4,0,1,1)', fill: 'forwards' },
    );
    setTimeout(() => location.assign(target), 135);
  });
}

let deferredInstall = null;
window.addEventListener('beforeinstallprompt', (event) => {
  event.preventDefault();
  deferredInstall = event;
  if (installButton) installButton.hidden = false;
});

installButton?.addEventListener('click', async () => {
  if (!deferredInstall) return;
  await deferredInstall.prompt();
  deferredInstall = null;
  installButton.hidden = true;
});
