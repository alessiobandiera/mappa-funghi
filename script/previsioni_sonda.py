#!/usr/bin/env python3
"""Sonda: formati e archivi delle previsioni da confrontare (LaMMA WRF 3 km, modelli Open-Meteo). Solo stampa, non salva nulla."""
import io, json, re, sys, time, urllib.parse, urllib.request, zipfile
from datetime import date, timedelta

UA = {"User-Agent": "mappa-funghi/1.0 (+https://github.com/alessiobandiera/mappa-funghi)"}


def get(url, timeout=120):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read(), r.headers


# ---- LaMMA: livelli del servizio WMS (nomi delle variabili)
for run in ("ARW_3KM_RUN00", "ARW_3KM_RUN12"):
    try:
        b, _ = get(f"https://geoportale.lamma.rete.toscana.it/geoserver/{run}/ows?service=WMS&request=GetCapabilities&version=1.3.0")
        t = b.decode("utf-8", "replace")
        nomi = re.findall(r"<Layer[^>]*>\s*<Name>([^<]+)</Name>", t)
        print(run, len(nomi), "livelli")
        for n in nomi:
            if re.search(r"prec|rain|Total", n, re.I): print("   ", n)
        dims = re.findall(r'<Dimension name="time"[^>]*>([^<]{0,300})', t)
        if dims: print("   dimensione tempo (primi 300 car.):", dims[0])
    except Exception as e:
        print(run, "errore", e)

# ---- LaMMA: zip della pioggia per alcune date
cand = ["Total_precipitation_surface_1_Hour_Accumulation", "Total_precipitation_surface", "Total_precipitation_surface_Mixed_intervals_Accumulation",
        "Precipitation_rate_surface", "Large-scale_precipitation_non-convective_surface_1_Hour_Accumulation"]
oggi = date.today()
trovato = None
for giorni in (1, 2, 30, 120, 200, 365, 540):
    d = oggi - timedelta(days=giorni)
    for v in cand:
        for liv in ("0_0", "0_1", "1_0", "2_0"):
            nome = f"arw_3km_{v}_{d:%Y%m%d}T000000000Z"
            url = f"https://geoportale.lamma.rete.toscana.it/download/arw_3km_run00/{nome}/{nome}_{liv}.zip"
            try:
                req = urllib.request.Request(url, headers=UA, method="HEAD")
                with urllib.request.urlopen(req, timeout=30) as r:
                    print("OK", giorni, "giorni fa:", url, r.headers.get("Content-Length"))
                    if trovato is None: trovato = url
                    break
            except Exception as e:
                pass
        else:
            continue
        break
    else:
        print("nessun file per", d)
if trovato:
    b, h = get(trovato, timeout=300)
    print("scaricato", len(b), "byte")
    z = zipfile.ZipFile(io.BytesIO(b))
    for i in z.infolist()[:20]: print("   ", i.filename, i.file_size)
    print("   file nello zip:", len(z.infolist()))
    first = z.infolist()[0]
    data = z.read(first)
    print("   inizio del primo file:", data[:16])
    open("/tmp/lamma_primo", "wb").write(data)
    try:
        import rasterio
        with rasterio.open("/tmp/lamma_primo") as r:
            print("   rasterio:", r.driver, r.count, "bande", r.width, "x", r.height, r.crs, r.transform, r.nodata)
            print("   tags:", dict(list(r.tags().items())[:10]))
            for k in range(1, min(r.count, 4) + 1): print("   banda", k, r.tags(k), r.descriptions[k - 1])
    except Exception as e:
        print("   rasterio:", e)
    try:
        import netCDF4
        n = netCDF4.Dataset("/tmp/lamma_primo")
        print("   netCDF:", {k: v.shape for k, v in n.variables.items()})
    except Exception as e:
        print("   netCDF4:", e)

# ---- Open-Meteo: previsioni passate, quali modelli rispondono e da quando
modelli = ["best_match", "italia_meteo_arpae_icon_2i", "icon_d2", "icon_eu", "icon_seamless", "ecmwf_ifs025", "ecmwf_ifs", "ecmwf_aifs025_single",
           "meteofrance_arome_france_hd", "meteofrance_arome_france", "meteofrance_arpege_europe", "meteofrance_seamless", "gfs_seamless", "ukmo_seamless"]
var = ",".join(["precipitation"] + [f"precipitation_previous_day{k}" for k in range(1, 8)])
for m in modelli:
    for s, e in (("2025-05-01", "2025-05-03"), ("2025-10-01", "2025-10-03"), ((oggi - timedelta(days=4)).isoformat(), (oggi - timedelta(days=2)).isoformat())):
        q = urllib.parse.urlencode(dict(latitude=43.95, longitude=10.5, hourly=var, models=m, start_date=s, end_date=e, timezone="Europe/Rome"))
        try:
            b, _ = get("https://previous-runs-api.open-meteo.com/v1/forecast?" + q)
            js = json.loads(b); H = js["hourly"]
            pieni = {k: sum(x is not None for x in v) for k, v in H.items() if k != "time"}
            print(f"{m:28s} {s}: " + " ".join(f"{k.replace('precipitation','p').replace('_previous_day','d')}={n}" for k, n in pieni.items()))
        except Exception as ex:
            print(f"{m:28s} {s}: errore {str(ex)[:120]}")
        time.sleep(1)
