#!/usr/bin/env python3
"""Porta i tipi di bosco sulle griglie delle mappe: Corine Land Cover 2018 IV livello (data/boschi/clc18_boschi.geojson) come base
e, sopra, la Carta degli Habitat ISPRA 1:50.000 (data/boschi/habitat_boschi.geojson.gz, più dettagliata: dal 10/10/2026).

- docs/terreno/f/<tessera>.png: un byte per pixel da 20 m, codice del tipo di bosco (0 = nessun poligono ISPRA)
- docs/dati/tipi_bosco.json: tipo prevalente per ogni maglia da 600 m della mappa principale (stessa griglia di BOSCHI_DATI)

Codici: 1 leccio/sughera (3111), 2 querce caducifoglie (3112), 3 altre latifoglie (3113), 4 castagno (3114), 5 faggio (3115),
6 igrofile (3116), 7 latifoglie esotiche (3117), 8 pini mediterranei e cipressi (3121), 9 pini montani (3122), 10 abeti (3123),
11 larice/cembro (3124), 12 conifere esotiche (3125), 13 misti di latifoglie (3131), 14 misti di conifere (3132).
Uso: python script/boschi_tipi.py      (serve Pillow)
"""
import gzip, json, os
from collections import Counter
from PIL import Image, ImageDraw

CODICI = ["3111", "3112", "3113", "3114", "3115", "3116", "3117", "3121", "3122", "3123", "3124", "3125", "3131", "3132"]
NOMI = ["leccio e sughera", "querce caducifoglie", "altre latifoglie", "castagno", "faggio", "salici, pioppi, ontani", "latifoglie esotiche",
        "pini mediterranei", "pini montani", "abeti", "larice", "conifere esotiche", "misto di latifoglie", "misto di conifere"]
G = json.load(open("data/boschi/clc18_boschi.geojson"))
HAB = "data/boschi/habitat_boschi.geojson.gz"


def tipo_habitat(h):
    """codice habitat Carta della Natura (CORINE Biotopes) → codice 1-14 dei tipi della mappa, None se non è bosco"""
    h = h.split("_")[0]
    regole = [("45.8", 3), ("45.", 1),                                           # agrifoglio; leccete, sugherete, macchia alta
              ("41.7", 2), ("41.5", 2), ("44.4", 2), ("41.2", 13),               # roverella, cerro, rovere, farnia; querco-carpineti
              ("41.9", 4), ("41.1", 5),                                          # castagneti; faggete
              ("44.D", 7), ("44.", 6), ("83.321", 6),                            # ripariali alloctoni; ripariali, ontani, salici; pioppeti
              ("83.324", 7), ("83.322", 7), ("41.L", 7), ("83.325", 3),          # robinia, eucalipti, latifoglie alloctone; altre piantagioni
              ("41.81", 3), ("41.86", 3), ("41.88", 3), ("41.8", 13), ("41.4", 13),  # ostrieti, frassineti; misti termofili e di forra
              ("41.3", 3), ("41.B", 3), ("41.C", 3), ("41.D", 3), ("41.F", 3), ("31.8C", 3),
              ("42.8", 8), ("42.A1", 8), ("42.A28", 8), ("42.A7", 10),           # pinete mediterranee, cipressete; tasso
              ("42.5", 9), ("42.6", 9), ("42.4", 9), ("42.7", 9), ("42.1B", 9),  # pino silvestre, nero, laricio; rimboschimenti di conifere indigene
              ("42.1", 10), ("42.2", 10), ("43.1", 14), ("42.3", 11),            # abetine, peccete; misti con abete; larice
              ("42.G", 12), ("83.31", 12)]                                       # conifere alloctone (douglasia…), piantagioni di conifere
    for pre, t in regole:
        if h.startswith(pre):
            return t
    return None


def anelli(geom):
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    for p in polys:
        yield p[0], p[1:]


def area(r):
    return abs(sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(r, r[1:] + r[:1]))) / 2


