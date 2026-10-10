#!/usr/bin/env python3
"""Boschi misti: per ogni pixel a 20 m e per ogni maglia da 600 m la miscela di alberi (fino a 3 gruppi con la loro quota), da tre fonti:
- Carta degli Habitat ISPRA 1:50.000 (data/boschi/habitat_boschi.geojson.gz): il tipo di bosco a grana fine
- Corine Land Cover 2018 IV livello (data/boschi/clc18_boschi.geojson)
- carte europee per specie a 30 m da satellite (Bonannella et al. 2022, data/boschi/specie30m/*.tif): probabilità di presenza 2018-2020,
  usate per ripartire le specie che il satellite riconosce (castagno, querce, leccio, faggio, abeti, pini montani) dentro il bosco.

Regola (pesi tarati sull'Inventario Forestale Toscano, script/boschi_misti.py --prova):
  base = (W_H·Habitat + W_C·Corine) / (pesi presenti); i tipi «misti» delle carte si dividono fra più gruppi (MISTI);
  la quota della base che cade sulle specie viste dal satellite viene ripartita per (1-ALFA)·base + ALFA·satellite;
  robinia, carpino nero e altre latifoglie, pino marittimo, boschi ripari, conifere esotiche restano quelli delle carte (il satellite non li vede).
  Quote sotto il 10% scartate, al massimo 3 gruppi.
Uscite: docs/terreno/m/<tessera>.png (RGB: R = gruppo1·16+gruppo2, G = gruppo3·16+quota1, B = quota2·16+quota3, quote in 15esimi)
        docs/dati/boschi_misti.json (maglie da 600 m: 6 caratteri esadecimali per maglia, gruppo e quota ×3; «000000» = niente)
Uso: python script/boschi_misti.py            (serve Pillow, numpy, rasterio, pyproj)
     python script/boschi_misti.py --prova    (solo il confronto con l'Inventario Forestale Toscano, data/boschi/ift_punti.json)
"""
import gzip, json, os, sys
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
GRUPPI = ["leccio", "querce", "latifoglie", "castagno", "faggio", "igrofile", "robinia", "pini", "pinimontani", "abeti", "larice", "esotiche"]
NG = len(GRUPPI)                     # codici 1-12 come i tipi 1-12 della mappa; 13 e 14 (misti delle carte) si dividono:
MISTI = {13: {"querce": .4, "latifoglie": .35, "castagno": .25}, 14: {"pinimontani": .4, "abeti": .35, "pini": .25}}
VISTI = ["castagno", "querce", "leccio", "faggio", "abeti", "pinimontani"]      # gruppi riconosciuti dal satellite
SATELLITE = {"castagno": ["castanea.sativa"], "querce": ["quercus.cerris", "quercus.robur"], "leccio": ["quercus.ilex", "quercus.suber"],
             "faggio": ["fagus.sylvatica"], "abeti": ["abies.alba", "picea.abies"], "pinimontani": ["pinus.nigra", "pinus.sylvestris"]}
PAR = dict(W_H=1.0, W_C=0.6, ALFA=0.3, GAMMA=1.0, TAU=20, SOGLIA=0.10)

# matrice tipo → vettore dei gruppi (tipi 1-14)
VT = np.zeros((15, NG), np.float32)
for t in range(1, 13):
    VT[t, t - 1] = 1
for t, d in MISTI.items():
    for g, q in d.items():
        VT[t, GRUPPI.index(g)] = q


def poligoni():
    """(clc, habitat): liste di (area, tipo 1-14, anello esterno, buchi), dal più grande al più piccolo"""
    import boschi_tipi as BT          # riusa lettura e corrispondenze di script/boschi_tipi.py (non ridisegna nulla all'import)
    return BT.POLIGONI_CLC, BT.POLIGONI_HAB


def disegna(lista, W, H, a_pixel, buchi=True):
    im = Image.new("L", (W, H), 0); d = ImageDraw.Draw(im)
    for _, cod, est, bb in lista:
        pts = [a_pixel(lo, la) for lo, la in est]
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        if max(xs) < 0 or min(xs) > W or max(ys) < 0 or min(ys) > H: continue
        d.polygon(pts, fill=cod)
        if buchi:
            for b in bb: d.polygon([a_pixel(lo, la) for lo, la in b], fill=0)
    return np.asarray(im)


class Satellite:
    def __init__(self, cartella="data/boschi/specie30m"):
        import rasterio
        from pyproj import Transformer
        self.r = {}
        for g, specie in SATELLITE.items():
            for sp in specie:
                p = f"{cartella}/{sp}.tif"
                if os.path.exists(p):
                    ds = rasterio.open(p); self.r[sp] = (ds.read(1), ds.transform)
        self.tr = Transformer.from_crs("EPSG:4326", "EPSG:3035", always_xy=True)

    def gruppi(self, lat, lon):
        """probabilità (0-100) per gruppo visto dal satellite, array (n, len(VISTI))"""
        x, y = self.tr.transform(lon, lat)
        out = np.zeros((len(lat), len(VISTI)), np.float32)
        for j, g in enumerate(VISTI):
            for sp in SATELLITE[g]:
                if sp not in self.r: continue
                a, T = self.r[sp]
                c = ((x - T.c) / T.a).astype(int); r = ((y - T.f) / T.e).astype(int)
                ok = (r >= 0) & (r < a.shape[0]) & (c >= 0) & (c < a.shape[1])
                v = np.zeros(len(lat), np.float32); v[ok] = a[r[ok], c[ok]]
                out[:, j] = np.maximum(out[:, j], v)
        return out


