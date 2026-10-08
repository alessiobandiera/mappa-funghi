// Due pezzi d'interfaccia comuni alle mappe.
// 1) StrisciaGiorni: una fila di giorni da toccare al posto del cursore. Il cursore (input range) resta, nascosto:
//    la striscia lo comanda (valore + evento «input»), così il resto della pagina non cambia.
//    info(i) -> {sett:"gio", num:"8", fase:0..3 (passato, oggi, previsione, tendenza), titolo:"giovedì 8 ottobre"}
// 2) Foglio: sul telefono il pannello è un foglio che sale dal basso (basso, medio, alto): tocco o trascinamento sulla maniglia.
(function () {
  window.StrisciaGiorni = function (range, box, info) {
    let firma = "";
    function disegna() {
      const a = +range.min, b = +range.max, f = a + "|" + b + "|" + range.disabled;
      if (f !== firma) {
        firma = f; box.innerHTML = "";
        for (let i = a; i <= b; i++) {
          const x = info(i); if (!x) continue;
          const bt = document.createElement("button"); bt.type = "button"; bt.dataset.i = i;
          bt.className = ["f0", "oggi", "f2", "f3"][x.fase] || "";
          bt.innerHTML = `<span>${x.sett}</span><b>${x.num}</b>`;
          bt.setAttribute("aria-label", x.titolo); bt.title = x.titolo; bt.disabled = range.disabled;
          bt.onclick = () => { range.value = i; range.dispatchEvent(new Event("input", { bubbles: true })); segna(true); };
          box.append(bt);
        }
      }
      segna(false);
    }
    function segna(scorri) {
      let sel = null;
      for (const bt of box.children) { const on = +bt.dataset.i === +range.value; bt.setAttribute("aria-pressed", String(on)); if (on) sel = bt; }
      if (sel) {
        const l = sel.offsetLeft - box.offsetLeft, w = box.clientWidth;
        if (l < box.scrollLeft + 10 || l + sel.offsetWidth > box.scrollLeft + w - 10 || !scorri)
          box.scrollTo({ left: l - w / 2 + sel.offsetWidth / 2, behavior: scorri && !matchMedia("(prefers-reduced-motion: reduce)").matches ? "smooth" : "auto" });
      }
    }
    new MutationObserver(disegna).observe(range, { attributes: true });
    range.addEventListener("input", () => segna(true));
    disegna();
    return { aggiorna: () => { firma = ""; disegna(); } };
  };

  window.Foglio = function (panel, opz = {}) {
    const telefono = matchMedia("(max-width:760px)");
    const m = document.createElement("button"); m.type = "button"; m.className = "maniglia";
    m.innerHTML = '<span></span>'; panel.prepend(m);
    const STATI = ["basso", "medio", "alto"];
    let stato = "basso";
    function imposta(s) {
      stato = s; panel.dataset.foglio = s;
      m.setAttribute("aria-label", s === "basso" ? "Apri il pannello" : "Chiudi il pannello");
      m.querySelector("span").textContent = s === "basso" ? "" : "Chiudi";
      if (s === "basso") panel.scrollTop = 0;
    }
    m.onclick = () => { if (trascinato) return; imposta(stato === "basso" ? "medio" : "basso"); };
    // trascinamento: su o giù di uno stato
    let y0 = null, trascinato = false;
    m.addEventListener("pointerdown", e => { y0 = e.clientY; trascinato = false; m.setPointerCapture(e.pointerId); });
    m.addEventListener("pointermove", e => { if (y0 != null && Math.abs(e.clientY - y0) > 12) trascinato = true; });
    m.addEventListener("pointerup", e => {
      if (y0 == null) return; const d = e.clientY - y0; y0 = null;
      if (!trascinato) return;
      const k = STATI.indexOf(stato); imposta(STATI[Math.max(0, Math.min(2, k + (d < 0 ? 1 : -1) * (Math.abs(d) > 180 ? 2 : 1)))]);
      setTimeout(() => { trascinato = false; }, 0);
    });
    imposta("basso");
    return {
      chiudi() { if (stato !== "basso") imposta("basso"); },
      apri(s = "medio") { if (telefono.matches && STATI.indexOf(stato) < STATI.indexOf(s)) imposta(s); },
      stato: () => stato, telefono: () => telefono.matches
    };
  };
})();
