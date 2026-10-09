#!/usr/bin/env python3
"""
Aggiorna i dati meteo della mappa funghi (Lucchesia e dintorni).

Fonti:
  - SIR Regione Toscana, archivio storico: pioggia giornaliera e temperature min/max MISURATE
    dalle stazioni della zona, fino a ieri (dati prevalidati).
  - CFR Regione Toscana: riepilogo di tutte le stazioni (pioggia cumulata 1-30 giorni, giorni
    asciutti), umidità e vento attuali. Salvati ogni giorno nell'archivio.
  - Open-Meteo: previsione, umidità dell'aria, vento, umidità e temperatura del suolo, e pioggia
    dove non c'è una stazione vicina.
  - Consorzio del fungo di Borgotaro: tabella "Stanno nascendo" (esiti reali, per tarare il modello).

Uscite:
  docs/dati/meteo.json     serie giornaliera per ogni punto della griglia della mappa
  docs/dati/stazioni.json  stazioni della zona con pioggia degli ultimi 30 giorni e giorni asciutti
  data/archivio/AAAA-MM-GG.json  fotografia giornaliera delle stazioni e della tabella di Borgotaro
  data/cache/sir.json      ultime serie SIR scaricate (riusate dall'aggiornamento leggero)

Uso:
  python script/aggiorna.py --completo   # ogni mattina
  python script/aggiorna.py --leggero    # ogni 3 ore: solo previsione, stazioni dalla cache
Solo libreria standard.
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import math
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from zoneinfo import ZoneInfo

RADICE = Path(__file__).resolve().parent.parent
DOCS = RADICE / "docs" / "dati"
ARCHIVIO = RADICE / "data" / "archivio"
CACHE = RADICE / "data" / "cache"
ROMA = ZoneInfo("Europe/Rome")
UA = "mappa-funghi/1.0 (+https://github.com/alessiobandiera/mappa-funghi)"

# stessa griglia della mappa
GRID = dict(lat0=43.72, lat1=44.36, dlat=0.05, lon0=10.05, lon1=10.95, dlon=0.07)
PAST, FUT = 60, 8          # 60 giorni passati (anche per rivedere le uscite); oggi e 7 giorni di previsione
BBOX = (43.55, 9.90, 44.50, 11.10)            # zona delle stazioni (sud, ovest, nord, est)
RAGGIO_PIOGGIA_KM, RAGGIO_TEMP_KM = 12.0, 15.0
GIORNI_SIR = 66


def log(*a):
    print(*a, flush=True)


def scarica(url: str, tentativi: int = 4, attesa: float = 5.0, timeout: int = 60) -> bytes:
    ultimo = None
    for t in range(tentativi):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            ultimo = e
            if e.code == 429:
                time.sleep(30 * (t + 1))
                continue
            if e.code < 500:
                raise
        except Exception as e:  # rete, timeout
            ultimo = e
        time.sleep(attesa * (t + 1))
    raise RuntimeError(f"download fallito: {url} ({ultimo})")


def km(lat1, lon1, lat2, lon2):
    return math.hypot(lat1 - lat2, (lon1 - lon2) * math.cos(math.radians((lat1 + lat2) / 2))) * 111.2


def costa(la):
    return 10.285 - (la - 43.72) * 0.75


def punti_griglia():
    pts, la = [], GRID["lat0"]
    while la <= GRID["lat1"] + 1e-9:
        lo = GRID["lon0"]
        while lo <= GRID["lon1"] + 1e-9:
            if lo >= costa(la):
                pts.append((round(la, 4), round(lo, 4)))
            lo += GRID["dlon"]
        la += GRID["dlat"]
    return pts


# --------------------------------------------------------------------------- SIR
def stazioni_sir(tipo: str) -> list[dict]:
    s, w, n, e = BBOX
    url = ("https://www.sir.toscana.it/open_layers/ajax_stations.php?"
           f"bbox={w},{s},{e},{n}&zoom=10&delay=3&element=&code=&regions=&basins=&models=sir"
           f"&from=2024&to=2030&types={tipo}")
    js = json.loads(scarica(url))
    out = []
    for f in js.get("features", []):
        m = re.search(r"Quota staz\. slm \[m\]</b>\s*([\d.]+)", f.get("description", ""))
        out.append(dict(id=f["id"], nome=f["name"], lat=float(f["lat"]), lon=float(f["lon"]),
                        quota=float(m.group(1)) if m else None))
    return out


def serie_sir(tipo: str, ident: str, dal: date) -> dict:
    """Serie giornaliera dall'archivio SIR: pioggia {data: mm} o temperatura {data: [min, max]}."""
    idst = "pluvio" if tipo == "pluvio" else "termo"
    txt = scarica(f"https://www.sir.toscana.it/archivio/download.php?IDST={idst}&IDS={ident}", timeout=180).decode("utf-8", "replace")
    out = {}
    for riga in txt.splitlines():
        a = riga.split(";")
        if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", a[0] or ""):
            continue
        d = date(int(a[0][6:]), int(a[0][3:5]), int(a[0][:2]))
        if d < dal:
            continue
        try:
            if tipo == "pluvio":
                if len(a) > 2 and a[2].strip() == "@":
                    continue
                out[d.isoformat()] = float(a[1].replace(",", "."))
            else:
                tx, tn = float(a[1].replace(",", ".")), float(a[2].replace(",", "."))
                if -40 < tn <= tx < 50:
                    out[d.isoformat()] = [tn, tx]
        except (ValueError, IndexError):
            continue
    return out


