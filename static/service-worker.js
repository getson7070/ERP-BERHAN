self.addEventListener('install', (event) => {
  event.waitUntil(caches.open('erp-static-v1').then((c)=>c.addAll(['/','/static/style.css','/manifest.webmanifest'])));
});
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then((resp) => {
      return resp || fetch(event.request).then((response) => {
        const copy = response.clone();
        caches.open('erp-dynamic-v1').then((cache)=> cache.put(event.request, copy));
        return response;
      }).catch(()=> caches.match('/'));
    })
  );
});
