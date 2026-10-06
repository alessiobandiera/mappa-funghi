#!/usr/bin/env python3
"""Osservazioni pubbliche di porcini da GBIF (in gran parte iNaturalist): data al giorno e posizione GPS.

Specie: Boletus edulis, aereus, reticulatus (= aestivalis), pinophilus.
Area: Europa centro-meridionale (lat 36-48,5, lon -10-20: Iberia, Francia, Alpi, Italia, Balcani occidentali).
Filtri: osservazioni umane, data al giorno tra giugno e dicembre, dal 2005, incertezza della posizione <= 2 km (o non dichiarata).
Doppioni: stessa specie, stesso giorno, punti a meno di ~100 m -> una sola osservazione.
Chi ha fatto l'osservazione non viene salvato (solo un codice anonimo per riconoscere i doppioni dello stesso utente).

Uscita: data/gbif/porcini.json  {"fonte", "colonne", "righe": [[data, lat, lon, specie, paese, incertezza_m, utente]]}
Solo libreria standard. GBIF chiede di citare i dataset: la licenza e il DOI della ricerca sono nel campo "fonte".
"""
import hashlib, json, os, sys, time, urllib.parse, urllib.request
from collections import Counter

UA = {"User-Agent": "mappa-funghi (github.com/alessiobandiera/mappa-funghi)"}
SPECIE = {"Boletus edulis": "edulis", "Boletus aereus": "aereus", "Boletus reticulatus": "reticulatus", "Boletus pinophilus": "pinophilus"}
OUT = "data/gbif/porcini.json"


def get(url, tent=5):
    for t in range(tent):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r:
                return json.loads(r.read())
        except Exception as e:
            if t == tent - 1:
                raise
            time.sleep(5 * (t + 1))


def main():
    righe, visti, conta = [], set(), Counter()
    for nome, breve in SPECIE.items():
        m = get("https://api.gbif.org/v1/species/match?" + urllib.parse.urlencode({"name": nome, "kingdom": "Fungi"}))
        key = m.get("usageKey"); print(nome, "->", key, m.get("scientificName"), m.get("status"), flush=True)
        if not key:
            continue
        off, tot = 0, None
        while True:
            q = [("taxonKey", key), ("hasCoordinate", "true"), ("hasGeospatialIssue", "false"),
                 ("decimalLatitude", "36,48.5"), ("decimalLongitude", "-10,20"), ("year", "2005,2026"), ("month", "6,12"),
                 ("basisOfRecord", "HUMAN_OBSERVATION"), ("occurrenceStatus", "PRESENT"), ("limit", "300"), ("offset", str(off))]
            js = get("https://api.gbif.org/v1/occurrence/search?" + urllib.parse.urlencode(q))
            tot = js.get("count", 0)
            for o in js.get("results", []):
                d = (o.get("eventDate") or "")[:10]
                if len(d) != 10 or not o.get("day"):
                    conta["senza giorno"] += 1; continue
                inc = o.get("coordinateUncertaintyInMeters")
                if inc is not None and inc > 2000:
                    conta["posizione imprecisa"] += 1; continue
                la, lo = round(o["decimalLatitude"], 5), round(o["decimalLongitude"], 5)
                k = (breve, d, round(la, 3), round(lo, 3))
                if k in visti:
                    conta["doppioni"] += 1; continue
                visti.add(k)
                utente = hashlib.sha1((o.get("recordedBy") or o.get("identifiedBy") or "").encode()).hexdigest()[:8]
                righe.append([d, la, lo, breve, o.get("countryCode") or "", int(inc) if inc is not None else None, utente])
            off += 300
            if js.get("endOfRecords") or off >= min(tot, 99900):
                break
            time.sleep(0.3)
        print(f"  {breve}: {tot} trovate su GBIF, tenute finora {len(righe)}", flush=True)
    righe.sort()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump({"fonte": "GBIF.org (osservazioni da iNaturalist e altri dataset, licenze CC0/CC BY/CC BY-NC), scaricate il "
                        + time.strftime("%Y-%m-%d") + " con l'API di ricerca; per citare: GBIF Occurrence Download",
               "colonne": ["data", "lat", "lon", "specie", "paese", "incertezza_m", "utente"], "righe": righe},
              open(OUT, "w"), separators=(",", ":"))
    print("tenute", len(righe), dict(conta))
    print("per paese", Counter(r[4] for r in righe).most_common(15))
    print("per specie", Counter(r[3] for r in righe))
    print("per anno", sorted(Counter(r[0][:4] for r in righe).items()))


if __name__ == "__main__":
    sys.exit(main())
