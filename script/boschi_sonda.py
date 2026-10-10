#!/usr/bin/env python3
"""Sonda 4: carte dei boschi gratuite di LaMMA e Regione Toscana. Solo stampa (data/boschi/sonda.txt)."""
import json, re, urllib.parse, urllib.request
UA = {"User-Agent": "mappa-funghi/1.0 (+https://github.com/alessiobandiera/mappa-funghi)"}
PUNTI = {"S. Bartolomeo in Pizzorna": (43.94605, 10.60511), "Pizzorne 1 km O": (43.9461, 10.593), "Fosciandora": (44.115, 10.47), "Abetone": (44.13, 10.66)}


def get(url, timeout=90):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
            return r.read()
    except Exception as e:
        print(f"   -- {url[:170]}: {str(e)[:150]}"); return None


print("=== LaMMA GeoServer: tutti i livelli")
for u in ["https://geoportale.lamma.rete.toscana.it/geoserver/ows?service=WMS&request=GetCapabilities&version=1.3.0",
          "https://geoportale.lamma.rete.toscana.it/geoserver/ows?service=WFS&request=GetCapabilities&version=2.0.0"]:
    b = get(u)
    if not b: continue
    t = b.decode("utf-8", "replace")
    for m in re.finditer(r"<(?:Layer[^>]*|wfs:FeatureType|FeatureType)>\s*<Name>([^<]+)</Name>\s*<Title>([^<]*)</Title>", t):
        print("  ", m.group(1), "=", m.group(2))
for u in ["https://geoportale.lamma.rete.toscana.it/geonetwork/srv/ita/q?any=bosc&_content_type=json&fast=index&from=1&to=40",
          "https://geoportale.lamma.rete.toscana.it/geonetwork/srv/ita/q?any=forest&_content_type=json&fast=index&from=1&to=40",
          "https://geoportale.lamma.rete.toscana.it/geonetwork/srv/api/records?any=bosc"]:
    b = get(u)
    if b:
        t = b.decode("utf-8", "replace")
        print("OK", u[:100], len(t)); print("   titoli:", sorted(set(re.findall(r'"(?:title|defaultTitle)"\s*:\s*"([^"]+)"', t)))[:40])
        print("   indirizzi:", sorted(set(re.findall(r'https?://[^"|\\s<>]+(?:wms|ows|wfs|zip|download)[^"|\\s<>]*', t, re.I)))[:20])

print("\n=== Regione Toscana: catalogo (titoli con bosc/forest/vegetaz)")
for q in ("bosc", "forestal", "vegetazione", "castagn", "inventario forestale"):
    b = get("https://www502.regione.toscana.it/geonetwork/srv/ita/q?" + urllib.parse.urlencode(dict(any=q, _content_type="json", fast="index", **{"from": 1, "to": 60})))
    if not b: continue
    t = b.decode("utf-8", "replace")
    tit = sorted(set(re.findall(r'"(?:title|defaultTitle)"\s*:\s*"([^"]+)"', t)))
    print(f"  «{q}»:", tit[:40])
    print("     indirizzi:", sorted(set(re.findall(r'https?://[^"|\\s<>]+(?:wms|ows|wfs|zip|download|map=)[^"|\\s<>]*', t, re.I)))[:25])

print("\n=== Regione Toscana: servizi WMS candidati")
for mappa in ("wmsforestale", "wmsforeste", "wmsboschi", "wmsift", "wmsvegetazione", "wmsucs", "wmspit", "wmsretecologica", "wmscastagneti"):
    for base in ("https://www502.regione.toscana.it/wmsraster/com.rt.wms.RTmap/wms?map=", "https://www502.regione.toscana.it/ows_/com.rt.wms.RTmap/wms?map="):
        b = get(base + mappa + "&service=WMS&request=GetCapabilities&version=1.3.0", timeout=40)
        if b and b"<Layer" in b:
            t = b.decode("utf-8", "replace")
            nomi = [n for n in re.findall(r"<Name>([^<]+)</Name>", t) if n not in ("default",)]
            print(f"  {mappa}: {len(nomi)} livelli:", [n for n in nomi if re.search(r"bosc|forest|veget|ift|tipi|castag", n, re.I)][:30] or nomi[:15])
            break
