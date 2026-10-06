// Confronto dell'indice sui casi di verifica con la pioggia MISURATA dalle stazioni SIR (come fa la mappa per i giorni passati)
// invece della pioggia della rianalisi Open-Meteo.
// Node:    node script/valida_sir.js [raggio_km=12]      (serve data/validazione/serie_om.json)
// Browser: con window.ML (valida_regole.js) caricato, window.OM = {casi:[...]} e window.SIR: ConfrontoSIR(OM, SIR, 12)
function ConfrontoSIR(OM, SIR, RAGGIO, ML, stampa) {
ML = ML || window.ML; RAGGIO = RAGGIO || 12;
const righeOut = []; const console = { log: t => { righeOut.push(t); if (stampa) stampa(t); } };
const RAGGIO_T = RAGGIO + 3;     // come aggiorna.py: 12 km pioggia, 15 km temperatura

// serie del caso con pioggia (media pesata 1/d², come fondi() in aggiorna.py) e temperature dalle stazioni SIR
function conSir(r, temperatura) {
  const s = SIR.casi[String(r.ci)]; if (!s) return null;
  const pl = s.pluvio.filter(([, k]) => k <= RAGGIO), tm = s.termo.filter(([id, k]) => k <= RAGGIO_T && SIR.stazioni[id].quota != null);
  if (!pl.length) return null;
  let giorniP = 0;
  const serie = r.serie.map(x => {
    const y = { ...x };
    const pesi = pl.filter(([, , d]) => x.d in d).map(([, k, d]) => [d[x.d], 1 / Math.max(k, 1) ** 2]);
    if (pesi.length) { y.p = Math.round(10 * pesi.reduce((a, [v, w]) => a + v * w, 0) / pesi.reduce((a, [, w]) => a + w, 0)) / 10; giorniP++; }
    if (temperatura) for (const [id, , d] of tm) if (x.d in d) {
      const corr = (SIR.stazioni[id].quota - r.quota) * 0.0065;
      y.tn = d[x.d][0] + corr; y.tx = d[x.d][1] + corr; break;
    }
    return y;
  });
  if (giorniP < 0.8 * serie.length) return null;
  return { ...r, serie, kmP: pl[0][1] };
}

const base = OM.casi;
const sir = base.map(r => conSir(r, false)), sirT = base.map(r => conSir(r, true));
const k = base.map((_, i) => sir[i] !== null);
const sel = a => a.filter((_, i) => k[i]);
const C = { om: ML.prepara(sel(base)), sir: ML.prepara(sel(sir)), sirT: ML.prepara(sel(sirT)) };
const y = C.om.map(c => c.y);
console.log(`raggio ${RAGGIO} km: casi con pluviometri SIR ${C.om.length} su ${base.length} (positivi ${y.reduce((a, b) => a + b, 0)})`);

// quanto differiscono le piogge: totale dei 10 giorni prima della data del caso
const t10 = c => { const i = c.D.findIndex(g => g.d === c.data); return c.D.slice(Math.max(0, i - 9), i + 1).reduce((a, g) => a + g.p, 0); };
const a = C.om.map(t10), b = C.sir.map(t10);
const corr = (u, v) => { const mu = u.reduce((s, x) => s + x, 0) / u.length, mv = v.reduce((s, x) => s + x, 0) / v.length;
  let n = 0, du = 0, dv = 0; u.forEach((x, i) => { n += (x - mu) * (v[i] - mv); du += (x - mu) ** 2; dv += (v[i] - mv) ** 2; }); return n / Math.sqrt(du * dv); };
const med = v => [...v].sort((x, z) => x - z)[v.length >> 1];
console.log(`pioggia dei 10 giorni prima: mediana Open-Meteo ${med(a).toFixed(0)} mm, SIR ${med(b).toFixed(0)} mm, correlazione ${corr(a, b).toFixed(2)}`);

// AUC con intervallo bootstrap e confronto appaiato
let seme = 7; const rnd = () => (seme = (seme * 16807) % 2147483647) / 2147483647;
function boot(s1, s0) {
  const d = [];
  for (let t = 0; t < 600; t++) {
    const ii = y.map(() => Math.floor(rnd() * y.length)), yy = ii.map(i => y[i]);
    if (!yy.some(v => v) || yy.every(v => v)) continue;
    d.push(ML.auc(ii.map(i => s1[i]), yy) - (s0 ? ML.auc(ii.map(i => s0[i]), yy) : 0));
  }
  d.sort((p, q) => p - q); return [d[Math.floor(d.length * .05)], d[Math.floor(d.length * .95)], d.filter(v => v > 0).length / d.length];
}
const punt = (cc, P) => cc.map(c => ML.punteggio(c, P));
const righe = [];
const riga = (nome, s, rif) => {
  const v = ML.auc(s, y), [lo, hi] = boot(s), alti = s.filter(x => x >= 60).length / s.length;
  let txt = `  ${nome.padEnd(46)} AUC ${v.toFixed(3)} (${lo.toFixed(2)}-${hi.toFixed(2)})  ≥60: ${(100 * alti).toFixed(0)}%`;
  if (rif) { const [dl, dh, pp] = boot(s, rif); txt += `  vs pioggia Open-Meteo ${dl >= 0 ? "+" : ""}${dl.toFixed(2)}…${dh >= 0 ? "+" : ""}${dh.toFixed(2)} (meglio nel ${(100 * pp).toFixed(0)}%)`; }
  console.log(txt); righe.push([nome, v]);
};
console.log("\nINDICE ATTUALE");
const sOM = punt(C.om, ML.ATTUALE);
riga("pioggia Open-Meteo (rianalisi)", sOM);
riga("pioggia SIR (come la mappa)", punt(C.sir, ML.ATTUALE), sOM);
riga("pioggia e temperature SIR", punt(C.sirT, ML.ATTUALE), sOM);
riga("Fungaiolo, pioggia Open-Meteo", C.om.map(ML.punteggioF));
riga("Fungaiolo, pioggia SIR", C.sir.map(ML.punteggioF));

console.log("\nPIOGGIA MINIMA SULL'INTERO PERIODO (pioggia SIR)");
const sSir = punt(C.sir, ML.ATTUALE);
for (const g of [7, 10, 14]) for (const mm of [30, 40, 60, 80])
  riga(`almeno ${mm} mm in ${g} giorni`, punt(C.sir, { ...ML.ATTUALE, cluster: g, totmin: mm }), sOM);
console.log("\n(stessa regola sulla pioggia Open-Meteo, per confronto)");
for (const mm of [40, 60]) riga(`Open-Meteo, almeno ${mm} mm in 10 giorni`, punt(C.om, { ...ML.ATTUALE, cluster: 10, totmin: mm }));

console.log("\nPER ZONA (indice attuale)");
const zone = [["Lucchesia, Garfagnana, Lunigiana, Abetone", c => c.lat >= 43.7 && c.lat <= 44.45 && c.lon >= 9.85 && c.lon <= 11]];
for (const [nome, f] of zone) {
  const kk = C.om.map(f), yy = y.filter((_, i) => kk[i]);
  if (yy.some(v => v) && !yy.every(v => v)) {
    const s1 = sOM.filter((_, i) => kk[i]), s2 = sSir.filter((_, i) => kk[i]);
    console.log(`  ${nome} n=${yy.length}: Open-Meteo ${ML.auc(s1, yy).toFixed(3)}, SIR ${ML.auc(s2, yy).toFixed(3)}`);
  }
}
return righeOut.join("\n");
}
if (typeof module !== "undefined" && require.main === module) {
  global.window = {};
  require("./valida_regole.js");
  const fs = require("fs");
  ConfrontoSIR(JSON.parse(fs.readFileSync("data/validazione/serie_om.json")), JSON.parse(fs.readFileSync("data/validazione/serie_sir.json")),
               +(process.argv[2] || 12), window.ML, t => console.log(t));
} else if (typeof window !== "undefined") window.ConfrontoSIR = ConfrontoSIR;
