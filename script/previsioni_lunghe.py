#!/usr/bin/env python3
"""Pioggia prevista da 0 a 14 giorni contro la pioggia misurata (per la previsione a 3 settimane, 10/10/2026).

L'archivio «Previous Runs» di Open-Meteo arriva a 7 giorni di anticipo; per andare oltre si usano le corse complete salvate
dalla Single Runs API: ECMWF IFS HRES 9 km (ecmwf_ifs) dal 2024, gli altri modelli globali dal 2 aprile 2026; 15-16 giorni ciascuna.
Una corsa al giorno, alle 00 UTC.
Stazioni e pioggia SIR: le stesse del confronto mensile (data/previsioni/stazioni.json e sir.json).

Anticipo k: la finestra SIR del giorno D (dalle 9 del giorno prima alle 9 di D) con D = giorno della corsa + k + 1,
cioè la pioggia del giorno civile «oggi + k» della mappa, spostata di 9 ore come l'archivio SIR.
Punteggi per anticipo: giorni ≥3 mm, ≥20 mm, «pioggia utile» ≥13 mm in 3 giorni (stessa corsa per i 3 giorni), frequenza
di base dei giorni di pioggia utile (= CSI di chi dice sempre «sì»).
Uscita: data/previsioni/lunghe_<modello>.json (si riprende da dove si era fermato) e data/previsioni/LUNGHE.md
Variabili: MODELLI, SOLO_CONFRONTO=1 (non scarica), SOLO_SCARICA=1 (non confronta), SONDA_SUOLO=1 (solo umidità del suolo a 16 giorni).
"""
import json, os, sys, time, urllib.error, urllib.parse, urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

DIR = Path(__file__).resolve().parent.parent / "data" / "previsioni"
UA = {"User-Agent": "mappa-funghi/1.0 (+https://github.com/alessiobandiera/mappa-funghi)"}
URL = "https://single-runs-api.open-meteo.com/v1/forecast"
DAL = {"ecmwf_ifs": date(2025, 4, 13)}          # la pioggia SIR del confronto parte dal 15/4/2025
DAL_ALTRI = date(2026, 4, 2)
MODELLI = [m for m in os.environ.get("MODELLI", "ecmwf_ifs,ecmwf_ifs025,ecmwf_aifs025_single,gfs_seamless").split(",") if m]
NOMI = {"ecmwf_ifs": "ECMWF IFS HRES 9 km", "ecmwf_ifs025": "ECMWF IFS 0,25°", "ecmwf_aifs025_single": "ECMWF AIFS (IA)", "gfs_seamless": "GFS (USA)",
        "media2": "media ECMWF IFS + AIFS", "media3": "media ECMWF IFS + AIFS + GFS"}
LEAD = range(0, 15)


def log(*a):
    print(datetime.now().strftime("%H:%M:%S"), *a, flush=True)


def chiedi(par, tentativi=6):
    url = URL + "?" + urllib.parse.urlencode(par)
    for t in range(tentativi):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            corpo = e.read()[:300].decode("utf-8", "replace")
            if e.code == 429:
                log("  429, attendo", corpo[:100]); time.sleep(65 * (t + 1)); continue
            if e.code == 400:
                log("  400", corpo[:200]); return None
            log("  HTTP", e.code, corpo[:100]); time.sleep(10 * (t + 1))
        except Exception as e:
            log("  errore", str(e)[:120]); time.sleep(5 + 5 * t)
    return None


def finestre9(tempi, valori):
    """somme dalle 9 del giorno prima alle 9 di D (ora italiana) → {D: mm}, solo finestre complete"""
    fin, n = {}, {}
    for t, v in zip(tempi, valori):
        d9 = t[:10] if int(t[11:13]) < 9 else (date.fromisoformat(t[:10]) + timedelta(days=1)).isoformat()
        n[d9] = n.get(d9, 0) + 1
        if v is not None:
            fin.setdefault(d9, []).append(v)
    # modelli a passo di 6 ore (AIFS) danno valori solo ogni 6 ore: completa se tutte le ore con dato coprono la finestra
    return {d: round(sum(v), 1) for d, v in fin.items() if n[d] == 24 and (len(v) == 24 or len(v) == 4)}


