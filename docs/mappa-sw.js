// Mappe senza rete (17/10/2026): tiene l'ultima previsione e le pagine, così nel bosco senza segnale si vede l'ultima
// previsione scaricata. Riguarda index.html e bosco.html; le pagine delle raccolte hanno il loro (raccolte-sw.js).
//
// - pagine, programmi e dati (meteo, boschi, stazioni): prima la rete, con un tempo limite; senza rete o con rete troppo lenta
//   la copia salvata, segnata con l'intestazione «X-Copia-Salvata» (le pagine lo dicono a chi guarda)
// - terreno a 20 m (docs/terreno/*): le tessere salvate a mano («Salva questa zona», cache ZONE, senza scadenza) e le ultime viste
// - sfondo della mappa (Esri, OpenTopoMap): solo le parti già guardate, al massimo SFONDO_MAX, rinnovate dopo 7 giorni; nessuno
//   scaricamento in anticipo (le regole dei servizi di mappe non lo permettono)
// - Leaflet e caratteri: copia salvata se c'è
// Per spegnerlo in caso di guai: pubblicare questo file con SPEGNI = true (si cancella da solo e cancella le copie).
const SPEGNI = false;
const V = "v1";
const PAGINE = "mappa-pagine-" + V, DATI = "mappa-dati-" + V, TERRENO = "mappa-terreno-" + V, ZONE = "mappa-zone",
      SFONDO = "mappa-sfondo-" + V, LIBRERIE = "mappa-librerie-" + V;
const TERRENO_MAX = 150, SFONDO_MAX = 1500, SFONDO_GIORNI = 7;     // al massimo ~20 MB di terreno visto e ~30 MB di sfondo
const ATTESA_PAGINE = 4000, ATTESA_DATI = 6000;     // ms: oltre, si usa la copia salvata (la risposta della rete aggiorna la copia)

self.addEventListener("install", e => { self.skipWaiting(); });
self.addEventListener("activate", e => {
  e.waitUntil((async () => {
    const tutte = await caches.keys();
    if (SPEGNI) {
      await Promise.all(tutte.filter(k => k.startsWith("mappa-")).map(k => caches.delete(k)));
      await self.registration.unregister();
      return;
    }
    const buone = [PAGINE, DATI, TERRENO, ZONE, SFONDO, LIBRERIE];
    await Promise.all(tutte.filter(k => k.startsWith("mappa-") && !buone.includes(k)).map(k => caches.delete(k)));
    await self.clients.claim();
  })());
});

const base = new URL("./", self.registration.scope).pathname;          // /mappa-funghi/
const chiave = u => { const x = new URL(u); x.search = ""; x.hash = ""; if (x.pathname === base) x.pathname = base + "index.html"; return x.href; };
// copia da salvare: corpo già decompresso, quindi senza le intestazioni della compressione; con la data del salvataggio
const daSalvare = async r => {
  const h = new Headers(r.headers); h.delete("content-encoding"); h.delete("content-length"); h.set("X-Salvato", new Date().toISOString());
  return new Response(await r.clone().blob(), { status: r.status, statusText: r.statusText, headers: h });
};
// se il telefono non ha più spazio la copia non si salva, ma la risposta della rete arriva lo stesso
const salva = async (cache, k, r) => { try { await cache.put(k, await daSalvare(r)); } catch (e) {} };
const conCopia = (r, quando) => {
  const h = new Headers(r.headers); h.set("X-Copia-Salvata", quando || "1");
  return new Response(r.body, { status: r.status, statusText: r.statusText, headers: h });
};

// prima la rete con tempo limite; la risposta della rete (anche se arriva tardi) aggiorna la copia
async function reteConCopia(req, nomeCache, attesa) {
  const k = chiave(req.url), cache = await caches.open(nomeCache);
  const rete = fetch(req).then(async r => {
    if (r.ok && r.type === "basic") await salva(cache, k, r);
    return r;
  });
  const copia = () => cache.match(k).then(c => c ? conCopia(c, c.headers.get("X-Salvato")) : null);
  let timer;
  const tardi = new Promise(res => { timer = setTimeout(res, attesa, "tardi"); });
  try {
    const r = await Promise.race([rete, tardi]);
    if (r !== "tardi") { clearTimeout(timer); return r; }
    const c = await copia(); if (c) return c;          // rete lenta: la copia, se c'è; altrimenti si aspetta la rete
    return await rete;
  } catch (err) {
    clearTimeout(timer);
    const c = await copia(); if (c) return c;
    return Response.error();
  }
}

