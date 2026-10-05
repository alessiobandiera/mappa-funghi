# Server dati della mappa funghi

Un container che fa quello che oggi fanno le GitHub Actions (scaricare SIR, CFR, Open-Meteo e Borgotaro),
ma da casa e senza il limite di 7 minuti per l'archivio CFR. In più tiene un database DuckDB con tutto lo storico.
Il sito resta su GitHub Pages: il server fa push dei dati, una Action pubblica la pagina.

```
crontab (ora italiana) → giro.sh → script/aggiorna.py → docs/dati, data/db, data/archivio
                                 → db.py → dati/funghi.duckdb
                                 → git push (solo con PUBBLICA=1) → Actions "Pubblica la mappa" → Pages
```

## Requisiti
Una macchina Linux sempre accesa con Docker e Docker Compose: LXC/VM su Proxmox, mini PC o Raspberry Pi 5
(l'immagine funziona su amd64 e arm64). Bastano 2 core e 2–4 GB di RAM.

## Installazione
1. Copia la cartella `server/` sulla macchina.
2. Crea la deploy key: `ssh-keygen -t ed25519 -N "" -f deploy_key -C mappa-funghi-server`
   e su GitHub: repository → Settings → Deploy keys → Add, incolla `deploy_key.pub`, spunta **Allow write access**.
3. `cp .env.esempio .env` (lascia `PUBBLICA=0` per la prova).
4. `docker compose up -d --build` e poi `docker compose logs -f`.

## Prova (PUBBLICA=0)
Il server gira accanto alle Actions senza toccare GitHub: a ogni giro riparte da `origin/main`,
calcola e copia l'uscita in `dati/prova/`. Lancia un giro subito con
`docker compose exec funghi /app/giro.sh leggero` e confronta `dati/prova/dati/meteo.json` con quello pubblicato.
In prova l'archivio non si accumula (riparte ogni volta da GitHub): serve solo a verificare che tutto giri.

## Passaggio al server (PUBBLICA=1)
Da fare quando nessun altro lavoro sta facendo push su `main` (per esempio le tessere del terreno).
1. Copia `server/actions/pubblica.yml` in `.github/workflows/`.
2. Sostituisci `.github/workflows/aggiorna.yml` con `server/actions/aggiorna.yml`
   (niente più orari né push automatici; resta lanciabile a mano se il server è fermo).
3. Fai push di questi due file, poi metti `PUBBLICA=1` in `.env` e `docker compose up -d`.

Per tornare alle Actions basta rimettere il vecchio `aggiorna.yml` e fermare il container.

## Orari (server/crontab)
- 06:45 completo
- 09:15, 12:15, 15:15, 18:15, 21:15 leggero (solo previsione)
- ogni ora al minuto 5 archivio CFR: riprende le stazioni mancanti di ieri, esce subito se è già completo

I giri non si sovrappongono: se uno è ancora in corso il successivo viene saltato.

## Database
`dati/funghi.duckdb` si rifà da zero a ogni giro dai CSV (la fonte resta l'archivio in `data/db`).
Tabelle: `stazioni`, `igro`, `anemo`, `termo`, `pluvio`, `copertura`, `casi`, `archivio_giornaliero`.
Viste: `umidita_giornaliera`, `pioggia_giornaliera`, `temperatura_giornaliera`.

```sh
duckdb -readonly dati/funghi.duckdb \
  "SELECT * FROM umidita_giornaliera WHERE stazione='TOS03001841' ORDER BY giorno"
```
Si apre anche con DBeaver o da Python (`duckdb.connect('dati/funghi.duckdb', read_only=True)`).

## Fase 2
Nel compose sono già segnati i posti per `api` (FastAPI in sola lettura sul database) e `cloudflared`
(tunnel Cloudflare, nessuna porta aperta sul router): serviranno per lo storico di una cella cliccata
sulla mappa e per inserire le uscite dal telefono.
