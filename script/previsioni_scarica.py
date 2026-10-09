#!/usr/bin/env python3
"""Dati per confrontare le previsioni di pioggia con la pioggia misurata (Lucchesia e dintorni, area della mappa).

- Pioggia misurata: stazioni SIR Regione Toscana (le stesse che usa la mappa), una ventina sparse sull'area.
- Previsioni passate Open-Meteo (Previous Runs API): per ogni modello la pioggia oraria prevista con 1..7 giorni di anticipo,
  sommata per giorno (ora italiana). Anticipo 0 = la corsa più recente (quasi un'analisi).
- LaMMA WRF-ARW 3 km (dati aperti Regione Toscana, CC BY): vedi script/previsioni_lamma.py.

Uscita: data/previsioni/stazioni.json, sir.json, om9_<modello>.json (per anticipo: «k» giornata civile, «wk» dalle 9 alle 9 come SIR)
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


def get_json(url, tentativi=8):
    for t in range(tentativi):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": A.UA}), timeout=90) as r:
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
            A.log(f"  errore {str(e)[:100]}"); time.sleep(5 + 5 * t)
    return None


def previsioni_om(modello, stazioni, file):
    """{id_stazione: {anticipo: {data: mm}}} per un modello: tutte le stazioni in una richiesta, blocchi di 60 giorni,
    salvataggio dopo ogni blocco (si riprende da dove si era fermato)."""
    out = json.load(open(file)) if file.exists() else {}
    fatti = set(out.pop("_fatti", []))
    for s in stazioni:
        out.setdefault(s["id"], {str(k): {} for k in LEAD})
    var = ["precipitation"] + [f"precipitation_previous_day{k}" for k in range(1, 8)]
    a = DAL
    while a <= AL:
        b = min(AL, a + timedelta(days=59))
        if a.isoformat() in fatti:
            a = b + timedelta(days=1); continue
        q = urllib.parse.urlencode(dict(latitude=",".join(str(s["lat"]) for s in stazioni), longitude=",".join(str(s["lon"]) for s in stazioni),
                                        hourly=",".join(var), models=modello, start_date=a.isoformat(), end_date=b.isoformat(), timezone="Europe/Rome"))
        js = get_json("https://previous-runs-api.open-meteo.com/v1/forecast?" + q)
        if js is None:
            A.log(f"  {modello}: {a} → {b} NON riuscito"); a = b + timedelta(days=1); continue
        if isinstance(js, dict):
            js = [js]
        for s, r in zip(stazioni, js):
            H = r.get("hourly") or {}
            for k in LEAD:
                vals = H.get(var[k]) or H.get(f"{var[k]}_{modello}")
                if not vals:
                    continue
                giorni, fin9 = {}, {}
                for t, v in zip(H["time"], vals):
                    giorni.setdefault(t[:10], []).append(v)
                    # come l'archivio SIR: il giorno D va dalle 9 del giorno prima alle 9 di D (ora italiana)
                    d9 = t[:10] if int(t[11:13]) < 9 else (date.fromisoformat(t[:10]) + timedelta(days=1)).isoformat()
                    fin9.setdefault(d9, []).append(v)
                for d, v in giorni.items():
                    if len(v) == 24 and all(x is not None for x in v):
                        out[s["id"]][str(k)][d] = round(sum(v), 1)
                for d, v in fin9.items():
                    if len(v) == 24 and all(x is not None for x in v):
                        out[s["id"]].setdefault("w" + str(k), {})[d] = round(sum(v), 1)
        fatti.add(a.isoformat())
        json.dump({**out, "_fatti": sorted(fatti)}, open(file, "w"), separators=(",", ":"))
        A.log(f"  {modello}: {a} → {b} fatto")
        time.sleep(3)
        a = b + timedelta(days=1)
    json.dump({**out, "_fatti": sorted(fatti)}, open(file, "w"), separators=(",", ":"))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    if (OUT / "stazioni.json").exists() and os.environ.get("RIFAI") != "1":   # stesse stazioni e stesso periodo delle altre parti
        meta = json.load(open(OUT / "stazioni.json"))["stazioni"]
        globals()["AL"] = date.fromisoformat(json.load(open(OUT / "stazioni.json"))["al"])
        st = None
    else:
        st = scegli_stazioni()
        A.log(f"{len(st)} stazioni: " + ", ".join(s["nome"] for s in st))
        meta = [dict(id=s["id"], nome=s["nome"], lat=s["lat"], lon=s["lon"], quota=s["quota"]) for s in st]
        json.dump(dict(dal=DAL.isoformat(), al=AL.isoformat(), stazioni=meta), open(OUT / "stazioni.json", "w"), ensure_ascii=False, indent=0)
    sir = {} if st is not None else None
    if sir is not None:
        for s in st:
            try:
                sir[s["id"]] = A.serie_sir("pluvio", s["id"], DAL)
            except Exception as e:
                A.log(f"  SIR {s['nome']}: {e}")
        json.dump(sir, open(OUT / "sir.json", "w"), separators=(",", ":"))
        A.log("SIR: " + ", ".join(f"{len(v)}" for v in sir.values()) + " giorni per stazione")
    for m in MODELLI:
        A.log(f"Open-Meteo {m}")
        previsioni_om(m, meta, OUT / f"om9_{m}.json")


if __name__ == "__main__":
    main()