def miscela(th, tc, sat, par=PAR):
    """th, tc: tipi (n,) 0-14 da Habitat e Corine; sat: (n, len(VISTI)) probabilità. → (n, NG) quote"""
    h, c = VT[th], VT[tc]
    wh = par["W_H"] * (th > 0); wc = par["W_C"] * (tc > 0)
    den = wh + wc
    base = (h * wh[:, None] + c * wc[:, None]) / np.where(den > 0, den, 1)[:, None]
    iv = [GRUPPI.index(g) for g in VISTI]
    s = np.where(sat >= par["TAU"], sat / 100.0, 0) ** par["GAMMA"]
    ss = s.sum(1)
    sn = s / np.where(ss > 0, ss, 1)[:, None]
    mv = base[:, iv].sum(1)
    a = par["ALFA"] * (ss > 0)
    base[:, iv] = (1 - a)[:, None] * base[:, iv] + (a * mv)[:, None] * sn
    # bosco che nessuna carta classifica: solo il satellite (se vede qualcosa)
    vuoto = den == 0
    if vuoto.any():
        base[np.ix_(vuoto, iv)] = sn[vuoto]
    base[base < par["SOGLIA"]] = 0
    tot = base.sum(1)
    return base / np.where(tot > 0, tot, 1)[:, None]


def prime3(m):
    """(n, NG) → codici (n,3) 1-12 (0 = niente) e quote in 15esimi (n,3)"""
    idx = np.argsort(-m, axis=1)[:, :3]
    q = np.take_along_axis(m, idx, 1)
    cod = np.where(q > 0, idx + 1, 0)
    q15 = np.round(q * 15).astype(int)
    return cod, q15


def ospiti(m):
    """quota → ospiti delle 4 specie (tabella OSPITI di docs/porcini.js)"""
    import re
    src = open("docs/porcini.js", encoding="utf-8").read()
    O = {g: [float(x) for x in re.search(rf"{g}:\s*\{{aereus:([\d.]+),\s*reticulatus:([\d.]+),\s*edulis:([\d.]+),\s*pinophilus:([\d.]+)\}}", src).groups()] for g in GRUPPI}
    M = np.array([O[g] for g in GRUPPI], np.float32)
    return m @ M


# ------------------------------------------------------------------ confronto con l'Inventario Forestale Toscano
IFT_SPECIE = {"251": "castagno", "281": "faggio", "79": "pini", "80": "pini", "76": "pinimontani", "221": "pinimontani", "361": "robinia",
              "311": "latifoglie", "342": "querce", "348": "querce", "340": "querce", "347": "querce", "216": "latifoglie", "344": "leccio",
              "11": "abeti", "10": "abeti", "91": "esotiche", "61": "esotiche", "51": "esotiche", "499": "latifoglie", "292": "latifoglie",
              "291": "latifoglie", "370": "igrofile", "320": "igrofile", "222": "igrofile", "220": "latifoglie"}


def prova():
    P = json.load(open("data/boschi/ift_punti.json"))
    clc, hab = poligoni()
    T = json.load(open("docs/dati/tipi_bosco.json")); N = 10
    W, H = T["colonne"] * N, T["righe"] * N
    ap = lambda lo, la: ((lo - T["lon0"]) / T["dlon"] * N, (la - T["lat0"]) / T["dlat"] * N)
    RH, RC = disegna(hab, W, H, ap, buchi=False), disegna(clc, W, H, ap)
    sat = Satellite()
    righe = []
    for la, lo, v in P:
        comp = {}
        for k in "123":
            g = IFT_SPECIE.get(v.get("COMPSPE" + k, "0")); q = float(v.get("COPERTU" + k) or 0)
            if g and q > 0: comp[g] = comp.get(g, 0) + q
        if not comp or not v.get("CATFOR"): continue
        R = int((la - T["lat0"]) / T["dlat"]); C = int((lo - T["lon0"]) / T["dlon"])
        ys, xs = np.mgrid[R * N:(R + 1) * N, C * N:(C + 1) * N]
        lat = T["lat0"] + (ys.ravel() + .5) / N * T["dlat"]; lon = T["lon0"] + (xs.ravel() + .5) / N * T["dlon"]
        righe.append((comp, RH[ys, xs].ravel(), RC[ys, xs].ravel(), sat.gruppi(lat, lon)))
    print(len(righe), "punti dell'Inventario con composizione")
    vera = np.array([[r[0].get(g, 0) for g in GRUPPI] for r in righe], np.float32); vera /= vera.sum(1, keepdims=True)
    Ov = ospiti(vera)

    def valuta(nome, par):
        m = np.array([miscela(r[1], r[2], r[3], par).mean(0) for r in righe])
        e = np.abs(ospiti(m) - Ov).mean()
        dom = (m.argmax(1) == vera.argmax(1)).mean()
        cast = vera[:, 3] > .5
        print(f"  {nome:52s} scarto negli alberi delle 4 specie {e:.3f}   gruppo principale uguale {100*dom:.0f}%   "
              f"castagno stimato nei castagneti {m[cast,3].mean():.2f}")
        return e
    solo = lambda **k: {**PAR, **k}
    valuta("solo Carta degli Habitat", solo(W_C=0, ALFA=0, SOGLIA=0))
    valuta("solo Corine", solo(W_H=0, W_C=1, ALFA=0, SOGLIA=0))
    valuta("Habitat + Corine (0,3)", solo(ALFA=0))
    valuta("solo satellite (dove vede)", solo(ALFA=1))
    best = None
    for wc in (0, .3, .6):
        for alfa in (.3, .5, .7):
            for gamma in (1, 2):
                for tau in (20, 40):
                    par = solo(W_C=wc, ALFA=alfa, GAMMA=gamma, TAU=tau)
                    m = np.array([miscela(r[1], r[2], r[3], par).mean(0) for r in righe])
                    e = np.abs(ospiti(m) - Ov).mean()
                    if best is None or e < best[0]: best = (e, par)
    print("migliore:", {k: best[1][k] for k in ("W_C", "ALFA", "GAMMA", "TAU")}, f"{best[0]:.3f}")
    valuta("parametri scelti (PAR)", PAR)


