#!/usr/bin/env python3
"""Calcola i fattori del terreno per la zona di prova a partire dai dati grezzi in data/terreno/.

Uscite in docs/terreno/ (immagini PNG senza perdita, lette pixel per pixel dalla pagina):
  <zona>_a.png  R = ristagno d'acqua (0-255)   G = forma (0 conca, 128 piano, 255 dosso)   B = riparo dalla tramontana
  <zona>_b.png  R,G = quota in decimetri/… (quota = R*256+G, in metri*2)   B = bosco (0 no, 1 latifoglie, 2 misto, 3 conifere)
  <zona>_c.png  R,G,B = sole relativo al terreno piano a metà settembre, ottobre, novembre (128 = come il piano)
  <zona>.json   limiti geografici, risoluzione, fonti
Tutto con numpy/scipy, senza librerie GIS.
"""
import heapq, json, math, os, sys
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw

ZONA = "pizzorne"
SRC = "data/terreno"
OUT = "docs/terreno"
os.makedirs(OUT, exist_ok=True)

try:
    from numba import njit
except Exception:
    def njit(*a, **k):
        return (lambda f: f) if not (a and callable(a[0])) else a[0]

# ---------------- altimetria sulla griglia di uscita ----------------
info_path = f"{SRC}/dem_info.json"
if os.path.exists(info_path):
    info = json.load(open(info_path))
    S, N, W, E = info["zona"]
    RES = 10.0
else:
    S, N, W, E = 43.88, 43.99, 10.50, 10.67
    info = {"fonte": "Terrarium (AWS, dati EU-DEM/SRTM)"}
    RES = 20.0
LAT0 = (S + N) / 2
DLAT = RES / 111320.0
DLON = RES / (111320.0 * math.cos(math.radians(LAT0)))
ny = int(round((N - S) / DLAT)); nx = int(round((E - W) / DLON))
lat = N - (np.arange(ny) + 0.5) * DLAT
lon = W + (np.arange(nx) + 0.5) * DLON
LON, LAT = np.meshgrid(lon, lat)

def fill_nan(a):
    m = ~np.isfinite(a)
    if m.any():
        idx = ndimage.distance_transform_edt(m, return_distances=False, return_indices=True)
        a = a[tuple(idx)]
    return a

if os.path.exists(info_path):
    if os.path.exists(f"{SRC}/dem.tif"):
        import tifffile
        dem = tifffile.imread(f"{SRC}/dem.tif").astype(np.float64)
        if dem.ndim == 3: dem = dem[..., 0] if dem.shape[-1] < 5 else dem[0]
    else:
        txt = open(f"{SRC}/dem.asc").read().split("\n")
        hdr = {}; k = 0
        while txt[k].split()[0].lower() in ("ncols", "nrows", "xllcorner", "yllcorner", "xllcenter", "yllcenter", "cellsize", "nodata_value", "dx", "dy"):
            p = txt[k].split(); hdr[p[0].lower()] = float(p[1]); k += 1
        dem = np.loadtxt(txt[k:]).astype(np.float64)
    dem[(dem < -500) | (dem > 5000)] = np.nan
    dem = fill_nan(dem)
    x0, y0, x1, y1 = map(float, info["bbox"].split(","))
    h, w = dem.shape
    if info["crs"] == "EPSG:4326":
        X, Y = LON, LAT
    else:
        from pyproj import Transformer
        t = Transformer.from_crs("EPSG:4326", info["crs"], always_xy=True)
        X, Y = t.transform(LON, LAT)
    col = (X - x0) / (x1 - x0) * w - 0.5
    row = (y1 - Y) / (y1 - y0) * h - 0.5
    z = ndimage.map_coordinates(dem, [row, col], order=1, mode="nearest")
else:
    d = np.load(f"{SRC}/dem_terrarium.npz")
    big = d["z"].astype(np.float64); zoom = int(d["zoom"]); tx0 = int(d["x0"]); ty0 = int(d["y0"])
    n = 2 ** zoom
    px = ((LON + 180) / 360 * n - tx0) * 256 - 0.5
    py = ((1 - np.arcsinh(np.tan(np.radians(LAT))) / np.pi) / 2 * n - ty0) * 256 - 0.5
    z = ndimage.map_coordinates(big, [py, px], order=1, mode="nearest")
    z = ndimage.gaussian_filter(z, 0.7)
