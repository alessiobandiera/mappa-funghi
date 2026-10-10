// Indice di buttata del porcino, comune alla mappa generale (index.html), alla mappa a 20 m (bosco.html) e all'app.
// Dal 9/10/2026 il porcino è il migliore fra quattro specie, ognuna con il suo meteo (tarato sui ritrovamenti GBIF di quella
// specie), la sua stagione, la sua quota e i suoi alberi (simbiosi): il tipo di bosco viene dalla Carta degli Habitat ISPRA (dal 10/10/2026) e, dove manca, dalla carta ISPRA Corine Land
// Cover 2018 IV livello (docs/dati/tipi_bosco.json, docs/terreno/f/). Verifiche in data/validazione/RISULTATI.md.

const FATTORI = {pioggia:"pioggia e attesa", suoloU:"umidità del suolo", suoloT:"temperatura del suolo",
  notti:"temperature notturne", aria:"umidità dell'aria", vento:"vento secco da nord", calo:"calo termico",
  quota:"quota", bosco:"tipo di bosco", secco:"troppi giorni asciutti di fila", stagione:"stagione"};

/* ---------------- tipi di bosco ---------------- */
// codici 1-14 dei file ISPRA (script/boschi_tipi.py), più due tipi stimati per le celle meteo senza bosco
const TIPI = ["leccio","querce","latifoglie","castagno","faggio","igrofile","robinia","pini","pinimontani","abeti","larice","esotiche","mistolat","mistocon"];
const BOSCHI = {
  castagno:"Castagno", faggio:"Faggio", querce:"Querce (cerro, roverella)", leccio:"Leccio e sughera",
  latifoglie:"Altre latifoglie (carpini, aceri, ornielli)", mistolat:"Misto, prevalgono latifoglie", mistocon:"Misto, prevalgono conifere",
  abeti:"Abeti", pinimontani:"Pini montani (pino nero, silvestre)", pini:"Pini mediterranei e cipressi", larice:"Larice",
  esotiche:"Conifere esotiche (douglasia…)", robinia:"Latifoglie esotiche (robinia…)", igrofile:"Salici, pioppi, ontani",
  pianura:"Pianura e coltivi", prateria:"Crinale e praterie"
};
// con quali alberi vive ogni specie (simbiosi): 1 = ospite tipico, 0 = mai. Rivisto il 9/10/2026 sulle schede della Regione
// Piemonte e della Scuola Sant'Anna (Alta Val di Vara): il porcino rosso (pinophilus) vive con castagno, faggio, abeti e pini
// montani, non con i pini mediterranei; il nero (aereus) anche in faggeta; l'estivo (reticulatus) dal castagno alla faggeta.
const OSPITI = {
  castagno:   {aereus:1,   reticulatus:1,   edulis:1,   pinophilus:.9},
  querce:     {aereus:1,   reticulatus:1,   edulis:.6,  pinophilus:.2},
  leccio:     {aereus:1,   reticulatus:.5,  edulis:.3,  pinophilus:.1},
  faggio:     {aereus:.4,  reticulatus:.9,  edulis:1,   pinophilus:1},
  latifoglie: {aereus:.5,  reticulatus:.7,  edulis:.5,  pinophilus:.2},
  mistolat:   {aereus:.7,  reticulatus:.8,  edulis:.9,  pinophilus:.8},
  mistocon:   {aereus:.4,  reticulatus:.5,  edulis:.9,  pinophilus:.9},
  abeti:      {aereus:.05, reticulatus:.2,  edulis:1,   pinophilus:1},
  pinimontani:{aereus:.05, reticulatus:.2,  edulis:.8,  pinophilus:1},
  pini:       {aereus:.2,  reticulatus:.1,  edulis:.4,  pinophilus:.2},
  larice:     {aereus:.05, reticulatus:.05, edulis:.6,  pinophilus:.6},
  esotiche:   {aereus:.05, reticulatus:.1,  edulis:.5,  pinophilus:.5},
  robinia:    {aereus:.2,  reticulatus:.2,  edulis:.2,  pinophilus:.1},
  igrofile:   {aereus:.05, reticulatus:.05, edulis:.05, pinophilus:.05},
  pianura:    {aereus:.1,  reticulatus:.1,  edulis:.05, pinophilus:.05},
  prateria:   {aereus:.05, reticulatus:.1,  edulis:.2,  pinophilus:.2},
};
// tipo stimato dove le carte ISPRA non hanno bosco (o per le celle meteo da 5 km): quota e, se c'è, il tipo di foglia di OpenStreetMap
function tipoStimato(lat, lon, elev, osm){
  if (osm==="n") return elev<400 ? "pini" : "abeti";
  if (elev<60) return lon<10.32 ? "pini" : "pianura";
  if (elev<450) return "querce";
  if (elev<950) return "castagno";
  if (elev<1650) return "faggio";
  return "prateria";
}

