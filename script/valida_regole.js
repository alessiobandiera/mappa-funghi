// Valutazione e taratura dell'indice sui casi reali (gira nel browser, sui dati in window.M.dati)
(function(){
const trap=(x,a,b,c,d,min=0)=>{ let v; if (x<=a||x>=d) v=0; else if (x>=b&&x<=c) v=1; else if (x<b) v=(x-a)/(b-a); else v=(d-x)/(d-c); return min+(1-min)*v; };
const avg=(arr,k)=>arr.reduce((s,g)=>s+g[k],0)/arr.length;
const tram=g=>(g.vd>=315||g.vd<=60)&&g.vm>=20&&g.ur<60;

// parametri attuali del porcino nella mappa (dal 5 ottobre: piena dal 12° giorno dopo la pioggia)
const ATTUALE={attesa:[7,12,18,26], pmin:20, suoloT:[8,12,22,26], notte:[3,8,19,22], secco:[5,13], suoloU:[0,.35,1.01,1.02],
  quota:[150,500,1600,2000], calo:.5, extra:20, esaurita:1};
// versione di stamattina: niente giorni asciutti, suolo 12-18
// proposta dal confronto sui 292 casi (ottobre 2026): serve pioggia vera, almeno 60 mm in 10 giorni
const PIOGGIA60={...ATTUALE, cluster:10, totmin:60};
const MATTINA={...ATTUALE, suoloT:[8,12,18,23], notte:[3,8,15,20], secco:[100,200], esaurita:0};

function valuta(D, idx, P, quota){
  const f={}; let best=0, ev=null;
  for (let j=Math.max(0,idx-P.attesa[3]); j<=idx; j++){
    const att=idx-j; let cum=0; for (let k=Math.max(0,j-2); k<=j; k++) cum+=D[k].p;
    if (cum<P.pmin*.5) continue;
    // pioggia totale del periodo piovoso (P.cluster giorni fino all'evento): un agosto con 80 mm in più temporali regge più a lungo
    let tot=cum; if (P.cluster){ tot=0; for (let k=Math.max(0,j-P.cluster+1); k<=j; k++) tot+=D[k].p; }
    if (P.totmin && tot<P.totmin) continue;           // pioggia minima sull'intero periodo (con P.cluster): es. 60 mm in 10 giorni
    if (P.esaurita){
      const tolle=P.secco[1]+Math.max(0,Math.min(P.maxextra||8,(tot-P.pmin)/P.extra)); let st=0, mx=0;
      for (let k=j+1;k<=idx;k++){ if (D[k].p<3&&D[k].ur<88){ st++; if(st>mx) mx=st; } else st=0; }
      if (mx>tolle) continue;
    }
    const v=trap(att,...P.attesa)*(.4+.6*Math.min(1,(P.cluster?tot:cum)/(P.pieno||P.pmin*1.5)));
    if (v>best){best=v; ev={mm:tot,att};}
  }
  f.pioggia=best;
  const u5=D.slice(idx-4,idx+1), u7=D.slice(idx-6,idx+1);
  const fin=D.slice(Math.max(0,idx-32),idx+1).map(g=>g.su), smin=Math.min(...fin), smax=Math.max(...fin);
  const rel=smax-smin>0.02?(avg(u5,"su")-smin)/(smax-smin):.5;
  f.suoloU=trap(rel,...P.suoloU,.15);
  f.suoloT=trap(avg(u7,"st"),...P.suoloT);
  f.notti=trap(avg(u7,"tmin"),...P.notte,.1);
  f.aria=trap(avg(u5,"ur"),45,65,100,101,.3);
  f.vento=Math.max(.2,1-.25*u5.filter(tram).length);
  let secchi=0; for (let k=idx;k>=Math.max(0,idx-25);k--){ if (D[k].p>=3||D[k].ur>=88) break; secchi++; }
  const extra=ev?Math.max(0,Math.min(P.maxextra||8,(ev.mm-P.pmin)/P.extra)):0;
  f.secco=trap(secchi,-1,0,P.secco[0]+extra,P.secco[1]+extra,.1);
  if (P.calo){ const prec=D.slice(Math.max(0,idx-20),idx-6); if (prec.length>=7){ const c=trap(avg(prec,"tmed")-avg(u7,"tmed"),-3,1.5,8,14,.3); f.calo=1-P.calo*(1-c); } }
  f.quota=trap(quota,...P.quota,.05);
  if (P.senza) for (const x of P.senza) delete f[x];   // prove: fattori esclusi (es. 'quota': nei casi il punto è il paese, non il bosco)
  const vals=Object.values(f), mn=Math.min(...vals); let ind=0;
  if (mn>0){ const geo=Math.exp(vals.reduce((s,v)=>s+Math.log(v),0)/vals.length); ind=Math.pow(geo,.6)*Math.pow(mn,.4)*Math.min(1,.5+f.pioggia)*Math.min(1,.5+f.suoloU); }
  return 100*ind;
}
// regole pubblicate da Fungaiolo, ricostruite (non il suo codice)
function fungaiolo(D,idx){
  let a=0; for (let j=idx;j>=0;j--) if (D[j].p>=20) a=Math.max(a,trap(idx-j,5,8,25,32));
  const b=trap(avg(D.slice(idx-4,idx+1),"ur"),45,65,101,102,.2), c=trap(avg(D.slice(idx-6,idx+1),"tmin"),2,7,16,20,.2);
  const cal=avg(D.slice(idx-20,idx-6),"tmed")-avg(D.slice(idx-6,idx+1),"tmed"), e=trap(cal,-3,0,8,14,.5);
  const t=D.slice(idx-4,idx+1).filter(tram).length;
  return 100*Math.pow(a*b*c*e*Math.max(.2,1-.25*t),1/2.2);
}
// casi pronti: serie giornaliera con temperature corrette per la quota del luogo
function prepara(dati){
  return dati.map(r=>{
    const corr=(r.zcella-r.quota)*0.0065;
    const D=r.serie.map(x=>{ const tn=x.tn+corr, tx=x.tx+corr, tm=(tn+tx)/2; return {d:x.d,p:x.p,tmin:tn,tmax:tx,tmed:tm,st:tm-1,ur:x.ur,su:(x.gt+x.gr)/2,vd:x.vd,vm:x.vm}; });
    let idx=D.findIndex(g=>g.d===r.data); if (idx<0) idx=D.length-1;           // dati più recenti mancanti: ultimo giorno disponibile
    const fin={g:[-2,0],s:[-4,3],m:[-10,10]}[r.prec]||[-4,3];
    const lo=Math.max(35,idx+fin[0]), hi=Math.min(D.length-1,idx+fin[1]);
    return {...r, D, lo, hi, y:(r.es==="A"||r.es==="D")?1:0, anno:+r.data.slice(0,4), quotaI:Math.max(300,Math.min(1600,r.quota))};
  }).filter(c=>c.hi>=c.lo);
}
// punteggio di un caso: il massimo dell'indice nella finestra di date compatibile con la fonte
const punteggio=(c,P)=>{ let m=0; for (let i=c.lo;i<=c.hi;i++) m=Math.max(m,valuta(c.D,i,P,c.quotaI)); return m; };
const punteggioF=c=>{ let m=0; for (let i=c.lo;i<=c.hi;i++) m=Math.max(m,fungaiolo(c.D,i)); return m; };
function auc(s,y){ let n=0,c=0; for (let i=0;i<s.length;i++) if (y[i]) for (let j=0;j<s.length;j++) if (!y[j]){ n++; c+= s[i]>s[j]?1:(s[i]===s[j]?.5:0); } return n?c/n:NaN; }
function acc(s,y,t){ let ok=0; s.forEach((v,i)=>{ if ((v>=t)===!!y[i]) ok++; }); return ok/s.length; }
function migliorSoglia(s,y){ let best=[0,0]; for (let t=0;t<=100;t+=2){ const a=acc(s,y,t); if (a>best[0]) best=[a,t]; } return best; }

// variazione casuale dei parametri, entro limiti sensati
function rnd(a,b){ return a+Math.random()*(b-a); }
function perturba(P,forza){
  const q={...P, attesa:[...P.attesa], suoloT:[...P.suoloT], notte:[...P.notte], secco:[...P.secco], suoloU:[...P.suoloU]};
  const j=(v,s)=>v+rnd(-s,s)*forza;
  let a=q.attesa.map((v,i)=>Math.round(j(v,3))); a.sort((x,y)=>x-y); a[0]=Math.max(2,a[0]); for(let i=1;i<4;i++) a[i]=Math.max(a[i],a[i-1]+1); q.attesa=a;
  q.pmin=Math.max(8,Math.min(45,j(q.pmin,6)));
  let t=q.suoloT.map(v=>j(v,2.5)); t.sort((x,y)=>x-y); q.suoloT=t;
  let n=q.notte.map(v=>j(v,2.5)); n.sort((x,y)=>x-y); q.notte=n;
  let s=q.secco.map(v=>Math.round(j(v,3))); s[0]=Math.max(1,s[0]); s[1]=Math.max(s[0]+2,s[1]); q.secco=s;
  q.suoloU=[0,Math.max(.05,Math.min(.8,j(q.suoloU[1],.15))),1.01,1.02];
  q.extra=Math.max(8,Math.min(60,j(q.extra,10)));
  q.calo=Math.max(0,Math.min(1,j(q.calo,.25)));
  return q;
}
function tara(casi,P0,iter){
  const y=casi.map(c=>c.y); let best=P0, bv=auc(casi.map(c=>punteggio(c,P0)),y);
  for (let k=0;k<iter;k++){
    const P=perturba(best, k<iter/2?1:.5); const v=auc(casi.map(c=>punteggio(c,P)),y);
    if (v>bv){ bv=v; best=P; }
  }
  return {P:best, auc:bv};
}
window.ML={trap,valuta,fungaiolo,prepara,punteggio,punteggioF,auc,acc,migliorSoglia,tara,ATTUALE,MATTINA,PIOGGIA60};
})();
