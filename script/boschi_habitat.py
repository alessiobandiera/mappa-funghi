#!/usr/bin/env python3
"""Boschi dalla Carta degli Habitat ISPRA (Carta della Natura, scala 1:50.000; Toscana 2019, anche Emilia-Romagna e Liguria)
per l'area della mappa: più dettagliata di Corine (aree piccole, tipi come castagneti, cerrete, querceti di roverella, ostrieti,
faggete, abetine, pinete, piantagioni di conifere).

Interroga il servizio ArcGIS di ISPRA (Natura/Carta_degli_Habitat_scala_1_50_000_e_1_25_000, livello 0) a riquadri di 0,1°,
solo gli habitat di bosco, e salva i poligoni in data/boschi/habitat_boschi.geojson.gz (WGS84, semplificati a ~10 m).
Fonte: ISPRA, Sistema Carta della Natura. Uso: python script/boschi_habitat.py        (solo libreria standard)
"""
import gzip, json, os, time, urllib.parse, urllib.request

URL = "https://sinacloud.isprambiente.it/arcgisina/rest/services/Natura/Carta_degli_Habitat_scala_1_50_000_e_1_25_000/MapServer/0/query"
SUD, NORD, OVEST, EST = 43.62, 44.50, 9.85, 11.05     # come script/boschi_clc.py
PASSO = 0.1
OUT = "data/boschi/habitat_boschi.geojson.gz"
C = "natura.natura.habitat.codice"
DOVE = " OR ".join(f"{C} LIKE '{p}%'" for p in ("41", "42", "43", "44", "45", "83.31", "83.32")) + f" OR {C} = '31.8C'"
UA = {"User-Agent": "mappa-funghi/1.0 (+https://github.com/alessiobandiera/mappa-funghi)"}


def chiedi(par, tentativi=6):
    q = urllib.parse.urlencode(par)
    for t in range(tentativi):
        try:
            with urllib.request.urlopen(urllib.request.Request(URL + "?" + q, headers=UA), timeout=180) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            print("  errore", str(e)[:150], "- riprovo", flush=True); time.sleep(5 * (t + 1))
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
                js = chiedi({"where": DOVE, "geometry": env, "geometryType": "esriGeometryEnvelope", "inSR": 4326,
                             "spatialRel": "esriSpatialRelIntersects", "outFields": f"natura.natura.habitat.objectid,{C},natura.natura.habitat.id_poly",
                             "returnGeometry": "true", "outSR": 4326, "maxAllowableOffset": 0.0001, "geometryPrecision": 5, "f": "geojson",
                             "resultOffset": off, "resultRecordCount": 1000})
                ff = js.get("features", [])
                for f in ff:
                    p = f.get("properties") or {}
                    oid = p.get("natura.natura.habitat.objectid") or p.get("objectid") or f.get("id")
                    if oid in visti or not f.get("geometry"):
                        continue
                    visti.add(oid)
                    feat.append({"type": "Feature", "properties": {"hab": str(p.get(C)).strip(), "poly": p.get("natura.natura.habitat.id_poly")},
                                 "geometry": f["geometry"]})
                if len(ff) < 1000 and not js.get("exceededTransferLimit") and not (js.get("properties") or {}).get("exceededTransferLimit"):
                    break
                off += 1000
            lo += PASSO
        print(f"latitudine {la:.2f}: {len(feat)} poligoni", flush=True); la += PASSO
    from collections import Counter
    print("habitat:", dict(Counter(f["properties"]["hab"] for f in feat).most_common()))
    with gzip.open(OUT, "wt", encoding="utf-8") as g:
        json.dump({"type": "FeatureCollection", "fonte": "ISPRA, Sistema Carta della Natura - Carta degli Habitat 1:50.000", "features": feat},
                  g, separators=(",", ":"))
    print("salvato", OUT, os.path.getsize(OUT) // 1024, "KB")


if __name__ == "__main__":
    main()
