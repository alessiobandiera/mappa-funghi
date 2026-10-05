#!/usr/bin/env python3
"""Scarica i dati grezzi del terreno per una zona di prova (Pizzorne).

Gira su GitHub Actions (che raggiunge i servizi della Regione e OSM) e salva in data/terreno/:
  - dem.tif o dem_terrarium.npz : altimetria (Regione Toscana 10 m se disponibile, altrimenti Terrarium ~30 m)
  - boschi.json                 : poligoni bosco OpenStreetMap
  - sonda.txt                   : resoconto di cosa ha funzionato (i log di Actions non sono leggibili da fuori)
"""
import io, json, math, os, sys, time, urllib.parse, urllib.request

S, N, W, E = 43.88, 43.99, 10.50, 10.67          # zona di prova: altopiano delle Pizzorne e versanti
OUT = "data/terreno"
os.makedirs(OUT, exist_ok=True)
log = []
def nota(s):
    print(s, flush=True); log.append(s)

def get(url, timeout=90, data=None):
    req = urllib.request.Request(url, data=data, headers={"User-Agent": "mappa-funghi (github.com/alessiobandiera/mappa-funghi)"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.headers.get("Content-Type", ""), r.read()

# ---------- 1. altimetria della Regione (WCS) ----------
BASI = [
    "https://www502.regione.toscana.it/wmsraster/com.rt.wms.RTmap/wms?map=wmsmorfologia",
    "https://www502.regione.toscana.it/wcsraster/com.rt.wcs.RTmap/wcs?map=wcsmorfologia",
    "https://www502.regione.toscana.it/wmsraster/com.rt.wms.RTmap/wcs?map=wmsmorfologia",
]
COPERTURE = ["rt_morfologia.dtm_10m_idrol.rt", "rt_morfologia.iddtm.10m.rt"]
dem_ok = False
for base in BASI:
    try:
        st, ct, b = get(base + "&SERVICE=WCS&VERSION=1.0.0&REQUEST=GetCapabilities", 60)
        txt = b.decode("utf-8", "replace")
        nota(f"[WCS caps] {base} -> {st} {ct} {len(b)}B")
        nota("   " + txt[:1500].replace("\n", " ")[:1500])
        with open(f"{OUT}/wcs_caps_{BASI.index(base)}.xml", "w") as f: f.write(txt)
    except Exception as e:
        nota(f"[WCS caps] {base} -> errore {e}"); continue
    for cov in COPERTURE:
        try:
            st, ct, b = get(base + f"&SERVICE=WCS&VERSION=1.0.0&REQUEST=DescribeCoverage&COVERAGE={cov}", 60)
            txt = b.decode("utf-8", "replace")
            nota(f"[Describe] {cov} -> {st} {len(b)}B: " + txt[:1200].replace("\n", " "))
        except Exception as e:
            nota(f"[Describe] {cov} -> errore {e}")
        for crs, bbox, extra in [
            ("EPSG:4326", f"{W},{S},{E},{N}", f"&WIDTH={round((E-W)*111320*math.cos(math.radians(43.93))/10)}&HEIGHT={round((N-S)*111320/10)}"),
            ("EPSG:3003", None, "&RESX=10&RESY=10"),
            ("EPSG:6707", None, "&RESX=10&RESY=10"),
            ("EPSG:25832", None, "&RESX=10&RESY=10"),
        ]:
            if bbox is None:
                try:
                    from pyproj import Transformer
                    t = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
                    xs, ys = zip(*[t.transform(x, y) for x in (W, E) for y in (S, N)])
                    bbox = f"{min(xs):.0f},{min(ys):.0f},{max(xs):.0f},{max(ys):.0f}"
                except Exception as e:
                    nota(f"   pyproj non disponibile per {crs}: {e}"); continue
            for fmt in ["GTiff", "GEOTIFF_FLOAT32", "image/tiff", "GEOTIFF_INT16", "AAIGrid"]:
                url = (base + f"&SERVICE=WCS&VERSION=1.0.0&REQUEST=GetCoverage&COVERAGE={cov}&CRS={crs}"
                       f"&BBOX={bbox}{extra}&FORMAT={urllib.parse.quote(fmt)}")
                try:
                    st, ct, b = get(url, 180)
                except Exception as e:
                    nota(f"[GetCoverage] {cov} {crs} {fmt} -> errore {e}"); continue
                tiff = b[:4] in (b"II*\x00", b"MM\x00*")
                nota(f"[GetCoverage] {cov} {crs} {fmt} -> {st} {ct} {len(b)}B tiff={tiff}" + ("" if tiff else " " + b[:300].decode("utf-8", "replace").replace("\n", " ")))
                if tiff and len(b) > 100000:
                    with open(f"{OUT}/dem.tif", "wb") as f: f.write(b)
                    json.dump({"fonte": "Regione Toscana - DTM 10 m", "coverage": cov, "crs": crs, "bbox": bbox, "formato": fmt,
                               "url": url, "zona": [S, N, W, E]}, open(f"{OUT}/dem_info.json", "w"), indent=1)
                    dem_ok = True; break
                if fmt == "AAIGrid" and st == 200 and b[:5].lower() == b"ncols":
                    with open(f"{OUT}/dem.asc", "wb") as f: f.write(b)
                    json.dump({"fonte": "Regione Toscana - DTM 10 m", "coverage": cov, "crs": crs, "bbox": bbox, "formato": fmt,
                               "url": url, "zona": [S, N, W, E]}, open(f"{OUT}/dem_info.json", "w"), indent=1)
                    dem_ok = True; break
            if dem_ok: break
        if dem_ok: break
    if dem_ok: break

# ---------- 2. riserva: tessere Terrarium (AWS), zoom 14 ----------
def tile_xy(lat, lon, z):
    n = 2 ** z
    x = (lon + 180) / 360 * n
    y = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n
    return x, y
try:
    from PIL import Image
    import numpy as np
    z = 14
    x0, y0 = tile_xy(N, W, z); x1, y1 = tile_xy(S, E, z)
    tx = range(int(x0), int(x1) + 1); ty = range(int(y0), int(y1) + 1)
    big = np.zeros((len(ty) * 256, len(tx) * 256), dtype=np.float32)
    for j, y in enumerate(ty):
        for i, x in enumerate(tx):
            for tent in range(4):
                try:
                    _, _, b = get(f"https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png", 60); break
                except Exception as e:
                    time.sleep(2 + 3 * tent)
            a = np.asarray(Image.open(io.BytesIO(b)).convert("RGB")).astype(np.float32)
            big[j*256:(j+1)*256, i*256:(i+1)*256] = a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
    np.savez_compressed(f"{OUT}/dem_terrarium.npz", z=big, zoom=z, x0=tx[0], y0=ty[0])
    nota(f"[Terrarium] z{z} tessere {len(tx)}x{len(ty)} -> {big.shape}, quota {big.min():.0f}-{big.max():.0f} m")
except Exception as e:
    nota(f"[Terrarium] errore {e}")

# ---------- 3. boschi OSM ----------
q = f"""[out:json][timeout:120];
(way["landuse"="forest"]({S},{W},{N},{E}); way["natural"="wood"]({S},{W},{N},{E});
 relation["landuse"="forest"]({S},{W},{N},{E}); relation["natural"="wood"]({S},{W},{N},{E}););
out geom;"""
for srv in ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter",
            "https://maps.mail.ru/osm/tools/overpass/api/interpreter"]:
    try:
        st, ct, b = get(srv, 200, data=urllib.parse.urlencode({"data": q}).encode())
        d = json.loads(b)
        json.dump(d, open(f"{OUT}/boschi.json", "w"), separators=(",", ":"))
        nota(f"[OSM] {srv} -> {len(d.get('elements', []))} elementi, {len(b)}B")
        break
    except Exception as e:
        nota(f"[OSM] {srv} -> errore {e}")

nota(f"DEM Regione: {'OK' if dem_ok else 'non disponibile'}")
open(f"{OUT}/sonda.txt", "w").write("\n".join(log) + "\n")
