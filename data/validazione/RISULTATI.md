# Confronto indice / casi reali

Metrica: AUC (0,5 = come tirare a caso, 1 = separa perfettamente i giorni buoni dai cattivi).

## 7 ottobre 2026 — confronto con Fungaiolo e «buttata esaurita» graduale

Fungaiolo (app vera, 7/10) dà 82-85 a Monti di Villa, Gallicano 1065 m e Camaiore 932 m; la nostra mappa 0. Pioggia vera:
10-11 settembre ~50 mm, 17-20 settembre 12-31 mm, poi 17 giorni di secco. Fungaiolo conta la pioggia stimata dal modello
(145 mm in 5 settimane a Monti di Villa contro 57 mm dei pluviometri SIR) e non considera il secco successivo. Tabella del Consorzio
di Borgotaro del 6/10: «2/5 nascita scarsa» ovunque.

Dopo troppo secco la nostra mappa azzera la buttata. Prova: ridurla gradualmente fino a un minimo invece di azzerarla.

| | ritrovamenti europei | Italia | Lucchesia (SIR) | indice oggi: Monti di Villa / Gallicano / Camaiore / Pizzorne / Castiglione |
|---|---|---|---|---|
| azzera (attuale) | 0,586 | 0,581 | 0,754 | 0 / 0 / 0 / 0 / 0 |
| **minimo 0,2, in 5 giorni** | **0,589** | **0,582** | **0,763** | 7 / 14 / 43 / 20 / 49 |
| minimo 0,2, in 10 giorni | 0,588 | 0,582 | 0,759 | 9 / 20 / 68 / 31 / 49 |