def aggiorna_sir(oggi: date) -> dict:
    dal = oggi - timedelta(days=GIORNI_SIR)
    risultato = {"aggiornato": datetime.now(ROMA).isoformat(timespec="minutes"), "pluvio": [], "termo": []}
    griglia = punti_griglia()
    for tipo in ("pluvio", "termo"):
        raggio = RAGGIO_PIOGGIA_KM if tipo == "pluvio" else RAGGIO_TEMP_KM
        tutte = stazioni_sir(tipo)
        # solo le stazioni abbastanza vicine ad almeno un punto della mappa
        st = [s for s in tutte if any(km(s["lat"], s["lon"], la, lo) <= raggio for la, lo in griglia)]
        log(f"SIR {tipo}: {len(st)} stazioni utili su {len(tutte)} nella zona")

        def una(s):
            try:
                s["dati"] = serie_sir(tipo, s["id"], dal)
            except Exception as e:
                log(f"  {s['id']} {s['nome']}: {e}")
                s["dati"] = {}
            return s
        fatte = []
        with ThreadPoolExecutor(max_workers=4) as ex:
            for s in ex.map(una, st):
                fatte.append(s)
                if len(fatte) % 10 == 0 or len(fatte) == len(st):
                    log(f"  {tipo}: {len(fatte)}/{len(st)} stazioni scaricate")
        st = fatte
        risultato[tipo] = [s for s in st if s["dati"]]
        log(f"  con dati recenti: {len(risultato[tipo])}")
    return risultato


# --------------------------------------------------------------------------- CFR
def righe_cfr(tipo: str) -> list[list[str]]:
    """Le pagine stazioni.php contengono le righe come  nome[i] = new Array("TOS...", ...)."""
    h = scarica(f"https://www.cfr.toscana.it/monitoraggio/stazioni.php?type={tipo}").decode("utf-8", "replace")
    righe = []
    for m in re.finditer(r'new Array\(("TOS[^)]*)\)', h):
        campi = [html.unescape(re.sub(r"<[^>]+>", "", c)) for c in re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(1))]
        if len(campi) > 8 and any(c not in ("", "-") for c in campi[5:]):
            righe.append(campi)
    # la stessa stazione può comparire in più array: tengo la riga più ricca
    migliori = {}
    for r in righe:
        if r[0] not in migliori or sum(c not in ("", "-") for c in r) > sum(c not in ("", "-") for c in migliori[r[0]]):
            migliori[r[0]] = r
    return list(migliori.values())


def num(x):
    try:
        return float(str(x).replace(",", "."))
    except ValueError:
        return None


