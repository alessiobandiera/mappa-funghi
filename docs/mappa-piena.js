// Mappa a schermo intero: un pulsante sulla mappa (sotto + e −) la allarga a tutto lo schermo e la rimette in finestra.
// Dove il browser lo permette (computer, Android, iPad) usa lo schermo intero vero; sull'iPhone allarga la mappa a tutta la pagina.
// Dentro l'app Raccolte (la pagina sta in un riquadro) chiede all'app di nascondere le sue barre.
// A schermo intero il pannello laterale sparisce: una barretta in basso tiene specie, vista e giorno (comanda i controlli del pannello).
// Uso: MappaPiena(map, {gruppi:[{sel:"#chips", nome:"Specie"}], giorno:"#day", etichetta:"#daylbl", onCambio:on=>{}})
(function () {
  const APRI = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/></svg>';
  const CHIUDI = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 4v5H4M15 4v5h5M9 20v-5H4M15 20v-5h5"/></svg>';
  const radice = document.documentElement, inRiquadro = window.parent !== window;
  const fsEl = () => document.fullscreenElement || document.webkitFullscreenElement;
  const zitto = p => { if (p && p.catch) p.catch(() => {}); };
  function chiediFS() {
    const r = radice.requestFullscreen || radice.webkitRequestFullscreen; if (!r) return false;
    try { zitto(r.call(radice)); return true; } catch (e) { return false; }
  }
  function esciFS() {
    if (!fsEl()) return; const f = document.exitFullscreen || document.webkitExitFullscreen;
    try { zitto(f.call(document)); } catch (e) {}
  }
  const css = document.createElement("style");
  css.textContent = `
.mp-ctl a{display:flex!important;align-items:center;justify-content:center;color:#333}
.mp-ctl svg{width:18px;height:18px}
.mp-barra{display:none;position:absolute;left:50%;bottom:calc(46px + env(safe-area-inset-bottom));transform:translateX(-50%);z-index:1000;
  background:var(--panel,#fff);color:var(--fg,#222);border:1px solid var(--line,#ccc);border-radius:14px;box-shadow:0 2px 12px rgba(0,0,0,.28);
  padding:6px;gap:6px;align-items:center;justify-content:center;flex-wrap:wrap;width:max-content;max-width:calc(100% - 24px);
  font:500 14px/1.2 var(--body,system-ui,sans-serif)}
.mappa-piena .mp-barra{display:flex}
.mp-barra select{font:inherit;color:inherit;background:var(--chip,transparent);border:1px solid var(--line,#ccc);border-radius:9px;padding:6px 8px;min-height:38px;max-width:12em}
.mp-giorno{display:flex;align-items:center;gap:4px}
.mp-giorno button{width:38px;height:38px;border-radius:9px;border:1px solid var(--line,#ccc);background:var(--chip,transparent);color:inherit;font:600 20px/1 system-ui,sans-serif;cursor:pointer}
.mp-giorno button:disabled{opacity:.35;cursor:default}
.mp-giorno span{min-width:7.5em;text-align:center;font-variant-numeric:tabular-nums}`;
  document.head.append(css);

  window.MappaPiena = function (map, opz = {}) {
    let on = false, mioFS = false;
    const Ctl = L.Control.extend({
      options: { position: "topleft" },
      onAdd() {
        const d = L.DomUtil.create("div", "leaflet-bar mp-ctl"), a = L.DomUtil.create("a", "", d);
        a.href = "#"; a.setAttribute("role", "button");
        L.DomEvent.disableClickPropagation(d);
        // stop: l'icona viene sostituita durante il clic, e senza fermarlo la mappa riceverebbe il clic (e aprirebbe un fumetto)
        L.DomEvent.on(a, "click", e => { L.DomEvent.stop(e); imposta(!on); });
        this.a = a; return d;
      }
    });
    const ctl = new Ctl().addTo(map);

    // ---- barretta in basso (solo a schermo intero)
    let barra = null; const gruppi = []; let giorno = null;
    if ((opz.gruppi && opz.gruppi.length) || opz.giorno) {
      barra = L.DomUtil.create("div", "mp-barra", map.getContainer());
      L.DomEvent.disableClickPropagation(barra); L.DomEvent.disableScrollPropagation(barra);
      const oss = new MutationObserver(() => aggiornaBarra());
      for (const g of opz.gruppi || []) {
        const box = document.querySelector(g.sel); if (!box) continue;
        const s = document.createElement("select"); s.setAttribute("aria-label", g.nome || "Scelta");
        s.onchange = () => { const b = box.querySelectorAll("button")[+s.value]; if (b) b.click(); };
        barra.append(s); gruppi.push({ box, s, firma: "" });
        oss.observe(box, { attributes: true, attributeFilter: ["aria-pressed"], subtree: true, childList: true });
      }
      const r = opz.giorno && document.querySelector(opz.giorno), lbl = opz.etichetta && document.querySelector(opz.etichetta);
      if (r) {
        const w = document.createElement("div"); w.className = "mp-giorno";
        w.innerHTML = '<button type="button" aria-label="Giorno prima">‹</button><span aria-live="polite"></span><button type="button" aria-label="Giorno dopo">›</button>';
        const [meno, t, piu] = w.children;
        const passo = d => {
          const v = Math.max(+r.min, Math.min(+r.max, +r.value + d)); if (v === +r.value) return;
          r.value = v; r.dispatchEvent(new Event("input", { bubbles: true })); aggiornaBarra();
        };
        meno.onclick = () => passo(-1); piu.onclick = () => passo(1);
        barra.append(w); giorno = { r, lbl, meno, t, piu };
        oss.observe(r, { attributes: true });
        if (lbl) oss.observe(lbl, { childList: true, characterData: true, subtree: true });
      }
    }
    function aggiornaBarra() {
      if (!barra || !on) return;
      for (const g of gruppi) {
        const bb = [...g.box.querySelectorAll("button")], firma = bb.map(b => b.textContent).join("|");
        if (firma !== g.firma) { g.firma = firma; g.s.innerHTML = bb.map((b, i) => `<option value="${i}">${b.textContent}</option>`).join(""); }
        const k = bb.findIndex(b => b.getAttribute("aria-pressed") === "true"); if (k >= 0) g.s.value = k;
      }
      if (giorno) {
        const { r, lbl, meno, t, piu } = giorno;
        t.textContent = lbl ? lbl.textContent : r.value;
        meno.disabled = r.disabled || +r.value <= +r.min; piu.disabled = r.disabled || +r.value >= +r.max;
      }
    }

    function pulsante() {
      ctl.a.innerHTML = on ? CHIUDI : APRI;
      const t = on ? "Torna alla finestra" : "Mappa a schermo intero";
      ctl.a.title = t; ctl.a.setAttribute("aria-label", t); ctl.a.setAttribute("aria-pressed", String(on));
    }
    function imposta(v, daFuori) {
      v = !!v; if (v === on) return; on = v;
      radice.classList.toggle("mappa-piena", on);
      pulsante(); aggiornaBarra();
      if (inRiquadro) { try { parent.postMessage({ tipo: "mappa-piena", on }, location.origin); } catch (e) {} }
      else if (on) mioFS = chiediFS();
      else { if (mioFS && !daFuori) esciFS(); mioFS = false; }
      requestAnimationFrame(() => map.invalidateSize()); setTimeout(() => map.invalidateSize(), 300);
      if (opz.onCambio) opz.onCambio(on);
    }
    document.addEventListener("keydown", e => { if (e.key === "Escape" && on && !fsEl()) imposta(false); });
    const cambioFS = () => { if (!fsEl() && on && mioFS) imposta(false, true); else map.invalidateSize(); };
    document.addEventListener("fullscreenchange", cambioFS); document.addEventListener("webkitfullscreenchange", cambioFS);
    addEventListener("message", e => { if (e.origin === location.origin && e.data && e.data.tipo === "mappa-piena-esci") imposta(false, true); });
    pulsante();
    return { attiva: () => on, imposta };
  };
})();
