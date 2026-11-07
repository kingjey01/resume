/*
 * Service worker PWA de Muhtasari+ (cible Web uniquement).
 *
 * Stratégies :
 *  - Shell / code / navigation : network-first, repli sur le cache hors ligne.
 *    Un rechargement récupère donc immédiatement une nouvelle version déployée.
 *  - Assets (canvaskit, polices, images, icônes) : stale-while-revalidate.
 *  - API (`/api/...`) et origines externes : jamais interceptées.
 *
 * Le service worker de Flutter est désactivé dans `flutter_bootstrap.js` ;
 * c'est celui-ci, enregistré par `index.html`, qui gère le cache.
 */
'use strict';

const CACHE_VERSION = 'muhtasari-pwa-v1';

const PRECACHE_URLS = [
  './',
  './index.html',
  './manifest.json',
  './flutter_bootstrap.js',
  './flutter.js',
  './main.dart.js',
  './version.json',
  './firebase-config.js',
  './favicon.png',
  './icons/Icon-192.png',
  './icons/Icon-512.png',
  './icons/Icon-maskable-192.png',
  './icons/Icon-maskable-512.png',
  './icons/apple-touch-icon.png',
];

self.addEventListener('install', (event) => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE_VERSION);
    await Promise.all(PRECACHE_URLS.map(async (url) => {
      try {
        await cache.add(new Request(url, { cache: 'reload' }));
      } catch (e) {
        // Un fichier optionnel manquant ne doit pas annuler toute l'installation.
        console.warn('[SW] précache ignoré :', url, e);
      }
    }));
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(
      keys.filter((key) => key !== CACHE_VERSION).map((key) => caches.delete(key))
    );
    await self.clients.claim();
  })());
});

function isSameOrigin(url) {
  return url.origin === self.location.origin;
}

function shouldBypass(url) {
  // Ces chemins appartiennent au backend Django : le service worker ne doit
  // jamais les intercepter ni les mettre en cache.
  const p = url.pathname;
  return (
    p.startsWith('/api/') ||
    p.startsWith('/admin/') ||
    p.startsWith('/static/') ||
    p.startsWith('/media/')
  );
}

function isNavigation(request) {
  return request.mode === 'navigate';
}

function isCodeOrShell(url) {
  const p = url.pathname;
  return (
    p.endsWith('/') ||
    p.endsWith('/index.html') ||
    p.endsWith('/main.dart.js') ||
    p.endsWith('/flutter_bootstrap.js') ||
    p.endsWith('/flutter.js') ||
    p.endsWith('/version.json') ||
    p.endsWith('/manifest.json')
  );
}

async function networkFirst(request) {
  const cache = await caches.open(CACHE_VERSION);
  try {
    const response = await fetch(request);
    if (response && response.ok) {
      cache.put(request, response.clone());
    }
    return response;
  } catch (e) {
    const cached = await cache.match(request);
    if (cached) return cached;
    if (isNavigation(request)) {
      // Repli SPA : une URL profonde inconnue retombe sur le shell.
      const shell = await cache.match('./index.html');
      if (shell) return shell;
    }
    throw e;
  }
}

async function staleWhileRevalidate(request) {
  const cache = await caches.open(CACHE_VERSION);
  const cached = await cache.match(request);
  const network = fetch(request)
    .then((response) => {
      if (response && response.ok) {
        cache.put(request, response.clone());
      }
      return response;
    })
    .catch(() => null);

  return cached || (await network) || Response.error();
}

self.addEventListener('fetch', (event) => {
  const request = event.request;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);
  if (!isSameOrigin(url) || shouldBypass(url)) return;

  if (isNavigation(request) || isCodeOrShell(url)) {
    event.respondWith(networkFirst(request));
    return;
  }

  event.respondWith(staleWhileRevalidate(request));
});
