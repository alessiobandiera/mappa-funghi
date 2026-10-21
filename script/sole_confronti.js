// Il sole conta? Ritrovamenti GBIF: giorno del ritrovamento contro gli stessi giorni della settimana ±1-4 settimane, stesso punto
// (come gbif_specie.js), con l'indice della mappa (docs/porcini.js, specie migliore con stagione) e il sole dei giorni prima.
// Sole = sole relativo stimato dalla radiazione ERA5 (0 = coperto, 1 = sereno), meno l'andamento della stagione in quel punto.
// Il sole del giorno stesso e del giorno prima dice soprattutto quando la gente esce a cercare (e fotografare): resta come correzione.
// Uso: node script/sole_confronti.js   ->   data/gbif/sole_confronti.json   (poi python script/sole_analisi.py)
const fs = require("fs");
const P = {}; new Function("P", fs.readFileSync(__dirname + "/../docs/porcini.js", "utf8") + ";P.SPECIE_PORCINI=SPECIE_PORCINI; P.stagione=stagione; P.valuta=valuta;")(P);
const SP = Object.fromEntries(P.SPECIE_PORCINI.map(sp => [sp.id, sp]));
const indice = (D, i) => Math.max(...Object.values(SP).map(sp => P.valuta(D, i, sp, 800).v * P.stagione(sp, D[i].d)));

const leggi = dir => { const o = {}; if (fs.existsSync(dir)) for (const f of fs.readdirSync(dir)) Object.assign(o, JSON.parse(fs.readFileSync(dir + "/" + f))); return o; };
const METEO = leggi("data/gbif/meteo"), SOLE = leggi("data/gbif/sole");
const oss = JSON.parse(fs.readFileSync("data/gbif/porcini.json")).righe;
const add = (d, n) => { const x = new Date(d + "T12:00:00Z"); x.setUTCDate(x.getUTCDate() + n); return x.toISOString().slice(0, 10); };
// Sole relativo dalla radiazione (FAO-56): le «ore di sole» di Open-Meteo/ERA5 risultano troppo alte (es. 14,3 ore su 15,3 con il
// 66% di nuvole), la radiazione no. Radiazione fuori dall'atmosfera Ra (FAO-56, eq. 21), poi Ångström-Prescott: n/N = (Rs/Ra − 0,25)/0,5.
function soleRelativo(lat, iso, rad) {
  const J = Math.round((Date.parse(iso + "T12:00:00Z") - Date.parse(iso.slice(0, 4) + "-01-01T12:00:00Z")) / 864e5) + 1;
  const f = lat * Math.PI / 180, dr = 1 + .033 * Math.cos(2 * Math.PI * J / 365), dec = .409 * Math.sin(2 * Math.PI * J / 365 - 1.39);
  const ws = Math.acos(Math.max(-1, Math.min(1, -Math.tan(f) * Math.tan(dec))));
  const Ra = 24 * 60 / Math.PI * .082 * dr * (ws * Math.sin(f) * Math.sin(dec) + Math.cos(f) * Math.cos(dec) * Math.sin(ws));
  return Ra > 0 ? Math.max(0, Math.min(1, (rad / Ra - .25) / .5)) : .5;
}
function serie(m, s, lat) {
  let u = [0, 10, 20, 70, .25, .25, 15, 10, 0], us = [5, 10, 50];
  return m.R.map((r, i) => {
    const x = r.map((v, k) => (v == null ? u[k] : v)); u = x; const [p, tn, tx, ur, s0, s1, st, vm, vd] = x, tm = (tn + tx) / 2, d = add(m.s, i);
    const z = s.R[i] ? s.R[i].map((v, k) => (v == null ? us[k] : v)) : us; us = z;
    return { d, p, tmin: tn, tmax: tx, tmed: tm, st: r[6] != null ? st : tm, ur, su: (s0 + s1) / 2, vm, vd,
             sole: z[0], fr: soleRelativo(lat, d, z[1]), rad: z[1], nuv: z[2] };
  });
}
// Andamento della stagione nel punto (parabola sui ~100 giorni della serie) tolto da sole e nuvole: i giorni di confronto sono
// simmetrici (±1-4 settimane), ma una stagione curva (es. il massimo del sole a luglio) sposterebbe la media dei confronti.
// Restano le giornate più o meno soleggiate del solito per quel periodo. Verificato con sole casuale: senza questa correzione
// la prova trovava un «effetto» che non c'era.
function togliStagione(D, k) {
  const n = D.length, t = D.map((_, i) => (i - n / 2) / n), y = D.map(g => g[k]);
  const S = [0, 0, 0, 0, 0], B = [0, 0, 0];
  for (let i = 0; i < n; i++) { const x = t[i]; S[0] += 1; S[1] += x; S[2] += x * x; S[3] += x ** 3; S[4] += x ** 4; B[0] += y[i]; B[1] += x * y[i]; B[2] += x * x * y[i]; }
  const A = [[S[0], S[1], S[2]], [S[1], S[2], S[3]], [S[2], S[3], S[4]]];
  const det = m => m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1]) - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0]) + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]);
  const d = det(A), c = [0, 1, 2].map(j => det(A.map((r, i) => r.map((v, q) => (q === j ? B[i] : v)))) / d);
  D.forEach((g, i) => { g[k + "_r"] = g[k] - (c[0] + c[1] * t[i] + c[2] * t[i] * t[i]); });
}
const media = (D, i, a, b, k) => { let t = 0; for (let j = i - b; j <= i - a; j++) t += D[j][k]; return t / (b - a + 1); };
const FIN = [[2, 7], [8, 14], [15, 21], [22, 28], [2, 14], [2, 21]];
const NOMI = ["fr0", "fr1", ...FIN.map(([a, b]) => `fr_${a}_${b}`), ...FIN.map(([a, b]) => `nuv_${a}_${b}`), "nuv0", "nuv1", "p0", "p1",
  ...FIN.map(([a, b]) => `p_${a}_${b}`), ...FIN.map(([a, b]) => `ur_${a}_${b}`), "sole_ass_2_7", "sole_ass_2_14", "sole_ass_8_14"];