def riepilogo_cfr() -> dict:
    out = {}
    try:
        elenco = json.loads(scarica("https://www.cfr.toscana.it/monitoraggio/actions.php?action=list&rt=0&type_gauge=pluvio&speed=km/h"))
        coord = {f["IDStazione"]: (float(f["Lat"]), float(f["Lon"])) for f in elenco["features"]}
    except Exception as e:
        log("CFR elenco stazioni:", e)
        coord = {}
    s, w, n, e = BBOX
    dentro = lambda i: i in coord and s <= coord[i][0] <= n and w <= coord[i][1] <= e
    # pioggia: codice, nome, comune, prov, zona, oggi, ora, 1g, 2g, 5g, 7g, 10g, 15g, 30g, giorni asciutti, quota
    try:
        for r in righe_cfr("pluvio_men"):
            if dentro(r[0]) and len(r) >= 16:
                out[r[0]] = dict(nome=r[1], comune=r[2], lat=coord[r[0]][0], lon=coord[r[0]][1], quota=num(r[15]),
                                 oggi=num(r[5]), ora=r[6], p1=num(r[7]), p2=num(r[8]), p5=num(r[9]), p7=num(r[10]),
                                 p10=num(r[11]), p15=num(r[12]), p30=num(r[13]), asciutti=num(r[14]))
    except Exception as e:
        log("CFR pioggia:", e)
    # umidità: codice, nome, prov, -, zona, quota, attuale, ora, poi coppie valore/ora (min e max)
    for tipo, chiave in (("igro", "umidita"), ("anemo", "vento")):
        try:
            for r in righe_cfr(tipo):
                if r[0] in out:
                    out[r[0]][chiave] = r[6:]
        except Exception as e:
            log(f"CFR {tipo}:", e)
    return out


# --------------------------------------------------------------------------- archivio stazioni (data/db)
# Le pagine di dettaglio del CFR mostrano solo da ieri a mezzanotte a ora: ogni giorno salviamo la giornata di ieri,
# un file per giorno e per sensore, mai riscritto (lo storico di git resta leggero). Schema in data/db/README.md.
DB = RADICE / "data" / "db"
TIPI_DB = ("igro", "anemo", "termo", "pluvio")
INTESTAZIONI = {
    "igro": "stazione,ora,umidita",
    "anemo": "stazione,ora,vento_medio_ms,raffica_ms,direzione",
    "termo": "stazione,ora,t_media,t_min,t_max,letture",
    "pluvio": "stazione,ora,mm",
}


def letture_cfr(tipo: str, ident: str):
    h = scarica(f"https://www.cfr.toscana.it/monitoraggio/dettaglio.php?id={ident}&title={ident}_{tipo}&type={tipo}",
                tentativi=2, attesa=2, timeout=20).decode("utf-8", "replace")
    out = []
    for m in re.finditer(r'new Array\("\d+","(\d\d/\d\d/\d{4} \d\d\.\d\d)","([^"]*)","([^"]*)"\)', h):
        try:
            t = datetime.strptime(m.group(1), "%d/%m/%Y %H.%M")
        except ValueError:
            continue
        out.append((t, m.group(2).strip(), m.group(3).strip()))
    return out


def _righe_da(tipo: str, ident: str, validi) -> list[str]:
    if tipo == "igro":
        return [f"{ident},{t:%Y-%m-%dT%H:%M},{v}" for t, v, _ in validi]
    if tipo == "anemo":
        out = []
        for t, v, d in validi:
            med, _, raf = v.partition("/")
            out.append(f"{ident},{t:%Y-%m-%dT%H:%M},{med},{raf},{d}")
        return out
    if tipo == "pluvio":
        # solo le letture con pioggia: le altre valgono 0 (quante letture ci sono lo dice copertura)
        return [f"{ident},{t:%Y-%m-%dT%H:%M},{v}" for t, v, _ in validi if num(v) not in (None, 0.0)]
    ore = {}   # temperatura ogni 5 minuti: media, minimo e massimo di ogni ora
    for t, v, _ in validi:
        x = num(v)
        if x is not None and -40 < x < 50:
            ore.setdefault(t.replace(minute=0), []).append(x)
    return [f"{ident},{h:%Y-%m-%dT%H:%M},{sum(v)/len(v):.1f},{min(v):.1f},{max(v):.1f},{len(v)}" for h, v in sorted(ore.items())]


def _leggi(p: Path) -> list[str]:
    return p.read_text(encoding="utf-8").splitlines()[1:] if p.exists() else []


def _scrivi_csv(p: Path, intest: str, righe) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(intest + "\n" + "".join(r + "\n" for r in sorted(set(righe))), encoding="utf-8")


