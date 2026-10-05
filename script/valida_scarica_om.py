#!/usr/bin/env python3
"""Meteo storico dei casi di verifica da Open-Meteo (archivio ERA5 / ERA5-Land, ~9 km, con umidità del suolo).

Stesso formato di data/validazione/serie.json (NASA POWER), così valida.js e valida_regole.js lo usano senza modifiche:
  serie: d, p (mm), tn, tx (°C), ur (%), gt/gr (umidità del suolo 0-7 e 7-28 cm, m3/m3), st (temperatura del suolo 0-7 cm),
         vm (raffica/vento max km/h), vd (direzione dominante, gradi)
Le temperature di Open-Meteo sono già riportate alla quota del punto (DEM 90 m): quota = zcella = quota restituita.
Uscita: data/validazione/serie_om.json. Solo libreria standard.
"""
import json, time, urllib.request, urllib.parse
from datetime import date, timedelta

CASI = json.load(open("data/validazione/casi.json"))
DAILY = "precipitation_sum,temperature_2m_min,temperature_2m_max,relative_humidity_2m_mean,wind_speed_10m_max,wind_direction_10m_dominant"
HOURLY = "soil_moisture_0_to_7cm,soil_moisture_7_to_28cm,soil_temperature_0_to_7cm"
UA = {"User-Agent": "mappa-funghi (validazione)"}


def get(url, tent=5):
    for t in range(tent):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(60 * (t + 1)); continue
            if e.code < 500 and t >= 1:
                raise
        except Exception:
            pass
        time.sleep(5 * (t + 1))
    raise RuntimeError("Open-Meteo non risponde: " + url)


def serie(lat, lon, s, e):
    q = urllib.parse.urlencode(dict(latitude=lat, longitude=lon, start_date=s.isoformat(), end_date=e.isoformat(),
                                    daily=DAILY, hourly=HOURLY, timezone="Europe/Rome"))
    js = get("https://archive-api.open-meteo.com/v1/archive?" + q)
    D, H = js["daily"], js["hourly"]
    # medie giornaliere del suolo dalle 24 ore
    giorno = {}
    for i, t in enumerate(H["time"]):
        g = giorno.setdefault(t[:10], [[], [], []])
        for k, nome in enumerate(HOURLY.split(",")):
            v = H[nome][i]
            if v is not None:
                g[k].append(v)
    out = []
    for i, d in enumerate(D["time"]):
        p, tn, tx = D["precipitation_sum"][i], D["temperature_2m_min"][i], D["temperature_2m_max"][i]
        if p is None or tn is None or tx is None:
            continue
        s0, s1, st = (sum(v) / len(v) if v else None for v in giorno.get(d, [[], [], []]))
        out.append(dict(d=d, p=round(p, 1), tn=tn, tx=tx, ur=D["relative_humidity_2m_mean"][i] or 70,
                        gt=round(s0, 3) if s0 is not None else 0.3, gr=round(s1, 3) if s1 is not None else 0.3,
                        st=round(st, 1) if st is not None else round((tn + tx) / 2 - 1, 1),
                        vm=D["wind_speed_10m_max"][i] or 0, vd=D["wind_direction_10m_dominant"][i] or 0))
    return js.get("elevation"), out


dati, err, cache = [], [], {}
oggi = date.today() - timedelta(days=6)          # l'archivio ha qualche giorno di ritardo
for i, (d, prec, lat, lon, es, luogo, url) in enumerate(CASI):
    D = date.fromisoformat(d)
    s, e = D - timedelta(days=80), min(D + timedelta(days=12), oggi)
    try:
        k = (round(lat, 3), round(lon, 3), s, e)
        if k not in cache:
            cache[k] = serie(lat, lon, s, e)
            time.sleep(0.6)
        quota, ser = cache[k]
        dati.append(dict(ci=i, data=d, prec=prec, lat=lat, lon=lon, es=es, luogo=luogo, quota=quota, zcella=quota, serie=ser))
    except Exception as ex:
        err.append(f"{i} {d} {luogo}: {ex}")
    if i % 25 == 0:
        print(f"{i + 1}/{len(CASI)}", flush=True)

json.dump({"fonte": "Open-Meteo archive (ERA5/ERA5-Land), CC BY 4.0", "casi": dati, "errori": err},
          open("data/validazione/serie_om.json", "w"), separators=(",", ":"))
print(f"fatti {len(dati)}, errori {len(err)}", err[:5])
