// Il sole conta? Casi della Lucchesia (come valida_lucchesia.js: pioggia SIR, bosco castagno, quota neutra), indice della mappa
// con e senza una correzione per il sole dei giorni prima (frazione del sole possibile ERA5, data/validazione/sole.json).
// Uso: node script/sole_lucchesia.js
const fs = require("fs"); global.window = {}; require("./valida_regole.js"); const ML = window.ML;
const P = {}; new Function("P", fs.readFileSync(__dirname + "/../docs/porcini.js", "utf8") + ";Object.assign(P,{valutaPorcino,tipoStimato,trap});")(P);
const S = JSON.parse(fs.readFileSync("data/validazione/serie.json")), SIR = JSON.parse(fs.readFileSync("data/validazione/serie_sir.json"));
const SOLE = JSON.parse(fs.readFileSync("data/validazione/sole.json")).casi;
const CASI = JSON.parse(fs.readFileSync("data/validazione/casi.json")), indice = new Map(CASI.map((c, i) => [`${c[0]}|${c[2].toFixed(2)}|${c[3].toFixed(2)}`, i]));
const add = (d, n) => { const x = new Date(d + "T12:00:00Z"); x.setUTCDate(x.getUTCDate() + n); return x.toISOString().slice(0, 10); };
function durata(lat, iso) {
  const n = (Date.parse(iso + "T12:00:00Z") - Date.parse(iso.slice(0, 4) + "-01-01T00:00:00Z")) / 864e5;
  const dec = 23.44 * Math.PI / 180 * Math.sin(2 * Math.PI * (284 + n) / 365), f = lat * Math.PI / 180;
  const c = -Math.tan(f) * Math.tan(dec); return c >= 1 ? 0 : c <= -1 ? 24 : 24 * Math.acos(c) / Math.PI;
}
// stessa scelta dei pluviometri e degli orari di valida_lucchesia.js
function conSir(r) {
  const ci = indice.get(`${r.data}|${(+r.lat).toFixed(2)}|${(+r.lon).toFixed(2)}`); if (ci == null) return null; const s = SIR.casi[String(ci)]; if (!s) return null;
  const pl = s.pluvio.filter(([, k]) => k <= 12), tm = s.termo.filter(([id, k]) => k <= 15 && SIR.stazioni[id].quota != null); if (!pl.length) return null; let gp = 0;
  const serie = r.serie.map(x => { const y = { ...x }; const pesi = pl.filter(([, , d]) => x.d in d).map(([, k, d]) => [d[x.d], 1 / Math.max(k, 1) ** 2]);
    if (pesi.length) { y.p = Math.round(10 * pesi.reduce((a, [v, w]) => a + v * w, 0) / pesi.reduce((a, [, w]) => a + w, 0)) / 10; gp++; }
    for (const [id, , d] of tm) if (x.d in d) { const c = (SIR.stazioni[id].quota - r.quota) * .0065; y.tn = d[x.d][0] + c; y.tx = d[x.d][1] + c; break; }
    return y; });
  if (gp < .8 * serie.length) return null;
  const p = serie.map(x => x.p); serie.forEach((x, i) => { const dopo = i + 1 < p.length ? p[i + 1] : p[i]; x.p = .375 * p[i] + .625 * dopo; });
  return { ...r, serie };
}
const casi = ML.prepara(S.casi.filter(c => c.lat >= 43.7 && c.lat <= 44.45 && c.lon >= 9.85 && c.lon <= 11).map(conSir).filter(Boolean)).filter(c => SOLE[String(c.ci)]);
for (const c of casi) {
  const so = SOLE[String(c.ci)], i0 = Math.round((Date.parse(c.D[0].d) - Date.parse(so.s)) / 864e5);
  c.D.forEach((x, i) => { x.st = x.tmed; const r = so.R[i + i0]; x.fr = r && r[0] != null ? Math.min(1, r[0] / durata(c.lat, x.d)) : null; });
  let u = .5; c.D.forEach(x => { if (x.fr == null) x.fr = u; u = x.fr; });
}
const y = casi.map(c => c.y);
const solePrima = (D, i, a, b) => { let t = 0; for (let j = i - b; j <= i - a; j++) t += D[j].fr; return t / (b - a + 1); };
const base = (c, i) => P.valutaPorcino(c.D, i, 800, "castagno").v;
const finestra = (c, f) => { let m = 0; for (let i = c.lo; i <= c.hi; i++) m = Math.max(m, f(c, i)); return m; };
console.log(`Lucchesia: ${casi.length} casi con sole (${y.filter(Boolean).length} con funghi)`);
const fr = casi.map(c => solePrima(c.D, Math.round((c.lo + c.hi) / 2), 2, 14));
const med = a => [...a].sort((p, q) => p - q)[a.length >> 1];
console.log(`  sole 2-14 giorni prima (frazione del possibile), mediana: con funghi ${med(fr.filter((_, i) => y[i])).toFixed(2)}, senza ${med(fr.filter((_, i) => !y[i])).toFixed(2)}`);
console.log(`  AUC indice ${ML.auc(casi.map(c => finestra(c, base)), y).toFixed(3)}   AUC sole 2-14 da solo ${ML.auc(fr, y).toFixed(3)}`);
// correzione: sotto la soglia s la buttata rallenta fino a ×m (sole 2-14 giorni prima)
for (const [s, m] of [[.3, .7], [.4, .7], [.5, .7], [.4, .5], [.5, .5]]) {
  const f = (c, i) => base(c, i) * P.trap(solePrima(c.D, i, 2, 14), 0, s, 2, 3, m);
  console.log(`  con sole: sotto ${Math.round(s * 100)}% fino a ×${m}   AUC ${ML.auc(casi.map(c => finestra(c, f)), y).toFixed(3)}`);
}
