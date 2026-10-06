#!/usr/bin/env python3
"""Meteo giornaliero (Open-Meteo archive, ERA5/ERA5-Land) attorno alle osservazioni GBIF dei porcini.

Le osservazioni si raggruppano per cella di 0,1° (la risoluzione di ERA5-Land) e anno: una richiesta per gruppo, dalla prima
osservazione meno 63 giorni (storia per l'indice e giorni di confronto) all'ultima più 28.
Riprende da dove era arrivato: i gruppi già scaricati sono in data/gbif/meteo/<anno>.json.
Si ferma da solo quando finisce il tempo (MINUTI) o il limite giornaliero di Open-Meteo, e salva.

Righe del meteo: [pioggia mm, tmin, tmax, umidità %, suolo 0-7 cm, suolo 7-28 cm (m3/m3), temp. suolo 0-7 cm, vento max km/h, direzione]
Variabili d'ambiente: MINUTI (default 300), SOLO_PAESI (es. "IT,FR,CH"), PRIMA_PAESI (ordine di priorità).
"""
import json, os, subprocess, sys, time, urllib.error, urllib.parse, urllib.request
from collections import defaultdict
from datetime import date, timedelta

UA = {"User-Agent": "mappa-funghi (github.com/alessiobandiera/mappa-funghi)"}
DAILY = ("precipitation_sum,temperature_2m_min,temperature_2m_max,relative_humidity_2m_mean,soil_moisture_0_to_7cm_mean,"
         "soil_moisture_7_to_28cm_mean,soil_temperature_0_to_7cm_mean,wind_speed_10m_max,wind_direction_10m_dominant")
DIR = "data/gbif/meteo"
PRIMA, DOPO = 63, 28


def gruppi():
    oss = json.load(open("data/gbif/porcini.json"))["righe"]
    solo = set(filter(None, os.environ.get("SOLO_PAESI", "").split(",")))
    g = defaultdict(list)
    for d, la, lo, sp, paese, inc, ut in oss:
        if solo and paese not in solo:
            continue
        g[f"{round(la, 1):.1f},{round(lo, 1):.1f},{d[:4]}"].append((d, paese))
    prio = os.environ.get("PRIMA_PAESI", "IT,CH,SI,HR,AT,FR,ES,PT,DE").split(",")
    rango = lambda p: prio.index(p) if p in prio else len(prio)
    # prima i paesi più simili ai nostri boschi, poi i gruppi con più osservazioni
    return sorted(g.items(), key=lambda kv: (min(rango(p) for _, p in kv[1]), -len(kv[1])))


def scarica(la, lo, s, e):
    q = urllib.parse.urlencode(dict(latitude=la, longitude=lo, start_date=s, end_date=e, daily=DAILY, timezone="auto"))
    with urllib.request.urlopen(urllib.request.Request("https://archive-api.open-meteo.com/v1/archive?" + q, headers=UA), timeout=90) as r:
        js = json.loads(r.read())
    D = js["daily"]; nomi = DAILY.split(",")
    R = [[(round(D[n][i], 3) if D[n][i] is not None else None) for n in nomi] for i in range(len(D["time"]))]
    return {"el": js.get("elevation"), "s": D["time"][0], "R": R}


def salva(cache, commit=False):
    os.makedirs(DIR, exist_ok=True)
    for anno, v in cache.items():
        json.dump(v, open(f"{DIR}/{anno}.json", "w"), separators=(",", ":"))
    if commit and os.environ.get("GITHUB_ACTIONS"):
        cmd = (f'git add {DIR} && git commit -q -m "Meteo dei punti GBIF: salvataggio intermedio [skip ci]" && '
               'git pull -q --rebase -X theirs origin main && git push -q origin HEAD:main')
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print("  salvataggio intermedio:", "ok" if r.returncode == 0 else r.stderr[-200:], flush=True)


def main():
    t0, limite = time.time(), float(os.environ.get("MINUTI", "300")) * 60
    cache = {}
    if os.path.isdir(DIR):
        for f in os.listdir(DIR):
            cache[f[:-5]] = json.load(open(f"{DIR}/{f}"))
    G = gruppi(); fatti = sum(len(v) for v in cache.values())
    print(f"gruppi cella-anno: {len(G)}, già scaricati: {fatti}", flush=True)
    ultimo_salv, nuovi, attese = time.time(), 0, 0
    ieri = (date.today() - timedelta(days=6)).isoformat()
    for k, oss in G:
        la, lo, anno = k.split(",")
        if k in cache.get(anno, {}):
            continue
        if time.time() - t0 > limite:
            print("tempo finito"); break
        dd = sorted(d for d, _ in oss)
        s = (date.fromisoformat(dd[0]) - timedelta(days=PRIMA)).isoformat()
        e = min((date.fromisoformat(dd[-1]) + timedelta(days=DOPO)).isoformat(), ieri)
        for t in range(6):
            try:
                cache.setdefault(anno, {})[k] = scarica(float(la), float(lo), s, e); nuovi += 1; break
            except urllib.error.HTTPError as ex:
                corpo = ex.read().decode("utf-8", "replace")[:200]
                if ex.code == 429:
                    if "Daily" in corpo:
                        print("limite giornaliero di Open-Meteo raggiunto"); salva(cache, True); return
                    attesa = 60 if "Minutely" in corpo else 600
                    print(f"  429 ({corpo[:80]}): aspetto {attesa} s", flush=True); attese += attesa; time.sleep(attesa)
                else:
                    print("  errore", k, ex.code, corpo[:100], flush=True); time.sleep(5)
            except Exception as ex:
                print("  errore", k, ex, flush=True); time.sleep(5)
        time.sleep(0.4)
        if nuovi and nuovi % 50 == 0:
            print(f"  {nuovi} nuovi gruppi ({(time.time() - t0) / 60:.0f} min, attese {attese / 60:.0f} min)", flush=True)
        if time.time() - ultimo_salv > 900:
            salva(cache, True); ultimo_salv = time.time()
    salva(cache)
    print(f"fine: {nuovi} nuovi, totale {sum(len(v) for v in cache.values())} su {len(G)}")


if __name__ == "__main__":
    sys.exit(main())
