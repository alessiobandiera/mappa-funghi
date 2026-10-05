#!/usr/bin/env python3
"""Scarica il meteo storico (NASA POWER) e la quota dei casi di verifica in data/validazione/casi.json.
Gira su GitHub Actions; il confronto tra regole si fa poi con script/valida.js sui dati salvati."""
import io, json, math, time, urllib.request
from datetime import date, timedelta

CASI = json.load(open("data/validazione/casi.json"))
PAR = "PRECTOTCORR,T2M_MIN,T2M_MAX,RH2M,GWETTOP,GWETROOT,WS10M_MAX,WD10M"
def get(url, t=120):
    req = urllib.request.Request(url, headers={"User-Agent": "mappa-funghi"})
    with urllib.request.urlopen(req, timeout=t) as r: return r.read()

tiles = {}
def quota(lat, lon, z=12):
    from PIL import Image
    n = 2 ** z; fx = (lon + 180) / 360 * n
    lr = math.radians(lat); fy = (1 - math.log(math.tan(lr) + 1 / math.cos(lr)) / math.pi) / 2 * n
    x, y = int(fx), int(fy)
    if (x, y) not in tiles:
        tiles[(x, y)] = Image.open(io.BytesIO(get(f"https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"))).convert("RGB")
    r, g, b = tiles[(x, y)].getpixel((int((fx - x) * 256), int((fy - y) * 256)))
    return round(r * 256 + g + b / 256 - 32768)

def serie(lat, lon, s, e):
    for t in range(5):
        try:
            js = json.loads(get(f"https://power.larc.nasa.gov/api/temporal/daily/point?parameters={PAR}&community=AG"
                                f"&longitude={lon}&latitude={lat}&start={s:%Y%m%d}&end={e:%Y%m%d}&format=JSON"))
            P = js["properties"]["parameter"]
            out = []
            for g in sorted(P["PRECTOTCORR"]):
                x = dict(d=f"{g[:4]}-{g[4:6]}-{g[6:]}", p=P["PRECTOTCORR"][g], tn=P["T2M_MIN"][g], tx=P["T2M_MAX"][g], ur=P["RH2M"][g],
                         gt=P["GWETTOP"][g], gr=P["GWETROOT"][g], vm=P["WS10M_MAX"][g] * 3.6, vd=P["WD10M"][g])
                if x["p"] > -900 and x["tn"] > -900: out.append(x)
            return js["geometry"]["coordinates"][2], out
        except Exception as ex:
            print("  riprovo:", ex, flush=True); time.sleep(5 + 5 * t)
    raise RuntimeError("NASA POWER non risponde")

dati, err = [], []
for i, (d, prec, lat, lon, es, luogo, url) in enumerate(CASI):
    D = date.fromisoformat(d)
    try:
        zc, ser = serie(lat, lon, D - timedelta(days=80), D + timedelta(days=12))
        q = 900 if abs(lat - 43.933) < .01 and abs(lon - 10.61) < .01 else quota(lat, lon)
        dati.append(dict(ci=i, data=d, prec=prec, lat=lat, lon=lon, es=es, luogo=luogo, quota=q, zcella=zc, serie=ser))
    except Exception as ex:
        err.append(f"{i} {d} {luogo}: {ex}")
    if i % 10 == 0: print(f"{i+1}/{len(CASI)}", flush=True)
    time.sleep(0.5)
# serie della stagione in corso alle Pizzorne (per i controlli locali, senza esiti)
zc, ser = serie(43.933, 10.61, date(2026, 7, 1), date.today() - timedelta(days=1))
json.dump({"casi": dati, "errori": err, "pizzorne_2026": {"zcella": zc, "quota": 900, "serie": ser}},
          open("data/validazione/serie.json", "w"), separators=(",", ":"))
print(f"fatti {len(dati)}, errori {len(err)}", err[:5])
