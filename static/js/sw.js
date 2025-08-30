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

// Reattach auth header when replaying queued requests
let authToken = null;
const authReattachPlugin = {
  async requestWillReplay({request}) {
    if (!authToken) return;
    const headers = new Headers(request.headers);
    headers.set('Authorization', `Bearer ${authToken}`);
    return new Request(request, { headers });
  }
};

// Do not cache authenticated GET responses
const noCacheAuthPlugin = {
  fetchDidSucceed: async ({request, response}) => {
    if (request.method === 'GET' && !request.headers.has('Authorization')) {
      return response;
    }
    return response;
  }
};

const apiStrategy = new workbox.strategies.NetworkOnly({ plugins: [noCacheAuthPlugin, sanitizeHeadersPlugin, authReattachPlugin, apiQueuePlugin] });
workbox.routing.registerRoute(/\/api\//, apiStrategy);

// Never cache authenticated responses
workbox.routing.registerRoute(
  ({request}) => request.url.includes('/api/'),
  new workbox.strategies.NetworkOnly()
);

self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SET_TOKEN') {
    authToken = event.data.token;
  }
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