def scarica(modello, stazioni):
    file = DIR / f"lunghe_{modello}.json"
    out = json.load(open(file)) if file.exists() else {}
    fatte = set(out.get("_corse", []))
    ultimo = date.today() - timedelta(days=2)
    r = DAL.get(modello, DAL_ALTRI)
    nuove = 0
    while r <= ultimo:
        if r.isoformat() in fatte:
            r += timedelta(days=1); continue
        js = chiedi(dict(latitude=",".join(str(s["lat"]) for s in stazioni), longitude=",".join(str(s["lon"]) for s in stazioni),
                         run=f"{r.isoformat()}T00:00", hourly="precipitation", models=modello, forecast_days=16, timezone="Europe/Rome"))
        if js is not None:
            if isinstance(js, dict):
                js = [js]
            for s, x in zip(stazioni, js):
                H = x.get("hourly") or {}
                v = H.get("precipitation") or H.get(f"precipitation_{modello}")
                if not v:
                    continue
                for d, mm in finestre9(H["time"], v).items():
                    k = (date.fromisoformat(d) - r).days - 1
                    if k in LEAD:
                        out.setdefault(s["id"], {}).setdefault(str(k), {})[d] = mm
            fatte.add(r.isoformat()); nuove += 1
        if nuove and nuove % 20 == 0:
            out["_corse"] = sorted(fatte); json.dump(out, open(file, "w"), separators=(",", ":"))
            log(f"  {modello}: corse fino al {r}")
        time.sleep(1.2)
        r += timedelta(days=1)
    out["_corse"] = sorted(fatte)
    json.dump(out, open(file, "w"), separators=(",", ":"))
    log(f"{modello}: {len(fatte)} corse")


def punteggi(cp, soglia):
    a = sum(1 for f, o in cp if f >= soglia and o >= soglia); b = sum(1 for f, o in cp if f >= soglia and o < soglia)
    c = sum(1 for f, o in cp if f < soglia and o >= soglia)
    return dict(CSI=a / (a + b + c) if a + b + c else None, POD=a / (a + c) if a + c else None, FAR=b / (a + b) if a + b else None,
                base=(a + c) / len(cp) if cp else None, n=len(cp))


def tabella(sir, mod, combo, righe, titolo):
    """punteggi per anticipo sugli stessi giorni e stazioni per tutti i modelli di `mod`"""
    add = lambda d, n: (date.fromisoformat(d) + timedelta(days=n)).isoformat()
    f2 = lambda x: "–" if x is None else f"{x:.2f}"
    nomi = list(mod)
    tutti = nomi + [c for c in combo if all(x in nomi for x in combo[c])]
    def val(p, m):
        return p[nomi.index(m)] if m in nomi else sum(p[nomi.index(x)] for x in combo[m]) / len(combo[m])
    righe += [f"## {titolo}", "",
              "| anticipo | modello | ≥3 mm CSI | ≥20 mm CSI | pioggia utile 3 gg CSI | presi | falsi allarmi | base | giorni |",
              "|---|---|---|---|---|---|---|---|---|"]
    sintesi, periodo = {}, set()
    for k in LEAD:
        giorni = {}
        for st, oss in sir.items():
            for d, o in oss.items():
                p = [mod[m].get(st, {}).get(str(k), {}).get(d) for m in nomi]
                if all(x is not None for x in p):
                    giorni[(st, d)] = (o, p)
        if not giorni:
            continue
        periodo |= {d for _, d in giorni}
        for m in tutti:
            cp = [(val(p, m), o) for o, p in giorni.values()]
            # pioggia utile: 3 giorni della stessa corsa (anticipi k-2, k-1, k) contro 3 giorni misurati
            tre = []
            if k >= 2:
                for (st, d), (o, p) in giorni.items():
                    d1, d2 = add(d, -1), add(d, -2)
                    o1, o2 = sir[st].get(d1), sir[st].get(d2)
                    q1 = [mod[x].get(st, {}).get(str(k - 1), {}).get(d1) for x in nomi]
                    q2 = [mod[x].get(st, {}).get(str(k - 2), {}).get(d2) for x in nomi]
                    if o1 is None or o2 is None or any(x is None for x in q1 + q2):
                        continue
                    tre.append((val(p, m) + val(q1, m) + val(q2, m), o + o1 + o2))
            u = punteggi(tre, 13) if tre else {}
            p3, p20 = punteggi(cp, 3), punteggi(cp, 20)
            righe.append(f"| {k} | {NOMI.get(m, m)} | {f2(p3['CSI'])} | {f2(p20['CSI'])} | {f2(u.get('CSI'))} | {f2(u.get('POD'))} | {f2(u.get('FAR'))} | "
                         f"{f2(u.get('base'))} | {len(giorni)} |")
            sintesi.setdefault(m, {})[k] = (p3["CSI"], u.get("CSI"), u.get("base"))
    if periodo:
        righe.insert(len(righe) - 2 - sum(len(v) for v in sintesi.values()), f"Giorni dal {min(periodo)} al {max(periodo)}.\n")
    righe += ["", "In breve, pioggia utile (CSI per anticipo; tra parentesi la frequenza di base):", ""]
    for m, s in sintesi.items():
        righe.append(f"- {NOMI.get(m, m)}: " + ", ".join(f"{k}: {v[1]:.2f}" + (f" ({v[2]:.2f})" if v[2] is not None else "")
                                                       for k, v in sorted(s.items()) if v[1] is not None))
    righe.append("")