print(f"griglia {ny}x{nx} a {RES:.0f} m, quota {z.min():.0f}-{z.max():.0f} m", flush=True)

# ---------------- pendenza ed esposizione ----------------
gy, gx = np.gradient(z, RES)          # gy: verso sud (righe crescenti), gx: verso est
dzN, dzE = -gy, gx
slope = np.arctan(np.hypot(dzN, dzE))
nrm = np.sqrt(dzE**2 + dzN**2 + 1)
nE, nN, nU = -dzE / nrm, -dzN / nrm, 1 / nrm

# ---------------- orizzonte (per ombre e cielo visibile), su griglia a ~30 m ----------------
f = max(1, int(round(30 / RES)))
zc = z[: (ny // f) * f, : (nx // f) * f].reshape(ny // f, f, nx // f, f).mean(axis=(1, 3))
CR = RES * f
NAZ = 24
AZS = np.arange(NAZ) * 360 / NAZ
def shift(a, dr, dc, fill):
    out = np.full_like(a, fill)
    h, w = a.shape
    r0, r1 = max(0, -dr), min(h, h - dr); c0, c1 = max(0, -dc), min(w, w - dc)
    if r1 > r0 and c1 > c0:
        out[r0:r1, c0:c1] = a[r0 + dr:r1 + dr, c0 + dc:c1 + dc]
    return out
hor = np.zeros((NAZ,) + zc.shape)
for i, az in enumerate(AZS):
    s, c = math.sin(math.radians(az)), math.cos(math.radians(az))
    best = np.full(zc.shape, -np.inf)
    for k in range(1, int(3000 / CR) + 1):
        dr, dc = int(round(-k * c)), int(round(k * s))
        if dr == 0 and dc == 0: continue
        dist = CR * math.hypot(dr, dc)
        zs = shift(zc, dr, dc, -1e9)
        np.maximum(best, (zs - zc) / dist, out=best)
    hor[i] = np.arctan(np.maximum(best, 0))
hor_full = np.stack([ndimage.zoom(h_, (ny / zc.shape[0], nx / zc.shape[1]), order=1)[:ny, :nx] for h_ in hor])
svf = np.mean(np.cos(hor_full) ** 2, axis=0)          # quota di cielo visibile (approssimata)
print("orizzonte calcolato", flush=True)

# ---------------- radiazione solare di metà settembre, ottobre, novembre ----------------
def sole(doy):
    phi = math.radians(LAT0)
    dec = math.radians(23.44 * math.sin(math.radians(360 / 365 * (284 + doy))))
    tot = np.zeros_like(z); flat = 0.0
    for hh in np.arange(6.0, 18.01, 0.25):
        ha = math.radians(15 * (hh - 12))
        sa = math.sin(phi) * math.sin(dec) + math.cos(phi) * math.cos(dec) * math.cos(ha)
        if sa <= 0.02: continue
        alt = math.asin(sa)
        az = (math.degrees(math.atan2(math.sin(ha), math.cos(ha) * math.sin(phi) - math.tan(dec) * math.cos(phi))) + 180) % 360
        tau = 0.72 ** (1 / sa)
        sE, sN, sU = math.sin(math.radians(az)) * math.cos(alt), math.cos(math.radians(az)) * math.cos(alt), sa
        cosi = np.clip(nE * sE + nN * sN + nU * sU, 0, None)
        # orizzonte nella direzione del sole (interpolato tra le direzioni calcolate)
        p = az / (360 / NAZ); i0 = int(p) % NAZ; i1 = (i0 + 1) % NAZ; t = p - int(p)
        hz = hor_full[i0] * (1 - t) + hor_full[i1] * t
        lit = np.clip((alt - hz) / math.radians(1.5) + 0.5, 0, 1)
        dirr = 1000 * tau * cosi * lit
        dif = 1000 * 0.12 * sa * svf * (1 + np.cos(slope)) / 2
        tot += dirr + dif
        flat += 1000 * tau * sa + 1000 * 0.12 * sa
    return tot / flat
SOLE = {k: sole(d) for k, d in (("set", 258), ("ott", 288), ("nov", 319))}
for k, v in SOLE.items():
    print(f"sole {k}: rapporto col piano {np.percentile(v,5):.2f}-{np.percentile(v,95):.2f}", flush=True)

# ---------------- idrologia: riempimento depressioni e flusso multiplo (TWI) ----------------
NB = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

@njit(cache=True)
def accumula(zf, order, res):
    h, w = zf.shape
    acc = np.ones(h * w) * res * res
    dr = np.array([-1, -1, -1, 0, 0, 1, 1, 1]); dc = np.array([-1, 0, 1, -1, 1, -1, 0, 1])
    L = np.array([0.354, 0.5, 0.354, 0.5, 0.5, 0.354, 0.5, 0.354]) * res   # larghezza di contorno (Quinn)
    dist = np.array([1.4142, 1, 1.4142, 1, 1, 1.4142, 1, 1.4142]) * res
    wts = np.zeros(8)
    for q in range(order.size):
        idx = order[q]; r = idx // w; c = idx % w
        z0 = zf[r, c]; tot = 0.0
        for k in range(8):
            rr = r + dr[k]; cc = c + dc[k]; wts[k] = 0.0
            if rr < 0 or rr >= h or cc < 0 or cc >= w: continue
            dz = z0 - zf[rr, cc]
            if dz > 0:
                wts[k] = (dz / dist[k]) ** 1.1 * L[k]; tot += wts[k]
        if tot > 0:
            a = acc[idx]
            for k in range(8):
                if wts[k] > 0:
                    acc[(r + dr[k]) * w + c + dc[k]] += a * wts[k] / tot
    return acc

def riempi(zz):
    """Priority-flood con piccola pendenza: nessuna depressione chiusa."""
    h, w = zz.shape
    zf = zz.copy(); done = np.zeros((h, w), bool); pq = []
    for r in range(h):
        for c in (0, w - 1):
            heapq.heappush(pq, (zf[r, c], r, c)); done[r, c] = True
    for c in range(1, w - 1):
        for r in (0, h - 1):
            heapq.heappush(pq, (zf[r, c], r, c)); done[r, c] = True
    eps = 1e-3
    while pq:
        v, r, c = heapq.heappop(pq)
        for dr, dc in NB:
            rr, cc = r + dr, c + dc
            if 0 <= rr < h and 0 <= cc < w and not done[rr, cc]:
                done[rr, cc] = True
                if zf[rr, cc] <= v: zf[rr, cc] = v + eps
                heapq.heappush(pq, (zf[rr, cc], rr, cc))
    return zf
zf = riempi(z)
order = np.argsort(-zf, axis=None, kind="stable")
acc = accumula(zf, order, RES).reshape(z.shape)
sca = acc / RES
twi = np.log(sca / np.maximum(np.tan(slope), 0.005))
print(f"TWI {np.percentile(twi,5):.1f}-{np.percentile(twi,95):.1f}", flush=True)

# ---------------- forma del versante (conca/dosso) ----------------
def tpi(rad):
    k = int(round(rad / RES)) * 2 + 1
    return z - ndimage.uniform_filter(z, k, mode="nearest")
t1, t2 = tpi(60), tpi(250)
forma = 0.5 * t1 / (t1.std() + 1e-6) + 0.5 * t2 / (t2.std() + 1e-6)

# ---------------- riparo dalla tramontana (indice di Winstral, venti da N-NE) ----------------
sx = np.zeros_like(z)
AZV = [350, 10, 30, 50]
for az in AZV:
    s, c = math.sin(math.radians(az)), math.cos(math.radians(az))
    best = np.full(z.shape, -np.inf)
    for k in range(1, int(300 / RES) + 1):
        dr, dc = int(round(-k * c)), int(round(k * s))
        if dr == 0 and dc == 0: continue
        dist = RES * math.hypot(dr, dc)
        zs = shift(z, dr, dc, -1e9)
        np.maximum(best, (zs - z) / dist, out=best)
    sx += np.degrees(np.arctan(best))
sx /= len(AZV)
print(f"riparo Sx {np.percentile(sx,5):.1f}-{np.percentile(sx,95):.1f} gradi", flush=True)

# ---------------- boschi OSM rasterizzati ----------------
bosco = np.zeros(z.shape, np.uint8)
def px(pt): return ((pt["lon"] - W) / DLON, (N - pt["lat"]) / DLAT)
def anelli(ways):
    """Unisce i tratti di un multipoligono in anelli chiusi."""
    segs = [[(p["lat"], p["lon"]) for p in w_] for w_ in ways if len(w_) >= 2]
    rings = []
    while segs:
        cur = segs.pop(0)
        changed = True
        while cur[0] != cur[-1] and changed:
            changed = False
            for i, s_ in enumerate(segs):
                if s_[0] == cur[-1]: cur = cur + s_[1:]
                elif s_[-1] == cur[-1]: cur = cur + s_[::-1][1:]
                elif s_[-1] == cur[0]: cur = s_ + cur[1:]
                elif s_[0] == cur[0]: cur = s_[::-1] + cur[1:]
                else: continue
                segs.pop(i); changed = True; break
        if len(cur) >= 3: rings.append(cur)
    return rings
TIPO = {"broadleaved": 1, "mixed": 2, "needleleaved": 3}
if os.path.exists(f"{SRC}/boschi.json"):
    els = json.load(open(f"{SRC}/boschi.json")).get("elements", [])
    img = Image.new("L", (nx, ny), 0); dr_ = ImageDraw.Draw(img)
    polys = []
    for e in els:
        code = TIPO.get(e.get("tags", {}).get("leaf_type"), 1)
        if e["type"] == "way" and e.get("geometry"):
            polys.append((code, [[(p["lat"], p["lon"]) for p in e["geometry"]]], []))
        elif e["type"] == "relation":
            outer = [m.get("geometry", []) for m in e.get("members", []) if m.get("role") == "outer" and m.get("geometry")]
            inner = [m.get("geometry", []) for m in e.get("members", []) if m.get("role") == "inner" and m.get("geometry")]
            polys.append((code, anelli(outer), anelli(inner)))
    for code, outs, ins in sorted(polys, key=lambda p: p[0] == 1, reverse=True):   # le latifoglie generiche sotto
        for r_ in outs:
            dr_.polygon([((lo - W) / DLON, (N - la) / DLAT) for la, lo in r_], fill=code)
        for r_ in ins:
            dr_.polygon([((lo - W) / DLON, (N - la) / DLAT) for la, lo in r_], fill=0)
    bosco = np.asarray(img).astype(np.uint8)
print(f"bosco: {100*(bosco>0).mean():.0f}% della zona", flush=True)

# ---------------- normalizzazione e scrittura ----------------
def rank01(a):
    r = np.empty(a.size); r[np.argsort(a, axis=None, kind="stable")] = np.linspace(0, 1, a.size)
    return r.reshape(a.shape)
acqua = 0.65 * rank01(twi) + 0.35 * rank01(-forma)
acqua = (acqua - acqua.min()) / (acqua.max() - acqua.min())
forma01 = np.clip(0.5 + forma / 4, 0, 1)
riparo = np.clip((sx + 10) / 30, 0, 1)                # -10° molto esposto ... +20° ben riparato
b8 = lambda a: np.clip(np.round(a * 255), 0, 255).astype(np.uint8)
sole8 = lambda a: np.clip(np.round(a * 128), 0, 255).astype(np.uint8)   # 128 = come il terreno piano
q2 = np.clip(np.round(z * 2), 0, 65535).astype(np.uint16)

Image.fromarray(np.dstack([b8(acqua), b8(forma01), b8(riparo)]), "RGB").save(f"{OUT}/{ZONA}_a.png", optimize=True)
Image.fromarray(np.dstack([(q2 >> 8).astype(np.uint8), (q2 & 255).astype(np.uint8), bosco]), "RGB").save(f"{OUT}/{ZONA}_b.png", optimize=True)
Image.fromarray(np.dstack([sole8(SOLE["set"]), sole8(SOLE["ott"]), sole8(SOLE["nov"])]), "RGB").save(f"{OUT}/{ZONA}_c.png", optimize=True)
json.dump({
    "zona": ZONA, "sud": S, "nord": N, "ovest": W, "est": E, "res_m": RES, "righe": ny, "colonne": nx,
    "dlat": DLAT, "dlon": DLON,
    "fonte_quota": info.get("fonte"), "fonte_boschi": "OpenStreetMap (ODbL)",
    "quota": [float(z.min()), float(z.max())],
    "note": "a: R ristagno, G forma (128 piano), B riparo tramontana | b: quota=(R*256+G)/2 m, B bosco 0/1/2/3 | c: sole/piano*128 set-ott-nov",
}, open(f"{OUT}/{ZONA}.json", "w"), indent=1)
for k in ("a", "b", "c"):
    print(k, os.path.getsize(f"{OUT}/{ZONA}_{k}.png") // 1024, "KB")