Il minimo conta poco; la velocità sì per il risultato di oggi (in 10 giorni una pioggerella dopo il secco riporta l'indice a 70-76).
**Applicato il 7/10** (solo porcino, docs/index.html e docs/bosco.html), dopo il ricontrollo:
- ritrovamenti europei (5.092): 0,5863 → 0,5886, differenza appaiata +0,0011…+0,0036 al 90%, meglio nel 100% dei ricampionamenti;
  positiva in ogni Paese e sia negli anni pari sia nei dispari; con esauritaMin=0 identico all'attuale (37.414/37.414 giorni);
- Lucchesia (71 casi SIR): 0,754 → 0,763 (non significativo da solo, meglio nel 73%); cambiano 7 casi, di cui 4 buttate vere
  che la mappa dava a 0 (es. 21/9/2023: 0 → 83);
- funzione della mappa = script di prova su 145 celle × 14 giorni (2.010 identici, 20 a ±1 per arrotondamento, già prima);
- oggi: celle a 0 dal 100% al 3%; 93% sotto 40 («poca roba»), 3% 40-69, 1% sopra 70.

## 7 ottobre 2026 — ritrovamenti GBIF in Europa (4.100, stesso metodo)

Meteo completo per Italia, Svizzera, Austria, Slovenia, Croazia e quasi tutta la Francia (Spagna e altri in scaricamento).

| AUC di strato | tutti (4.100) | Italia (502) | Francia (711) | Svizzera (211) | Austria (2.582) |
|---|---|---|---|---|---|
| indice della mappa | 0,577 | 0,570 | 0,604 | 0,569 | 0,569 |
| **indice senza «calo termico»** | **0,587** | **0,582** | **0,613** | **0,592** | **0,578** |
| Fungaiolo | 0,548 | 0,545 | 0,546 | 0,566 | 0,548 |
| modello statistico addestrato senza quel paese | — | 0,621 | 0,645 | 0,663 | 0,622 |

- **Togliere il calo termico migliora in ogni paese** (tutti: +0,006…+0,014 al 90%, meglio nel 100% dei ricampionamenti) e anche
  in Lucchesia con pioggia SIR (0,746 invece di 0,739). **Ma togliendolo del tutto l'indice arriva a 100 molto più spesso**
  (15% dei giorni invece del 3,4%; 41% dei casi della Lucchesia invece del 14%): più pareggi in cima, meno distinzione tra
  giorni buoni e ottimi. **Con peso ridotto il guadagno resta senza questo difetto**:

  | peso del calo | AUC ritrovamenti | confronti decisi vinti | giorni a 100 | AUC Lucchesia (SIR) |
  |---|---|---|---|---|
  | 0,5 (attuale) | 0,577 | 58,3% | 3,4% | 0,739 |
  | 0,25 | 0,583 | 59,0% | 3,5% | 0,752 |
  | **0,15** | **0,585** | **59,2%** | **3,6%** | **0,754** |
  | 0 | 0,587 | 59,9% | 15,0% | 0,746 |

  Proposta: `calo:.15` per il porcino in docs/index.html e docs/bosco.html.
- Lettiera di foglie (prova del 7 ottobre): far trattenere alle foglie 1-5 mm di pioggia al giorno o rendere la temperatura del
  suolo più lenta e più calda dell'aria cambia l'AUC di ±0,005, dentro l'errore. Serve il tipo di bosco del ritrovamento (app).
- Gli altri fattori (suolo, notti, aria, vento, secco, esaurita, attesa) spostano meno di ±0,003: restano come sono.
- Il **modello statistico** è migliore dell'indice sui ritrovamenti di paesi mai visti (+0,05/+0,09), ma sui 71 casi della
  Lucchesia con pioggia SIR no (0,689 contro 0,739; media dei due 0,744). Pesa soprattutto l'umidità del suolo 7-28 cm
  (valore assoluto ERA5, che nella mappa viene da un altro modello) e la temperatura del suolo con un ottimo verso 14 °C.
  Per ora non sostituisce l'indice: i casi propri dall'app diranno se aggiungerlo come secondo parere.

## 6 ottobre 2026 (sera) — ritrovamenti pubblici GBIF / iNaturalist, Italia

7.531 osservazioni di porcini con data e GPS in Europa centro-meridionale (data/gbif/porcini.json); meteo ERA5-Land per cella
di 0,1° e anno (data/gbif/meteo/, in scaricamento: prima l'Italia). Sono solo ritrovamenti, quindi il confronto è nello stesso punto:
**il giorno del ritrovamento contro gli stessi giorni della settimana 1-4 settimane prima e dopo, a coppie simmetriche**
(si annullano luogo, persona, fine settimana e andamento della stagione: il giorno dell'anno risulta 0,500, come deve).

Italia, 455 ritrovamenti (2.812 giorni di confronto), quota neutra:

| | AUC di strato |
|---|---|
| **indice della mappa** | **0,565** (0,54-0,59 al 90%) |
| Fungaiolo | 0,546 |
| modello statistico (regressione condizionata), addestrato fino al 2021 e verificato 2022-2026 | 0,588 (indice 0,570) |

- Conta soprattutto la **pioggia di 8-21 giorni prima** (0,58 e 0,56); quella degli ultimi 7 giorni no: l'attesa dell'indice è giusta.
- **Il fattore «calo di temperatura» peggiora l'indice**: senza, 0,576 sui ritrovamenti (meglio sia negli anni pari sia nei dispari)
  e 0,746 invece di 0,739 sui casi della Lucchesia con pioggia SIR. È l'unico cambiamento che regge su entrambe le fonti.
- Soglia di pioggia 30-35 mm invece di 20: meglio sui ritrovamenti (0,585-0,592) ma peggio in Lucchesia con i pluviometri
  (0,706): le soglie dipendono dalla fonte della pioggia, non si cambiano.
- Script: script/gbif_scarica.py, gbif_meteo.py (workflow «Porcini da GBIF», riprende da solo ogni 6 ore),
  gbif_confronti.js + gbif_analisi.py (analisi), gbif_tara.js (taratura con verifica su dati tenuti fuori).

Casi: data/validazione/casi.json (292: 156 positivi A+D, 136 negativi S+N).

## 6 ottobre 2026 — pioggia misurata dalle stazioni SIR

Pioggia SIR come fa la mappa per i giorni passati: media pesata 1/d² dei pluviometri entro 12 km (al massimo 4),
temperature dalla stazione più vicina entro 15 km corrette per la quota. Gli altri dati (umidità, suolo, vento) da Open-Meteo.
249 casi su 292 hanno pluviometri SIR entro 12 km (in Val Taro il Passo del Brattello, 955 m, a 5,6 km da Borgotaro, dal 2016).

**La quota va neutralizzata nella verifica.** Le coordinate dei casi sono spesso il paese citato dall'articolo o dal forum
(26 casi in Lucchesia sotto i 500 m, 22 positivi), non il bosco dove si raccoglie: il fattore quota abbassava l'indice
proprio sui casi buoni. I casi verificano il QUANDO, non il DOVE. Nella mappa invece la quota è quella vera della cella e il fattore resta.

| quota neutra | tutti (249) | Lucchesia, Garfagnana, Lunigiana, Abetone (71) | Val Taro e Parma ovest (152) |
|---|---|---|---|
| indice, pioggia Open-Meteo | 0,55 | 0,72 | 0,47 |
| **indice, pioggia SIR (come la mappa)** | **0,58** | **0,74** (0,64-0,84 al 90%) | 0,48 |
| indice, SIR, almeno 60 mm in 10 giorni | 0,57 | 0,69 | 0,52 |
| Fungaiolo, pioggia SIR | 0,60 | 0,63 | 0,55 |

Conclusioni:
- **Nella zona della mappa l'indice funziona**: 0,74 con le stazioni, meglio di Fungaiolo (0,63).
- **La regola dei 60 mm in 10 giorni non si conferma** con la pioggia misurata e la quota neutra: era un effetto della rianalisi
  e della quota dei casi. La mappa resta com'è.
- Togliere la temperatura del suolo migliora di poco (+0,01), non significativo: niente modifiche.
- **In Val Taro nessuna regola funziona** (0,48-0,55): punto generico di Borgotaro, raccolte tra 600 e 1500 m nello stesso giorno,
  esiti soggettivi del forum ("una ventina" è poco per uno e tanto per un altro), stessa buttata raccontata da persone diverse.
  Questi casi servono a poco per tarare: servono casi con posto e quota veri.

## 5 ottobre 2026 — pioggia Open-Meteo (rianalisi ERA5), quota del punto

| | n | indice attuale | Fungaiolo |
|---|---|---|---|
| tutti | 292 | 0,51 | 0,58 |
| casi originali (quelli su cui l'indice era stato tarato) | 117 | 0,67 | 0,59 |
| casi nuovi (forum, giornali) | 175 | 0,45 | 0,57 |

Con 60 mm in 10 giorni l'AUC saliva a 0,60, ma sui dati NASA POWER crollava (0,75 → 0,52) e con le stazioni SIR non regge (vedi sopra).
Modelli statistici (un anno alla volta fuori): regressione logistica 0,58, gradient boosting 0,57.

## Prossimo passo
Casi propri con GPS: posto, quota e bosco veri, esito certo (anche i giri a vuoto). Sono quelli che servono per tarare.

## File
- serie_sir.json: pioggia e temperature SIR attorno a ogni caso (workflow «Pioggia delle stazioni SIR per i casi», a mano)
- variabili_om.json: indice e variabili Open-Meteo per caso
- script/valida_sir.js: confronto Open-Meteo / SIR (`node script/valida_sir.js` con serie_om.json, oppure nel browser)
- script/valida_ml.py, script/valida_confronto.js, script/valida_regole.js (opzioni di prova: totmin, cluster, senza)
- serie_om.json non è nel repository: il workflow «Meteo storico dei casi» da GitHub viene rallentato da Open-Meteo
  (limite di richieste) e va in timeout; il meteo dei casi è stato scaricato dal browser.

## 8 ottobre 2026 — porcino d'autunno (applicato)

Domanda: i porcini estivi (reticulatus, aereus) e quelli d'autunno (edulis, pinophilus) nascono con condizioni diverse?
Ritrovamenti GBIF divisi per specie e mese (6.340, indice di allora): aereus 0,645, reticulatus 0,597, edulis 0,578;
giugno-luglio 0,585, agosto-settembre 0,609, **ottobre-dicembre 0,568** (il periodo peggiore).

Taratura sui soli ritrovamenti d'autunno, verificata su dati non usati (anni pari ↔ dispari, Italia tenuta fuori):
0,550 → 0,600, 0,588 → 0,612, 0,563 → 0,575. In tutte le prove l'autunno vuole un'attesa più lunga, suolo e notti più freddi,
più giorni asciutti tollerati. In estate la taratura non migliora (i parametri attuali vanno già bene).

Profilo d'autunno: attesa 8/15/22/30 giorni (era 7/12/18/26), suolo 4/8/20/25 °C (era 8/12/22/26), notti 2/5/19/22 °C (era 3/8/19/22),
secco 10/18 giorni (era 5/13). Passaggio graduale dal 1° al 31 ottobre (`autunno`, `autunnoDa:274`, `autunnoGiorni:30`, funzione
`profiloStagione` in index.html, bosco.html e valida_regole.js).

| passaggio | GBIF ott-dic | settembre | estate | Lucchesia (49 casi, suolo NASA + pioggia SIR) |
|---|---|---|---|---|
| nessuno | 0,573 | 0,624 | 0,590 | 0,680 |
| 15/9 → 15/10 | 0,608 | 0,632 | = | 0,671 |
| **1/10 → 31/10 (scelto)** | **0,593** | 0,624 | = | **0,685** |

(Profilo deciso dalla data del ritrovamento per tutti i giorni confrontati. Valutando ogni giorno con il suo profilo, come fa la
mappa, i ritrovamenti di fine settembre perdono un po' perché i giorni di ottobre confrontati salgono: agosto-settembre 0,609 → 0,602.)
Analisi ufficiale dopo l'applicazione (gbif_analisi.py, con anche l'esaurimento graduale ora negli script): tutti 0,596, edulis 0,584,
pinophilus 0,615, ottobre-dicembre 0,593. Mappa e script danno lo stesso indice (±1 di arrotondamento, senza il fattore bosco).
Effetto sulla mappa: media delle celle l'8/10 13,5 → 21,1, il 15/10 1,7 → 10,2 (il secco di settembre pesa meno in autunno).
Da verificare con le uscite dell'app.