def confronta():
    sir = json.load(open(DIR / "sir.json"))
    mod = {m: json.load(open(DIR / f"lunghe_{m}.json")) for m in MODELLI if (DIR / f"lunghe_{m}.json").exists()}
    righe = ["# Pioggia prevista a 0-14 giorni contro la pioggia misurata (stazioni SIR)", "",
             f"Corse delle 00 UTC (Single Runs API di Open-Meteo), {len(sir)} stazioni SIR. Anticipo k = pioggia del giorno «oggi + k» "
             "(finestra SIR dalle 9 alle 9). In ogni tabella stessi giorni e stazioni per tutti i modelli a ogni anticipo. CSI: 1 = perfetto, 0 = mai preso; "
             "«base» = frequenza dei giorni con l'evento, cioè il CSI di chi dice sempre «sì». Pioggia utile: ≥13 mm in 3 giorni, i 3 giorni dalla stessa corsa.", ""]
    if "ecmwf_ifs" in mod:
        tabella(sir, {"ecmwf_ifs": mod["ecmwf_ifs"]}, {}, righe, "ECMWF IFS HRES 9 km, periodo lungo")
    altri = {m: v for m, v in mod.items() if m != "ecmwf_ifs"}
    if altri:
        tabella(sir, altri, {"media2": ["ecmwf_ifs025", "ecmwf_aifs025_single"], "media3": ["ecmwf_ifs025", "ecmwf_aifs025_single", "gfs_seamless"]},
                righe, "Modelli della media della mappa e GFS, dal 2 aprile 2026")
    testo = "\n".join(righe)
    print(testo)
    open(DIR / "LUNGHE.md", "w").write(testo + "\n")


def sonda_suolo():
    """umidità e temperatura del suolo a 16 giorni: quali modelli le danno e fin dove"""
    q = urllib.parse.urlencode(dict(latitude=44.03, longitude=10.45, forecast_days=16, timezone="Europe/Rome",
                                    hourly="soil_moisture_0_to_7cm,soil_moisture_7_to_28cm,soil_moisture_3_to_9cm,soil_moisture_9_to_27cm,soil_temperature_0_to_7cm,soil_temperature_6cm",
                                    models="ecmwf_ifs025,ecmwf_ifs,ecmwf_aifs025_single,gfs_seamless,gem_seamless,best_match"))
    for t in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request("https://api.open-meteo.com/v1/forecast?" + q, headers=UA), timeout=120) as r:
                js = json.loads(r.read()); break
        except Exception as e:
            log("sonda suolo:", str(e)[:200]); time.sleep(10)
    else:
        return
    H = js["hourly"]
    for k, v in H.items():
        if k == "time": continue
        ok = [t for t, x in zip(H["time"], v) if x is not None]
        log(f"  {k}: {len(ok)} ore, {ok[0] if ok else '-'} … {ok[-1] if ok else '-'}, ultimi {[x for x in v if x is not None][-2:]}")


def main():
    if os.environ.get("SONDA_SUOLO") == "1":
        return sonda_suolo()
    stazioni = json.load(open(DIR / "stazioni.json"))["stazioni"]
    if os.environ.get("SOLO_CONFRONTO") != "1":
        for m in MODELLI:
            log("Single Runs", m)
            scarica(m, stazioni)
    if os.environ.get("SOLO_SCARICA") != "1":
        confronta()


if __name__ == "__main__":
    main()