def archivia_db(oggi: date, budget_s: float = 420) -> dict:
    """Archivia la giornata di ieri, a tempo limitato. Il CFR risponde lentamente: quello che non si finisce resta
    in data/db/_in_corso e il giro successivo scarica solo le stazioni mancanti. Un sensore passa nell'archivio
    definitivo quando ha risposto almeno il 90% delle stazioni, o comunque il giorno dopo (con quello che c'è)."""
    t0 = time.monotonic()
    giorno = oggi - timedelta(days=1)
    corso = DB / "_in_corso"
    finale = lambda tp, g: DB / tp / g[:4] / f"{g}.csv"
    cop_p = lambda g: DB / "copertura" / g[:4] / f"{g}.csv"
    chiusi = []

    def chiudi(tp: str, g: str):
        _scrivi_csv(finale(tp, g), INTESTAZIONI[tp], _leggi(corso / f"{g}-{tp}.csv"))
        (corso / f"{g}-{tp}.csv").unlink(missing_ok=True)
        chiusi.append(f"{g} {tp}")

    # giorni precedenti rimasti a metà: si chiudono con quello che c'è (il CFR non li mostra più)
    if corso.exists():
        for p in sorted(corso.glob("*.csv")):
            g, tp = p.stem[:10], p.stem[11:]
            if g < giorno.isoformat() and tp in INTESTAZIONI:
                chiudi(tp, g)
    mancanti = [t for t in TIPI_DB if not finale(t, giorno.isoformat()).exists()]
    if not mancanti:
        return {"giorno": giorno.isoformat(), "stato": "già archiviato", "chiusi": chiusi}

    elenco = json.loads(scarica("https://www.cfr.toscana.it/monitoraggio/actions.php?action=list&rt=0&type_gauge=pluvio"))
    anag = {f["IDStazione"]: f for f in elenco["features"]}
    s, w, n, e = BBOX
    dentro = lambda i: i in anag and s <= float(anag[i]["Lat"]) <= n and w <= float(anag[i]["Lon"]) <= e
    sensori, previste = {}, {}
    for tipo in TIPI_DB:
        ids = [i for i in sorted({r[0] for r in righe_cfr("pluvio_men" if tipo == "pluvio" else tipo)}) if dentro(i)]
        previste[tipo] = ids
        for i in ids:
            sensori.setdefault(i, []).append(tipo)

    g = giorno.isoformat()
    copertura = {tuple(r.split(",")[:2]): r for r in _leggi(cop_p(g))}
    fatte = lambda tp, i: (tp, i) in copertura and int(copertura[(tp, i)].split(",")[2]) > 0
    lavori = [(tp, i) for tp in mancanti for i in previste[tp] if not fatte(tp, i)]
    log(f"Archivio stazioni: {len(lavori)} serie da scaricare per il {g}")

    def una(job):
        if time.monotonic() - t0 > budget_s:
            return job, None
        try:
            return job, [x for x in letture_cfr(*job) if x[0].date() == giorno]
        except Exception as ex:
            return job, ex
    nuove = {t: [] for t in mancanti}
    with ThreadPoolExecutor(max_workers=4) as ex:
        for (tipo, ident), dati in ex.map(una, lavori):
            if dati is None:
                continue                                   # tempo finito: resta da fare
            if isinstance(dati, Exception):
                copertura.setdefault((tipo, ident), f"{tipo},{ident},0,{type(dati).__name__}")
                continue
            validi = [d for d in dati if d[1] not in ("", "-", "@")]
            copertura[(tipo, ident)] = f"{tipo},{ident},{len(validi)},"
            nuove[tipo] += _righe_da(tipo, ident, validi)
    corso.mkdir(parents=True, exist_ok=True)
    stato = {}
    for tipo in mancanti:
        p = corso / f"{g}-{tipo}.csv"
        if nuove[tipo] or p.exists():
            _scrivi_csv(p, INTESTAZIONI[tipo], _leggi(p) + nuove[tipo])
        ok = sum(1 for i in previste[tipo] if fatte(tipo, i))
        stato[tipo] = f"{ok}/{len(previste[tipo])}"
        if previste[tipo] and ok >= 0.9 * len(previste[tipo]):
            if not p.exists():
                _scrivi_csv(p, INTESTAZIONI[tipo], [])
            chiudi(tipo, g)
    _scrivi_csv(cop_p(g), "tipo,stazione,letture,nota", copertura.values())
    with open(DB / "stazioni.csv", "w", encoding="utf-8", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["stazione", "nome", "comune", "provincia", "lat", "lon", "sensori"])
        for i in sorted(sensori):
            a = anag[i]
            wr.writerow([i, a.get("Nome", ""), a.get("Comune", ""), a.get("Provincia", ""),
                         round(float(a["Lat"]), 5), round(float(a["Lon"]), 5), " ".join(sensori[i])])
    esito = {"giorno": g, "stazioni_pronte": stato, "chiusi": chiusi, "secondi": round(time.monotonic() - t0)}
    (DB / "ultimo_giro.json").write_text(json.dumps(dict(esito, quando=datetime.now(ROMA).isoformat(timespec="minutes")), indent=1))
    return esito



