#!/usr/bin/env python3
"""Sonda per la previsione a 3 settimane (10/10/2026): cosa danno Open-Meteo e i suoi archivi oltre i 7 giorni.

1. previsione normale a 16 giorni: variabili della mappa giorno per giorno
2. pioggia oraria dei modelli della media (AROME, ICON-2I, ECMWF IFS, AIFS) e di altri candidati fino a 16 giorni
3. API stagionale (EC46, 46 giorni): nomi dei modelli e delle variabili, membri, media
4. Single Runs API (corse passate complete, per verificare la pioggia a 8-15 giorni): modelli e date disponibili
Uso: python script/lungo_sonda.py        (solo libreria standard) → uscita in data/previsioni/lungo_sonda.txt (dal workflow)
"""
import json, time, urllib.error, urllib.parse, urllib.request
from collections import Counter

LA, LO = 44.03, 10.45     # Pizzorna / media valle del Serchio
UA = {"User-Agent": "mappa-funghi/1.0 (+https://github.com/alessiobandiera/mappa-funghi)"}


def chiedi(base, **par):
    url = base + "?" + urllib.parse.urlencode(par)
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"_errore": f"HTTP {e.code}: {e.read()[:400].decode('utf-8', 'replace')}"}
    except Exception as e:
        return {"_errore": str(e)[:300]}


def per_giorno(tempi, valori):
    c = {}
    for t, v in zip(tempi, valori):
        n = c.setdefault(t[:10], [0, 0]); n[1] += 1; n[0] += v is not None
    return c


def riassunto(js, blocco="hourly"):
    if "_errore" in js:
        print("   ", js["_errore"]); return
    H = js.get(blocco) or {}
    if not H:
        print("    nessun blocco", blocco, list(js)); return
    t = H["time"]
    print(f"    {blocco}: {len(t)} passi, da {t[0]} a {t[-1]}; variabili: {len(H) - 1}")
    for k, v in list(H.items())[:60]:
        if k == "time": continue
        pg = per_giorno(t, v)
        ok = [d for d, (a, n) in pg.items() if a]
        piena = [d for d, (a, n) in pg.items() if a == n]
        print(f"      {k}: dati in {len(ok)} giorni ({ok[0] if ok else '-'} … {ok[-1] if ok else '-'}), completi {len(piena)}; ultimi valori {[x for x in v if x is not None][-3:]}")


print("== 1. previsione normale, 16 giorni")
js = chiedi("https://api.open-meteo.com/v1/forecast", latitude=LA, longitude=LO, forecast_days=16, timezone="Europe/Rome",
            daily="precipitation_sum,temperature_2m_min,temperature_2m_max,temperature_2m_mean,relative_humidity_2m_mean,wind_direction_10m_dominant,wind_speed_10m_max",
            hourly="soil_moisture_3_to_9cm,soil_moisture_9_to_27cm,soil_temperature_6cm,precipitation")
riassunto(js, "daily"); riassunto(js, "hourly")
time.sleep(2)

print("== 2. pioggia oraria per modello, 16 giorni")
MOD = ["meteofrance_arome_france_hd", "italia_meteo_arpae_icon_2i", "ecmwf_ifs025", "ecmwf_aifs025_single", "ecmwf_ifs", "gfs_seamless",
       "gfs_graphcast025", "icon_seamless", "gem_seamless", "ukmo_seamless", "meteofrance_seamless", "best_match"]
js = chiedi("https://api.open-meteo.com/v1/forecast", latitude=LA, longitude=LO, forecast_days=16, timezone="Europe/Rome",
            hourly="precipitation", models=",".join(MOD))
riassunto(js, "hourly")
time.sleep(2)

print("== 3. API stagionale")
BASE = "https://seasonal-api.open-meteo.com/v1/seasonal"
print("  -- predefinito, daily temperature_2m_max")
js = chiedi(BASE, latitude=LA, longitude=LO, daily="temperature_2m_max", forecast_days=46)
if "_errore" not in js:
    print("    chiavi:", list(js), "daily:", list(js.get("daily", {}))[:8], "…", len(js.get("daily", {})))
else:
    print("   ", js["_errore"])
for modello in ["ecmwf_ec46", "ec46", "ecmwf_ec46_ensemble_mean", "ecmwf_ec46_mean", "ecmwf_seasonal_seamless", "ecmwf_seas5", "ecmwf_seasonal_ensemble_mean"]:
    time.sleep(2)
    js = chiedi(BASE, latitude=LA, longitude=LO, daily="precipitation_sum", models=modello, forecast_days=30)
    if "_errore" in js:
        print(f"  {modello}: {js['_errore'][:200]}"); continue
    D = js.get("daily", {})
    print(f"  {modello}: {len(D) - 1} serie daily, giorni {D.get('time', ['-'])[0]} … {D.get('time', ['-'])[-1]}; chiavi {list(D)[:5]}")
