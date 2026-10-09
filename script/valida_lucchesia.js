// Verifica sui casi della Lucchesia (data/validazione): pioggia misurata dalle stazioni SIR (entro 12 km), temperature SIR
// corrette per la quota; umidità del suolo da NASA POWER. Indice del porcino con lo stesso codice della mappa (docs/porcini.js):
// bosco castagno oppure stimato dalla quota, quota neutra (800 m). Temperatura del suolo = media dell'aria, come la mappa
// (Open-Meteo 6 cm è in media uguale alla media dell'aria: verificato il 9/10/2026).
// Uso: node script/valida_lucchesia.js
const fs = require("fs"); global.window = {}; require("./valida_regole.js"); const ML = window.ML;
const P = {}; new Function("P", fs.readFileSync(__dirname + "/../docs/porcini.js", "utf8") + ";Object.assign(P,{valutaPorcino,tipoStimato});")(P);
const S = JSON.parse(fs.readFileSync("data/validazione/serie.json")), SIR = JSON.parse(fs.readFileSync("data/validazione/serie_sir.json"));
const CASI = JSON.parse(fs.readFileSync("data/validazione/casi.json")), indice = new Map(CASI.map((c, i) => [`${c[0]}|${c[2].toFixed(2)}|${c[3].toFixed(2)}`, i]));
function conSir(r) {
  const ci = indice.get(`${r.data}|${(+r.lat).toFixed(2)}|${(+r.lon).toFixed(2)}`); if (ci == null) return null; const s = SIR.casi[String(ci)]; if (!s) return null;
  const pl = s.pluvio.filter(([, k]) => k <= 12), tm = s.termo.filter(([id, k]) => k <= 15 && SIR.stazioni[id].quota != null); if (!pl.length) return null; let gp = 0;
  const serie = r.serie.map(x => { const y = { ...x }; const pesi = pl.filter(([, , d]) => x.d in d).map(([, k, d]) => [d[x.d], 1 / Math.max(k, 1) ** 2]);
    if (pesi.length) { y.p = Math.round(10 * pesi.reduce((a, [v, w]) => a + v * w, 0) / pesi.reduce((a, [, w]) => a + w, 0)) / 10; gp++; }
    for (const [id, , d] of tm) if (x.d in d) { const c = (SIR.stazioni[id].quota - r.quota) * .0065; y.tn = d[x.d][0] + c; y.tx = d[x.d][1] + c; break; }
    return y; });
  return gp < .8 * serie.length ? null : { ...r, serie };
}
const casi = ML.prepara(S.casi.filter(c => c.lat >= 43.7 && c.lat <= 44.45 && c.lon >= 9.85 && c.lon <= 11).map(conSir).filter(Boolean)), y = casi.map(c => c.y);
for (const c of casi) for (const x of c.D) x.st = x.tmed;   // suolo = media dell'aria, come la mappa
const finestra = (c, f) => { let m = 0; for (let i = c.lo; i <= c.hi; i++) m = Math.max(m, f(c, i)); return m; };
console.log(`Lucchesia: ${casi.length} casi (${y.filter(Boolean).length} con funghi)`);
for (const [nome, f] of [["castagno", (c, i) => P.valutaPorcino(c.D, i, 800, "castagno").v],
                         ["bosco stimato dalla quota", (c, i) => P.valutaPorcino(c.D, i, 800, P.tipoStimato(c.lat, c.lon, c.quota)).v]]) {
  const s = casi.map(c => finestra(c, f)), pos = s.filter((_, i) => y[i]), neg = s.filter((_, i) => !y[i]), med = a => [...a].sort((p, q) => p - q)[a.length >> 1].toFixed(0);
  console.log(`  ${nome.padEnd(26)} AUC ${ML.auc(s, y).toFixed(3)}   con funghi ≥30: ${pos.filter(v => v >= 30).length}/${pos.length}   senza ≥30: ${neg.filter(v => v >= 30).length}/${neg.length}   mediane ${med(pos)} / ${med(neg)}`);
}
