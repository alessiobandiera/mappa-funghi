# Confronto indice / casi reali — 5 ottobre 2026

292 casi (156 positivi A+D, 136 negativi S+N), meteo Open-Meteo archive (ERA5/ERA5-Land) per ogni caso.
Metrica: AUC (0,5 = come tirare a caso, 1 = separa perfettamente i giorni buoni dai cattivi).

| | n | indice attuale | Fungaiolo |
|---|---|---|---|
| tutti | 292 | 0,51 | 0,58 |
| casi originali (quelli su cui l'indice era stato tarato) | 117 | 0,67 | 0,59 |
| casi nuovi (forum, giornali) | 175 | 0,45 | 0,57 |
| giornali e blog | 124 | 0,66 | 0,57 |
| forum | 168 | 0,45 | 0,58 |
| Lucchesia, Garfagnana, Lunigiana, Abetone | 76 | 0,62 | 0,54 |
| Val Taro e Parma ovest | 185 | 0,47 | 0,60 |

Modelli statistici (un anno alla volta fuori): regressione logistica 0,58, gradient boosting 0,57.

## Diagnosi
- L'indice dà ≥ 60 nel 72% dei casi, anche in quelli con "cappotto": è troppo generoso.
- Si accende con piogge modeste (10-20 mm in 3 giorni). Nei negativi del forum (es. settembre 2016 in Val Taro,
  "secco", "cappotti") ERA5 vede 20-40 mm sparsi e l'indice va a 80-90.
- Richiedere pioggia vera migliora: **almeno 60 mm in 10 giorni** porta l'AUC da 0,51 a 0,60
  (miglioramento +0,03…+0,15 al 90%), forum da 0,45 a 0,57, e l'indice dice ≥ 60 solo nel 33% dei casi.
- MA sui dati NASA POWER (con cui era stato tarato) la stessa regola crolla da 0,75 a 0,52:
  **le soglie di pioggia dipendono dalla fonte meteo**. Vanno tarate sulla stessa fonte che usa la mappa
  (stazioni SIR/CFR per i giorni passati), non su una rianalisi.

## Limiti
- Molti casi del forum hanno la zona generica (punto di Borgotaro, 420 m) mentre si cerca spesso a 1000-1400 m.
- Esiti dei forum soggettivi ("una ventina" = scarso per qualcuno, buono per altri).
- ERA5 smussa i temporali estivi: piogge locali sbagliate in più e in meno.

## Prossimo passo
Pioggia misurata dalle stazioni per i casi: SIR Regione Toscana (Toscana) e ARPAE Emilia-Romagna (Val Taro),
poi ripetere il confronto e tarare le soglie su quella fonte.

File: variabili_om.json (indice e variabili per caso), script/valida_ml.py, script/valida_confronto.js,
script/valida_scarica_om.py (riscarica il meteo quando GitHub Actions ha runner disponibili).
