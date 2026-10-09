#!/usr/bin/env python3
"""Sonda LaMMA: dove e in che formato si trovano le previsioni WRF/MOLOCH (pioggia). Solo stampa."""
import io, re, urllib.request, zipfile
from datetime import date, timedelta
UA = {"User-Agent": "mappa-funghi/1.0 (+https://github.com/alessiobandiera/mappa-funghi)"}


def prova(url, n=600, metodo="GET", timeout=25):
    try:
        req = urllib.request.Request(url, headers=UA, method=metodo)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            b = r.read(200000) if metodo == "GET" else b""
            print(f"OK {r.status} {url}  [{r.headers.get('Content-Type')} {r.headers.get('Content-Length')}]")
            if n and b: print("   ", re.sub(r"\s+", " ", b[:n].decode("utf-8", "replace")))
            return b
    except Exception as e:
        print(f"-- {url}: {str(e)[:150]}")


# file noti dalle pagine di dati.toscana.it (per sapere se l'archivio esiste ancora)
prova("https://geoportale.lamma.rete.toscana.it/download/arw_3km_run12/arw_3km_Surface_wind_gust_surface_20251125T120000000Z/arw_3km_Surface_wind_gust_surface_20251125T120000000Z_0_0.zip", n=0, metodo="HEAD")
prova("https://geoportale.lamma.rete.toscana.it/download/arw_3km_run00/arw_3km_Dew_point_temperature_height_above_ground_20251219T000000000Z/arw_3km_Dew_point_temperature_height_above_ground_20251219T000000000Z_2_0.zip", n=0, metodo="HEAD")
for u in ["https://geoportale.lamma.rete.toscana.it/download/", "https://geoportale.lamma.rete.toscana.it/download/arw_3km_run00/",
          "https://geoportale.lamma.rete.toscana.it/geoserver/ows?service=WMS&request=GetCapabilities&version=1.3.0",
          "http://geoportale.lamma.rete.toscana.it/geoserver/ARW_3KM_RUN00/ows?service=WMS&request=GetCapabilities",
          "https://geoportale.lamma.rete.toscana.it/geoserver/web/",
          "https://dati.lamma.rete.toscana.it/thredds/catalog.xml", "http://dati.lamma.rete.toscana.it/thredds/catalog.html",
          "https://thredds.lamma.rete.toscana.it/thredds/catalog.xml", "https://www.lamma.toscana.it/opendata", "https://www.lamma.toscana.it/dati-aperti",
          "https://dati.toscana.it/organization/lamma-toscana"]:
    b = prova(u, n=1500)
    if b and b"<Name>" in b:
        nomi = re.findall(rb"<Name>([^<]+)</Name>", b)
        print("   livelli:", len(nomi), [n.decode() for n in nomi if re.search(rb"prec|rain|tp|Total", n, re.I)][:30])
    if b and b"catalogRef" in b:
        print("   catalogo:", re.findall(rb'xlink:title="([^"]+)"', b)[:40])
    if b and u.endswith("/download/") or (b and "download/arw" in u):
        print("   cartelle:", re.findall(rb'href="([^"]+)"', b)[:60])