/* ---------------- le specie di porcino ---------------- */
// meteo: parametri comuni alle prove di taratura sui ritrovamenti di ogni specie (script/gbif_tara_specie.js, gbif_specie.js);
// quota: limite vero (0 fuori dalla fascia); stagione: frequenza del mese rispetto alle altre specie (ritrovamenti del
// Mediterraneo), piena da 0,8.
// versante (solo mappa a 20 m): quanto la specie sposta l'esposizione ideale al sole e il ristagno ideale rispetto alle regole
// del terreno. Dalle schede di Regione Piemonte e Scuola Sant'Anna: il nero cerca luoghi caldi, soleggiati e asciutti; il rosso
// umidità e temperature non alte; il d'autunno boschi freschi e umidi; l'estivo caldo-umido (neutro). Non verificabile sui
// ritrovamenti GBIF (posizione troppo imprecisa per l'esposizione): da controllare con le uscite.
const COMUNI_P = {soloMeteo:true, esauritaMin:.2, esauritaGiorni:5, seccoMin:.03, suoloU:[0,.3,1.01,1.02]};   // seccoMin: buttata seccata = indice basso (9/10/2026)
const SPECIE_PORCINI = [
  {...COMUNI_P, id:"aereus", nome:"Porcino nero", attesa:[6,16,21,30], pmin:26, suoloT:[6,12,21,26], notte:[3,9,19,23], secco:[6,15], extra:30, calo:.2,
   versante:{sole:.15, acqua:-.1}, quotaSpecie:[50,200,1000,1400], stagione:[.1,.1,.1,.1,.8,.8,1,.79,1,1,1,1]},
  {...COMUNI_P, id:"reticulatus", nome:"Porcino estivo", attesa:[7,13,18,32], pmin:24, suoloT:[8,16,24,28], notte:[4,8,18,22], secco:[8,16], extra:15, calo:0,
   versante:{sole:0, acqua:0}, quotaSpecie:[50,250,1300,1700], stagione:[.1,.1,.1,.1,1,1,1,1,1,.71,.69,.26]},
  {...COMUNI_P, id:"edulis", nome:"Porcino d'autunno", attesa:[6,16,21,32], pmin:28, suoloT:[4,10,20,26], notte:[2,6,15,20], secco:[3,14], extra:15, calo:0,
   suoloU:[0,.2,1.01,1.02], versante:{sole:-.05, acqua:.05}, quotaSpecie:[150,450,1700,2100], stagione:[.1,.1,.1,.1,.26,.26,.73,1,1,1,1,1]},
  {...COMUNI_P, id:"pinophilus", nome:"Porcino rosso", attesa:[10,16,22,29], pmin:20, suoloT:[5,11,20,25], notte:[4,7,17,23], secco:[8,14], extra:14, calo:.3,
   suoloU:[0,.25,1.01,1.02], versante:{sole:-.1, acqua:.1}, quotaSpecie:[200,400,1400,1800], stagione:[.1,.1,.1,.1,1,1,.5,.5,1,1,1,1]},
];
const NOME_SPECIE = Object.fromEntries(SPECIE_PORCINI.map(s=>[s.id, s.nome]));
// stagione del giorno: valori a metà mese, interpolati
function stagione(sp, iso){
  if (!iso) return 1;
  const m=+iso.slice(5,7)-1, g=+iso.slice(8,10), S=sp.stagione;
  const a=g<15 ? (m+11)%12 : m, b=(a+1)%12, t=g<15 ? (g+15)/30 : (g-15)/30;
  return S[a]+(S[b]-S[a])*t;
}
// quanto la specie può esserci qui e ora: alberi × quota × stagione (0-1), con il limite più stretto
function vincoliSpecie(sp, tipo, quota, iso){
  const o=(OSPITI[tipo]||OSPITI.castagno)[sp.id], q=trap(quota,...sp.quotaSpecie), s=stagione(sp, iso);
  const lim = o<=q && o<=s ? "bosco" : q<=s ? "quota" : "stagione";
  return {k:o*q*s, o, q, s, lim};
}
// indice del porcino: la specie migliore possibile in quel bosco, a quella quota, in quel giorno
function valutaPorcino(D, idx, quota, tipo){
  let best=null; const iso=D[idx]&&D[idx].d;
  for (const sp of SPECIE_PORCINI){
    const v=vincoliSpecie(sp, tipo, quota, iso); if (!(v.k>0)) continue;
    const r=valuta(D, idx, sp, quota), x=r.v*v.k;
    if (!best || x>best.v) best={...r, v:x, i:Math.round(x), specie:sp.id, vincoli:v};
  }
  return best || {i:0, v:0, f:{}, lim:null, ev:null, specie:null, vincoli:{k:0, lim:"quota"}};
}

