#!/usr/bin/env python3
"""Fattori del terreno a 20 m su tutta l'area della mappa, divisi in tessere.

Gira su GitHub Actions (serve la rete: altimetria Terrarium/AWS e boschi OpenStreetMap).
Per ogni tessera (circa 11 x 10 km) calcola, con 3 km di margine per ombre, vento e scorrimento dell'acqua:
  ristagno (indice topografico di umidità + forma del versante), forma (conca/dosso), riparo dalla tramontana,
  sole relativo al terreno piano a metà settembre, ottobre e novembre (con le ombre dei rilievi), quota, bosco.
Uscite in docs/terreno/t/:  <id>_a.png  <id>_b.png  <id>_c.png  (stessa codifica della prova Pizzorne)
e docs/terreno/tessere.json con i limiti di ogni tessera.
Le tessere senza bosco non si scrivono.
"""
import heapq, io, json, math, os, sys, time, urllib.parse, urllib.request
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw

try:
    from numba import njit
except Exception:                                   # senza numba funziona lo stesso, più lentamente
    def njit(*a, **k):
        return (lambda f: f) if not (a and callable(a[0])) else a[0]

N0, S0, W0, E0 = 44.42, 43.72, 10.05, 10.95         # area della mappa principale
RES = 20.0
LATM = (N0 + S0) / 2
DLAT = RES / 111320.0
DLON = RES / (111320.0 * math.cos(math.radians(LATM)))
TR, TC = 556, 500                                   # tessera: ~11,1 x 10 km
MARG = 150                                          # 3 km di margine
OUT = "docs/terreno/t"
os.makedirs(OUT, exist_ok=True)
UA = {"User-Agent": "mappa-funghi (github.com/alessiobandiera/mappa-funghi)"}


def log(*a):
    print(*a, flush=True)


def get(url, data=None, timeout=120):
    req = urllib.request.Request(url, data=data, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


# ---------------- altimetria: mosaico Terrarium a zoom 13 (~14 m per pixel, dati originali ~30 m) ----------------
Z = 13
def txy(lat, lon):
    n = 2 ** Z
    return (lon + 180) / 360 * n, (1 - np.arcsinh(np.tan(np.radians(lat))) / np.pi) / 2 * n

MOS = None; TX0 = TY0 = 0; ZM = Z
def prepara_mosaico():
    global MOS, TX0, TY0
    mx0, my0 = txy(N0 + 0.05, W0 - 0.05); mx1, my1 = txy(S0 - 0.05, E0 + 0.05)
    TX = range(int(mx0), int(mx1) + 1); TY = range(int(my0), int(my1) + 1)
    log(f"altimetria: {len(TX)}x{len(TY)} tessere Terrarium")
    MOS = np.zeros((len(TY) * 256, len(TX) * 256), np.float32)
    for j, y in enumerate(TY):
        for i, x in enumerate(TX):
            for t in range(5):
                try:
                    b = get(f"https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{Z}/{x}/{y}.png", timeout=60); break
                except Exception as e:
                    time.sleep(2 + 3 * t)
            a = np.asarray(Image.open(io.BytesIO(b)).convert("RGB")).astype(np.float32)
            MOS[j*256:(j+1)*256, i*256:(i+1)*256] = a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
    TX0, TY0 = TX[0], TY[0]
    log(f"mosaico {MOS.shape}, quota {MOS.min():.0f}-{MOS.max():.0f} m")

def quota(LAT, LON):
    n = 2 ** ZM
    fx = (LON + 180) / 360 * n; fy = (1 - np.arcsinh(np.tan(np.radians(LAT))) / np.pi) / 2 * n
    z = ndimage.map_coordinates(MOS, [(fy - TY0) * 256 - 0.5, (fx - TX0) * 256 - 0.5], order=1, mode="nearest")
    return ndimage.gaussian_filter(z.astype(np.float64), 0.6)


# ---------------- boschi OpenStreetMap ----------------
SERVER = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter",
          "https://maps.mail.ru/osm/tools/overpass/api/interpreter"]
def boschi(S, N, W, E):
    q = f"""[out:json][timeout:180];
(way["landuse"="forest"]({S},{W},{N},{E}); way["natural"="wood"]({S},{W},{N},{E});
 relation["landuse"="forest"]({S},{W},{N},{E}); relation["natural"="wood"]({S},{W},{N},{E}););
out geom;"""
    for t in range(6):
        srv = SERVER[t % len(SERVER)]
        try:
            return json.loads(get(srv, urllib.parse.urlencode({"data": q}).encode(), timeout=240)).get("elements", [])
        except Exception as e:
            log(f"   OSM {srv}: {e}"); time.sleep(10 + 10 * t)
    raise RuntimeError("OpenStreetMap non risponde")

