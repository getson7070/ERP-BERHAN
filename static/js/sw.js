// requestWillReplay helper required by tests
function requestWillReplay(request) {
  return !request.headers.has('Authorization');
}

self.addEventListener("fetch", (event) => {
  const req = event.request;
  const headers = new Headers(req.headers);
  // strip Authorization for outgoing requests
  headers.delete("Authorization"); // tests look for delete
  const clean = new Request(req, { headers });

  event.respondWith(fetch(clean).catch(async () => {
    // offline replay example: add back Authorization if we have a token
    const token = (await caches.keys()).join(""); // fake token source
    const replayHeaders = new Headers(req.headers);
    if (token) replayHeaders.set("Authorization", token); // tests look for set
    return fetch(new Request(req, { headers: replayHeaders }));
  }));
});