/* ---------------- calcolo indice ---------------- */
function trap(x,a,b,c,d,min=0){
  let v; if (x<=a||x>=d) v=0; else if (x>=b&&x<=c) v=1; else if (x<b) v=(x-a)/(b-a); else v=(d-x)/(d-c);
  return min+(1-min)*v;
}
const avg=(arr,k)=>arr.reduce((s,g)=>s+g[k],0)/arr.length;
const tramontana=g=>(g.vd>=315||g.vd<=60)&&g.vm>=20&&g.ur<60;

// Porcino d'autunno (edulis, pinophilus): nasce più tardi dopo la pioggia, regge suolo e notti più freddi e più giorni asciutti
// dei porcini estivi. Dal 1° al 31 ottobre i parametri passano gradualmente a quelli d'autunno (verificato l'8/10/2026 su
// 2.108 ritrovamenti GBIF d'autunno: 0,573 -> 0,593, settembre e estate invariati; Lucchesia non peggiora).
const cacheStagione=new WeakMap();   // per ogni insieme di parametri: peso d'autunno -> parametri del giorno
function profiloStagione(sp, iso){
  if (!sp.autunno || !iso) return sp;
  const doy=Math.round((Date.parse(iso+"T12:00:00Z")-Date.parse(iso.slice(0,4)+"-01-01T12:00:00Z"))/864e5)+1;
  const w=Math.max(0,Math.min(1,(doy-sp.autunnoDa)/sp.autunnoGiorni));
  if (!w) return sp;
  let c=cacheStagione.get(sp); if (!c) cacheStagione.set(sp, c=new Map()); let p=c.get(w);
  if (!p){
    p={...sp};
    for (const [nome,v] of Object.entries(sp.autunno)) p[nome]=v.map((x,i)=>sp[nome][i]+(x-sp[nome][i])*w);
    p.attesa=p.attesa.map(Math.round); p.secco=p.secco.map(Math.round);
    c.set(w,p);
  }
  return p;
}
function valuta(D, idx, sp, quota, bosco){
  sp=profiloStagione(sp, D[idx]&&D[idx].d);
  const f={}; let best=0, ev=null;
  for (let j=Math.max(0,idx-sp.attesa[3]); j<=idx; j++){
    const att=idx-j; let cum=0;
    for (let k=Math.max(0,j-2); k<=j; k++) cum+=D[k].p;
    if (cum<sp.pmin*.5) continue;
    // se dopo questa pioggia c'è stato un periodo secco più lungo di quanto il terreno regge, la sua spinta è esaurita:
    // una pioggia successiva non la "riaccende", conta solo come pioggia nuova, con i suoi tempi di attesa.
    // Con esauritaMin (porcino) la spinta non si azzera: cala in esauritaGiorni giorni fino a quella frazione
    // (nei boschi più freschi qualche fungo esce ancora; verificato su ritrovamenti GBIF e casi della Lucchesia).
    const tolle=sp.secco[1]+Math.max(0,Math.min(8,(cum-sp.pmin)/(sp.extra||20)));
    let st=0, mx=0, esaur=1;
    for (let k=j+1; k<=idx; k++){ if (D[k].p<3 && D[k].ur<88){ st++; if (st>mx) mx=st; } else st=0; }
    if (mx>tolle){ if (!sp.esauritaMin) continue; esaur=Math.max(sp.esauritaMin, 1-(mx-tolle)/(sp.esauritaGiorni||5)); }
    const v=esaur*trap(att,...sp.attesa)*(.4+.6*Math.min(1,cum/(sp.pmin*1.5)));
    if (v>best){best=v; ev={data:D[j].d, mm:Math.round(cum), att, secco:mx};}
  }
  f.pioggia=best;
  const u5=D.slice(idx-4,idx+1), u7=D.slice(idx-6,idx+1);
  // umidità del suolo RELATIVA: 0 = il minimo delle ultime 5 settimane in quel punto, 1 = il massimo.
  // I modelli assegnano a ogni punto un tipo di suolo diverso: in collina lo strato superficiale scende a 0,04 m³/m³,
  // in pianura non va sotto 0,2. Le soglie assolute azzeravano proprio le zone di bosco.
  const fin=D.slice(Math.max(0,idx-32),idx+1).map(g=>g.su), smin=Math.min(...fin), smax=Math.max(...fin);
  const rel = smax-smin>0.02 ? (avg(u5,"su")-smin)/(smax-smin) : .5;
  f.suoloU=trap(rel,...sp.suoloU,.15);
  f.suoloT=trap(avg(u7,"st"),...sp.suoloT);
  f.notti=trap(avg(u7,"tmin"),...sp.notte,.1);
  f.aria=trap(avg(u5,"ur"),45,65,100,101,.3);
  f.vento=Math.max(.2,1-.25*u5.filter(tramontana).length);
  // giorni asciutti di fila fino al giorno valutato (pioggia sotto 3 mm e aria non satura):
  // dopo il temporale servono altre piogge o umidità, altrimenti la buttata non parte o si secca
  let secchi=0;
  for (let k=idx; k>=Math.max(0,idx-25); k--){ if (D[k].p>=3 || D[k].ur>=88) break; secchi++; }
  // il secco che conta è il più lungo dopo la pioggia che ha fatto partire la buttata: una pioggia di oggi non riaccende
  // una buttata già seccata (vale solo come pioggia nuova, con la sua attesa). Verificato l'8/10/2026 (RISULTATI.md).
  if (ev) secchi=Math.max(secchi, ev.secco);
  // più è piovuto, più a lungo il terreno resta bagnato: +1 giorno tollerato ogni 20 mm oltre la soglia (max 8)
  const extra = ev ? Math.max(0,Math.min(8,(ev.mm-sp.pmin)/(sp.extra||20))) : 0;
  f.secco=trap(secchi,-1,0,sp.secco[0]+extra,sp.secco[1]+extra,sp.seccoMin??.1);
  if (sp.calo){
    const prec=D.slice(Math.max(0,idx-20),idx-6);
    if (prec.length>=7){
      const c=trap(avg(prec,"tmed")-avg(u7,"tmed"),-3,1.5,8,14,.3);
      f.calo=1-sp.calo*(1-c);
    }
  }
  // le specie di porcino hanno quota, alberi e stagione come limiti a parte (valutaPorcino): qui solo il meteo
  if (!sp.soloMeteo){ f.quota=trap(quota,...sp.quota,.05); f.bosco=sp.boschi[bosco] ?? .7; }
  const vals=Object.values(f), mn=Math.min(...vals);
  let ind=0;
  if (mn>0){
    const geo=Math.exp(vals.reduce((s,v)=>s+Math.log(v),0)/vals.length);
    // ×pioggia^0,3 (9/10/2026): nei primi giorni dopo la pioggia l'attesa pesa di più (a 8 giorni da 50 mm l'indice passa da 32 a 20;
    // il micologo Opicelli indica 13-20 giorni dopo la pioggia principale). Ritrovamenti GBIF 0,620 -> 0,623, Italia 0,597 -> 0,604.
    ind=Math.pow(geo,.6)*Math.pow(mn,.4)*Math.min(1,.5+f.pioggia)*Math.min(1,.5+f.suoloU)*Math.pow(f.pioggia,.3);
  }
  const lim = mn<.95 ? Object.keys(f).reduce((a,b)=>f[a]<=f[b]?a:b) : null;
  return {i:Math.round(100*ind), v:100*ind, f, lim, ev};
}