# --------------------------------------------------------------------------- Open-Meteo
DAILY = ["precipitation_sum", "temperature_2m_min", "temperature_2m_max", "temperature_2m_mean",
         "relative_humidity_2m_mean", "wind_direction_10m_dominant", "wind_speed_10m_max"]
HOURLY = ["soil_moisture_3_to_9cm", "soil_moisture_9_to_27cm", "soil_temperature_6cm", "precipitation"]


def media(v):
    v = [x for x in v if x is not None]
    return sum(v) / len(v) if v else None


def open_meteo(pts) -> list[dict]:
    celle = []
    for i in range(0, len(pts), 20):
        parte = pts[i:i + 20]
        q = urllib.parse.urlencode(dict(latitude=",".join(str(p[0]) for p in parte),
                                        longitude=",".join(str(p[1]) for p in parte),
                                        daily=",".join(DAILY), hourly=",".join(HOURLY),
                                        past_days=PAST, forecast_days=FUT, timezone="Europe/Rome"))
        js = json.loads(scarica("https://api.open-meteo.com/v1/forecast?" + q, tentativi=6))
        if isinstance(js, dict):
            js = [js]
        for (la, lo), r in zip(parte, js):
            d, h = r["daily"], r["hourly"]
            per_giorno = {}
            for k, t in enumerate(h["time"]):
                g = per_giorno.setdefault(t[:10], {"um": [], "st": [], "ph": [0.0] * 24})
                g["um"].append(media([h["soil_moisture_3_to_9cm"][k], h["soil_moisture_9_to_27cm"][k]]))
                g["st"].append(h["soil_temperature_6cm"][k])
                g["ph"][int(t[11:13])] += h["precipitation"][k] or 0.0       # pioggia oraria del modello (ora italiana)
            giorni = []
            for k, t in enumerate(d["time"]):
                tn, tx = d["temperature_2m_min"][k], d["temperature_2m_max"][k]
                if tn is None or tx is None:
                    continue
                tm = d["temperature_2m_mean"][k] if d["temperature_2m_mean"][k] is not None else (tn + tx) / 2
                g = per_giorno.get(t, {"um": [], "st": [], "ph": [0.0] * 24})
                giorni.append(dict(d=t, p=d["precipitation_sum"][k] or 0.0, tmin=tn, tmax=tx, tmed=tm,
                                   ur=d["relative_humidity_2m_mean"][k] if d["relative_humidity_2m_mean"][k] is not None else 70,
                                   vd=d["wind_direction_10m_dominant"][k] if d["wind_direction_10m_dominant"][k] is not None else 180,
                                   vm=d["wind_speed_10m_max"][k] or 0.0,
                                   su=media(g["um"]) if media(g["um"]) is not None else 0.25,
                                   st=media(g["st"]) if media(g["st"]) is not None else tm, ph=g["ph"]))
            celle.append(dict(lat=la, lon=lo, elev=round(r.get("elevation", 0)), giorni=giorni))
        log(f"Open-Meteo: {len(celle)}/{len(pts)} punti")
        time.sleep(2.5)
    return celle


# Pioggia prevista (9/10/2026): media oraria di 4 modelli, ciascuno fin dove arriva (AROME France HD ~1,5 km fino a domani,
# ICON-2I ItaliaMeteo 2 km fino a dopodomani, ECMWF IFS e AIFS fino a 7 giorni). Confrontata con la pioggia SIR di 15 stazioni
# da aprile 2025 (data/previsioni/CONFRONTO.md): giorni di «pioggia utile» (≥13 mm in 3 giorni) presi con CSI 0,68/0,65/0,62
# a 0/1/2 giorni contro 0,46/0,36/0,57 della scelta automatica di Open-Meteo (ICON e ICON-D2, che qui sottostimano).
MODELLI_PIOGGIA = ["meteofrance_arome_france_hd", "italia_meteo_arpae_icon_2i", "ecmwf_ifs025", "ecmwf_aifs025_single"]


