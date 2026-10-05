// Confronto dell'indice attuale sui casi, con due fonti meteo: NASA POWER (serie.json) e Open-Meteo (serie_om.json).
// Uso: node script/valida_confronto.js            -> stampa le AUC e scrive data/validazione/punteggi.json
global.window = {}; require('./valida_regole.js'); const ML = window.ML;
const fs = require('fs'), path = require('path');
const dir = path.join(__dirname, '..', 'data', 'validazione');
const carica = f => fs.existsSync(path.join(dir, f)) ? JSON.parse(fs.readFileSync(path.join(dir, f))) : null;

// il suolo misurato da Open-Meteo (st) sostituisce la stima "aria - 1 °C" quando c'è
function prepara(casi) {
  const C = ML.prepara(casi);
  for (const c of C) {
    const src = casi.find(r => r.ci === c.ci);
    src.serie.forEach((x, i) => { if (x.st !== undefined && c.D[i]) c.D[i].st = x.st; });
  }
  return C;
}
const fonte = c => c.url && /fungodiborgotaro\.com\/forum|funghiemicologia/.test(c.url) ? 'forum' : 'giornali/blog';
const regione = c => c.lat > 44.36 && c.lon < 10.0 ? 'Val Taro e Parma ovest' : (c.lat >= 43.7 && c.lat <= 44.45 && c.lon >= 9.85 && c.lon <= 11.0 ? 'Lucchesia, Garfagnana, Lunigiana, Abetone' : 'altre zone');

function riga(nome, C, P) {
  if (C.length < 8) return;
  const y = C.map(c => c.y), s = C.map(c => ML.punteggio(c, P)), f = C.map(c => ML.punteggioF(c));
  const [acc, t] = ML.migliorSoglia(s, y);
  console.log(`${nome.padEnd(44)} n=${String(C.length).padStart(3)} pos=${String(y.filter(v => v).length).padStart(3)}  AUC indice ${ML.auc(s, y).toFixed(3)}  AUC Fungaiolo ${ML.auc(f, y).toFixed(3)}  acc ${(100 * acc).toFixed(0)}% (soglia ${t})`);
}

const CASI = JSON.parse(fs.readFileSync(path.join(dir, 'casi.json')));
const nasa = carica('serie.json'), om = carica('serie_om.json');
const P = ML.ATTUALE;
if (nasa) riga('NASA POWER, casi originali', prepara(nasa.casi), P);
if (om) {
  const C = prepara(om.casi);
  C.forEach(c => { c.url = CASI[c.ci][6]; });
  if (nasa) {
    const vecchi = new Set(nasa.casi.map(r => r.data + r.lat + r.lon));
    riga('Open-Meteo, stessi casi di NASA', C.filter(c => vecchi.has(c.data + c.lat + c.lon)), P);
  }
  riga('Open-Meteo, tutti i casi', C, P);
  for (const g of ['giornali/blog', 'forum']) riga('  fonte: ' + g, C.filter(c => fonte(c) === g), P);
  for (const g of ['Lucchesia, Garfagnana, Lunigiana, Abetone', 'Val Taro e Parma ovest', 'altre zone']) riga('  zona: ' + g, C.filter(c => regione(c) === g), P);
  for (const m of [[6, 8, 'giugno-agosto'], [9, 9, 'settembre'], [10, 10, 'ottobre'], [11, 12, 'novembre-dicembre']])
    riga('  mese: ' + m[2], C.filter(c => { const k = +c.data.slice(5, 7); return k >= m[0] && k <= m[1]; }), P);
  // punteggi per l'analisi in Python
  fs.writeFileSync(path.join(dir, 'punteggi.json'), JSON.stringify(C.map(c => ({ ci: c.ci, indice: ML.punteggio(c, P), fungaiolo: ML.punteggioF(c) }))));
  console.log('\nscritto data/validazione/punteggi.json');
}
