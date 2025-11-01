self.addEventListener('install', event => {
  self.skipWaiting();
  event.waitUntil(caches.open('erp-cache-v1').then(cache => cache.addAll(['/','/offline'])));
});
self.addEventListener('activate', event => { self.clients.claim(); });
self.addEventListener('fetch', event => {
  event.respondWith(fetch(event.request).catch(() => caches.match(event.request)));
});
