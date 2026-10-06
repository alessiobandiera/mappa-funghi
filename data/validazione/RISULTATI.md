# Confronto indice / casi reali

Metrica: AUC (0,5 = come tirare a caso, 1 = separa perfettamente i giorni buoni dai cattivi).
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
