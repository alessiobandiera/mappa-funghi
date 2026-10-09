#!/usr/bin/env python3
"""Confronto delle previsioni di pioggia con la pioggia misurata dalle stazioni SIR (dati di script/previsioni_scarica.py).

Per ogni anticipo (0 = corsa più recente, 1 = previsione del giorno prima, ... 7) e per ogni modello, sugli stessi giorni e stazioni:
- giorni di pioggia ≥3 mm (la soglia dei «giorni secchi» dell'indice): presi (POD), falsi allarmi (FAR), punteggio CSI, rapporto previsti/osservati
- piogge forti ≥20 mm: POD, FAR, CSI
- errore medio assoluto e scarto medio (mm/giorno)
- «pioggia utile» per la buttata: ≥13 mm in 3 giorni (metà della soglia del porcino): POD, FAR, CSI
Uso: python script/previsioni_confronta.py   → stampa e salva data/previsioni/CONFRONTO.md
"""
import json, os, statistics as S
from datetime import date, timedelta
from pathlib import Path

DIR = Path(__file__).resolve().parent.parent / "data" / "previsioni"
sir = json.load(open(DIR / "sir.json"))
modelli = {}
for f in sorted(DIR.glob("om9_*.json")):   # somme dalle 9 alle 9, come i valori giornalieri SIR
    modelli[f.stem[4:]] = json.load(open(f))
if (DIR / "lamma.json").exists():
    modelli["lamma_wrf"] = json.load(open(DIR / "lamma.json"))
NOMI = {"best_match": "Open-Meteo automatico (usato ora)", "italia_meteo_arpae_icon_2i": "ICON-2I ItaliaMeteo 2 km",
        "meteofrance_arome_france_hd": "AROME France HD 1,5 km", "icon_d2": "ICON-D2 2 km", "icon_seamless": "ICON (DWD)",
        "ecmwf_ifs025": "ECMWF IFS", "ecmwf_aifs025_single": "ECMWF AIFS (IA)", "gfs_seamless": "GFS (USA)", "lamma_wrf": "LaMMA WRF 3 km",
        "media": "media dei modelli disponibili"}
add = lambda d, n: (date.fromisoformat(d) + timedelta(days=n)).isoformat()


def punteggi(coppie):
    """coppie: [(previsto, osservato)] → dizionario di punteggi"""
    out = {"n": len(coppie)}
    for nome, soglia in (("p3", 3), ("p20", 20)):
        a = sum(1 for f, o in coppie if f >= soglia and o >= soglia); b = sum(1 for f, o in coppie if f >= soglia and o < soglia)
        c = sum(1 for f, o in coppie if f < soglia and o >= soglia)
        out[nome] = dict(POD=a / (a + c) if a + c else None, FAR=b / (a + b) if a + b else None, CSI=a / (a + b + c) if a + b + c else None,
                         bias=(a + b) / (a + c) if a + c else None, oss=a + c)
    out["MAE"] = S.mean(abs(f - o) for f, o in coppie); out["scarto"] = S.mean(f - o for f, o in coppie)
    return out


def serie(mod, st, k):
    return modelli[mod].get(st, {}).get("w" + str(k), {})


def confronta(k, nomi):
    """Stesse stazioni e giorni per tutti i modelli in `nomi` all'anticipo k."""
    giorni = {}
    for st, oss in sir.items():
        for d, o in oss.items():
            prev = [serie(m, st, k).get(d) for m in nomi]
            if all(p is not None for p in prev):
                giorni[(st, d)] = (o, prev)
    ris = {m: punteggi([(p[i], o) for o, p in giorni.values()]) for i, m in enumerate(nomi)}
    ris["media"] = punteggi([(sum(p) / len(p), o) for o, p in giorni.values()])
    # pioggia utile: somma di 3 giorni (stesso anticipo per ogni giorno), quando tutti e tre i giorni ci sono
    tre = {}
    for (st, d), (o, p) in giorni.items():
        d1, d2 = add(d, -1), add(d, -2)
        if (st, d1) in giorni and (st, d2) in giorni:
            O = o + giorni[(st, d1)][0] + giorni[(st, d2)][0]
            P = [p[i] + giorni[(st, d1)][1][i] + giorni[(st, d2)][1][i] for i in range(len(nomi))]
            tre[(st, d)] = (O, P)
    for i, m in enumerate(list(nomi) + ["media"]):
        cp = [((P[i] if m != "media" else sum(P) / len(P)), O) for O, P in tre.values()]
        a = sum(1 for f, o in cp if f >= 13 and o >= 13); b = sum(1 for f, o in cp if f >= 13 and o < 13); c = sum(1 for f, o in cp if f < 13 and o >= 13)
        ris[m]["utile"] = dict(POD=a / (a + c) if a + c else None, FAR=b / (a + b) if a + b else None, CSI=a / (a + b + c) if a + b + c else None)
    return ris, len(giorni)


f2 = lambda x: "–" if x is None else f"{x:.2f}"
righe = ["# Previsioni di pioggia contro pioggia misurata (stazioni SIR)", "",
         f"Stazioni: {len(sir)}. Modelli: {', '.join(NOMI.get(m, m) for m in modelli)}.",
         "Giorno D = pioggia dalle 9 del giorno prima alle 9 di D (come l'archivio SIR). Ogni tabella usa gli stessi giorni e stazioni per tutti i modelli con quell'anticipo. CSI: 1 = perfetto, 0 = mai preso.", ""]
for k in range(0, 8):
    nomi = [m for m in modelli if any(serie(m, st, k) for st in sir)]
    if not nomi: continue
    ris, n = confronta(k, nomi)
    if not n: continue
    righe += [f"## Anticipo {k} giorn{'o' if k == 1 else 'i'} ({n} giorni-stazione)", "",
              "| modello | ≥3 mm CSI | presi | falsi allarmi | prev./oss. | ≥20 mm CSI | presi | falsi | pioggia utile 3 gg CSI | presi | falsi | errore mm | scarto mm |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for m in sorted(ris, key=lambda m: -(ris[m]["p3"]["CSI"] or 0)):
        r = ris[m]
        righe.append(f"| {NOMI.get(m, m)} | {f2(r['p3']['CSI'])} | {f2(r['p3']['POD'])} | {f2(r['p3']['FAR'])} | {f2(r['p3']['bias'])} | "
                     f"{f2(r['p20']['CSI'])} | {f2(r['p20']['POD'])} | {f2(r['p20']['FAR'])} | {f2(r['utile']['CSI'])} | {f2(r['utile']['POD'])} | {f2(r['utile']['FAR'])} | "
                     f"{r['MAE']:.2f} | {r['scarto']:+.2f} |")
    righe.append("")
testo = "\n".join(righe)
print(testo)
open(DIR / "CONFRONTO.md", "w").write(testo + "\n")