def pioggia_prevista(celle: list[dict], oggi: date) -> int:
    """Sostituisce pioggia giornaliera e oraria da ieri in poi con la media dei modelli. Restituisce i giorni sostituiti."""
    fatti = 0
    for i in range(0, len(celle), 20):
        parte = celle[i:i + 20]
        q = urllib.parse.urlencode(dict(latitude=",".join(str(c["lat"]) for c in parte), longitude=",".join(str(c["lon"]) for c in parte),
                                        hourly="precipitation", models=",".join(MODELLI_PIOGGIA), past_days=2, forecast_days=FUT,
                                        timezone="Europe/Rome"))
        js = json.loads(scarica("https://api.open-meteo.com/v1/forecast?" + q, tentativi=6))
        if isinstance(js, dict):
            js = [js]
        for c, r in zip(parte, js):
            h = r["hourly"]
            serie = [h.get(f"precipitation_{m}") or [None] * len(h["time"]) for m in MODELLI_PIOGGIA]
            ore = {}
            for k, t in enumerate(h["time"]):
                v = [x[k] for x in serie if x[k] is not None]
                if v:
                    ore.setdefault(t[:10], [None] * 24)[int(t[11:13])] = sum(v) / len(v)
            for g in c["giorni"]:
                ph = ore.get(g["d"])
                if g["d"] < (oggi - timedelta(days=1)).isoformat() or not ph or any(x is None for x in ph):
                    continue
                g["ph"] = ph
                if g["d"] >= oggi.isoformat():
                    g["p"] = round(sum(ph), 1)
                    fatti += 1
        time.sleep(2.5)
    return fatti


# --------------------------------------------------------------------------- fusione
def _idw(valori):
    """media pesata sull'inverso del quadrato della distanza: valori = [(valore, km)]"""
    pesi = [(v, 1 / max(k, 1.0) ** 2) for v, k in valori if v is not None]
    return sum(v * w for v, w in pesi) / sum(w for _, w in pesi) if pesi else None


def _ora_cfr(ora: str, oggi: date):
    """«09/10 17.45» → ore decimali se è di oggi, altrimenti None"""
    m = re.fullmatch(r"(\d\d)/(\d\d) (\d\d)\.(\d\d)", (ora or "").strip())
    if not m or int(m.group(1)) != oggi.day or int(m.group(2)) != oggi.month:
        return None
    return int(m.group(3)) + int(m.group(4)) / 60


