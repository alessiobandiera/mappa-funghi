#!/usr/bin/env python3
"""Sonda 3: legenda e copertura della Carta degli Habitat ISPRA sull'area della mappa; livello «idift» della Regione. Solo stampa."""
import json, re, urllib.parse, urllib.request
UA = {"User-Agent": "mappa-funghi/1.0 (+https://github.com/alessiobandiera/mappa-funghi)"}


def get(url, timeout=90):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
            return r.read()
    except Exception as e:
        print(f"   -- {url[:160]}: {str(e)[:160]}"); return None


H = "https://sinacloud.isprambiente.it/arcgisina/rest/services/Natura/Carta_degli_Habitat_scala_1_50_000_e_1_25_000/MapServer"
for u in (H + "/0?f=json", H + "/legend?f=json"):
    b = get(u)
    if not b: continue
    js = json.loads(b)
    r = (js.get("drawingInfo") or {}).get("renderer") or {}
    if r: print("renderer:", r.get("type"), r.get("field1"), len(r.get("uniqueValueInfos", [])))
    for v in r.get("uniqueValueInfos", []):
        if str(v.get("value", "")).startswith(("41", "42", "43", "44", "45", "83.3", "31.8")):
            print("   ", v.get("value"), "=", v.get("label"))
    for l in js.get("layers", []):
        for x in l.get("legend", []):
            if re.match(r"(41|42|43|44|45|83\.3|31\.8)", x.get("label", "")) or re.match(r"(41|42|43|44|45|83\.3|31\.8)", str(x.get("values", ""))):
                print("   legenda:", x.get("label"), x.get("values"))
# copertura: punti in Emilia, Liguria, Lunigiana, Garfagnana, Pistoiese
for nome, (la, lo) in {"Emilia (Frassinoro)": (44.30, 10.57), "Emilia (Pievepelago)": (44.20, 10.62), "Emilia (Villa Minozzo)": (44.37, 10.47),
                       "Liguria (Sarzana)": (44.11, 9.96), "Liguria (Castelnuovo Magra)": (44.10, 10.02), "Lunigiana (Fivizzano)": (44.24, 10.12),
                       "Garfagnana (Castelnuovo)": (44.12, 10.40), "Pistoiese (San Marcello)": (44.06, 10.79), "Pizzorne (S. Bartolomeo)": (43.94605, 10.60511)}.items():
    q = urllib.parse.urlencode(dict(geometry=f"{lo},{la}", geometryType="esriGeometryPoint", inSR=4326, spatialRel="esriSpatialRelIntersects",
                                    distance=600, units="esriSRUnit_Meter", outFields="natura.natura.habitat.codice,natura.natura.habitat.id_poly",
                                    returnGeometry="false", f="json"))
    b = get(H + "/0/query?" + q)
    if b:
        ff = json.loads(b).get("features", [])
        print(f"  {nome}: {len(ff)} aree entro 600 m:", sorted({(f['attributes']['natura.natura.habitat.codice'], f['attributes']['natura.natura.habitat.id_poly'][:3]) for f in ff})[:12])
# paginazione e limite di record del servizio
b = get(H + "/0?f=json")
if b:
    js = json.loads(b); print("maxRecordCount:", js.get("maxRecordCount"), "capabilities:", js.get("capabilities"), "supportsPagination:", (js.get("advancedQueryCapabilities") or {}).get("supportsPagination"))

print("\n=== Regione Toscana, livello idift")
W = "https://www502.regione.toscana.it/wmsraster/com.rt.wms.RTmap/wms?map=wmsucs"
b = get(W + "&service=WMS&request=GetCapabilities&version=1.3.0")
if b:
    t = b.decode("utf-8", "replace")
    for m in re.finditer(r"<Name>(rt_ucs\.idift[^<]*)</Name>\s*<Title>([^<]*)</Title>", t):
        print("  ", m.group(1), "=", m.group(2))
    ab = re.findall(r"<Name>rt_ucs\.idift\.rt\.all</Name>.*?<Abstract>([^<]*)</Abstract>", t, re.S)
    print("   descrizione:", ab[:1])
for nome, (la, lo) in {"S. Bartolomeo": (43.94605, 10.60511), "Pizzorne 1 km O": (43.9461, 10.593)}.items():
    d = 0.002
    q = urllib.parse.urlencode(dict(service="WMS", version="1.1.1", request="GetFeatureInfo", layers="rt_ucs.idift.rt.all", query_layers="rt_ucs.idift.rt.all",
                                    styles="", srs="EPSG:4326", bbox=f"{lo-d},{la-d},{lo+d},{la+d}", width=21, height=21, x=10, y=10,
                                    info_format="text/plain", feature_count=5))
    b = get(W + "&" + q)
    if b: print(f"  idift @ {nome}:", re.sub(r"\s+", " ", b.decode("utf-8", "replace"))[:900])