// prima la copia (zone salvate, poi ultime viste), altrimenti la rete
async function terreno(req) {
  const k = chiave(req.url);
  const z = await (await caches.open(ZONE)).match(k); if (z) { aggiornaTerreno(req, k); return z; }
  const cache = await caches.open(TERRENO), c = await cache.match(k);
  if (c) { aggiornaTerreno(req, k); return c; }
  try {
    const r = await fetch(req);
    if (r.ok) { await salva(cache, k, r); pota(TERRENO, TERRENO_MAX); }
    return r;
  } catch (err) { return Response.error(); }
}
// le tessere cambiano solo quando si rifanno le carte: si rinfresca la copia di nascosto, al massimo una volta al giorno
const rinfrescate = new Map();
function aggiornaTerreno(req, k) {
  if (Date.now() - (rinfrescate.get(k) || 0) < 864e5) return; rinfrescate.set(k, Date.now());
  fetch(req, { cache: "no-cache" }).then(async r => {
    if (!r.ok) return;
    const zone = await caches.open(ZONE), vis = await caches.open(TERRENO);
    if (await zone.match(k)) await salva(zone, k, r);
    if (await vis.match(k)) await salva(vis, k, r);
  }).catch(() => {});
}
async function pota(nome, max) {
  const c = await caches.open(nome), ks = await c.keys();
  if (ks.length > max) await Promise.all(ks.slice(0, ks.length - max + Math.round(max / 10)).map(k => c.delete(k)));
}

// sfondo e librerie esterne: risposte CORS (le risposte «opache» pesano moltissimo nello spazio del browser)
async function esterno(req, nomeCache, max, giorni) {
  const k = req.url, cache = await caches.open(nomeCache), c = await cache.match(k) || (nomeCache === LIBRERIE ? await caches.match(k) : null);
  const vecchia = c && giorni && Date.now() - Date.parse(c.headers.get("X-Salvato") || 0) > giorni * 864e5;
  if (c && !vecchia) return c;
  try {
    const r = await fetch(k, { mode: "cors", credentials: "omit" });
    if (r.ok) {
      await salva(cache, k, r);
      if (max) pota(nomeCache, max);
      return r;
    }
    return c || r;
  } catch (err) {
    if (c) return c;
    try { return await fetch(req); } catch (e2) { return Response.error(); }
  }
}

const SFONDI = /(^|\.)(arcgisonline\.com|opentopomap\.org)$/;
const LIBRERIE_HOST = /^(cdnjs\.cloudflare\.com|fonts\.googleapis\.com|fonts\.gstatic\.com)$/;

self.addEventListener("fetch", e => {
  if (SPEGNI || e.request.method !== "GET") return;
  const u = new URL(e.request.url);
  if (u.origin === location.origin) {
    if (!u.pathname.startsWith(base)) return;
    const p = u.pathname.slice(base.length);
    if (/^raccolte/.test(p) || p === "mappa-sw.js") return;                  // l'app delle raccolte ha il suo
    if (p.startsWith("terreno/") && p !== "terreno/tessere.json" && p !== "terreno/campione.json") return e.respondWith(terreno(e.request));
    if (p.startsWith("dati/") || p.startsWith("terreno/")) return e.respondWith(reteConCopia(e.request, DATI, ATTESA_DATI));
    if (p === "" || /\.(html|js|css|png|svg|webmanifest)$/.test(p)) return e.respondWith(reteConCopia(e.request, PAGINE, ATTESA_PAGINE));
    return;
  }
  if (SFONDI.test(u.hostname)) return e.respondWith(esterno(e.request, SFONDO, SFONDO_MAX, SFONDO_GIORNI));
  if (LIBRERIE_HOST.test(u.hostname)) return e.respondWith(esterno(e.request, LIBRERIE, 0, 0));
});