def fondi(celle: list[dict], sir: dict, oggi: date, cfr: dict | None = None) -> dict:
    """Per i giorni passati sostituisce pioggia e temperature del modello con i valori misurati vicini.

    Pioggia (corretto il 9/10/2026): l'archivio SIR dà per il giorno D la pioggia dalle 9 del giorno prima alle 9 di D
    (verificato sulle letture del CFR), non da mezzanotte a mezzanotte. Ogni finestra 9→9 misurata viene ripartita fra i due
    giorni civili secondo l'andamento orario della pioggia del modello (se il modello non ne dà, in proporzione alle ore).
    Ieri e l'altro ieri: totali esatti 0-24 del CFR (riepilogo «1 giorno» e «2 giorni»). Oggi: pioggia misurata dal CFR da
    mezzanotte all'ultima lettura, più il modello per le ore che restano. Temperature SIR: già da mezzanotte a mezzanotte."""
    misurati_p = misurati_t = totale = esatti = 0
    pluvio, termo = sir.get("pluvio", []), sir.get("termo", [])
    cfr_st = [dict(v, id=k) for k, v in (cfr or {}).items() if v.get("lat") is not None]
    ieri, altroieri = (oggi - timedelta(days=1)).isoformat(), (oggi - timedelta(days=2)).isoformat()
    for c in celle:
        vic_p = [(s, km(c["lat"], c["lon"], s["lat"], s["lon"])) for s in pluvio]
        vic_p = sorted([x for x in vic_p if x[1] <= RAGGIO_PIOGGIA_KM], key=lambda x: x[1])[:4]
        vic_t = [(s, km(c["lat"], c["lon"], s["lat"], s["lon"])) for s in termo if s.get("quota") is not None]
        vic_t = sorted([x for x in vic_t if x[1] <= RAGGIO_TEMP_KM], key=lambda x: x[1])[:3]
        vic_c = [(s, km(c["lat"], c["lon"], s["lat"], s["lon"])) for s in cfr_st]
        vic_c = sorted([x for x in vic_c if x[1] <= RAGGIO_PIOGGIA_KM], key=lambda x: x[1])[:4]
        c["stazioni"] = dict(pioggia=[s["nome"] for s, _ in vic_p], temperatura=[s["nome"] for s, _ in vic_t[:1]])
        G = {g["d"]: g for g in c["giorni"]}
        # finestre SIR 9→9 della cella: W[D] = pioggia dalle 9 del giorno prima alle 9 di D
        W = {}
        for d in G:
            v = _idw([(s["dati"].get(d), k) for s, k in vic_p])
            if v is not None:
                W[d] = v
        ph = lambda d, a, b: sum((G[d].get("ph") or [0.0] * 24)[a:b]) if d in G else 0.0
        prima = lambda d: (date.fromisoformat(d) - timedelta(days=1)).isoformat()
        dopo = lambda d: (date.fromisoformat(d) + timedelta(days=1)).isoformat()
        nuova = {}
        for d, g in G.items():
            g["fp"] = g["ft"] = 0
            if d >= oggi.isoformat():
                continue
            totale += 1
            # parte 0-9 del giorno d, dalla finestra W[d] (che comincia alle 9 del giorno prima)
            if d in W:
                m_a, m_tot = ph(d, 0, 9), ph(prima(d), 9, 24) + ph(d, 0, 9)
                parte_a, mis_a = W[d] * (m_a / m_tot if m_tot >= 0.3 else 9 / 24), True
            else:
                parte_a, mis_a = ph(d, 0, 9), False
            # parte 9-24 del giorno d, dalla finestra W[d+1]
            d1 = dopo(d)
            if d1 in W:
                m_b, m_tot = ph(d, 9, 24), ph(d, 9, 24) + ph(d1, 0, 9)
                parte_b, mis_b = W[d1] * (m_b / m_tot if m_tot >= 0.3 else 15 / 24), True
            else:
                parte_b, mis_b = ph(d, 9, 24), False
            if mis_a or mis_b:
                nuova[d] = parte_a + parte_b
                g["fp"] = 1
            # ieri e l'altro ieri: totali esatti 0-24 del CFR
            if d in (ieri, altroieri) and vic_c:
                v = _idw([((s.get("p1") if d == ieri else (s["p2"] - s["p1"] if s.get("p2") is not None and s.get("p1") is not None
                           and s["p2"] >= s["p1"] else None)), k) for s, k in vic_c])
                if v is not None:
                    nuova[d] = v; g["fp"] = 1; esatti += 1
        for d, v in nuova.items():
            G[d]["p"] = round(v, 1)
            misurati_p += 1
        # oggi: misurata dal CFR fino all'ultima lettura, poi il modello
        go = G.get(oggi.isoformat())
        if go is not None and vic_c:
            letture = [(s.get("oggi"), _ora_cfr(s.get("ora"), oggi), k) for s, k in vic_c]
            letture = [(v, h, k) for v, h, k in letture if v is not None and h is not None]
            if letture:
                h = min(x[1] for x in letture)
                v = _idw([(v, k) for v, _, k in letture])
                resto = sum(go["ph"][int(h) + 1:]) + go["ph"][min(23, int(h))] * (1 - (h - int(h)))
                go["p"] = round(v + resto, 1)
                go["fp"] = 2          # in parte misurata
        for d, g in G.items():
            if d >= oggi.isoformat():
                continue
            # temperatura: stazione più vicina con dato, corretta per la differenza di quota (SIR: giornata civile)
            for s, k in vic_t:
                if d in s["dati"]:
                    tn, tx = s["dati"][d]
                    corr = (s["quota"] - c["elev"]) * 0.0065
                    nuova_tm = (tn + tx) / 2 + corr
                    g["st"] = g["st"] + (nuova_tm - g["tmed"])          # il suolo segue lo scarto dell'aria
                    g["tmin"], g["tmax"], g["tmed"] = tn + corr, tx + corr, nuova_tm
                    g["ft"] = 1
                    misurati_t += 1
                    break
        for g in c["giorni"]:
            g.pop("ph", None)
    return dict(giorni_passati=totale, pioggia_misurata=misurati_p, pioggia_esatta_cfr=esatti, temperatura_misurata=misurati_t)