function variabili(D, i) {
  return [D[i].fr_r, D[i - 1].fr_r, ...FIN.map(([a, b]) => media(D, i, a, b, "fr_r")), ...FIN.map(([a, b]) => media(D, i, a, b, "nuv_r")),
          D[i].nuv_r, D[i - 1].nuv_r, D[i].p, D[i - 1].p, ...FIN.map(([a, b]) => media(D, i, a, b, "p")), ...FIN.map(([a, b]) => media(D, i, a, b, "ur")),
          media(D, i, 2, 7, "fr"), media(D, i, 2, 14, "fr"), media(D, i, 8, 14, "fr")]   // sole relativo vero (senza togliere la stagione), per provarlo come fattore.map(v => Math.round(v * 1000) / 1000);
}

const giorni = new Map(), visti = new Set(), cache = {}, righe = [], strati = [];
const gruppo = (d, la, lo) => `${(Math.round(la * 10) / 10).toFixed(1)},${(Math.round(lo * 10) / 10).toFixed(1)},${d.slice(0, 4)}`;
for (const [d, la, lo] of oss) { const g = gruppo(d, la, lo); if (!giorni.has(g)) giorni.set(g, new Set()); giorni.get(g).add(d); }
let senza = 0;
for (const [d, la, lo, sp, paese] of oss) {
  const g = gruppo(d, la, lo);
  if (visti.has(g + d + sp) || !METEO[g]) continue; visti.add(g + d + sp);
  if (!SOLE[g] || SOLE[g].s !== METEO[g].s) { senza++; continue; }
  if (!cache[g]) { cache[g] = serie(METEO[g], SOLE[g], la); togliStagione(cache[g], "fr"); togliStagione(cache[g], "nuv"); }
  const D = cache[g], i0 = D.findIndex(x => x.d === d); if (i0 < 38) continue;
  const rif = []; for (const w of [1, 2, 3, 4]) { const a = i0 - 7 * w, b = i0 + 7 * w; if (a >= 38 && b < D.length && !giorni.get(g).has(D[a].d) && !giorni.get(g).has(D[b].d)) rif.push(a, b); }
  if (rif.length < 2) continue;
  strati.push([d, paese, sp, la, lo]); const n = strati.length;
  for (const [i, caso] of [[i0, 1], ...rif.map(i => [i, 0])]) righe.push([n, caso, Math.round(indice(D, i) * 10) / 10, ...variabili(D, i)]);
}
fs.writeFileSync("data/gbif/sole_confronti.json", JSON.stringify({ colonne: ["strato", "caso", "indice", ...NOMI],
  strati_colonne: ["data", "paese", "specie", "lat", "lon"], strati, righe }));
console.log(`strati ${strati.length}, righe ${righe.length}, ritrovamenti senza sole (ancora da scaricare) ${senza}`);
