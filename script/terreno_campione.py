#!/usr/bin/env python3
"""Campione di 1500 punti di bosco presi a caso da tutte le tessere (docs/terreno/t): ristagno, sole set/ott/nov, riparo.
Serve alla pagina per dire «meglio o peggio di un bosco tipico» con lo stesso meteo."""
import json, random
import numpy as np
from PIL import Image
idx = json.load(open("docs/terreno/tessere.json"))
random.seed(1); punti = []
pesi = [t["bosco"] * t["righe"] * t["colonne"] for t in idx["tessere"]]
quanti = [round(1500 * p / sum(pesi)) for p in pesi]
for t, n in zip(idx["tessere"], quanti):
    if not n: continue
    a = np.asarray(Image.open(f"docs/terreno/t/{t['id']}_a.png")); b = np.asarray(Image.open(f"docs/terreno/t/{t['id']}_b.png"))
    c = np.asarray(Image.open(f"docs/terreno/t/{t['id']}_c.png"))
    rr, cc = np.nonzero(b[..., 2] > 0)
    for k in random.sample(range(len(rr)), min(n, len(rr))):
        r, q = rr[k], cc[k]
        punti.append([round(a[r, q, 0] / 255, 3), round(c[r, q, 0] / 128, 3), round(c[r, q, 1] / 128, 3), round(c[r, q, 2] / 128, 3), round(a[r, q, 2] / 255, 3)])
json.dump({"nota": "ristagno, sole metà settembre, ottobre, novembre (1 = piano), riparo", "punti": punti},
          open("docs/terreno/campione.json", "w"), separators=(",", ":"))
print(len(punti), "punti")
