const BRIDGE = 'http://127.0.0.1:8765';

function getToken() {
  const raw = location.hash.startsWith('#') ? location.hash.slice(1) : '';
  if (raw) {
    const params = new URLSearchParams(raw);
    const token = params.get('bridgeToken');
    if (token) {
      sessionStorage.setItem('appleosBridgeToken', token);
      history.replaceState(null, '', location.pathname + location.search);
      return token;
    }
  }
  return sessionStorage.getItem('appleosBridgeToken') || '';
}

function addStyles() {
  if (document.getElementById('appleos-device-apps-style')) return;
  const style = document.createElement('style');
  style.id = 'appleos-device-apps-style';
  style.textContent = `
#appleos-device-apps-button{position:fixed;left:10px;top:38px;z-index:2147483000;border:1px solid rgba(255,255,255,.16);border-radius:13px;padding:8px 11px;background:rgba(22,24,30,.42);color:#fff;font:600 11px Inter,-apple-system,sans-serif;backdrop-filter:blur(24px) saturate(160%);box-shadow:0 10px 28px rgba(0,0,0,.24),inset 0 1px rgba(255,255,255,.13);cursor:pointer;transition:transform .28s cubic-bezier(.16,1,.3,1),background .2s}
#appleos-device-apps-button:hover{transform:translateY(-2px) scale(1.025);background:rgba(46,49,60,.56)}
#appleos-device-apps-overlay{position:fixed;inset:0;z-index:2147483100;display:none;align-items:center;justify-content:center;padding:48px;background:rgba(0,0,0,.22);backdrop-filter:blur(34px) saturate(155%)}
#appleos-device-apps-overlay.open{display:flex;animation:appleosAppsIn .32s cubic-bezier(.16,1,.3,1) both}
#appleos-device-apps-panel{width:min(980px,94vw);max-height:82vh;overflow:hidden;border:1px solid rgba(255,255,255,.15);border-radius:30px;background:linear-gradient(145deg,rgba(38,40,48,.74),rgba(20,22,28,.64));box-shadow:0 32px 90px rgba(0,0,0,.44),inset 0 1px rgba(255,255,255,.16);padding:20px;display:flex;flex-direction:column;gap:16px}
.appleos-device-header{display:flex;gap:12px;align-items:center}.appleos-device-header h2{margin:0;font:650 20px Inter,-apple-system,sans-serif;color:white;flex:1}.appleos-device-search{width:min(320px,45vw);border:1px solid rgba(255,255,255,.11);border-radius:999px;padding:9px 14px;background:rgba(255,255,255,.08);color:#fff;outline:none}.appleos-device-close{border:0;background:rgba(255,255,255,.09);color:#fff;border-radius:999px;width:32px;height:32px;cursor:pointer}
#appleos-device-app-grid{overflow:auto;display:grid;grid-template-columns:repeat(auto-fill,minmax(105px,1fr));gap:16px;padding:5px 2px 14px}.appleos-native-app{border:0;background:transparent;color:#fff;display:flex;flex-direction:column;align-items:center;gap:8px;padding:8px;border-radius:18px;cursor:pointer;transition:transform .28s cubic-bezier(.16,1,.3,1),background .2s}.appleos-native-app:hover{transform:translateY(-5px) scale(1.04);background:rgba(255,255,255,.07)}.appleos-native-icon{width:66px;height:66px;border-radius:17px;display:grid;place-items:center;font:700 23px Inter,-apple-system,sans-serif;background:linear-gradient(145deg,rgba(105,145,255,.9),rgba(106,74,195,.82));box-shadow:inset 0 1px rgba(255,255,255,.35),0 9px 22px rgba(0,0,0,.24)}.appleos-native-name{max-width:96px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font:500 11px Inter,-apple-system,sans-serif}.appleos-native-meta{font:500 9px Inter,-apple-system,sans-serif;color:rgba(255,255,255,.43);max-width:96px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
@keyframes appleosAppsIn{from{opacity:0;transform:scale(1.025)}to{opacity:1;transform:scale(1)}}
@media(prefers-reduced-motion:reduce){#appleos-device-apps-button,.appleos-native-app{transition:none!important}#appleos-device-apps-overlay.open{animation:none!important}}
`;
  document.head.append(style);
}

async function api(path, options = {}) {
  const token = getToken();
  if (!token) throw new Error('No bridge token');
  const headers = new Headers(options.headers || {});
  headers.set('Authorization', `Bearer ${token}`);
  const response = await fetch(`${BRIDGE}${path}`, { ...options, headers });
  if (!response.ok) throw new Error(`Bridge ${response.status}`);
  return response;
}

async function launchApp(id, button) {
  button.disabled = true;
  try {
    await api(`/v1/apps/${encodeURIComponent(id)}/launch`, { method: 'POST' });
  } finally {
    setTimeout(() => { button.disabled = false; }, 350);
  }
}

function createUI(apps) {
  addStyles();
  const button = document.createElement('button');
  button.id = 'appleos-device-apps-button';
  button.textContent = `Applications · ${apps.length}`;
  button.title = 'Open applications installed on this device';

  const overlay = document.createElement('div');
  overlay.id = 'appleos-device-apps-overlay';
  overlay.innerHTML = `
    <div id="appleos-device-apps-panel" role="dialog" aria-modal="true" aria-label="Device applications">
      <div class="appleos-device-header">
        <h2>Device Applications</h2>
        <input class="appleos-device-search" type="search" placeholder="Search applications" aria-label="Search applications" />
        <button class="appleos-device-close" aria-label="Close">×</button>
      </div>
      <div id="appleos-device-app-grid"></div>
    </div>`;

  const grid = overlay.querySelector('#appleos-device-app-grid');
  const search = overlay.querySelector('.appleos-device-search');
  const close = () => overlay.classList.remove('open');

  const render = () => {
    const q = search.value.trim().toLowerCase();
    grid.replaceChildren();
    for (const app of apps.filter((item) => item.name.toLowerCase().includes(q))) {
      const appButton = document.createElement('button');
      appButton.className = 'appleos-native-app';
      appButton.title = app.name;
      const first = [...app.name.trim()][0]?.toUpperCase() || 'A';
      appButton.innerHTML = `<span class="appleos-native-icon">${first}</span><span class="appleos-native-name"></span><span class="appleos-native-meta"></span>`;
      appButton.querySelector('.appleos-native-name').textContent = app.name;
      appButton.querySelector('.appleos-native-meta').textContent = app.icon || 'Linux app';
      appButton.addEventListener('click', () => launchApp(app.id, appButton).catch(console.warn));
      grid.append(appButton);
    }
  };

  button.addEventListener('click', () => {
    overlay.classList.add('open');
    search.focus();
    render();
  });
  overlay.querySelector('.appleos-device-close').addEventListener('click', close);
  overlay.addEventListener('click', (event) => { if (event.target === overlay) close(); });
  search.addEventListener('input', render);
  addEventListener('keydown', (event) => { if (event.key === 'Escape') close(); });

  document.body.append(button, overlay);
}

async function connect() {
  const token = getToken();
  if (!token) return;
  try {
    const response = await api('/v1/apps');
    const payload = await response.json();
    if (Array.isArray(payload.apps)) createUI(payload.apps);
  } catch {
    // The bridge is optional. Normal AppleOS stays untouched when it is absent.
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', connect, { once: true });
} else {
  connect();
}