def anelli(ways):
    segs = [[(p["lat"], p["lon"]) for p in w] for w in ways if len(w) >= 2]
    rings = []
    while segs:
        cur = segs.pop(0); changed = True
        while cur[0] != cur[-1] and changed:
            changed = False
            for i, s in enumerate(segs):
                if s[0] == cur[-1]: cur = cur + s[1:]
                elif s[-1] == cur[-1]: cur = cur + s[::-1][1:]
                elif s[-1] == cur[0]: cur = s + cur[1:]
                elif s[0] == cur[0]: cur = s[::-1] + cur[1:]
                else: continue
                segs.pop(i); changed = True; break
        if len(cur) >= 3: rings.append(cur)
    return rings

TIPO = {"broadleaved": 1, "mixed": 2, "needleleaved": 3}
def raster_boschi(els, N, W, ny, nx):
    img = Image.new("L", (nx, ny), 0); dr = ImageDraw.Draw(img)
    polys = []
    for e in els:
        code = TIPO.get(e.get("tags", {}).get("leaf_type"), 1)
        if e["type"] == "way" and e.get("geometry"):
            polys.append((code, [[(p["lat"], p["lon"]) for p in e["geometry"]]], []))
        elif e["type"] == "relation":
            mem = e.get("members", [])
            polys.append((code, anelli([m["geometry"] for m in mem if m.get("role") == "outer" and m.get("geometry")]),
                                anelli([m["geometry"] for m in mem if m.get("role") == "inner" and m.get("geometry")])))
    xy = lambda r: [((lo - W) / DLON, (N - la) / DLAT) for la, lo in r]
    for code, outs, ins in sorted(polys, key=lambda p: p[0] == 1, reverse=True):
        for r in outs: dr.polygon(xy(r), fill=code)
        for r in ins: dr.polygon(xy(r), fill=0)
    return np.asarray(img).astype(np.uint8)


# ---------------- calcoli sul terreno ----------------
def shift(a, dr, dc, fill):
    out = np.full_like(a, fill); h, w = a.shape
    r0, r1 = max(0, -dr), min(h, h - dr); c0, c1 = max(0, -dc), min(w, w - dc)
    if r1 > r0 and c1 > c0: out[r0:r1, c0:c1] = a[r0 + dr:r1 + dr, c0 + dc:c1 + dc]
    return out

NB = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
def riempi(zz):
    h, w = zz.shape; zf = zz.copy(); done = np.zeros((h, w), bool); pq = []
    for r in range(h):
        for c in (0, w - 1): heapq.heappush(pq, (zf[r, c], r, c)); done[r, c] = True
    for c in range(1, w - 1):
        for r in (0, h - 1): heapq.heappush(pq, (zf[r, c], r, c)); done[r, c] = True
    while pq:
        v, r, c = heapq.heappop(pq)
        for dr, dc in NB:
            rr, cc = r + dr, c + dc
            if 0 <= rr < h and 0 <= cc < w and not done[rr, cc]:
                done[rr, cc] = True
                if zf[rr, cc] <= v: zf[rr, cc] = v + 1e-3
                heapq.heappush(pq, (zf[rr, cc], rr, cc))
    return zf

@njit(cache=True)
def accumula(zf, order, res):
    h, w = zf.shape
    acc = np.ones(h * w) * res * res
    dr = np.array([-1, -1, -1, 0, 0, 1, 1, 1]); dc = np.array([-1, 0, 1, -1, 1, -1, 0, 1])
    L = np.array([0.354, 0.5, 0.354, 0.5, 0.5, 0.354, 0.5, 0.354]) * res
    dist = np.array([1.4142, 1, 1.4142, 1, 1, 1.4142, 1, 1.4142]) * res
    wts = np.zeros(8)
    for q in range(order.size):
        idx = order[q]; r = idx // w; c = idx % w; z0 = zf[r, c]; tot = 0.0
        for k in range(8):
            rr = r + dr[k]; cc = c + dc[k]; wts[k] = 0.0
            if rr < 0 or rr >= h or cc < 0 or cc >= w: continue
            d = z0 - zf[rr, cc]
            if d > 0:
                wts[k] = (d / dist[k]) ** 1.1 * L[k]; tot += wts[k]
        if tot > 0:
            a = acc[idx]
            for k in range(8):
                if wts[k] > 0: acc[(r + dr[k]) * w + c + dc[k]] += a * wts[k] / tot
    return acc

