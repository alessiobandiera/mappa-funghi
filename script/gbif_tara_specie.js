// Taratura dei parametri dell'indice sui ritrovamenti GBIF (stesso punto: giorno del ritrovamento contro gli stessi giorni
// della settimana ±1-4 settimane). Ricerca casuale sui parametri a partire da quelli attuali, con la quota neutra.
// Verifica: su ritrovamenti mai usati per tarare (anni dispari / pari, e Italia tenuta fuori).
// Uso: SPECIE=edulis node script/gbif_tara_specie.js [iterazioni=300] [semina=1]  ->  data/gbif/parametri-<specie>.json
global.window = {};
require("./valida_regole.js");
const ML = window.ML, fs = require("fs");
const ITER = +(process.argv[2] || 300);
let seme = +(process.argv[3] || 1); Math.random = () => (seme = (seme * 16807) % 2147483647) / 2147483647;   // ripetibile

const SPECIE_T = process.env.SPECIE; const oss = JSON.parse(fs.readFileSync("data/gbif/porcini.json")).righe.filter(r => !SPECIE_T || r[3] === SPECIE_T);
const METEO = {};
for (const f of fs.readdirSync("data/gbif/meteo")) Object.assign(METEO, JSON.parse(fs.readFileSync("data/gbif/meteo/" + f)));
const add = (d, n) => { const x = new Date(d + "T12:00:00Z"); x.setUTCDate(x.getUTCDate() + n); return x.toISOString().slice(0, 10); };
function serie(m) {
  let u = [0, 10, 20, 70, .25, .25, 15, 10, 0];
  return m.R.map((r, i) => { const x = r.map((v, k) => (v == null ? u[k] : v)); u = x; const [p, tn, tx, ur, s0, s1, st, vm, vd] = x, tm = (tn + tx) / 2;
    return { d: add(m.s, i), p, tmin: tn, tmax: tx, tmed: tm, st: tm - 1, ur, su: (s0 + s1) / 2, vm, vd }; });
}
// strati: {D, idx: [caso, rif...], paese, anno}
const visti = new Set(), giorni = new Map(), strati = [], cacheD = {};
for (const [d, la, lo, , paese] of oss) {
  const g = `${(Math.round(la * 10) / 10).toFixed(1)},${(Math.round(lo * 10) / 10).toFixed(1)},${d.slice(0, 4)}`;
  if (!giorni.has(g)) giorni.set(g, new Set()); giorni.get(g).add(d);
}
for (const [d, la, lo, , paese] of oss) {
  const g = `${(Math.round(la * 10) / 10).toFixed(1)},${(Math.round(lo * 10) / 10).toFixed(1)},${d.slice(0, 4)}`;
  if (visti.has(g + d) || !METEO[g]) continue; visti.add(g + d);
  const D = cacheD[g] || (cacheD[g] = serie(METEO[g])), i0 = D.findIndex(x => x.d === d);
  if (i0 < 38) continue;
  const rif = [];                                               // coppie simmetriche, come in gbif_confronti.js
  for (const w of [1, 2, 3, 4]) { const a = i0 - 7 * w, b = i0 + 7 * w;
    if (a >= 38 && b < D.length && !giorni.get(g).has(D[a].d) && !giorni.get(g).has(D[b].d)) rif.push(a, b); }
  if (rif.length >= 2) strati.push({ D, idx: [i0, ...rif], paese, anno: +d.slice(0, 4) });
}
function aucStrati(ss, P) {
  let tot = 0, n = 0;
  for (const s of ss) { const v = s.idx.map(i => ML.valuta(s.D, i, P, 800)); for (let k = 1; k < v.length; k++) { tot += v[0] > v[k] ? 1 : v[0] === v[k] ? .5 : 0; n++; } }
  return tot / n;
}
const BASE = { ...ML.ATTUALE, autunno: null, senza: ["quota"] };   // una specie alla volta: niente profilo d'autunno (lo sostituiscono le specie)
function tara(ss) {
  let best = BASE, bv = aucStrati(ss, BASE);
  for (let k = 0; k < ITER; k++) {
    const P = { ...perturba(best, k < ITER / 2 ? 1 : .5), senza: ["quota"] };
    const v = aucStrati(ss, P); if (v > bv) { bv = v; best = P; }
  }
  return { P: best, auc: bv };
}
// stessa perturbazione di valida_regole.js (non è esportata là)
function perturba(P, f) {
  const r = (a, b) => a + Math.random() * (b - a), j = (v, s) => v + r(-s, s) * f;
  const q = { ...P, attesa: [...P.attesa], suoloT: [...P.suoloT], notte: [...P.notte], secco: [...P.secco], suoloU: [...P.suoloU] };
  let a = q.attesa.map(v => Math.round(j(v, 3))); a.sort((x, y) => x - y); a[0] = Math.max(2, a[0]); for (let i = 1; i < 4; i++) a[i] = Math.max(a[i], a[i - 1] + 1); q.attesa = a;
  q.pmin = Math.max(8, Math.min(45, j(q.pmin, 6)));
  q.suoloT = q.suoloT.map(v => j(v, 2.5)).sort((x, y) => x - y); q.notte = q.notte.map(v => j(v, 2.5)).sort((x, y) => x - y);
  let s = q.secco.map(v => Math.round(j(v, 3))); s[0] = Math.max(1, s[0]); s[1] = Math.max(s[0] + 2, s[1]); q.secco = s;
  q.suoloU = [0, Math.max(.05, Math.min(.8, j(q.suoloU[1], .15))), 1.01, 1.02];
  q.extra = Math.max(8, Math.min(60, j(q.extra, 10))); q.calo = Math.max(0, Math.min(1, j(q.calo, .25)));
  return q;
}
const mostra = P => JSON.stringify({ attesa: P.attesa, pmin: +P.pmin.toFixed(1), suoloT: P.suoloT.map(v => +v.toFixed(1)), notte: P.notte.map(v => +v.toFixed(1)),
  secco: P.secco, suoloU: +P.suoloU[1].toFixed(2), extra: +P.extra.toFixed(1), calo: +P.calo.toFixed(2) });

