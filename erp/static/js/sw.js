// Minimal service worker that does NOT forward Authorization headers.
self.addEventListener('install', event => {
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(clients.claim());
});

self.addEventListener('fetch', event => {
  const req = event.request;
  const newHeaders = new Headers(req.headers);
  newHeaders.delete('Authorization');
  const cleanReq = new Request(req, { headers: newHeaders, credentials: 'omit' });
  event.respondWith(fetch(cleanReq).catch(() => new Response('offline', { status: 200 })));
});