NAZ = 24
def fattori(z):
    ny, nx = z.shape
    gy, gx = np.gradient(z, RES); dzN, dzE = -gy, gx
    slope = np.arctan(np.hypot(dzN, dzE)); nrm = np.sqrt(dzE**2 + dzN**2 + 1)
    nE, nN, nU = -dzE / nrm, -dzN / nrm, 1 / nrm
    # orizzonte su griglia a 40 m, fino a 3 km
    f = 2; CR = RES * f
    zc = z[:(ny // f) * f, :(nx // f) * f].reshape(ny // f, f, nx // f, f).mean(axis=(1, 3))
    hor = np.zeros((NAZ,) + zc.shape, np.float32)
    for i in range(NAZ):
        az = math.radians(i * 360 / NAZ); s, c = math.sin(az), math.cos(az)
        best = np.full(zc.shape, -np.inf)
        for k in range(1, int(3000 / CR) + 1):
            dr, dc = int(round(-k * c)), int(round(k * s))
            np.maximum(best, (shift(zc, dr, dc, -1e9) - zc) / (CR * math.hypot(dr, dc)), out=best)
        hor[i] = np.arctan(np.maximum(best, 0))
    zoomf = (ny / zc.shape[0], nx / zc.shape[1])
    svf = ndimage.zoom(np.mean(np.cos(hor) ** 2, axis=0), zoomf, order=1)[:ny, :nx]
    svf = np.pad(svf, ((0, ny - svf.shape[0]), (0, nx - svf.shape[1])), mode="edge")
    phi = math.radians(LATM)
    def sole(doy):
        dec = math.radians(23.44 * math.sin(math.radians(360 / 365 * (284 + doy))))
        tot = np.zeros_like(z); flat = 0.0
        for hh in np.arange(6.0, 18.01, 0.25):
            ha = math.radians(15 * (hh - 12))
            sa = math.sin(phi) * math.sin(dec) + math.cos(phi) * math.cos(dec) * math.cos(ha)
            if sa <= 0.02: continue
            alt = math.asin(sa)
            az = (math.degrees(math.atan2(math.sin(ha), math.cos(ha) * math.sin(phi) - math.tan(dec) * math.cos(phi))) + 180) % 360
            tau = 0.72 ** (1 / sa)
            sE, sN = math.sin(math.radians(az)) * math.cos(alt), math.cos(math.radians(az)) * math.cos(alt)
            cosi = np.clip(nE * sE + nN * sN + nU * sa, 0, None)
            p = az / (360 / NAZ); i0 = int(p) % NAZ; i1 = (i0 + 1) % NAZ; t = p - int(p)
            hz = ndimage.zoom(hor[i0] * (1 - t) + hor[i1] * t, zoomf, order=1)
            hz = np.pad(hz, ((0, max(0, ny - hz.shape[0])), (0, max(0, nx - hz.shape[1]))), mode="edge")[:ny, :nx]
            lit = np.clip((alt - hz) / math.radians(1.5) + 0.5, 0, 1)
            tot += 1000 * tau * cosi * lit + 1000 * 0.12 * sa * svf * (1 + np.cos(slope)) / 2
            flat += 1000 * tau * sa + 1000 * 0.12 * sa
        return tot / flat
    SOLE = [sole(d) for d in (258, 288, 319)]
    zf = riempi(z)
    acc = accumula(zf, np.argsort(-zf, axis=None, kind="stable"), RES).reshape(z.shape)
    twi = np.log(acc / RES / np.maximum(np.tan(slope), 0.005))
    def tpi(rad):
        k = int(round(rad / RES)) * 2 + 1
        return z - ndimage.uniform_filter(z, k, mode="nearest")
    t1, t2 = tpi(60), tpi(250)
    forma = 0.5 * t1 / 8.0 + 0.5 * t2 / 30.0          # scale fisse (m), uguali per tutte le tessere
    sx = np.zeros_like(z)
    for azd in (350, 10, 30, 50):
        s, c = math.sin(math.radians(azd)), math.cos(math.radians(azd))
        best = np.full(z.shape, -np.inf)
        for k in range(1, int(300 / RES) + 1):
            dr, dc = int(round(-k * c)), int(round(k * s))
            np.maximum(best, (shift(z, dr, dc, -1e9) - z) / (RES * math.hypot(dr, dc)), out=best)
        sx += np.degrees(np.arctan(best))
    sx /= 4
    return twi, forma, sx, SOLE


# ---------------- tessere ----------------
def main():
    prepara_mosaico()
    NYG = int(math.ceil((N0 - S0) / DLAT)); NXG = int(math.ceil((E0 - W0) / DLON))
    NI, NJ = math.ceil(NYG / TR), math.ceil(NXG / TC)
    log(f"griglia {NYG}x{NXG} a {RES:.0f} m, {NI}x{NJ} tessere")
    indice = {"res_m": RES, "dlat": DLAT, "dlon": DLON, "nord": N0, "ovest": W0, "righe_tessera": TR, "colonne_tessera": TC,
              "fonte_quota": "Terrarium/Mapzen (EU-DEM e SRTM, ~30 m)", "fonte_boschi": "OpenStreetMap (ODbL)", "tessere": []}
    solo = os.environ.get("SOLO_TESSERE")                    # per prove: "3_4,3_5"
    t_inizio = time.time()
    for i in range(NI):
        for j in range(NJ):
            tid = f"{i}_{j}"
            if solo and tid not in solo.split(","): continue
            r0, c0 = i * TR, j * TC
            r1, c1 = min(NYG, r0 + TR), min(NXG, c0 + TC)
            R0, C0 = r0 - MARG, c0 - MARG                     # con il margine
            ny, nx = (r1 - r0) + 2 * MARG, (c1 - c0) + 2 * MARG
            Nt = N0 - R0 * DLAT; Wt = W0 + C0 * DLON
            lat = Nt - (np.arange(ny) + 0.5) * DLAT; lon = Wt + (np.arange(nx) + 0.5) * DLON
            core = (slice(MARG, MARG + r1 - r0), slice(MARG, MARG + c1 - c0))
            Nc, Sc = N0 - r0 * DLAT, N0 - r1 * DLAT; Wc, Ec = W0 + c0 * DLON, W0 + c1 * DLON
            try:
                els = boschi(Sc, Nc, Wc, Ec)
            except Exception as e:
                log(f"{tid}: boschi non disponibili ({e}), salto"); continue
            bosco = raster_boschi(els, Nc, Wc, r1 - r0, c1 - c0)
            if (bosco > 0).mean() < 0.005:
                log(f"{tid}: niente bosco"); continue
            LON, LAT = np.meshgrid(lon, lat)
            z = quota(LAT, LON)
            if (z[core] < 2).mean() > 0.97:
                log(f"{tid}: mare"); continue
            t0 = time.time()
            twi, forma, sx, SOLE = fattori(z)
            # normalizzazione con scale fisse, uguali in tutte le tessere (niente salti ai bordi)
            acqua = np.clip(0.65 * (twi - 5) / 8 + 0.35 * np.clip(0.5 - forma / 3, 0, 1), 0, 1)
            forma01 = np.clip(0.5 + forma / 4, 0, 1)
            riparo = np.clip((sx + 10) / 30, 0, 1)
            m = bosco > 0
            b8 = lambda a: np.where(m, np.clip(np.round(a[core] * 255), 0, 255), 0).astype(np.uint8)
            s8 = lambda a: np.where(m, np.clip(np.round(a[core] * 128), 0, 255), 0).astype(np.uint8)
            q2 = np.where(m, np.clip(np.round(z[core] * 2), 0, 65535), 0).astype(np.uint16)
            Image.fromarray(np.dstack([b8(acqua), b8(forma01), b8(riparo)]), "RGB").save(f"{OUT}/{tid}_a.png", optimize=True)
            Image.fromarray(np.dstack([(q2 >> 8).astype(np.uint8), (q2 & 255).astype(np.uint8), bosco]), "RGB").save(f"{OUT}/{tid}_b.png", optimize=True)
            Image.fromarray(np.dstack([s8(SOLE[0]), s8(SOLE[1]), s8(SOLE[2])]), "RGB").save(f"{OUT}/{tid}_c.png", optimize=True)
            indice["tessere"].append({"id": tid, "nord": Nc, "sud": Sc, "ovest": Wc, "est": Ec, "righe": r1 - r0, "colonne": c1 - c0,
                                      "bosco": round(float(m.mean()), 3)})
            kb = sum(os.path.getsize(f"{OUT}/{tid}_{k}.png") for k in "abc") // 1024
            log(f"{tid}: bosco {100*m.mean():.0f}%, quota {z[core].min():.0f}-{z[core].max():.0f} m, {time.time()-t0:.0f} s, {kb} KB")
            json.dump(indice, open("docs/terreno/tessere.json", "w"), indent=1)
            time.sleep(2)                                    # rispetto per Overpass
    log(f"fatto: {len(indice['tessere'])} tessere in {time.time()-t_inizio:.0f} s")
    json.dump(indice, open("docs/terreno/tessere.json", "w"), indent=1)


if __name__ == "__main__":
    main()
