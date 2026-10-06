#!/usr/bin/env python3
"""Pioggia e temperatura MISURATE dalle stazioni SIR Toscana per i casi di verifica.

Per ogni caso di data/validazione/casi.json prende le stazioni SIR vicine (pluviometri entro 25 km, al massimo 4;
termometri entro 30 km, al massimo 3), ne scarica lo storico completo dall'archivio SIR e salva la finestra
da 90 giorni prima a 15 giorni dopo la data del caso.

Uscita: data/validazione/serie_sir.json
  {"stazioni": {id: {nome, tipo, lat, lon, quota}},
   "casi": {indice_caso: {"pluvio": [[id, km, {data: mm}], ...], "termo": [[id, km, {data: [min, max]}], ...]}}}
Solo libreria standard. Il sito SIR è raggiungibile da GitHub Actions (lo usa già aggiorna.py).
"""
import json, math, re, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

UA = "mappa-funghi/1.0 (+https://github.com/alessiobandiera/mappa-funghi)"
BBOX = (42.9, 9.3, 44.75, 12.0)          # sud, ovest, nord, est: tutta la Toscana centro-nord e il crinale verso Parma
RAGGIO = {"pluvio": 25.0, "termo": 30.0}
MASSIMO = {"pluvio": 4, "termo": 3}
PRIMA, DOPO = 90, 15
OUT = "data/validazione/serie_sir.json"


def scarica(url, timeout=60, tentativi=4):
    for t in range(tentativi):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:
            if t == tentativi - 1:
                raise
            time.sleep(5 * (t + 1))


def km(a, b, c, d):
    p = math.radians
    h = math.sin(p(c - a) / 2) ** 2 + math.cos(p(a)) * math.cos(p(c)) * math.sin(p(d - b) / 2) ** 2
    return 12742 * math.asin(math.sqrt(h))


def stazioni(tipo):
    s, w, n, e = BBOX
    url = ("https://www.sir.toscana.it/open_layers/ajax_stations.php?"
           f"bbox={w},{s},{e},{n}&zoom=10&delay=3&element=&code=&regions=&basins=&models=sir"
           f"&from=1990&to=2030&types={tipo}")
    out = []
    for f in json.loads(scarica(url)).get("features", []):
        m = re.search(r"Quota staz\. slm \[m\]</b>\s*([\d.]+)", f.get("description", ""))
        out.append(dict(id=f["id"], nome=f["name"], tipo=tipo, lat=float(f["lat"]), lon=float(f["lon"]),
                        quota=float(m.group(1)) if m else None))
    return out


def storico(tipo, ident):
    idst = "pluvio" if tipo == "pluvio" else "termo"
    txt = scarica(f"https://www.sir.toscana.it/archivio/download.php?IDST={idst}&IDS={ident}", timeout=240).decode("utf-8", "replace")
    out = {}
    for riga in txt.splitlines():
        a = riga.split(";")
        if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", a[0] or ""):
            continue
        d = f"{a[0][6:]}-{a[0][3:5]}-{a[0][:2]}"
        try:
            if tipo == "pluvio":
                if len(a) > 2 and a[2].strip() == "@":      # dato mancante o non validato
                    continue
                v = float(a[1].replace(",", "."))
                if 0 <= v < 600:
                    out[d] = v
            else:
                tx, tn = float(a[1].replace(",", ".")), float(a[2].replace(",", "."))
                if -40 < tn <= tx < 50:
                    out[d] = [tn, tx]
        except (ValueError, IndexError):
            continue
    return out


def main():
    casi = json.load(open("data/validazione/casi.json"))
    elenco = {t: stazioni(t) for t in ("pluvio", "termo")}
    print({t: len(v) for t, v in elenco.items()}, "stazioni SIR nell'area", flush=True)

    # stazioni candidate per ogni caso (più di quelle che servono: alcune non avranno dati in quegli anni)
    scelte, servono = {}, set()
    for i, c in enumerate(casi):
        for t in ("pluvio", "termo"):
            v = sorted((km(c[2], c[3], s["lat"], s["lon"]), s["id"]) for s in elenco[t])
            v = [(round(d, 1), sid) for d, sid in v if d <= RAGGIO[t]][: MASSIMO[t] * 3]
            scelte[(i, t)] = v
            servono |= {(t, sid) for _, sid in v}
    print(len(servono), "storici da scaricare", flush=True)

    dati, t0 = {}, time.time()
    def uno(k):
        try:
            return k, storico(*k)
        except Exception as e:
            print("  errore", k, e, flush=True)
            return k, {}
    with ThreadPoolExecutor(max_workers=4) as ex:
        for n, (k, v) in enumerate(ex.map(uno, sorted(servono)), 1):
            dati[k] = v
            if n % 10 == 0:
                print(f"  {n}/{len(servono)} ({time.time() - t0:.0f} s)", flush=True)

    meta = {s["id"]: {k: s[k] for k in ("nome", "tipo", "lat", "lon", "quota")} for t in elenco for s in elenco[t]}
    out = {"fonte": "SIR Regione Toscana, archivio giornaliero (www.sir.toscana.it)", "finestra": [PRIMA, DOPO],
           "stazioni": {}, "casi": {}}
    for i, c in enumerate(casi):
        d0 = date.fromisoformat(c[0])
        giorni = [(d0 + timedelta(days=k)).isoformat() for k in range(-PRIMA, DOPO + 1)]
        caso = {}
        for t in ("pluvio", "termo"):
            lista = []
            for dist, sid in scelte[(i, t)]:
                serie = dati.get((t, sid), {})
                fin = {g: serie[g] for g in giorni if g in serie}
                if len(fin) >= 0.8 * len(giorni):          # almeno l'80% dei giorni presenti
                    lista.append([sid, dist, fin])
                    out["stazioni"][sid] = meta[sid]
                if len(lista) == MASSIMO[t]:
                    break
            caso[t] = lista
        if caso["pluvio"] or caso["termo"]:
            out["casi"][str(i)] = caso
    json.dump(out, open(OUT, "w"), separators=(",", ":"))
    n = len(out["casi"]); np_ = sum(1 for v in out["casi"].values() if v["pluvio"])
    print(f"casi con dati SIR: {n} su {len(casi)} (con pioggia: {np_}); stazioni usate: {len(out['stazioni'])}")


if __name__ == "__main__":
    sys.exit(main())
