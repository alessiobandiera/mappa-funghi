# Previsioni di pioggia contro pioggia misurata

- `stazioni.json`: 15 stazioni SIR sparse sull'area della mappa; `sir.json`: pioggia giornaliera SIR (dalle 9 del giorno prima alle 9 del giorno).
- `om9_<modello>.json`: previsioni passate Open-Meteo (Previous Runs API) negli stessi punti, per anticipo 0-7 giorni:
  chiave `k` = giornata civile, `wk` = dalle 9 alle 9 come SIR. Scaricate con `script/previsioni_scarica.py` (workflow «Previsioni passate contro pioggia misurata»), che **il 1° di ogni mese**
  estende tutto fino al giorno prima e rifà il confronto.
- `CONFRONTO.md`: risultato di `script/previsioni_confronta.py`, con in cima il **verdetto**: se un'alternativa batte la scelta attuale
  di più di 0,03 (CSI della pioggia utile) a qualche anticipo, scrive «Da rivedere». Da qui la scelta della pioggia prevista della mappa
  (media di AROME France HD, ICON-2I, ECMWF IFS e AIFS, in `script/aggiorna.py`).
- `diagnosi_sir.txt`: orari dei valori giornalieri SIR (pioggia 9→9, temperature 0→24), da `script/diagnosi_sir.py`.
- `sonda.txt`: modelli e archivi disponibili (LaMMA non più scaricabile).
