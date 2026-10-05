#!/usr/bin/env python3
"""Fattori del terreno a 20 m per tutta la zona della mappa, divisi in tasselli.

Gira su GitHub Actions (scarica quota e boschi, calcola, salva). Uscite:
  docs/terreno/zone.json          indice dei tasselli e parametri della griglia
  docs/terreno/t/R_C_a.png        R ristagno (0-255)  G riparo dalla tramontana (0-255)  B bosco (0 no, 1 latifoglie, 2 misto, 3 conifere)
  docs/terreno/t/R_C_b.png        quota a passi di 5 m: q = R*256+G, quota = 5*q
  docs/terreno/t/R_C_c.png        sole rispetto al terreno piano a metà settembre/ottobre/novembre (64 = come il piano, scala 1/64)
  data/terreno/zona_resoconto.json, data/terreno/zona_anteprima.png   per controllo
I pixel fuori dal bosco valgono 0 in tutti i canali (comprimono meglio e la pagina li salta).
Tasselli: 0,1° di latitudine × 0,14° di longitudine (circa 11 × 11 km), allineati alla griglia meteo della mappa.
"""
import io, json, math, os, sys, time, traceback, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw
from numba import njit

T0 = time.time()
LAT0, LON0 = 43.72, 10.05            # angolo sud-ovest (come la griglia meteo della mappa)
TR, TC = 7, 7                        # tasselli in latitudine e longitudine
TLAT, TLON = 0.10, 0.14
PR, PC = 556, 561                    # pixel per tassello: ~20,0 m in entrambe le direzioni a 44° N
DLAT, DLON = TLAT / PR, TLON / PC
M = 150                              # margine in pixel (3 km) per orizzonte e bacini
NY, NX = TR * PR + 2 * M, TC * PC + 2 * M
NORD = LAT0 + TR * TLAT + M * DLAT
OVEST = LON0 - M * DLON
SUD, EST = NORD - NY * DLAT, OVEST + NX * DLON
RES = 20.0
OUT, TMP, REP = "docs/terreno", "/tmp/terreno", "data/terreno"
PROVA = os.environ.get("TERRENO_PROVA")          # prova locale: un tassello sulle Pizzorne con i dati già scaricati
if PROVA:
    LAT0, LON0, TR, TC = 43.88, 10.50, 1, 1
    NY, NX = TR * PR + 2 * M, TC * PC + 2 * M
    NORD = LAT0 + TR * TLAT + M * DLAT; OVEST = LON0 - M * DLON
    SUD, EST = NORD - NY * DLAT, OVEST + NX * DLON
    OUT, REP = PROVA + "/docs", PROVA + "/rep"
for d in (OUT + "/t", TMP, REP):
    os.makedirs(d, exist_ok=True)
rep = {"inizio": time.strftime("%Y-%m-%d %H:%M"), "griglia": [NY, NX], "passi": []}


def passo(s):
    msg = f"[{time.time() - T0:6.0f}s] {s}"
    print(msg, flush=True); rep["passi"].append(msg)


