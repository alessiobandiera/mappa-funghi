// Solo nell'app per iPhone (Capacitor): le pagine sono dentro l'app, i dati arrivano dal sito.
// Va caricato per primo in raccolte.html, index.html e bosco.html (lo inserisce app-ios/prepara.mjs). Nel sito non c'è.
//
// - dati/… e terreno/…: dal sito pubblicato; l'ultima copia resta nell'app (IndexedDB «app-copie») per quando la rete manca.
//   Meteo e indici: prima la rete (al massimo 6 s), poi la copia, con l'intestazione «X-Copia-Salvata» come nel sito.
//   Tessere a 20 m: prima la copia (le «zone salvate» non scadono, le altre al massimo TERRENO_MAX file), poi la rete.
// - sfondo delle mappe (Leaflet): le tessere già viste restano nell'app (al massimo SFONDO_MAX), nessuno scaricamento anticipato.
// - window.AppCopie: zone salvate per il bosco (usato da bosco.html al posto della Cache del browser).
(function () {
  const C = window.Capacitor;
  if (!(C && typeof C.isNativePlatform === "function" && C.isNativePlatform())) return;
  window.APP_NATIVA = true;
  const SITO = window.APP_SITO || "https://alessiobandiera.github.io/mappa-funghi/";
  const TERRENO_MAX = 150, SFONDO_MAX = 1500, ATTESA = 6000;
  const reteVera = window.fetch.bind(window);

  // ---- archivio delle copie
  const DB = new Promise((ok, ko) => {
    const r = indexedDB.open("app-copie", 1);
    r.onupgradeneeded = () => { const s = r.result.createObjectStore("file", { keyPath: "k" }); s.createIndex("gruppo", "gruppo"); };
    r.onsuccess = () => ok(r.result); r.onerror = () => ko(r.error);
  });
  const tx = async (modo, fn) => { const db = await DB; return new Promise((ok, ko) => {
    const t = db.transaction("file", modo), s = t.objectStore("file"), r = fn(s); t.oncomplete = () => ok(r && r.result); t.onerror = () => ko(t.error); }); };
  const leggi = k => tx("readonly", s => s.get(k));
  const scrivi = x => tx("readwrite", s => s.put(x)).catch(() => {});
  async function pota(gruppo, max) {
    const tutti = (await tx("readonly", s => s.index("gruppo").getAll(gruppo))) || [];
    const via = tutti.filter(x => !x.permanente).sort((a, b) => a.usato - b.usato);
    const troppi = tutti.length - max; if (troppi <= 0) return;
    await tx("readwrite", s => { via.slice(0, troppi + Math.round(max / 10)).forEach(x => s.delete(x.k)); });
  }
  const daCopia = (x, copia = true) => new Response(x.blob, { status: 200, headers: { "Content-Type": x.tipo || "application/octet-stream", ...(copia ? { "X-Copia-Salvata": x.salvato } : {}) } });
  async function salvaRisposta(k, r, gruppo, permanente) {
    const blob = await r.clone().blob(), vecchio = await leggi(k);
    await scrivi({ k, blob, tipo: r.headers.get("Content-Type") || "", salvato: new Date().toISOString(), usato: Date.now(), gruppo,
                   permanente: !!(permanente || (vecchio && vecchio.permanente)) });
  }

  // ---- dati dal sito: prima la rete con tempo limite, poi la copia
  async function reteConCopia(remoto, k) {
    const rete = reteVera(remoto, { cache: "no-store" }).then(async r => { if (r.ok) await salvaRisposta(k, r, "dati"); return r; });
    let timer; const tardi = new Promise(ok => { timer = setTimeout(ok, ATTESA, "tardi"); });
    try {
      const r = await Promise.race([rete, tardi]);
      if (r !== "tardi") { clearTimeout(timer); if (r.ok) return r; const c = await leggi(k); return c ? daCopia(c) : r; }
      const c = await leggi(k); if (c) return daCopia(c);
      return await rete;
    } catch (e) {
      clearTimeout(timer); const c = await leggi(k); if (c) return daCopia(c);
      throw e;
    }
  }
  // tessere a 20 m: prima la copia (rinfrescata di nascosto al massimo una volta al giorno), poi la rete
  async function terreno(remoto, k) {
    const c = await leggi(k);
    if (c) {
      if (Date.now() - Date.parse(c.salvato) > 864e5) reteVera(remoto).then(r => r.ok && salvaRisposta(k, r, "terreno")).catch(() => {});
      c.usato = Date.now(); scrivi(c); return daCopia(c, false);
    }
    const r = await reteVera(remoto);
    if (r.ok) { await salvaRisposta(k, r, "terreno"); pota("terreno", TERRENO_MAX); }
    return r;
  }
  window.fetch = async function (input, init) {
    const url = typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
    const u = new URL(url, location.href);
    if (u.origin === location.origin) {
      const p = u.pathname.replace(/^\/+/, "");
      if (/^(dati|terreno)\//.test(p)) {
        const remoto = SITO + p + u.search, k = SITO + p;
        if (p.startsWith("terreno/") && !/^terreno\/(tessere|campione)\.json$/.test(p)) return terreno(remoto, k);
        return reteConCopia(remoto, k);
      }
    }
    return reteVera(input, init);
  };

  // ---- zone salvate per il bosco (bosco.html)
  window.AppCopie = {
    async salva(urls, avanzamento) {
      let n = 0;
      for (const u of urls) {
        const p = new URL(u, location.href).pathname.replace(/^\/+/, ""), k = SITO + p;
        const r = await reteVera(SITO + p, { cache: "no-cache" });
        if (r.ok) await salvaRisposta(k, r, "terreno", true);
        else if (p.includes("/t/")) throw new Error(p + " " + r.status);
        avanzamento && avanzamento(++n / urls.length);
      }
    },
    async elenco() {
      const tutti = (await tx("readonly", s => s.index("gruppo").getAll("terreno"))) || [], ids = new Set(); let byte = 0;
      for (const x of tutti) if (x.permanente) { byte += x.blob.size; const m = x.k.match(/terreno\/t\/(.+)_a\.png$/); if (m) ids.add(m[1]); }
      return { ids: [...ids], byte };
    },
    async elimina() {
      const tutti = (await tx("readonly", s => s.index("gruppo").getAll("terreno"))) || [];
      await tx("readwrite", s => { tutti.filter(x => x.permanente).forEach(x => s.delete(x.k)); });
    }
  };

  // ---- sfondo delle mappe: Leaflet scarica le tessere con fetch e le tiene nell'app
  async function tessera(url) {
    const c = await leggi(url);
    if (c && Date.now() - Date.parse(c.salvato) < 7 * 864e5) return c.blob;
    try {
      const r = await reteVera(url, { mode: "cors" });
      if (!r.ok) throw new Error(r.status);
      await salvaRisposta(url, r, "sfondo"); pota("sfondo", SFONDO_MAX);
      return await r.blob();
    } catch (e) { if (c) return c.blob; throw e; }
  }
  function aggiusta(L) {
    if (!L || !L.TileLayer || L.__app) return; L.__app = true;
    L.TileLayer.prototype.createTile = function (coords, done) {
      const img = document.createElement("img"); img.alt = ""; img.setAttribute("role", "presentation");
      tessera(this.getTileUrl(coords)).then(b => {
        const u = URL.createObjectURL(b);
        img.onload = () => { URL.revokeObjectURL(u); done(null, img); }; img.onerror = e => { URL.revokeObjectURL(u); done(e, img); };
        img.src = u;
      }).catch(e => done(e, img));
      return img;
    };
  }
  // Leaflet arriva dopo (script nella pagina o caricato a richiesta): lo si aggiusta appena compare
  let Lvero = window.L;
  if (Lvero) aggiusta(Lvero);
  else Object.defineProperty(window, "L", { configurable: true, get: () => Lvero, set: v => { Lvero = v; aggiusta(v); } });
})();
