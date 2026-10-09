// Modello per specie di porcino: parametri meteo, stagione (dai ritrovamenti, corretta per lo sforzo di raccolta) e quota.
// Verifica sui ritrovamenti GBIF: ogni specie con i suoi parametri contro l'indice attuale; e l'indice combinato
// (la specie migliore possibile in quel giorno) su tutti i ritrovamenti. Tipo di bosco ignoto nei ritrovamenti: ospite = 1.
// Dal 9/10/2026 le specie si valutano con lo stesso codice della mappa (valuta di docs/porcini.js) e con la temperatura del suolo
// vera (ERA5 0-7 cm), come la mappa (Open-Meteo 6 cm); prima: stima «aria − 1» e la copia del calcolo in valida_regole.js.
// Uso: node script/gbif_specie.js
const fs = require("fs");
global.window = {};
require("./valida_regole.js");
const ML = window.ML;
// parametri delle specie: gli stessi della mappa (docs/porcini.js), letti da lì
const P_JS = {}; new Function("P_JS", fs.readFileSync(__dirname + "/../docs/porcini.js", "utf8") + ";P_JS.SPECIE_PORCINI=SPECIE_PORCINI; P_JS.stagione=stagione; P_JS.valuta=valuta;")(P_JS);
const SPECIE_P = Object.fromEntries(P_JS.SPECIE_PORCINI.map(sp => [sp.id, sp]));
const STAGIONE = Object.fromEntries(P_JS.SPECIE_PORCINI.map(sp => [sp.id, sp.stagione]));
const stagione = (sp, iso) => P_JS.stagione(SPECIE_P[sp], iso);
const QN = P => ({ ...P, senza: ["quota"] });
const VS = (D, i, sp) => P_JS.valuta(D, i, SPECIE_P[sp], 800).v;   // quota, alberi e stagione a parte (soloMeteo)
const combinato = (D, i) => Math.max(...Object.keys(SPECIE_P).map(sp => VS(D, i, sp) * stagione(sp, D[i].d)));

const oss = JSON.parse(fs.readFileSync("data/gbif/porcini.json")).righe, METEO = {};
for (const f of fs.readdirSync("data/gbif/meteo")) Object.assign(METEO, JSON.parse(fs.readFileSync("data/gbif/meteo/" + f)));
const add = (d, n) => { const x = new Date(d + "T12:00:00Z"); x.setUTCDate(x.getUTCDate() + n); return x.toISOString().slice(0, 10); };
function serie(m) { let u = [0, 10, 20, 70, .25, .25, 15, 10, 0];
  return m.R.map((r, i) => { const x = r.map((v, k) => (v == null ? u[k] : v)); u = x; const [p, tn, tx, ur, s0, s1, st, vm, vd] = x, tm = (tn + tx) / 2;
    return { d: add(m.s, i), p, tmin: tn, tmax: tx, tmed: tm, st: r[6] != null ? st : tm, ur, su: (s0 + s1) / 2, vm, vd }; }); }
const giorni = new Map(), strati = [], cache = {}, visti = new Set();
for (const [d, la, lo] of oss) { const g = `${(Math.round(la * 10) / 10).toFixed(1)},${(Math.round(lo * 10) / 10).toFixed(1)},${d.slice(0, 4)}`; if (!giorni.has(g)) giorni.set(g, new Set()); giorni.get(g).add(d); }
for (const [d, la, lo, sp, paese] of oss) {
  const g = `${(Math.round(la * 10) / 10).toFixed(1)},${(Math.round(lo * 10) / 10).toFixed(1)},${d.slice(0, 4)}`;
  if (visti.has(g + d + sp) || !METEO[g]) continue; visti.add(g + d + sp);
  const D = cache[g] || (cache[g] = serie(METEO[g])), i0 = D.findIndex(x => x.d === d); if (i0 < 38) continue;
  const rif = []; for (const w of [1, 2, 3, 4]) { const a = i0 - 7 * w, b = i0 + 7 * w; if (a >= 38 && b < D.length && !giorni.get(g).has(D[a].d) && !giorni.get(g).has(D[b].d)) rif.push(a, b); }
  if (rif.length >= 2) strati.push({ D, idx: [i0, ...rif], sp, paese, anno: +d.slice(0, 4), mese: +d.slice(5, 7) });
}
const auc = (ss, f) => { let t = 0, n = 0; for (const s of ss) { const v = s.idx.map(i => f(s.D, i, s)); for (let k = 1; k < v.length; k++) { t += v[0] > v[k] ? 1 : v[0] === v[k] ? .5 : 0; n++; } } return t / n; };
const ORA = (D, i) => ML.valuta(D, i, QN(ML.ATTUALE), 800);   // indice di prima delle specie (8/10), come riferimento
const G = [["tutti", s => true], ["Italia", s => s.paese === "IT"], ["anni pari", s => s.anno % 2 === 0], ["anni dispari", s => s.anno % 2 === 1]];
console.log("Ogni specie con i suoi parametri (AUC, quota neutra) — indice attuale → parametri della specie");
for (const sp of Object.keys(SPECIE_P)) {
  const ss = strati.filter(s => s.sp === sp);
  console.log(`  ${sp.padEnd(12)}` + G.map(([n, f]) => { const x = ss.filter(f); return `${n} ${auc(x, ORA).toFixed(3)}→${auc(x, (D, i) => VS(D, i, sp)).toFixed(3)}`; }).join("   ") + `   n=${ss.length}`);
}
console.log("\nIndice combinato (specie migliore, con stagione), su tutti i ritrovamenti — attuale → combinato");
for (const [n, f] of [...G, ["giu-ago", s => s.mese >= 6 && s.mese <= 8], ["settembre", s => s.mese === 9], ["ott-dic", s => s.mese >= 10]]) {
  const x = strati.filter(f); console.log(`  ${n.padEnd(12)} ${auc(x, ORA).toFixed(3)} → ${auc(x, combinato).toFixed(3)}   n=${x.length}`);
}
module.exports = { SPECIE_P, STAGIONE };
