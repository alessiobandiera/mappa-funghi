// Fa funzionare la pagina delle raccolte anche senza rete (nel bosco). Riguarda solo raccolte.* e Leaflet, non la mappa.
const CACHE = "raccolte-v4";
const BASE = ["raccolte.html", "raccolte.webmanifest", "raccolte-icona-180.png", "raccolte-icona-512.png"];
const LEAFLET = ["https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js",
                 "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css"];
self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(BASE).then(() => c.addAll(LEAFLET).catch(() => {}))).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k.startsWith("raccolte-") && k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const u = new URL(e.request.url);
  if (e.request.method !== "GET") return;
  const nostra = u.origin === location.origin && /\/raccolte[^/]*$/.test(u.pathname);
  if (nostra) {
    // prima la rete (versione aggiornata), senza rete la copia salvata
    e.respondWith(fetch(e.request).then(r => { const c = r.clone(); caches.open(CACHE).then(k => k.put(e.request, c)); return r; })
      .catch(() => caches.match(e.request, { ignoreSearch: true })));
  } else if (LEAFLET.includes(u.href)) {
    e.respondWith(caches.match(e.request).then(r => r || fetch(e.request)));
  }
});
