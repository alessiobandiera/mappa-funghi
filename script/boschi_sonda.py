#!/usr/bin/env python3
"""Sonda: carte dei boschi più dettagliate di Corine per l'area della mappa. Solo stampa (data/boschi/sonda.txt).
1) ISPRA ArcGIS (sinacloud): servizi Carta della Natura / habitat
2) Regione Toscana: servizi WMS di uso del suolo / boschi
3) Zenodo: carte europee per specie a 30 m (Bonannella et al. 2022), valore a San Bartolomeo in Pizzorna"""
import json, re, urllib.parse, urllib.request
UA = {"User-Agent": "mappa-funghi/1.0 (+https://github.com/alessiobandiera/mappa-funghi)"}
PUNTI = {"S. Bartolomeo in Pizzorna": (43.94605, 10.60511), "Castagneto Garfagnana (Fosciandora)": (44.115, 10.47),
         "Faggeta Abetone": (44.13, 10.66), "Querceto colline lucchesi (Monte Pisano N)": (43.80, 10.50)}


def get(url, timeout=60, n=None):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
            return r.read(n) if n else r.read()
    except Exception as e:
        print(f"   -- {url[:140]}: {str(e)[:120]}"); return None


print("=== 1) ISPRA ArcGIS")
base = "https://sinacloud.isprambiente.it/arcgisina/rest/services"
b = get(base + "?f=json")
if b:
    js = json.loads(b); print("cartelle:", js.get("folders")); print("servizi:", [s["name"] for s in js.get("services", [])][:50])
    for cart in js.get("folders", []):
        if re.search(r"natura|habitat|carta|ecolog|biotop|veget", cart, re.I):
            b2 = get(f"{base}/{cart}?f=json")
            if b2:
                for s in json.loads(b2).get("services", []):
                    print("  ", s["name"], s["type"])
                    b3 = get(f"{base}/{s['name']}/{s['type']}?f=json")
                    if b3:
                        print("     livelli:", [(l["id"], l["name"]) for l in json.loads(b3).get("layers", [])][:40])

print("\n=== 2) Regione Toscana")
for u in ["https://www502.regione.toscana.it/ows_ucs/com.rt.wms.RTmap/ows?map=owsucs&service=WMS&request=GetCapabilities",
          "https://www502.regione.toscana.it/wmsraster/com.rt.wms.RTmap/wms?map=wmsucs&service=WMS&request=GetCapabilities",
          "https://www502.regione.toscana.it/ows_ucs/com.rt.wms.RTmap/wms?map=wmsucs&service=WMS&request=GetCapabilities",
          "https://www502.regione.toscana.it/ows_boschi/com.rt.wms.RTmap/ows?map=owsboschi&service=WMS&request=GetCapabilities",
          "https://www502.regione.toscana.it/geonetwork/srv/api/records?any=bosch&from=1&to=20",
          "https://www502.regione.toscana.it/geonetwork/srv/ita/q?any=castagn&_content_type=json&fast=index&from=1&to=20",
          "https://www502.regione.toscana.it/geonetwork/srv/ita/q?any=tipi%20forestali&_content_type=json&fast=index&from=1&to=20",
          "https://www502.regione.toscana.it/geonetwork/srv/ita/q?any=uso%20e%20copertura%20del%20suolo&_content_type=json&fast=index&from=1&to=20"]:
    b = get(u)
    if not b: continue
    t = b.decode("utf-8", "replace")
    print("OK", u[:120], len(t))
    nomi = re.findall(r"<Name>([^<]+)</Name>", t)
    if nomi: print("   livelli:", nomi[:60])
    tit = re.findall(r'"(?:title|defaultTitle)"\s*:\s*"([^"]+)"', t)
    if tit: print("   titoli:", tit[:30])
    uu = re.findall(r'https?://[^"\s<>]+(?:wms|ows|wfs|zip|download)[^"\s<>]*', t, re.I)
    if uu: print("   indirizzi:", sorted(set(uu))[:30])

print("\n=== 3) Zenodo, carte europee per specie (Bonannella et al. 2022)")
specie = {}
for pagina in (1, 2, 3):
    q = urllib.parse.urlencode(dict(q='"realized distribution at 30m"', size=25, page=pagina))
    b = get("https://zenodo.org/api/records?" + q)
    if not b: break
    hits = json.loads(b)["hits"]["hits"]
    if not hits: break
    for h in hits:
        tit = h["metadata"]["title"]; lic = (h["metadata"].get("license") or {}).get("id")
        file_p = [f for f in h.get("files", []) if "anv.eml_p_30m" in f["key"] and "2018..2020" in f["key"]]
        print(f"  {h['id']}  {tit[:90]}  licenza {lic}  file 2018-2020: {[f['key'] for f in file_p][:1]}")
        if file_p: specie[tit] = file_p[0]["links"]["self"]
try:
    import rasterio
    from rasterio.warp import transform
    for tit, url in specie.items():
        if not re.search(r"castanea|cerris|pubescens|robur|petraea|fagus|ilex|pinaster|pinea|nigra|sylvestris|abies|picea|ostrya|carpinus", tit, re.I):
            continue
        try:
            with rasterio.open("/vsicurl/" + url) as r:
                vals = []
                for nome, (la, lo) in PUNTI.items():
                    xs, ys = transform("EPSG:4326", r.crs, [lo], [la])
                    v = next(r.sample([(xs[0], ys[0])]))[0]
                    vals.append(f"{nome.split(' ')[0]} {v}")
                print(f"  {tit[:60]:60s} " + " | ".join(vals) + f"  (dtype {r.dtypes[0]}, nodata {r.nodata})")
        except Exception as e:
            print("  ", tit[:60], "errore", str(e)[:120])
except ImportError as e:
    print("rasterio non disponibile", e)