const IT = strati.filter(s => s.paese === "IT"), ALTRI = strati.filter(s => s.paese !== "IT");
console.log(`strati: ${strati.length} (Italia ${IT.length}, altri ${ALTRI.length})`);
console.log(`indice attuale (quota neutra): tutti ${aucStrati(strati, BASE).toFixed(3)}, Italia ${aucStrati(IT, BASE).toFixed(3)}`);
const prove = [];
if (ALTRI.length >= 100) prove.push(["tarato fuori dall'Italia, verificato in Italia", ALTRI, IT]);
const pari = strati.filter(s => s.anno % 2 === 0), dispari = strati.filter(s => s.anno % 2 === 1);
prove.push(["tarato sugli anni pari, verificato sui dispari", pari, dispari], ["tarato sui dispari, verificato sui pari", dispari, pari]);
for (const [nome, tr, te] of prove) {
  const t = tara(tr);
  console.log(`\n${nome}: taratura ${t.auc.toFixed(3)} (era ${aucStrati(tr, BASE).toFixed(3)}), verifica ${aucStrati(te, t.P).toFixed(3)} (era ${aucStrati(te, BASE).toFixed(3)})`);
  console.log("  " + mostra(t.P));
}
const fin = tara(strati);
console.log(`\nsu tutti: ${fin.auc.toFixed(3)} (era ${aucStrati(strati, BASE).toFixed(3)})\n  ${mostra(fin.P)}`);
fs.writeFileSync("data/gbif/parametri-" + (SPECIE_T || "tutte") + ".json", JSON.stringify({ base: mostra(BASE), tarati: fin.P, auc: fin.auc }, null, 1));