# Corine prima, dal poligono più grande al più piccolo (i piccoli e i buchi sovrascrivono i grandi); poi la Carta degli Habitat,
# che dove c'è prevale. Degli habitat si disegna solo il contorno esterno: i buchi sono altri habitat (disegnati dopo, se di bosco)
# oppure zone non di bosco, dove decide comunque la maschera dei boschi di OpenStreetMap.
poligoni = []
for f in G["features"]:
    c = f["properties"]["clc"]
    if c not in CODICI: continue
    for est, buchi in anelli(f["geometry"]):
        poligoni.append((area(est), CODICI.index(c) + 1, est, buchi))
poligoni.sort(key=lambda t: -t[0])
habitat = []
if os.path.exists(HAB):
    for f in json.load(gzip.open(HAB, "rt", encoding="utf-8"))["features"]:
        t = tipo_habitat(f["properties"]["hab"])
        if not t: continue
        for est, _ in anelli(f["geometry"]):
            habitat.append((area(est), t, est, []))
    habitat.sort(key=lambda t: -t[0])
    print("poligoni Carta degli Habitat usati:", len(habitat))
poligoni += habitat


def disegna(W, H, a_pixel):
    """Raster W x H con i codici; a_pixel(lon, lat) -> (x, y) in pixel."""
    im = Image.new("L", (W, H), 0); d = ImageDraw.Draw(im)
    for _, cod, est, buchi in poligoni:
        pts = [a_pixel(lo, la) for lo, la in est]
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        if max(xs) < 0 or min(xs) > W or max(ys) < 0 or min(ys) > H: continue
        d.polygon(pts, fill=cod)
        for b in buchi: d.polygon([a_pixel(lo, la) for lo, la in b], fill=0)
    return im


# ---- tessere a 20 m
IDX = json.load(open("docs/terreno/tessere.json"))
os.makedirs("docs/terreno/f", exist_ok=True)
tot = Counter()
for t in IDX["tessere"]:
    W, H = t["colonne"], t["righe"]
    im = disegna(W, H, lambda lo, la: ((lo - t["ovest"]) / IDX["dlon"], (t["nord"] - la) / IDX["dlat"]))
    im.save(f"docs/terreno/f/{t['id']}.png", optimize=True)
    tot.update(im.getdata())
print("tessere:", len(IDX["tessere"]), "pixel per tipo:", {(NOMI[k - 1] if k else "nessuno"): v for k, v in tot.most_common()})

# ---- maglie da 600 m della mappa principale (griglia di BOSCHI_DATI in index.html), 10 x 10 campioni per maglia
B = dict(lat0=43.7, lon0=10.0, righe=126, colonne=130, dlat=0.1 / 18, dlon=0.1 / 13)
N = 10
im = disegna(B["colonne"] * N, B["righe"] * N, lambda lo, la: ((lo - B["lon0"]) / B["dlon"] * N, (la - B["lat0"]) / B["dlat"] * N))
px = im.load()
car = "0123456789abcde"
righe = []
for R in range(B["righe"]):
    s = ""
    for C in range(B["colonne"]):
        c = Counter(px[C * N + i, R * N + j] for i in range(N) for j in range(N))
        bosco = [(n, k) for k, n in c.items() if k]
        # tipo prevalente fra i campioni di bosco, se il bosco ISPRA copre almeno il 20% della maglia
        s += car[max(bosco)[1]] if bosco and sum(n for n, _ in bosco) >= 0.2 * N * N else "0"
    righe.append(s)
json.dump({"fonte": "ISPRA, Carta della Natura - Carta degli Habitat 1:50.000; dove manca, Corine Land Cover 2018 IV livello", "codici": CODICI, "nomi": NOMI, **B, "righe_dati": righe},
          open("docs/dati/tipi_bosco.json", "w"), ensure_ascii=False, separators=(",", ":"))
print("maglie da 600 m con tipo:", sum(ch != "0" for r in righe for ch in r), "su", B["righe"] * B["colonne"])
