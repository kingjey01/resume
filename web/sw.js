// Service Worker to block Google Fonts requests
self.addEventListener('fetch', function(event) {
  // Block Google Fonts requests
  if (event.request.url.includes('fonts.gstatic.com') || 
      event.request.url.includes('fonts.googleapis.com')) {
    event.respondWith(new Response(null, { status: 204 }));
    return;
  }
  
  // Let other requests pass through
  event.respondWith(fetch(event.request));
});

self.addEventListener('install', function(event) {
  self.skipWaiting();
});

self.addEventListener('activate', function(event) {
  event.waitUntil(self.clients.claim());
});