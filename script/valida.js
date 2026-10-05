// Confronto tra regole dell'indice sui casi storici (data/validazione/serie.json) e sulle uscite locali.
// Uso: node script/valida.js
global.window={}; require('./valida_regole.js'); const ML=window.ML;
const fs=require('fs');
const S=JSON.parse(fs.readFileSync(__dirname+'/../data/validazione/serie.json'));
const C=ML.prepara(S.casi); const y=C.map(c=>c.y);
const A=ML.ATTUALE;
const VAR={
  "attuale":A,
  "solo 60 mm":{...A, pieno:60},
  "finestra precedente (da 10 gg)":{...A, attesa:[6,10,18,26]},
  "60 mm + 12 gg":{...A, pieno:60, attesa:[7,12,18,26]},
  "45 mm + 12 gg":{...A, pieno:45, attesa:[7,12,18,26]},
  "60 mm + 12 gg, fine a 28":{...A, pieno:60, attesa:[7,12,20,28]},
  "secco: pioggia 10 gg, +1 g/20 mm":{...A, cluster:10},
  "secco: pioggia 10 gg, +1 g/10 mm":{...A, cluster:10, extra:10, maxextra:10},
  "secco 10gg/10mm + 12 gg":{...A, cluster:10, extra:10, maxextra:10, attesa:[7,12,18,26]},
  "secco 10gg/10mm + 12 gg + 45 mm":{...A, cluster:10, extra:10, maxextra:10, attesa:[7,12,18,26], pieno:45},
  "suolo meno severo (.20)":{...A, suoloU:[0,.20,1.01,1.02]},
  "suolo .20 + 12 gg":{...A, suoloU:[0,.20,1.01,1.02], attesa:[7,12,18,26]},
  "suolo .10 + 12 gg":{...A, suoloU:[0,.10,1.01,1.02], attesa:[7,12,18,26]},
  "suolo .20 + 12 gg + 45 mm":{...A, suoloU:[0,.20,1.01,1.02], attesa:[7,12,18,26], pieno:45},
};
// bootstrap per l'incertezza della differenza rispetto all'attuale
function boot(sa,sb,y,n=1000){ let w=0; const N=y.length; const d=[];
  for(let k=0;k<n;k++){ const id=Array.from({length:N},()=>Math.floor(Math.random()*N));
    const yy=id.map(i=>y[i]); d.push(ML.auc(id.map(i=>sb[i]),yy)-ML.auc(id.map(i=>sa[i]),yy)); }
  d.sort((a,b)=>a-b); return [d[Math.floor(.05*n)], d[Math.floor(.95*n)]]; }
const base=C.map(c=>ML.punteggio(c,A));
console.log(`casi ${C.length} (positivi ${y.filter(v=>v).length}), errori di scaricamento ${S.errori.length}`);
for (const [nome,P] of Object.entries(VAR)){
  const s=C.map(c=>ML.punteggio(c,P));
  const [lo,hi]=nome==="attuale"?[0,0]:boot(base,s,y);
  const [acc,t]=ML.migliorSoglia(s,y);
  console.log(`${nome.padEnd(26)} AUC ${ML.auc(s,y).toFixed(3)}  diff 90%: ${lo>=0?"+":""}${lo.toFixed(3)} .. ${hi>=0?"+":""}${hi.toFixed(3)}  accuratezza ${(100*acc).toFixed(0)}% (soglia ${t})`);
}
// uscite personali (facoltative, mai nel repository): data/validazione/uscite_locali.json
// formato: {"punto":{"lat":..,"lon":..,"quota":..}, "uscite":[["AAAA-MM-GG","esito"],...]} — confrontate sulla serie pizzorne_2026
const fl=__dirname+'/../data/validazione/uscite_locali.json';
if (fs.existsSync(fl)){
  const U=JSON.parse(fs.readFileSync(fl)).uscite;
  const pz=S.pizzorne_2026; const corr=(pz.zcella-pz.quota)*0.0065;
  const D=pz.serie.map(x=>{ const tn=x.tn+corr, tx=x.tx+corr, tm=(tn+tx)/2; return {d:x.d,p:x.p,tmin:tn,tmax:tx,tmed:tm,st:tm-1,ur:x.ur,su:(x.gt+x.gr)/2,vd:x.vd,vm:x.vm}; });
  console.log("\nuscite locali: "+U.map(u=>u[0].slice(5)+" "+u[1]).join(" | "));
  for (const [nome,P] of Object.entries(VAR))
    console.log(nome.padEnd(26)+U.map(([d])=>{ const i=D.findIndex(g=>g.d===d); return String(Math.round(ML.valuta(D,i,P,900))).padStart(5); }).join("  "));
}
