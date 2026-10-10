#!/usr/bin/env python3
"""Carte europee per specie a 30 m (Bonannella et al. 2022, PeerJ; Zenodo, CC BY 4.0): probabilità di presenza 2018-2020
(distribuzione «realizzata», 0-100), ricavata da serie Landsat e rilievi a terra con machine learning. Si legge solo la finestra
dell'area della mappa (lettura a pezzi dei Cloud Optimized GeoTIFF, senza scaricare i file europei).
Uscita: data/boschi/specie30m/<specie>.tif (EPSG:3035, uint8). Serve rasterio."""
import json, os, sys, urllib.request
import rasterio
from rasterio.warp import transform_bounds
from rasterio.windows import from_bounds

RECORD = {"castanea.sativa": 6951628, "quercus.cerris": 6967119, "quercus.robur": 6967309, "quercus.ilex": 6967263, "quercus.suber": 6967371,
          "fagus.sylvatica": 6956944, "abies.alba": 6953790, "picea.abies": 6961187, "pinus.nigra": 6964167, "pinus.sylvestris": 6966804,
          "pinus.pinea": 6966748, "pinus.halepensis": 6962632}
SUD, NORD, OVEST, EST = 43.60, 44.52, 9.83, 11.07
OUT = "data/boschi/specie30m"
UA = {"User-Agent": "mappa-funghi/1.0 (+https://github.com/alessiobandiera/mappa-funghi)"}
os.makedirs(OUT, exist_ok=True)
for sp, rec in RECORD.items():
    dest = f"{OUT}/{sp}.tif"
    if os.path.exists(dest):
        print(sp, "già fatto"); continue
    js = json.loads(urllib.request.urlopen(urllib.request.Request(f"https://zenodo.org/api/records/{rec}", headers=UA), timeout=60).read())
    f = [x for x in js["files"] if "anv.eml_p_30m" in x["key"] and "2018..2020" in x["key"]][0]
    url = f["links"]["self"]
    with rasterio.open("/vsicurl/" + url) as r:
        b = transform_bounds("EPSG:4326", r.crs, OVEST, SUD, EST, NORD)
        w = from_bounds(*b, transform=r.transform).round_offsets().round_lengths()
        a = r.read(1, window=w)
        prof = dict(driver="GTiff", width=a.shape[1], height=a.shape[0], count=1, dtype="uint8", crs=r.crs,
                    transform=r.window_transform(w), nodata=0, compress="deflate", predictor=2, tiled=True)
        with rasterio.open(dest, "w", **prof) as o:
            o.write(a, 1)
    print(sp, f["key"], a.shape, "pixel > 50:", int((a > 50).sum()), "dimensione", os.path.getsize(dest) // 1024, "KB", flush=True)