VAR_D = ["precipitation_sum", "temperature_2m_max", "temperature_2m_min", "temperature_2m_mean", "relative_humidity_2m_mean",
         "wind_speed_10m_max", "wind_speed_10m_mean", "wind_direction_10m_dominant", "soil_moisture_0_to_7cm_mean", "soil_moisture_7_to_28cm_mean",
         "soil_temperature_0_to_7cm_mean", "soil_moisture_0_to_10cm_mean", "rain_sum", "shortwave_radiation_sum"]
VAR_H = ["precipitation", "temperature_2m", "relative_humidity_2m", "wind_speed_10m", "wind_direction_10m", "soil_moisture_0_to_7cm",
         "soil_moisture_7_to_28cm", "soil_temperature_0_to_7cm"]
print("  -- variabili daily una per una (modello predefinito e ecmwf_ec46)")
for v in VAR_D:
    time.sleep(1.5)
    js = chiedi(BASE, latitude=LA, longitude=LO, daily=v, forecast_days=30)
    js2 = chiedi(BASE, latitude=LA, longitude=LO, daily=v, forecast_days=30, models="ecmwf_ec46")
    for nome, j in (("pred.", js), ("ec46", js2)):
        if "_errore" in j:
            print(f"    {v} [{nome}]: {j['_errore'][:160]}"); continue
        D = j["daily"]; ks = [k for k in D if k != "time"]
        prima = D[ks[0]] if ks else []
        print(f"    {v} [{nome}]: {len(ks)} serie ({ks[:2]}…), {len(D['time'])} giorni, primi valori {prima[:5]}")
print("  -- variabili orarie/6 ore (ecmwf_ec46)")
for v in VAR_H:
    time.sleep(1.5)
    for chiave in ("hourly", "six_hourly"):
        js = chiedi(BASE, latitude=LA, longitude=LO, forecast_days=30, models="ecmwf_ec46", **{chiave: v})
        if "_errore" in js:
            print(f"    {v} [{chiave}]: {js['_errore'][:160]}"); continue
        B = js.get(chiave) or {}
        ks = [k for k in B if k != "time"]
        print(f"    {v} [{chiave}]: {len(ks)} serie, {len(B.get('time', []))} passi da {B.get('time', ['-'])[0]}, primi {B[ks[0]][:4] if ks else []}")
print("  -- più punti in una richiesta, tutte le variabili daily utili")
js = chiedi(BASE, latitude=f"{LA},43.85", longitude=f"{LO},10.50", forecast_days=30, models="ecmwf_ec46",
            daily="precipitation_sum,temperature_2m_max,temperature_2m_min,temperature_2m_mean")
print("   ", "errore " + js["_errore"][:200] if isinstance(js, dict) and "_errore" in js else f"ok, {len(js) if isinstance(js, list) else 1} punti")
if isinstance(js, list) and js:
    D = js[0]["daily"]
    soglie = Counter()
    ks = [k for k in D if k.startswith("precipitation_sum")]
    for i, d in enumerate(D["time"][:30]):
        v = sorted(x for x in (D[k][i] for k in ks) if x is not None)
        if v:
            print(f"      {d}: membri {len(v)}, mediana {v[len(v) // 2]:.1f}, media {sum(v) / len(v):.1f}, ≥3 mm {sum(x >= 3 for x in v)}/{len(v)}, max {v[-1]:.1f}")
time.sleep(2)

print("== 4. Single Runs API (corse passate complete)")
SR = "https://single-runs-api.open-meteo.com/v1/forecast"
for modello in ["ecmwf_ifs025", "ecmwf_aifs025_single", "ecmwf_ifs", "gfs_seamless", "gfs025", "italia_meteo_arpae_icon_2i", "meteofrance_arome_france_hd", "icon_global"]:
    for run in ["2024-10-01T00:00", "2026-04-02T00:00", "2026-04-15T00:00", "2026-07-01T00:00", "2026-10-01T00:00"]:
        time.sleep(1.5)
        js = chiedi(SR, latitude=LA, longitude=LO, run=run, hourly="precipitation", models=modello, forecast_days=16, timezone="Europe/Rome")
        if "_errore" in js:
            print(f"  {modello} {run}: {js['_errore'][:160]}"); continue
        H = js.get("hourly", {}); ks = [k for k in H if k != "time"]
        v = H[ks[0]] if ks else []
        ok = [t for t, x in zip(H.get("time", []), v) if x is not None]
        print(f"  {modello} {run}: {len(ok)} ore con dati, {ok[0] if ok else '-'} … {ok[-1] if ok else '-'}; totale {sum(x for x in v if x is not None):.1f} mm")
time.sleep(2)
print("  -- più punti in una richiesta")
js = chiedi(SR, latitude=f"{LA},43.85,44.2", longitude=f"{LO},10.50,10.3", run="2026-09-01T00:00", hourly="precipitation",
            models="ecmwf_ifs025,ecmwf_aifs025_single,gfs_seamless", forecast_days=16, timezone="Europe/Rome")
print("   ", "errore " + js["_errore"][:200] if isinstance(js, dict) and "_errore" in js else
      f"ok, {len(js) if isinstance(js, list) else 1} punti, chiavi {list((js[0] if isinstance(js, list) else js).get('hourly', {}))}")
print("fine")
