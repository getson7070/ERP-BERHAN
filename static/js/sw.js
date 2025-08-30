importScripts('https://storage.googleapis.com/workbox-cdn/releases/6.5.4/workbox-sw.js');

workbox.setConfig({debug: false});
workbox.core.skipWaiting();
workbox.core.clientsClaim();

// Basic precache of core pages
const PRECACHE = ['/', '/choose_login', '/dashboard', '/search'];
workbox.precaching.precacheAndRoute(PRECACHE);

// Cache static assets with a stale-while-revalidate strategy
workbox.routing.registerRoute(
  ({request}) => ['document', 'script', 'style', 'image'].includes(request.destination),
  new workbox.strategies.StaleWhileRevalidate({cacheName: 'static-resources'})
);

// Background sync strategy for API writes
const apiQueuePlugin = new workbox.backgroundSync.BackgroundSyncPlugin('apiQueue', { maxRetentionTime: 60 });

// Remove sensitive headers on queued requests
const sanitizeHeadersPlugin = {
  requestWillFetch: async ({request}) => {
    const url = new URL(request.url);
    if (url.pathname.startsWith('/api/')) {
      const headers = new Headers(request.headers);
      headers.delete('Authorization');
      headers.delete('Cookie');
      return new Request(request, { headers });
    }
    return request;
  }
};

const apiStrategy = new workbox.strategies.NetworkOnly({ plugins: [sanitizeHeadersPlugin, apiQueuePlugin] });
workbox.routing.registerRoute(/\/api\//, apiStrategy);

// Never cache authenticated responses
workbox.routing.registerRoute(
  ({request}) => request.url.includes('/api/'),
  new workbox.strategies.NetworkOnly()
);

self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
