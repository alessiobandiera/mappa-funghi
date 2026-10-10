#!/usr/bin/env python3
"""Inventario Forestale Toscano (Regione Toscana, servizio WMS uso del suolo, livello rt_ucs.idift.rt.all; griglia 400 m,
fotointerpretazione 1978 e rilievi anni '90) letto su un campione di maglie di bosco della mappa (una su 4), per confrontarlo con le
altre carte. Uscita: data/boschi/ift_punti.json  [lat, lon, {campi}] . Solo libreria standard."""
import json, re, time, urllib.parse, urllib.request
UA = {"User-Agent": "mappa-funghi/1.0 (+https://github.com/alessiobandiera/mappa-funghi)"}
W = "https://www502.regione.toscana.it/wmsraster/com.rt.wms.RTmap/wms?map=wmsucs&"
CAMPI = ("CODICE", "CATFOR", "CATFOR_AG", "TIPO", "CONIF_LAT", "COMPSPE1", "COMPSPE2", "COMPSPE3", "COPERTU1", "COPERTU2", "COPERTU3",
         "COPCOMPL", "QUOTA", "USOSUO")

h = open("docs/index.html", encoding="utf-8").read()
B = json.loads(re.search(r"const BOSCHI_DATI=(\{.*?\});", h).group(1))
B64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
punti, s, n = [], B["dati"], 0
for R in range(B["righe"]):
    for C in range(B["colonne"]):
        k = (R * B["colonne"] + C) * 2
        if B64.index(s[k]) * 64 + B64.index(s[k + 1]) <= 0: continue
        n += 1
        if n % 4: continue
        punti.append((round(B["lat0"] + (R + .5) * B["dlat"], 5), round(B["lon0"] + (C + .5) * B["dlon"], 5)))
print(len(punti), "punti su", n, "maglie di bosco", flush=True)
out, fatti = [], 0
for la, lo in punti:
    d = 0.0008
    q = urllib.parse.urlencode(dict(service="WMS", version="1.1.1", request="GetFeatureInfo", layers="rt_ucs.idift.rt.all",
                                    query_layers="rt_ucs.idift.rt.all", styles="", srs="EPSG:4326", bbox=f"{lo-d},{la-d},{lo+d},{la+d}",
                                    width=9, height=9, x=4, y=4, info_format="text/plain", feature_count=1))
    for t in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(W + q, headers=UA), timeout=40) as r:
                txt = r.read().decode("utf-8", "replace"); break
        except Exception as e:
            txt = None; time.sleep(3 * (t + 1))
    v = {}
    if txt:
        for c in CAMPI:
            m = re.search(rf"\b{c} = '([^']*)'", txt)
            if m: v[c] = m.group(1)
    out.append([la, lo, v]); fatti += 1
    if fatti % 200 == 0:
        print(f"{fatti}/{len(punti)} (con dati: {sum(1 for x in out if x[2])})", flush=True)
        json.dump(out, open("data/boschi/ift_punti.json", "w"), ensure_ascii=False, separators=(",", ":"))
    time.sleep(0.15)
json.dump(out, open("data/boschi/ift_punti.json", "w"), ensure_ascii=False, separators=(",", ":"))
print("fatto:", len(out), "punti, con dati IFT:", sum(1 for x in out if x[2]))
