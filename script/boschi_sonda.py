#!/usr/bin/env python3
"""Sonda 2: Carta degli Habitat ISPRA e uso del suolo Regione Toscana sull'area della mappa. Solo stampa (data/boschi/sonda.txt)."""
import json, re, urllib.parse, urllib.request
UA = {"User-Agent": "mappa-funghi/1.0 (+https://github.com/alessiobandiera/mappa-funghi)"}
PUNTI = {"S. Bartolomeo in Pizzorna": (43.94605, 10.60511), "Pizzorne 1 km O": (43.9461, 10.593), "Pizzorne 1 km N": (43.955, 10.6051),
         "Fosciandora": (44.115, 10.47), "Abetone": (44.13, 10.66)}
SUD, NORD, OVEST, EST = 43.62, 44.50, 9.85, 11.05


def get(url, timeout=90):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
            return r.read()
    except Exception as e:
        print(f"   -- {url[:160]}: {str(e)[:160]}"); return None


print("=== Carta degli Habitat ISPRA")
H = "https://sinacloud.isprambiente.it/arcgisina/rest/services/Natura/Carta_degli_Habitat_scala_1_50_000_e_1_25_000/MapServer/0"
b = get(H + "?f=json")
campi = []
if b:
    js = json.loads(b); campi = [f["name"] for f in js.get("fields", [])]
    print("campi:", [(f["name"], f["type"]) for f in js.get("fields", [])])
    print("descrizione:", (js.get("description") or "")[:500])
for nome, (la, lo) in PUNTI.items():
    q = urllib.parse.urlencode(dict(geometry=f"{lo},{la}", geometryType="esriGeometryPoint", inSR=4326, spatialRel="esriSpatialRelIntersects",
                                    outFields="*", returnGeometry="false", f="json"))
    b = get(H + "/query?" + q)
    if b:
        print(f"  {nome}:", [f["attributes"] for f in json.loads(b).get("features", [])][:2])
# classi nell'area: raggruppa per i campi che sembrano codice/nome dell'habitat
for c in [c for c in campi if re.search(r"cod|hab|nome|descr|legend|cl", c, re.I)][:3]:
    q = urllib.parse.urlencode(dict(where="1=1", geometry=f"{OVEST},{SUD},{EST},{NORD}", geometryType="esriGeometryEnvelope", inSR=4326,
                                    spatialRel="esriSpatialRelIntersects", groupByFieldsForStatistics=c,
                                    outStatistics=json.dumps([{"statisticType": "count", "onStatisticField": c, "outStatisticFieldName": "n"}]), f="json"))
    b = get(H + "/query?" + q)
    if b:
        st = json.loads(b).get("features", [])
        print(f"  classi per {c}: {len(st)}")
        for f in sorted(st, key=lambda f: -f["attributes"]["n"])[:70]:
            print("     ", f["attributes"])

print("\n=== Regione Toscana, uso e copertura del suolo")
W = "https://www502.regione.toscana.it/wmsraster/com.rt.wms.RTmap/wms?map=wmsucs"
b = get(W + "&service=WMS&request=GetCapabilities&version=1.3.0")
if b:
    t = b.decode("utf-8", "replace")
    nomi = re.findall(r"<Name>([^<]+)</Name>", t)
    print("livelli:", [n for n in nomi if n not in ("default", "classify_level_1")])
    fmt = re.findall(r"<GetFeatureInfo>.*?</GetFeatureInfo>", t, re.S)
    print("formati GetFeatureInfo:", re.findall(r"<Format>([^<]+)</Format>", fmt[0]) if fmt else None)
    for lay in [n for n in nomi if re.search(r"10k\.20(19|23)|2023", n) and "label" not in n][:4]:
        for nome, (la, lo) in list(PUNTI.items())[:3]:
            d = 0.0005
            q = urllib.parse.urlencode(dict(service="WMS", version="1.1.1", request="GetFeatureInfo", layers=lay, query_layers=lay, styles="",
                                            srs="EPSG:4326", bbox=f"{lo-d},{la-d},{lo+d},{la+d}", width=11, height=11, x=5, y=5,
                                            info_format="text/plain", feature_count=3))
            b2 = get(W + "&" + q)
            if b2: print(f"  {lay} @ {nome}:", re.sub(r"\s+", " ", b2.decode("utf-8", "replace"))[:600])
# metadati delle edizioni 2019/2023 (download?)
b = get("https://www502.regione.toscana.it/geonetwork/srv/ita/q?any=uso%20e%20copertura%20del%20suolo&_content_type=json&fast=index&from=1&to=30")
if b:
    t = b.decode("utf-8", "replace")
    print("download citati:", sorted(set(re.findall(r'https?://[^"|\\s]+\.(?:zip|gpkg|shp)', t)))[:20])
    print("servizi citati:", sorted(set(re.findall(r'https?://[^"|\\s]+(?:wfs|ows)[^"|\\s]*', t, re.I)))[:20])
