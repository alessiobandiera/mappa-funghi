#!/usr/bin/env python3
"""Dati per confrontare le previsioni di pioggia con la pioggia misurata (Lucchesia e dintorni, area della mappa).

- Pioggia misurata: stazioni SIR Regione Toscana (le stesse che usa la mappa), una ventina sparse sull'area.
- Previsioni passate Open-Meteo (Previous Runs API): per ogni modello la pioggia oraria prevista con 1..7 giorni di anticipo,
  sommata per giorno (ora italiana). Anticipo 0 = la corsa più recente (quasi un'analisi).
- LaMMA WRF-ARW 3 km (dati aperti Regione Toscana, CC BY): vedi script/previsioni_lamma.py.

Uscita: data/previsioni/stazioni.json, sir.json, om_<modello>.json
Variabili d'ambiente: DAL (default 2025-04-15), MODELLI (elenco separato da virgole), MAX_STAZIONI (default 20).
Uso: python script/previsioni_scarica.py        (solo libreria standard)
"""
import json, math, os, sys, time, urllib.error, urllib.parse, urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import aggiorna as A   # stazioni SIR, serie SIR, griglia della mappa

OUT = A.RADICE / "data" / "previsioni"
DAL = date.fromisoformat(os.environ.get("DAL", "2025-04-15"))
AL = date.today() - timedelta(days=1)
MODELLI = os.environ.get("MODELLI", "best_match,italia_meteo_arpae_icon_2i,icon_seamless,ecmwf_ifs025,meteofrance_seamless,gfs_seamless").split(",")
MAX_ST = int(os.environ.get("MAX_STAZIONI", "20"))
LEAD = range(0, 8)


def km(a, b, c, d):
    return A.km(a, b, c, d)


def scegli_stazioni():
    tutte = A.stazioni_sir("pluvio")
    griglia = A.punti_griglia()
    vicine = [s for s in tutte if any(km(s["lat"], s["lon"], la, lo) <= 8 for la, lo in griglia)]
    # sparse sull'area: si sceglie ogni volta la stazione più lontana da quelle già scelte (partendo da Lucca)
    scelte = [min(vicine, key=lambda s: km(s["lat"], s["lon"], 43.84, 10.50))]
    while len(scelte) < min(MAX_ST, len(vicine)):
        s = max((s for s in vicine if s not in scelte), key=lambda s: min(km(s["lat"], s["lon"], t["lat"], t["lon"]) for t in scelte))
        scelte.append(s)
    return scelte


def get_json(url, tentativi=6):
    for t in range(tentativi):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": A.UA}), timeout=180) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            corpo = e.read()[:300]
            A.log(f"  HTTP {e.code}: {corpo}")
            if e.code == 429:
                time.sleep(65 * (t + 1)); continue
            if e.code == 400:
                return None
            time.sleep(10 * (t + 1))
        except Exception as e:
            A.log(f"  errore {e}"); time.sleep(10 * (t + 1))
    return None


def previsioni_om(modello, stazioni):
    """{id_stazione: {anticipo: {data: mm}}} per un modello; pezzi di 120 giorni per richiesta."""
    out = {s["id"]: {str(k): {} for k in LEAD} for s in stazioni}
    var = ["precipitation"] + [f"precipitation_previous_day{k}" for k in range(1, 8)]
    a = DAL
    while a <= AL:
        b = min(AL, a + timedelta(days=119))
        for s in stazioni:
            q = urllib.parse.urlencode(dict(latitude=s["lat"], longitude=s["lon"], hourly=",".join(var), models=modello,
                                            start_date=a.isoformat(), end_date=b.isoformat(), timezone="Europe/Rome"))
            js = get_json("https://previous-runs-api.open-meteo.com/v1/forecast?" + q)
            time.sleep(4)
            if not js or "hourly" not in js:
                continue
            H = js["hourly"]
            for k in LEAD:
                nome = var[k]
                vals = H.get(nome) or H.get(f"{nome}_{modello}")
                if not vals:
                    continue
                giorni = {}
                for t, v in zip(H["time"], vals):
                    giorni.setdefault(t[:10], []).append(v)
                for d, v in giorni.items():
                    if len(v) == 24 and all(x is not None for x in v):
                        out[s["id"]][str(k)][d] = round(sum(v), 1)
        A.log(f"  {modello}: {a} → {b} fatto")
        a = b + timedelta(days=1)
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    st = scegli_stazioni()
    A.log(f"{len(st)} stazioni: " + ", ".join(s["nome"] for s in st))
    meta = [dict(id=s["id"], nome=s["nome"], lat=s["lat"], lon=s["lon"], quota=s["quota"]) for s in st]
    json.dump(dict(dal=DAL.isoformat(), al=AL.isoformat(), stazioni=meta), open(OUT / "stazioni.json", "w"), ensure_ascii=False, indent=0)
    sir = {}
    for s in st:
        try:
            sir[s["id"]] = A.serie_sir("pluvio", s["id"], DAL)
        except Exception as e:
            A.log(f"  SIR {s['nome']}: {e}")
    json.dump(sir, open(OUT / "sir.json", "w"), separators=(",", ":"))
    A.log("SIR: " + ", ".join(f"{len(v)}" for v in sir.values()) + " giorni per stazione")
    for m in MODELLI:
        if (OUT / f"om_{m}.json").exists() and os.environ.get("RIFAI") != "1":
            A.log(f"{m}: già scaricato"); continue
        A.log(f"Open-Meteo {m}")
        json.dump(previsioni_om(m, meta), open(OUT / f"om_{m}.json", "w"), separators=(",", ":"))


if __name__ == "__main__":
    main()
