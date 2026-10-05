# Archivio delle stazioni CFR (Regione Toscana)

Letture delle stazioni del Centro Funzionale nella zona della mappa (lat 43,55–44,50, lon 9,90–11,10),
salvate ogni giorno da `script/aggiorna.py`. Il CFR mostra online solo da ieri a mezzanotte a ora:
questo archivio conserva lo storico, che altrimenti andrebbe perso (in particolare l'umidità, che il CFR non archivia).

## Come è organizzato

Un file CSV per **sensore** e per **giorno**, mai riscritto dopo la creazione:

```
data/db/
  stazioni.csv                     anagrafica: stazione, nome, comune, provincia, lat, lon, sensori
  igro/AAAA/AAAA-MM-GG.csv         umidità relativa, ogni 15 minuti
  anemo/AAAA/AAAA-MM-GG.csv        vento ogni 15 minuti
  termo/AAAA/AAAA-MM-GG.csv        temperatura, aggregata per ora (le letture originali sono ogni 5 minuti)
  pluvio/AAAA/AAAA-MM-GG.csv       pioggia ogni 5 minuti, SOLO le letture diverse da zero
  copertura/AAAA/AAAA-MM-GG.csv    quante letture valide ha ogni stazione per ogni sensore quel giorno
```

| file | colonne |
|---|---|
| igro | `stazione, ora, umidita` (%) |
| anemo | `stazione, ora, vento_medio_ms, raffica_ms, direzione` (m/s, gradi da cui proviene) |
| termo | `stazione, ora, t_media, t_min, t_max, letture` (°C, ora = inizio dell'ora) |
| pluvio | `stazione, ora, mm` — una riga mancante vale 0 se la stazione ha letture in `copertura` |

`ora` è l'ora locale italiana come pubblicata dal CFR, formato `AAAA-MM-GGTHH:MM`.
`stazione` è il codice CFR (es. `TOS03001841` = Pizzorne, Villa Basilica, 938 m).

## Interrogarlo

Con DuckDB, direttamente dai file pubblicati su GitHub o dalla copia locale:

```sql
-- umidità minima notturna alle Pizzorne, giorno per giorno
SELECT substr(ora,1,10) AS giorno, min(umidita) AS minima, avg(umidita) AS media,
       sum(CASE WHEN umidita >= 95 THEN 0.25 ELSE 0 END) AS ore_sopra_95
FROM read_csv_auto('data/db/igro/*/*.csv')
WHERE stazione = 'TOS03001841'
GROUP BY giorno ORDER BY giorno;
```

Con Python/pandas: `pd.concat(pd.read_csv(f) for f in glob.glob("data/db/igro/*/*.csv"))`.

Dati: © Centro Funzionale Regione Toscana (www.cfr.toscana.it). Da verificare al primo giorno di pioggia:
se il valore di `pluvio` è la pioggia dei 5 minuti (come sembra) o una cumulata.
