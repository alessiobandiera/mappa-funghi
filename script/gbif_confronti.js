// Osservazioni GBIF dei porcini: per ogni ritrovamento (cella, giorno) l'indice della mappa e le variabili meteo
// nel giorno del ritrovamento e negli stessi giorni della settimana 1-4 settimane prima e dopo (giorni di confronto).
// Il confronto nello stesso punto annulla luogo, persona e abitudine di uscire nel fine settimana: resta l'effetto del meteo.
// Uso: node script/gbif_confronti.js   ->   data/gbif/confronti.json (righe: gruppo, caso 0/1, punteggi..., variabili...)
global.window = {};
require("./valida_regole.js");
const ML = window.ML, fs = require("fs");
const oss = JSON.parse(fs.readFileSync("data/gbif/porcini.json")).righe;
const METEO = {};
for (const f of fs.existsSync("data/gbif/meteo") ? fs.readdirSync("data/gbif/meteo") : []) Object.assign(METEO, JSON.parse(fs.readFileSync("data/gbif/meteo/" + f)));

const add = (d, n) => { const x = new Date(d + "T12:00:00Z"); x.setUTCDate(x.getUTCDate() + n); return x.toISOString().slice(0, 10); };
const QN = { ...ML.ATTUALE, senza: ["quota"] };
const P60 = { ...QN, cluster: 10, totmin: 60 };
const avg = (a) => a.reduce((s, x) => s + x, 0) / a.length;
const sum = (D, i, a, b) => { let s = 0; for (let k = i - b; k <= i - a; k++) s += D[k].p; return s; };   // pioggia da a a b giorni fa

// serie nel formato di valida_regole.js (le temperature di Open-Meteo sono già alla quota della cella)
function serie(m) {
  let ultimo = [0, 10, 20, 70, .25, .25, 15, 10, 0];
  return m.R.map((r, i) => {
    const x = r.map((v, k) => (v == null ? ultimo[k] : v)); ultimo = x;
    const [p, tn, tx, ur, s0, s1, st, vm, vd] = x, tm = (tn + tx) / 2;
    return { d: add(m.s, i), p, tmin: tn, tmax: tx, tmed: tm, st: tm - 1, stv: st, ur, su: (s0 + s1) / 2, s0, s1, vm, vd };
  });
}
const NOMI = ["p_0_3", "p_4_7", "p_8_14", "p_15_21", "p_22_35", "max3_35", "giorni_da_20mm", "tmin7", "tmax7", "calo",
  "suolo_u7", "suolo_u_rel", "suolo_prof7", "suolo_t7", "umid5", "vento_max5", "giorno_anno"];
function variabili(D, i) {
  let max3 = 0, da20 = 36;
  for (let k = i; k >= i - 35; k--) { const c = D[k].p + D[k - 1].p + D[k - 2].p; if (c > max3) max3 = c; if (da20 === 36 && D[k].p >= 20) da20 = i - k; }
  const u7 = D.slice(i - 6, i + 1), u5 = D.slice(i - 4, i + 1), prec = D.slice(i - 20, i - 6);
  const fin = D.slice(i - 32, i + 1).map(g => g.su), mn = Math.min(...fin), mx = Math.max(...fin);
  const gda = Math.floor((Date.parse(D[i].d) - Date.parse(D[i].d.slice(0, 4) + "-01-01")) / 864e5);
  return [sum(D, i, 0, 3), sum(D, i, 4, 7), sum(D, i, 8, 14), sum(D, i, 15, 21), sum(D, i, 22, 35), max3, da20,
    avg(u7.map(g => g.tmin)), avg(u7.map(g => g.tmax)), avg(prec.map(g => g.tmed)) - avg(u7.map(g => g.tmed)),
    avg(u7.map(g => g.s0)), mx - mn > .02 ? (avg(u5.map(g => g.su)) - mn) / (mx - mn) : .5, avg(u7.map(g => g.s1)),
    avg(u7.map(g => g.stv)), avg(u5.map(g => g.ur)), Math.max(...u5.map(g => g.vm)), gda].map(v => Math.round(v * 1000) / 1000);
}

// un caso per cella e giorno (più osservazioni nello stesso posto e giorno contano una volta)
const casi = new Map();
for (const [d, la, lo, sp, paese] of oss) {
  const g = `${(Math.round(la * 10) / 10).toFixed(1)},${(Math.round(lo * 10) / 10).toFixed(1)},${d.slice(0, 4)}`;
  const k = g + "|" + d;
  if (!casi.has(k)) casi.set(k, { g, d, la, lo, sp, paese });
}
const giorniOss = new Map();
for (const c of casi.values()) { if (!giorniOss.has(c.g)) giorniOss.set(c.g, new Set()); giorniOss.get(c.g).add(c.d); }

const righe = [], strati = []; let strato = 0, saltati = 0; const cacheD = {};
for (const c of casi.values()) {
  const m = METEO[c.g]; if (!m) { saltati++; continue; }
  const D = cacheD[c.g] || (cacheD[c.g] = serie(m));
  const i0 = D.findIndex(x => x.d === c.d); if (i0 < 38) { saltati++; continue; }
  const rif = [];
  for (const w of [-4, -3, -2, -1, 1, 2, 3, 4]) {
    const i = i0 + 7 * w;
    if (i < 38 || i >= D.length) continue;
    if (giorniOss.get(c.g).has(D[i].d)) continue;              // anche quel giorno qualcuno ha trovato porcini: non è un confronto
    rif.push(i);
  }
  if (rif.length < 2) { saltati++; continue; }
  strato++; strati.push([c.d, c.paese, c.sp, c.la, c.lo, m.el]);
  const quota = Math.max(300, Math.min(1600, m.el || 800));
  for (const [i, caso] of [[i0, 1], ...rif.map(i => [i, 0])]) {
    righe.push([strato, caso, Math.round(ML.valuta(D, i, ML.ATTUALE, quota) * 10) / 10, Math.round(ML.valuta(D, i, QN, 800) * 10) / 10,
      Math.round(ML.valuta(D, i, P60, 800) * 10) / 10, Math.round(ML.fungaiolo(D, i) * 10) / 10, ...variabili(D, i)]);
  }
}
fs.writeFileSync("data/gbif/confronti.json", JSON.stringify({
  colonne: ["strato", "caso", "indice", "indice_quota_neutra", "indice_60mm", "fungaiolo", ...NOMI],
  strati_colonne: ["data", "paese", "specie", "lat", "lon", "quota_cella"], strati,     // strati[n-1] = caso dello strato n
  righe }));
console.log(`casi ${casi.size}, con meteo e confronti ${strato}, saltati ${saltati}, righe ${righe.length}`);