def compatta(celle: list[dict], meta: dict) -> dict:
    campi = ["d", "p", "tmin", "tmax", "tmed", "ur", "vd", "vm", "su", "st", "fp", "ft"]
    r = lambda x, n=1: round(x, n) if isinstance(x, float) else x
    return dict(meta, campi=campi, celle=[dict(lat=c["lat"], lon=c["lon"], elev=c["elev"], stazioni=c.get("stazioni", {}),
                                               giorni=[[r(g[k], 3 if k == "su" else 1) for k in campi] for g in c["giorni"]])
                                          for c in celle])


# --------------------------------------------------------------------------- Borgotaro
def borgotaro() -> list[str]:
    try:
        h = scarica("https://www.fungodiborgotaro.com/stannonascendo.php").decode("utf-8", "replace")
        testo = html.unescape(re.sub(r"<[^>]+>", "\n", re.sub(r"<(script|style)[\s\S]*?</\1>", "", h)))
        righe = [re.sub(r"\s+", " ", x).strip() for x in testo.splitlines()]
        return [x for x in righe if x][:400]
    except Exception as e:
        log("Borgotaro:", e)
        return []


# --------------------------------------------------------------------------- main
def scrivi(p: Path, obj, compatto=True):
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":") if compatto else None, indent=None if compatto else 1)


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--completo", action="store_true")
    g.add_argument("--leggero", action="store_true")
    args = ap.parse_args()

    adesso = datetime.now(ROMA)
    oggi = adesso.date()
    cache_sir = CACHE / "sir.json"

    if args.completo:
        sir = aggiorna_sir(oggi)
        scrivi(cache_sir, sir)
        cfr = riepilogo_cfr()
        log(f"CFR: {len(cfr)} stazioni nella zona")
        scrivi(DOCS / "stazioni.json", dict(aggiornato=adesso.isoformat(timespec="minutes"),
                                             stazioni=[dict(id=k, **v) for k, v in cfr.items()]))
        scrivi(ARCHIVIO / f"{oggi.isoformat()}.json",
               dict(data=oggi.isoformat(), ora=adesso.strftime("%H:%M"), stazioni_cfr=cfr, borgotaro=borgotaro()),
               compatto=False)
    else:
        sir = json.loads(cache_sir.read_text()) if cache_sir.exists() else {}
        try:   # pioggia di oggi fino all'ultima lettura: il riepilogo CFR è leggero (poche pagine)
            cfr = riepilogo_cfr()
            log(f"CFR: {len(cfr)} stazioni nella zona")
            scrivi(DOCS / "stazioni.json", dict(aggiornato=adesso.isoformat(timespec="minutes"),
                                                 stazioni=[dict(id=k, **v) for k, v in cfr.items()]))
        except Exception as e:
            log("CFR:", e)
            try:
                cfr = {x.pop("id"): x for x in json.loads((DOCS / "stazioni.json").read_text())["stazioni"]}
            except Exception:
                cfr = {}


    celle = open_meteo(punti_griglia())
    try:
        log("Pioggia prevista, media dei modelli:", pioggia_prevista(celle, oggi), "giorni")
    except Exception as e:
        log("Pioggia prevista dai modelli non riuscita, resta la scelta automatica:", e)
    statistiche = fondi(celle, sir, oggi, cfr)
    log("Fusione:", statistiche)
    meta = dict(aggiornato=adesso.isoformat(timespec="minutes"), oggi=oggi.isoformat(),
                stazioni_sir=dict(pioggia=len(sir.get("pluvio", [])), temperatura=len(sir.get("termo", []))),
                fusione=statistiche,
                fonti="Pioggia e temperature misurate: SIR/CFR Regione Toscana. Modello e previsione: Open-Meteo.com (CC BY 4.0); pioggia prevista: media di AROME France HD (Météo-France), ICON-2I (ItaliaMeteo-ARPAE), ECMWF IFS e AIFS.")
    scrivi(DOCS / "meteo.json", compatta(celle, meta))
    log("Scritto docs/dati/meteo.json")

    # archivio delle stazioni, per ultimo e a tempo limitato: anche negli aggiornamenti leggeri,
    # così quello che non finisce (o una mattina saltata) si recupera nel giro successivo
    try:
        # su GitHub Actions 7 minuti; sul server di casa si può alzare (variabile BUDGET_ARCHIVIO_S)
        log("Archivio stazioni:", archivia_db(oggi, budget_s=float(os.environ.get("BUDGET_ARCHIVIO_S", 420))))
    except Exception as e:
        log("Archivio stazioni non riuscito:", e)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log("ERRORE:", e)
        sys.exit(1)
