#!/usr/bin/env python3
"""Tipi di bosco dalla carta ISPRA Corine Land Cover 2018 IV livello, per l'area della mappa.

Interroga il servizio ArcGIS di ISPRA (layer «Corine Land Cover 2018 IV livello») a riquadri di 0,1°, solo le classi di bosco
(311x latifoglie, 312x conifere, 313x misti), e salva i poligoni in data/boschi/clc18_boschi.geojson (WGS84, semplificati a ~10 m).
Fonte: ISPRA, Corine Land Cover 2018 IV livello (dati aperti).
Uso: python script/boschi_clc.py        (solo libreria standard)
"""
import json, os, time, urllib.parse, urllib.request

URL = "https://sinacloud.isprambiente.it/arcgisina/rest/services/corine_land_cover/CorineLandCover/MapServer/4/query"
SUD, NORD, OVEST, EST = 43.62, 44.50, 9.85, 11.05          # area della mappa con un po' di margine
PASSO = 0.1
OUT = "data/boschi/clc18_boschi.geojson"


def chiedi(par, tentativi=5):
    q = urllib.parse.urlencode(par)
    for t in range(tentativi):
        try:
            with urllib.request.urlopen(URL + "?" + q, timeout=120) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            print("  errore", e, "- riprovo"); time.sleep(5 * (t + 1))
    raise RuntimeError("servizio ISPRA non raggiungibile")


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    visti, feat = set(), []
    la = SUD
    while la < NORD - 1e-9:
        lo = OVEST
        while lo < EST - 1e-9:
            env = f"{lo},{la},{min(lo + PASSO, EST)},{min(la + PASSO, NORD)}"
            off = 0
            while True:
                js = chiedi({"where": "clc18 LIKE '31%' OR clc18 LIKE '3.1%'", "geometry": env, "geometryType": "esriGeometryEnvelope",
                             "inSR": 4326, "spatialRel": "esriSpatialRelIntersects", "outFields": "objectid,clc18", "returnGeometry": "true",
                             "outSR": 4326, "maxAllowableOffset": 0.0001, "geometryPrecision": 5, "f": "geojson",
                             "resultOffset": off, "resultRecordCount": 1000})
                ff = js.get("features", [])
                for f in ff:
                    oid = f["properties"].get("objectid")
                    if oid in visti: continue
                    visti.add(oid); feat.append({"type": "Feature", "properties": {"clc": str(f["properties"]["clc18"]).replace(".", "").strip()},
                                                 "geometry": f["geometry"]})
                if len(ff) < 1000 or not js.get("exceededTransferLimit", len(ff) == 1000): break
                off += 1000
            lo += PASSO
        print(f"latitudine {la:.2f}: {len(feat)} poligoni"); la += PASSO
    from collections import Counter
    print("classi:", dict(Counter(f["properties"]["clc"] for f in feat).most_common()))
    json.dump({"type": "FeatureCollection", "fonte": "ISPRA, Corine Land Cover 2018 IV livello", "features": feat},
              open(OUT, "w"), separators=(",", ":"))
    print("salvato", OUT, os.path.getsize(OUT) // 1024, "KB")


if __name__ == "__main__":
    main()
