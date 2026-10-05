#!/usr/bin/env python3
"""Ricostruisce il database DuckDB dai file dell'archivio (data/db, data/archivio, data/validazione).

I CSV restano la fonte: sono scritti una volta e mai riscritti, quindi il database si può rifare da zero
in pochi secondi a ogni giro. Si scrive su un file temporaneo e poi lo si sostituisce, così chi lo sta
leggendo (DBeaver, un notebook, la futura API) non vede mai un database a metà.

Uscita: $DATI_DIR/funghi.duckdb (di default /dati/funghi.duckdb)
"""
from __future__ import annotations

import glob
import json
import os
import sys
import time
from pathlib import Path

import duckdb

REPO = Path(os.environ.get("REPO_DIR", Path(__file__).resolve().parent.parent))
DATI = Path(os.environ.get("DATI_DIR", "/dati"))
DB = REPO / "data" / "db"

SENSORI = {
    # tabella: (cartella, tipi delle colonne)
    "igro":      ("igro",      {"stazione": "VARCHAR", "ora": "TIMESTAMP", "umidita": "DOUBLE"}),
    "anemo":     ("anemo",     {"stazione": "VARCHAR", "ora": "TIMESTAMP", "vento_medio_ms": "DOUBLE",
                                "raffica_ms": "DOUBLE", "direzione": "VARCHAR"}),
    "termo":     ("termo",     {"stazione": "VARCHAR", "ora": "TIMESTAMP", "t_media": "DOUBLE",
                                "t_min": "DOUBLE", "t_max": "DOUBLE", "letture": "INTEGER"}),
    "pluvio":    ("pluvio",    {"stazione": "VARCHAR", "ora": "TIMESTAMP", "mm": "DOUBLE"}),
    "copertura": ("copertura", {"tipo": "VARCHAR", "stazione": "VARCHAR", "letture": "INTEGER", "nota": "VARCHAR"}),
}


def tabella_csv(con, nome: str, cartella: str, colonne: dict) -> int:
    file = sorted(glob.glob(str(DB / cartella / "*" / "*.csv")))
    defin = ", ".join(f"{c} {t}" for c, t in colonne.items())
    if not file:
        con.execute(f"CREATE TABLE {nome} ({defin})")
        return 0
    cols = "{" + ", ".join(f"'{c}': '{t}'" for c, t in colonne.items()) + "}"
    extra = ", giorno DATE" if nome == "copertura" else ""
    sel = "*, CAST(regexp_extract(filename, '(\\d{4}-\\d{2}-\\d{2})\\.csv$', 1) AS DATE) AS giorno" if extra else "*"
    con.execute(f"""CREATE TABLE {nome} AS SELECT {sel} FROM read_csv(?, header=true, columns={cols},
                    filename=true, timestampformat='%Y-%m-%dT%H:%M')""", [file])
    con.execute(f"ALTER TABLE {nome} DROP COLUMN filename")
    return con.execute(f"SELECT count(*) FROM {nome}").fetchone()[0]


def costruisci(dest: Path) -> dict:
    tmp = dest.with_suffix(".tmp")
    tmp.unlink(missing_ok=True)
    con = duckdb.connect(str(tmp))
    righe = {}

    stz = DB / "stazioni.csv"
    if stz.exists():
        con.execute("CREATE TABLE stazioni AS SELECT * FROM read_csv(?, header=true, all_varchar=false)", [str(stz)])
        righe["stazioni"] = con.execute("SELECT count(*) FROM stazioni").fetchone()[0]

    for nome, (cartella, colonne) in SENSORI.items():
        righe[nome] = tabella_csv(con, nome, cartella, colonne)

    # casi di verifica (data/validazione/casi.json, stesso ordine dei campi del file)
    casi = REPO / "data" / "validazione" / "casi.json"
    con.execute("""CREATE TABLE casi (data DATE, tipo VARCHAR, lat DOUBLE, lon DOUBLE,
                   classe VARCHAR, luogo VARCHAR, fonte VARCHAR)""")
    file_casi = [casi, REPO / "data" / "validazione" / "uscite_locali.json"]
    for f in file_casi:
        if f.exists():
            for r in json.loads(f.read_text(encoding="utf-8")):
                if isinstance(r, list) and len(r) >= 5:
                    con.execute("INSERT INTO casi VALUES (?, ?, ?, ?, ?, ?, ?)", (r + [None] * 7)[:7])
    righe["casi"] = con.execute("SELECT count(*) FROM casi").fetchone()[0]

    # fotografie giornaliere (stazioni CFR + tabella di Borgotaro), tenute come JSON
    arch = sorted(glob.glob(str(REPO / "data" / "archivio" / "*.json")))
    con.execute("CREATE TABLE archivio_giornaliero (data DATE, contenuto JSON)")
    for f in arch:
        con.execute("INSERT INTO archivio_giornaliero VALUES (?, ?)", [Path(f).stem, Path(f).read_text(encoding="utf-8")])
    righe["archivio_giornaliero"] = len(arch)

    # viste pronte per l'uso più comune
    con.execute("""CREATE VIEW umidita_giornaliera AS
        SELECT stazione, CAST(ora AS DATE) AS giorno, min(umidita) AS minima, avg(umidita) AS media,
               sum(CASE WHEN umidita >= 95 THEN 0.25 ELSE 0 END) AS ore_sopra_95
        FROM igro GROUP BY ALL""")
    con.execute("""CREATE VIEW pioggia_giornaliera AS
        SELECT c.stazione, c.giorno, coalesce(sum(p.mm), 0) AS mm
        FROM copertura c LEFT JOIN pluvio p ON p.stazione = c.stazione AND CAST(p.ora AS DATE) = c.giorno
        WHERE c.tipo = 'pluvio' AND c.letture > 0 GROUP BY ALL""")
    con.execute("""CREATE VIEW temperatura_giornaliera AS
        SELECT stazione, CAST(ora AS DATE) AS giorno, min(t_min) AS t_min, max(t_max) AS t_max, avg(t_media) AS t_media
        FROM termo GROUP BY ALL""")
    con.close()
    os.replace(tmp, dest)
    return righe


if __name__ == "__main__":
    DATI.mkdir(parents=True, exist_ok=True)
    t0 = time.monotonic()
    try:
        r = costruisci(DATI / "funghi.duckdb")
    except Exception as e:
        print("Database: errore", e, flush=True)
        sys.exit(1)
    print(f"Database aggiornato in {time.monotonic() - t0:.1f} s:", r, flush=True)
