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

// IndexedDB setup for storing successful API responses
const dbPromise = new Promise((resolve, reject) => {
  const open = indexedDB.open('erp-sync', 1);
  open.onupgradeneeded = () => open.result.createObjectStore('responses');
  open.onsuccess = () => resolve(open.result);
  open.onerror = () => reject(open.error);
});

async function storeResponse(url, data) {
  const db = await dbPromise;
  const tx = db.transaction('responses', 'readwrite');
  tx.objectStore('responses').put(data, url);
  return tx.complete;
}

const sanitizeHeadersPlugin = {
  requestWillEnqueue: async ({request}) => {
    const headers = new Headers(request.headers);
    ['Authorization', 'Cookie'].forEach((h) => headers.delete(h));
    return {request: new Request(request, {headers})};
  }
};

const bgSyncPlugin = new workbox.backgroundSync.BackgroundSyncPlugin('apiQueue', {
  maxRetentionTime: 24 * 60
});

const apiStrategy = new workbox.strategies.NetworkFirst({
  cacheName: 'api-cache',
  plugins: [
    {
      fetchDidSucceed: async ({request, response}) => {
        if (request.method === 'GET' && !request.headers.has('Authorization')) {
          const clone = response.clone();
          try {
            const data = await clone.json();
            storeResponse(request.url, data);
          } catch (_) {}
        }
        return response;
      }
    },
    sanitizeHeadersPlugin,
    bgSyncPlugin
  ]
});

workbox.routing.registerRoute(/\/api\//, apiStrategy);

self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