# ------------------------------------------------------------------ uscite per la mappa
def produci():
    clc, hab = poligoni()
    sat = Satellite()
    IDX = json.load(open("docs/terreno/tessere.json"))
    os.makedirs("docs/terreno/m", exist_ok=True)
    conta = np.zeros(NG)
    for t in IDX["tessere"]:
        W, H = t["colonne"], t["righe"]
        ap = lambda lo, la: ((lo - t["ovest"]) / IDX["dlon"], (t["nord"] - la) / IDX["dlat"])
        rh, rc = disegna(hab, W, H, ap, buchi=False), disegna(clc, W, H, ap)
        ys, xs = np.mgrid[0:H, 0:W]
        lat = t["nord"] - (ys.ravel() + .5) * IDX["dlat"]; lon = t["ovest"] + (xs.ravel() + .5) * IDX["dlon"]
        m = miscela(rh.ravel(), rc.ravel(), sat.gruppi(lat, lon))
        conta += m.sum(0)
        cod, q = prime3(m)
        rgb = np.stack([cod[:, 0] * 16 + cod[:, 1], cod[:, 2] * 16 + q[:, 0], q[:, 1] * 16 + q[:, 2]], 1).astype(np.uint8).reshape(H, W, 3)
        Image.fromarray(rgb, "RGB").save(f"docs/terreno/m/{t['id']}.png", optimize=True)
        print("tessera", t["id"], flush=True)
    print("quote complessive:", {g: round(100 * x / conta.sum(), 1) for g, x in zip(GRUPPI, conta)})
    # maglie da 600 m (stessa griglia di tipi_bosco.json)
    T = json.load(open("docs/dati/tipi_bosco.json")); N = 10
    W, H = T["colonne"] * N, T["righe"] * N
    ap = lambda lo, la: ((lo - T["lon0"]) / T["dlon"] * N, (la - T["lat0"]) / T["dlat"] * N)
    rh, rc = disegna(hab, W, H, ap, buchi=False), disegna(clc, W, H, ap)
    ys, xs = np.mgrid[0:H, 0:W]
    lat = T["lat0"] + (ys.ravel() + .5) / N * T["dlat"]; lon = T["lon0"] + (xs.ravel() + .5) / N * T["dlon"]
    m = miscela(rh.ravel(), rc.ravel(), sat.gruppi(lat, lon)).reshape(H, W, NG)
    mm = m.reshape(T["righe"], N, T["colonne"], N, NG).mean((1, 3)).reshape(-1, NG)
    mm[mm < PAR["SOGLIA"]] = 0
    tot = mm.sum(1); mm = mm / np.where(tot > 0, tot, 1)[:, None]
    cod, q = prime3(mm)
    hexa = "0123456789abcdef"
    righe = []
    for R in range(T["righe"]):
        s = ""
        for C in range(T["colonne"]):
            i = R * T["colonne"] + C
            s += "".join(hexa[cod[i, k]] + hexa[min(15, q[i, k])] for k in range(3))
        righe.append(s)
    json.dump({"fonte": "Carta degli Habitat ISPRA, Corine Land Cover 2018, carte europee per specie a 30 m (Bonannella et al. 2022, CC BY 4.0)",
               "gruppi": GRUPPI, "parametri": PAR, **{k: T[k] for k in ("lat0", "lon0", "righe", "colonne", "dlat", "dlon")}, "righe_dati": righe},
              open("docs/dati/boschi_misti.json", "w"), ensure_ascii=False, separators=(",", ":"))
    print("maglie con miscela:", int((tot > 0).sum()))


if __name__ == "__main__":
    prova() if "--prova" in sys.argv else produci()
