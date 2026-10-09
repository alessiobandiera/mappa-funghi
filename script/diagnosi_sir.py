#!/usr/bin/env python3
"""Diagnosi: su quali ore sono calcolati i valori giornalieri dell'archivio SIR (pioggia e temperature)?
Confronto con le letture del CFR archiviate in data/db (pioggia cumulata da mezzanotte ogni 5 minuti, temperatura oraria).
Stampa soltanto."""
import csv, glob, sys
from collections import defaultdict
from datetime import date, datetime, time, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import aggiorna as A

T = defaultdict(dict)   # stazione -> ora -> (min, max)
for f in sorted(glob.glob(str(A.RADICE / "data/db/termo/2026/*.csv"))):
    for r in csv.DictReader(open(f)):
        T[r["stazione"]][datetime.fromisoformat(r["ora"])] = (float(r["t_min"]), float(r["t_max"]))
stazioni = [s for s in A.stazioni_sir("termo") if s["id"] in T][:12]
print("stazioni termo in comune:", len(stazioni))
giorni = sorted({t.date() for st in T.values() for t in st})
print("giorni CFR:", giorni[0], "…", giorni[-1])
for s in stazioni:
    sir = A.serie_sir("termo", s["id"], date(2026, 10, 1))
    for D in giorni[1:]:
        v = sir.get(D.isoformat())
        if not v: continue
        def fin(h0):   # minimo e massimo dalle h0 del giorno prima alle h0 del giorno (h0=0: giornata civile)
            a = datetime.combine(D, time()) + timedelta(hours=h0) - timedelta(days=1 if h0 else 0)
            b = a + timedelta(days=1)
            x = [mm for t, mm in T[s["id"]].items() if a <= t < b]
            return (min(m[0] for m in x), max(m[1] for m in x), len(x)) if x else None
        out = [f"{h0:02d}→{h0:02d}: " + (f"{r[0]:5.1f} {r[1]:5.1f} ({r[2]}h)" if (r := fin(h0)) else "–") for h0 in (0, 9)]
        print(f"{s['id']} {D}  SIR min/max {v[0]:5.1f} {v[1]:5.1f} | " + " | ".join(out))
