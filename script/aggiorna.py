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
import html
import json
import math
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
PAST, FUT = 33, 4
BBOX = (43.55, 9.90, 44.50, 11.10)            # zona delle stazioni (sud, ovest, nord, est)
RAGGIO_PIOGGIA_KM, RAGGIO_TEMP_KM = 12.0, 15.0
GIORNI_SIR = 45


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
        with ThreadPoolExecutor(max_workers=4) as ex:
            st = list(ex.map(una, st))
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


# --------------------------------------------------------------------------- Open-Meteo
DAILY = ["precipitation_sum", "temperature_2m_min", "temperature_2m_max", "temperature_2m_mean",
         "relative_humidity_2m_mean", "wind_direction_10m_dominant", "wind_speed_10m_max"]
HOURLY = ["soil_moisture_3_to_9cm", "soil_moisture_9_to_27cm", "soil_temperature_6cm"]


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
                g = per_giorno.setdefault(t[:10], {"um": [], "st": []})
                g["um"].append(media([h["soil_moisture_3_to_9cm"][k], h["soil_moisture_9_to_27cm"][k]]))
                g["st"].append(h["soil_temperature_6cm"][k])
            giorni = []
            for k, t in enumerate(d["time"]):
                tn, tx = d["temperature_2m_min"][k], d["temperature_2m_max"][k]
                if tn is None or tx is None:
                    continue
                tm = d["temperature_2m_mean"][k] if d["temperature_2m_mean"][k] is not None else (tn + tx) / 2
                g = per_giorno.get(t, {"um": [], "st": []})
                giorni.append(dict(d=t, p=d["precipitation_sum"][k] or 0.0, tmin=tn, tmax=tx, tmed=tm,
                                   ur=d["relative_humidity_2m_mean"][k] if d["relative_humidity_2m_mean"][k] is not None else 70,
                                   vd=d["wind_direction_10m_dominant"][k] if d["wind_direction_10m_dominant"][k] is not None else 180,
                                   vm=d["wind_speed_10m_max"][k] or 0.0,
                                   su=media(g["um"]) if media(g["um"]) is not None else 0.25,
                                   st=media(g["st"]) if media(g["st"]) is not None else tm))
            celle.append(dict(lat=la, lon=lo, elev=round(r.get("elevation", 0)), giorni=giorni))
        log(f"Open-Meteo: {len(celle)}/{len(pts)} punti")
        time.sleep(2.5)
    return celle


# --------------------------------------------------------------------------- fusione
def fondi(celle: list[dict], sir: dict, oggi: date) -> dict:
    """Per i giorni passati sostituisce pioggia e temperature del modello con i valori misurati vicini."""
    misurati_p = misurati_t = totale = 0
    pluvio, termo = sir.get("pluvio", []), sir.get("termo", [])
    for c in celle:
        vic_p = [(s, km(c["lat"], c["lon"], s["lat"], s["lon"])) for s in pluvio]
        vic_p = sorted([x for x in vic_p if x[1] <= RAGGIO_PIOGGIA_KM], key=lambda x: x[1])[:4]
        vic_t = [(s, km(c["lat"], c["lon"], s["lat"], s["lon"])) for s in termo if s.get("quota") is not None]
        vic_t = sorted([x for x in vic_t if x[1] <= RAGGIO_TEMP_KM], key=lambda x: x[1])[:3]
        c["stazioni"] = dict(pioggia=[s["nome"] for s, _ in vic_p], temperatura=[s["nome"] for s, _ in vic_t[:1]])
        for g in c["giorni"]:
            g["fp"] = g["ft"] = 0
            if g["d"] >= oggi.isoformat():
                continue
            totale += 1
            # pioggia: media pesata sull'inverso del quadrato della distanza
            pesi = [(s["dati"][g["d"]], 1 / max(k, 1.0) ** 2) for s, k in vic_p if g["d"] in s["dati"]]
            if pesi:
                g["p"] = round(sum(v * w for v, w in pesi) / sum(w for _, w in pesi), 1)
                g["fp"] = 1
                misurati_p += 1
            # temperatura: stazione più vicina con dato, corretta per la differenza di quota
            for s, k in vic_t:
                if g["d"] in s["dati"]:
                    tn, tx = s["dati"][g["d"]]
                    corr = (s["quota"] - c["elev"]) * 0.0065
                    nuova_tm = (tn + tx) / 2 + corr
                    g["st"] = g["st"] + (nuova_tm - g["tmed"])          # il suolo segue lo scarto dell'aria
                    g["tmin"], g["tmax"], g["tmed"] = tn + corr, tx + corr, nuova_tm
                    g["ft"] = 1
                    misurati_t += 1
                    break
    return dict(giorni_passati=totale, pioggia_misurata=misurati_p, temperatura_misurata=misurati_t)


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

    celle = open_meteo(punti_griglia())
    statistiche = fondi(celle, sir, oggi)
    log("Fusione:", statistiche)
    meta = dict(aggiornato=adesso.isoformat(timespec="minutes"), oggi=oggi.isoformat(),
                stazioni_sir=dict(pioggia=len(sir.get("pluvio", [])), temperatura=len(sir.get("termo", []))),
                fusione=statistiche,
                fonti="Pioggia e temperature misurate: SIR/CFR Regione Toscana. Modello e previsione: Open-Meteo.com (CC BY 4.0).")
    scrivi(DOCS / "meteo.json", compatta(celle, meta))
    log("Scritto docs/dati/meteo.json")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log("ERRORE:", e)
        sys.exit(1)
