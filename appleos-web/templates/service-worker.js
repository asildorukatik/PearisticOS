const SHELL_CACHE = 'appleos-shell-v1';
const RUNTIME_CACHE = 'appleos-runtime-v1';
const PRECACHE = [
  './',
  './index.html',
  './manifest.webmanifest',
  './assets/css/appleos.css',
  './assets/js/app-shell.js',
  './assets/js/gpu-effects.js',
  './assets/js/wasm-math.js',
  './assets/icons/apple-logo-128.png',
  './assets/icons/apple-logo-192.png',
  './assets/icons/apple-logo-512.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(SHELL_CACHE).then((cache) => cache.addAll(PRECACHE)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(
      keys.filter((key) => key.startsWith('appleos-') && ![SHELL_CACHE, RUNTIME_CACHE].includes(key))
        .map((key) => caches.delete(key))
    )).then(() => self.clients.claim())
  );
});

async function networkFirst(request) {
  const cache = await caches.open(RUNTIME_CACHE);
  try {
    const response = await fetch(request);
    if (response && response.ok) cache.put(request, response.clone());
    return response;
  } catch {
    return (await cache.match(request)) || (await caches.match('./index.html'));
  }
}

async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;
  const response = await fetch(request);
  if (response && response.ok) {
    const cache = await caches.open(RUNTIME_CACHE);
    cache.put(request, response.clone());
  }
  return response;
}

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  if (event.request.method !== 'GET' || url.origin !== self.location.origin) return;

  if (event.request.mode === 'navigate' || event.request.destination === 'document') {
    event.respondWith(networkFirst(event.request));
    return;
  }

  if (url.pathname.includes('/desktop/assets/') || url.pathname.includes('/assets/wasm/')) {
    event.respondWith(cacheFirst(event.request));
    return;
  }

  // Cache Mobile and Desktop resources only after the user actually selects them.
  if (url.pathname.includes('/desktop/') || url.pathname.includes('/mobile/')) {
    event.respondWith(networkFirst(event.request));
    return;
  }

  event.respondWith(cacheFirst(event.request));
});