def get(url, timeout=120, data=None, tent=4):
    for t in range(tent):
        try:
            req = urllib.request.Request(url, data=data, headers={"User-Agent": "mappa-funghi (github.com/alessiobandiera/mappa-funghi)"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:
            if t == tent - 1: raise
            time.sleep(3 + 5 * t)


# ------------------------------------------------------------------ quota (Terrarium, zoom 13 ≈ 14 m a 44° N)
def quota():
    if PROVA:
        d = np.load("data/terreno/dem_terrarium.npz"); big = d["z"].astype(np.float32); z = int(d["zoom"]); n = 2 ** z
        lat = NORD - (np.arange(NY) + 0.5) * DLAT; lon = OVEST + (np.arange(NX) + 0.5) * DLON
        py = ((1 - np.arcsinh(np.tan(np.radians(lat))) / np.pi) / 2 * n - int(d["y0"])) * 256 - 0.5
        px = ((lon + 180) / 360 * n - int(d["x0"])) * 256 - 0.5
        PY, PX = np.meshgrid(py, px, indexing="ij")
        return ndimage.gaussian_filter(ndimage.map_coordinates(big, [PY, PX], order=1, mode="nearest"), 0.8)
    z = 13; n = 2 ** z
    fx = lambda lon: (lon + 180) / 360 * n
    fy = lambda lat: (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n
    xs = range(int(fx(OVEST)), int(fx(EST)) + 1); ys = range(int(fy(NORD)), int(fy(SUD)) + 1)
    big = np.zeros((len(ys) * 256, len(xs) * 256), np.float32)
    def una(xy):
        x, y = xy
        a = np.asarray(Image.open(io.BytesIO(get(f"https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png", 60))).convert("RGB")).astype(np.float32)
        return xy, a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
    with ThreadPoolExecutor(8) as ex:
        for (x, y), a in ex.map(una, [(x, y) for y in ys for x in xs]):
            j, i = y - ys[0], x - xs[0]
            big[j * 256:(j + 1) * 256, i * 256:(i + 1) * 256] = a
    passo(f"quota: {len(xs)}x{len(ys)} tessere Terrarium")
    lat = NORD - (np.arange(NY) + 0.5) * DLAT
    lon = OVEST + (np.arange(NX) + 0.5) * DLON
    py = ((1 - np.arcsinh(np.tan(np.radians(lat))) / np.pi) / 2 * n - ys[0]) * 256 - 0.5
    px = ((lon + 180) / 360 * n - xs[0]) * 256 - 0.5
    zz = np.empty((NY, NX), np.float32)
    for r0 in range(0, NY, 512):                      # a blocchi per non occupare troppa memoria
        PY, PX = np.meshgrid(py[r0:r0 + 512], px, indexing="ij")
        zz[r0:r0 + 512] = ndimage.map_coordinates(big, [PY, PX], order=1, mode="nearest")
    zz = ndimage.gaussian_filter(zz, 0.8)
    zz[zz < -5] = -5                                   # mare
    return zz


# ------------------------------------------------------------------ boschi OSM, a blocchi
def boschi():
    els = {}
    if PROVA:
        for el in json.load(open("data/terreno/boschi.json"))["elements"]:
            els[(el["type"], el["id"])] = el
    srv = ["https://overpass.kumi.systems/api/interpreter", "https://overpass-api.de/api/interpreter",
           "https://maps.mail.ru/osm/tools/overpass/api/interpreter"]
    nb = 0 if PROVA else 4
    for bi in range(nb):
        for bj in range(nb):
            s = SUD + (NORD - SUD) * bi / nb; nn = SUD + (NORD - SUD) * (bi + 1) / nb
            w = OVEST + (EST - OVEST) * bj / nb; e = OVEST + (EST - OVEST) * (bj + 1) / nb
            q = f"""[out:json][timeout:180];
(way["landuse"="forest"]({s},{w},{nn},{e}); way["natural"="wood"]({s},{w},{nn},{e});
 relation["landuse"="forest"]({s},{w},{nn},{e}); relation["natural"="wood"]({s},{w},{nn},{e}););
out geom;"""
            ok = False
            for k in range(6):
                try:
                    d = json.loads(get(srv[k % len(srv)], 240, urllib.parse.urlencode({"data": q}).encode(), tent=1))
                    for el in d.get("elements", []):
                        els[(el["type"], el["id"])] = el
                    ok = True; break
                except Exception as ex:
                    passo(f"  boschi blocco {bi},{bj} tentativo {k}: {ex}"); time.sleep(10 + 10 * k)
            if not ok:
                raise RuntimeError(f"Overpass non risponde per il blocco {bi},{bj}")
            time.sleep(3)
    passo(f"boschi: {len(els)} poligoni OSM")
    img = Image.new("L", (NX, NY), 0); dr = ImageDraw.Draw(img)
    TIPO = {"broadleaved": 1, "mixed": 2, "needleleaved": 3}
    P = lambda la, lo: ((lo - OVEST) / DLON, (NORD - la) / DLAT)

    def anelli(ways):
        segs = [[(p["lat"], p["lon"]) for p in w_] for w_ in ways if len(w_) >= 2]
        rings = []
        while segs:
            cur = segs.pop(0); changed = True
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
    polys = []
    for el in els.values():
        code = TIPO.get(el.get("tags", {}).get("leaf_type"), 1)
        if el["type"] == "way" and el.get("geometry"):
            polys.append((code, [[(p["lat"], p["lon"]) for p in el["geometry"]]], []))
        elif el["type"] == "relation":
            mem = el.get("members", [])
            polys.append((code, anelli([m["geometry"] for m in mem if m.get("role") == "outer" and m.get("geometry")]),
                          anelli([m["geometry"] for m in mem if m.get("role") == "inner" and m.get("geometry")])))
    for code, outs, ins in sorted(polys, key=lambda p: p[0] == 1, reverse=True):
        for r_ in outs: dr.polygon([P(la, lo) for la, lo in r_], fill=code)
        for r_ in ins: dr.polygon([P(la, lo) for la, lo in r_], fill=0)
    return np.asarray(img).astype(np.uint8)


# ------------------------------------------------------------------ idrologia (numba)
@njit(cache=True)
def _push(hk, hi, size, k, i):
    j = size; hk[j] = k; hi[j] = i; size += 1
    while j > 0:
        p = (j - 1) // 2
        if hk[p] <= hk[j]: break
        hk[p], hk[j] = hk[j], hk[p]; hi[p], hi[j] = hi[j], hi[p]; j = p
    return size


@njit(cache=True)
def riempi(z):
    """Priority-flood (Barnes) con un heap su array: nessuna depressione chiusa."""
    h, w = z.shape
    zf = z.copy()
    n = h * w
    hk = np.empty(n, np.float64); hi = np.empty(n, np.int64); size = 0
    done = np.zeros(n, np.bool_)
    for r in range(h):
        for c in range(w):
            if r == 0 or c == 0 or r == h - 1 or c == w - 1:
                i = r * w + c; done[i] = True; size = _push(hk, hi, size, zf[r, c], i)
    eps = 1e-3
    while size > 0:
        v = hk[0]; i = hi[0]
        size -= 1; hk[0] = hk[size]; hi[0] = hi[size]
        j = 0
        while True:
            l = 2 * j + 1; rr = l + 1; m = j
            if l < size and hk[l] < hk[m]: m = l
            if rr < size and hk[rr] < hk[m]: m = rr
            if m == j: break
            hk[m], hk[j] = hk[j], hk[m]; hi[m], hi[j] = hi[j], hi[m]; j = m
        r = i // w; c = i % w
        for dr in range(-1, 2):
            for dc in range(-1, 2):
                if dr == 0 and dc == 0: continue
                r2 = r + dr; c2 = c + dc
                if r2 < 0 or r2 >= h or c2 < 0 or c2 >= w: continue
                i2 = r2 * w + c2
                if done[i2]: continue
                done[i2] = True
                if zf[r2, c2] <= v: zf[r2, c2] = v + eps
                size = _push(hk, hi, size, zf[r2, c2], i2)
    return zf


@njit(cache=True)
def accumula(zf, order, res):
    h, w = zf.shape
    acc = np.ones(h * w, np.float64) * res * res
    dr = np.array([-1, -1, -1, 0, 0, 1, 1, 1]); dc = np.array([-1, 0, 1, -1, 1, -1, 0, 1])
    L = np.array([0.354, 0.5, 0.354, 0.5, 0.5, 0.354, 0.5, 0.354]) * res
    dist = np.array([1.4142, 1, 1.4142, 1, 1, 1.4142, 1, 1.4142]) * res
    wts = np.zeros(8)
    for q in range(order.size):
        idx = order[q]; r = idx // w; c = idx % w
        z0 = zf[r, c]; tot = 0.0
        for k in range(8):
            rr = r + dr[k]; cc = c + dc[k]; wts[k] = 0.0
            if rr < 0 or rr >= h or cc < 0 or cc >= w: continue
            d = z0 - zf[rr, cc]
            if d > 0:
                wts[k] = (d / dist[k]) ** 1.1 * L[k]; tot += wts[k]
        if tot > 0:
            a = acc[idx]
            for k in range(8):
                if wts[k] > 0:
                    acc[(r + dr[k]) * w + c + dc[k]] += a * wts[k] / tot
    return acc


def shift(a, dr, dc, fill):
    out = np.full_like(a, fill)
    h, w = a.shape
    r0, r1 = max(0, -dr), min(h, h - dr); c0, c1 = max(0, -dc), min(w, w - dc)
    if r1 > r0 and c1 > c0:
        out[r0:r1, c0:c1] = a[r0 + dr:r1 + dr, c0 + dc:c1 + dc]
    return out


def main():
    z = quota()
    passo(f"quota {z.min():.0f}-{z.max():.0f} m su {NY}x{NX}")
    bosco = boschi()
    passo(f"bosco: {100 * (bosco > 0).mean():.0f}% della griglia")

    gy, gx = np.gradient(z, RES)
    dzN, dzE = -gy, gx
    del gy, gx
    slope = np.arctan(np.hypot(dzN, dzE)).astype(np.float32)
    nrm = np.sqrt(dzE ** 2 + dzN ** 2 + 1)
    nE, nN, nU = (-dzE / nrm).astype(np.float32), (-dzN / nrm).astype(np.float32), (1 / nrm).astype(np.float32)
    del dzN, dzE, nrm

    # orizzonte su griglia a 60 m, 24 direzioni, fino a 3 km
    f = 3; hc, wc = NY // f, NX // f
    zc = z[:hc * f, :wc * f].reshape(hc, f, wc, f).mean(axis=(1, 3))
    NAZ = 24; CR = RES * f
    hor = np.zeros((NAZ, hc, wc), np.float32)
    for i in range(NAZ):
        az = math.radians(i * 360 / NAZ); s, c = math.sin(az), math.cos(az)
        best = np.zeros((hc, wc), np.float32)
        for k in range(1, int(3000 / CR) + 1):
            dr, dc = int(round(-k * c)), int(round(k * s))
            if dr == 0 and dc == 0: continue
            np.maximum(best, (shift(zc, dr, dc, -1e9) - zc) / (CR * math.hypot(dr, dc)), out=best)
        hor[i] = np.arctan(best)
    up = lambda a: ndimage.zoom(a, (NY / hc, NX / wc), order=1)[:NY, :NX]
    svf = up(np.mean(np.cos(hor) ** 2, axis=0)).astype(np.float32)
    passo("orizzonte")

    def sole(doy):
        phi = math.radians((SUD + NORD) / 2)
        dec = math.radians(23.44 * math.sin(math.radians(360 / 365 * (284 + doy))))
        tot = np.zeros((NY, NX), np.float32); flat = 0.0
        dif0 = (svf * (1 + np.cos(slope)) / 2).astype(np.float32)
        for hh in np.arange(6.25, 18.0, 0.5):
            ha = math.radians(15 * (hh - 12))
            sa = math.sin(phi) * math.sin(dec) + math.cos(phi) * math.cos(dec) * math.cos(ha)
            if sa <= 0.02: continue
            alt = math.asin(sa)
            az = (math.degrees(math.atan2(math.sin(ha), math.cos(ha) * math.sin(phi) - math.tan(dec) * math.cos(phi))) + 180) % 360
            tau = 0.72 ** (1 / sa)
            sE, sN = math.sin(math.radians(az)) * math.cos(alt), math.cos(math.radians(az)) * math.cos(alt)
            p = az / (360 / NAZ); i0 = int(p) % NAZ; i1 = (i0 + 1) % NAZ; t = p - int(p)
            lit = up(np.clip((alt - (hor[i0] * (1 - t) + hor[i1] * t)) / math.radians(1.5) + 0.5, 0, 1))
            tot += 1000 * tau * np.clip(nE * sE + nN * sN + nU * sa, 0, None) * lit + 120 * sa * dif0
            flat += 1000 * tau * sa + 120 * sa
        return tot / flat
    SOLE = [sole(d) for d in (258, 288, 319)]
    del hor
    passo("sole set/ott/nov")

    zf = riempi(z.astype(np.float64))
    order = np.argsort(-zf, axis=None, kind="stable")
    acc = accumula(zf, order, RES).reshape(z.shape)
    del zf, order
    twi = np.log(acc / RES / np.maximum(np.tan(slope), 0.005)).astype(np.float32)
    del acc
    passo(f"TWI {np.percentile(twi, 5):.1f}-{np.percentile(twi, 95):.1f}")

    def tpi(rad):
        return z - ndimage.uniform_filter(z, int(round(rad / RES)) * 2 + 1, mode="nearest")
    t1, t2 = tpi(60), tpi(250)
    forma = 0.5 * t1 / (t1.std() + 1e-6) + 0.5 * t2 / (t2.std() + 1e-6)
    del t1, t2

    sx = np.zeros_like(z)
    AZV = [350, 10, 30, 50]
    for az in AZV:
        s, c = math.sin(math.radians(az)), math.cos(math.radians(az))
        best = np.full(z.shape, -np.inf, np.float32)
        for k in range(1, int(300 / RES) + 1):
            dr, dc = int(round(-k * c)), int(round(k * s))
            if dr == 0 and dc == 0: continue
            np.maximum(best, (shift(z, dr, dc, -1e9) - z) / (RES * math.hypot(dr, dc)), out=best)
        sx += np.degrees(np.arctan(best))
    sx /= len(AZV)
    passo(f"riparo {np.percentile(sx, 5):.1f}-{np.percentile(sx, 95):.1f} gradi")

    # ristagno: graduatoria su tutta la terraferma (stessa scala in tutti i tasselli)
    terra = z > 2
    def rank01(a):
        v = a[terra]; r = np.empty(v.size, np.float32); r[np.argsort(v, kind="stable")] = np.linspace(0, 1, v.size, dtype=np.float32)
        out = np.zeros(a.shape, np.float32); out[terra] = r; return out
    acqua = 0.65 * rank01(twi) + 0.35 * rank01(-forma)
    acqua = (acqua - acqua[terra].min()) / (acqua[terra].max() - acqua[terra].min())
    riparo = np.clip((sx + 10) / 30, 0, 1)
    del twi, forma, sx
    q8 = lambda a, step: (np.clip(np.round(a * 255), 0, 255).astype(np.uint8) // step) * step
    A_R, A_G = q8(acqua, 8), q8(riparo, 8)
    qz = np.clip(np.round(z / 5), 0, 65535).astype(np.uint16)
    C = [np.clip(np.round(s * 64), 0, 255).astype(np.uint8) // 2 * 2 for s in SOLE]
    del acqua, riparo, SOLE

    indice = []
    for tr in range(TR):
        for tc in range(TC):
            r1 = M + (TR - 1 - tr) * PR; c1 = M + tc * PC            # tr = 0 è la fila più a sud
            sl = (slice(r1, r1 + PR), slice(c1, c1 + PC))
            bm = bosco[sl]
            if (bm > 0).sum() < 200:
                continue
            msk = bm > 0
            def m(a): o = a[sl].copy(); o[~msk] = 0; return o
            nome = f"{tr}_{tc}"
            Image.fromarray(np.dstack([m(A_R), m(A_G), bm]), "RGB").save(f"{OUT}/t/{nome}_a.png", optimize=True)
            Image.fromarray(np.dstack([m((qz >> 8).astype(np.uint8)), m((qz & 255).astype(np.uint8)), np.zeros_like(bm)]), "RGB").save(f"{OUT}/t/{nome}_b.png", optimize=True)
            Image.fromarray(np.dstack([m(C[0]), m(C[1]), m(C[2])]), "RGB").save(f"{OUT}/t/{nome}_c.png", optimize=True)
            indice.append({"id": nome, "sud": round(LAT0 + tr * TLAT, 4), "ovest": round(LON0 + tc * TLON, 4),
                           "bosco": round(float(msk.mean()), 3)})
    tot_kb = sum(os.path.getsize(f"{OUT}/t/{x}") for x in os.listdir(f"{OUT}/t")) // 1024
    json.dump({"lat0": LAT0, "lon0": LON0, "tlat": TLAT, "tlon": TLON, "righe": PR, "colonne": PC, "res_m": RES,
               "tasselli": indice, "aggiornato": time.strftime("%Y-%m-%d"),
               "fonte_quota": "Terrarium/Mapzen (EU-DEM e SRTM, circa 30 m) ricampionata a 20 m",
               "fonte_boschi": "OpenStreetMap (ODbL)",
               "codifica": "a: R ristagno, G riparo (0-255, passi di 8), B bosco 0/1/2/3 | b: quota = 5*(R*256+G) m | c: sole/piano*64 set-ott-nov"},
              open(f"{OUT}/zone.json", "w"), indent=1)
    passo(f"tasselli: {len(indice)}, {tot_kb} KB")

    # anteprima a 1/8 per il controllo
    k = 8
    prev = np.dstack([A_R[::k, ::k], A_G[::k, ::k], (bosco[::k, ::k] > 0).astype(np.uint8) * 160])
    Image.fromarray(prev, "RGB").save(f"{REP}/zona_anteprima.png", optimize=True)


try:
    main(); rep["esito"] = "ok"
except Exception:
    rep["esito"] = "errore"; rep["traccia"] = traceback.format_exc(); print(rep["traccia"], flush=True)
rep["secondi"] = round(time.time() - T0)
json.dump(rep, open(f"{REP}/zona_resoconto.json", "w"), indent=1)
sys.exit(0 if rep["esito"] == "ok" else 1)
