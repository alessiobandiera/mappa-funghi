#!/usr/bin/env python3
"""Sole e nuvole (Open-Meteo archive, ERA5) per verificare se le giornate senza sole rallentano la buttata.

Solo per le verifiche, non tocca la mappa. Stessi punti e stessi giorni dei dati già usati per le verifiche:
  - casi della Lucchesia e dintorni (data/validazione/serie.json)  -> data/validazione/sole.json  {"casi": {ci: {s, R}}}
  - ritrovamenti GBIF, gruppi cella 0,1° e anno di data/gbif/meteo   -> data/gbif/sole/<anno>.json   {gruppo: {s, R}}
Righe R (una per giorno, dal giorno s): [ore di sole, radiazione MJ/m², nuvolosità media %] (None se manca).
Riprende da dove era arrivato; si ferma da solo al limite giornaliero di Open-Meteo o quando finisce il tempo (MINUTI) e salva.
Ordine GBIF: prima i paesi più simili ai nostri boschi (PRIMA_PAESI), poi gli altri.
"""
import http.client, json, os, subprocess, sys, time, urllib.parse
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(__file__))
from gbif_meteo import gruppi  # noqa: E402  stesso ordine del meteo dei punti

UA = {"User-Agent": "mappa-funghi (github.com/alessiobandiera/mappa-funghi)"}
VAR = ["sunshine_duration", "shortwave_radiation_sum", "cloud_cover_mean"]
DIR_G, FILE_C = "data/gbif/sole", "data/validazione/sole.json"
LOG = "data/gbif/sole_log.txt"     # i log di Actions non si leggono dalla sessione: avanzamento e attese salvati qui


def log(*a):
    riga = time.strftime("%Y-%m-%d %H:%M:%S ") + " ".join(str(x) for x in a)
    print(riga, flush=True)
    with open(LOG, "a") as f:
        f.write(riga + "\n")


class Basta(Exception):
    pass


# una sola connessione tenuta aperta: dal registro del 21/10 quasi tutto il tempo se ne andava in strette di mano TLS
# scadute (90 s l'una) aprendo una connessione nuova per ogni richiesta
_conn = None


def _get(path):
    global _conn
    if _conn is None:
        _conn = http.client.HTTPSConnection("archive-api.open-meteo.com", timeout=30)
    try:
        _conn.request("GET", path, headers=UA)
        r = _conn.getresponse()
        return r.status, r.read()
    except Exception:
        try:
            _conn.close()
        except Exception:
            pass
        _conn = None
        raise


def scarica(la, lo, s, e, var):
    q = urllib.parse.urlencode(dict(latitude=la, longitude=lo, start_date=s, end_date=e, daily=",".join(var), timezone="auto"))
    for t in range(6):
        try:
            stato, corpo = _get("/v1/archive?" + q)
        except Exception as ex:
            log("errore", repr(ex)[:150]); time.sleep(3 * (t + 1)); continue
        if stato == 200:
            D = json.loads(corpo)["daily"]
            n = len(D["time"])
            col = [D.get(v, [None] * n) for v in VAR]
            conv = [lambda x: round(x / 3600, 2), lambda x: round(x, 2), lambda x: round(x)]
            return {"s": D["time"][0], "R": [[(conv[j](col[j][i]) if col[j][i] is not None else None) for j in range(len(VAR))]
                                             for i in range(n)]}
        testo = corpo.decode("utf-8", "replace")[:300]
        if stato == 429:
            if "Daily" in testo:
                raise Basta("limite giornaliero di Open-Meteo raggiunto")
            attesa = 65 if "Minutely" in testo else 900
            log(f"429 ({testo[:120]}): aspetto {attesa} s"); time.sleep(attesa)
        elif stato == 400 and "cloud_cover_mean" in testo and "cloud_cover_mean" in var:
            return None   # variabile non disponibile: lo dice il chiamante
        else:
            log("errore", stato, testo[:150]); time.sleep(5 * (t + 1))
    raise RuntimeError(f"Open-Meteo non risponde per {la},{lo} {s}..{e}")


def commit(msg):
    if not os.environ.get("GITHUB_ACTIONS"):
        return
    cmd = (f'git add {DIR_G} {FILE_C} {LOG} && git commit -q -m "{msg} [skip ci]" && '
           'git pull -q --rebase -X theirs origin main && git push -q origin HEAD:main')
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print("  salvataggio:", "ok" if r.returncode == 0 else (r.stderr or r.stdout)[-200:], flush=True)


def main():
    global VAR
    t0, limite = time.time(), float(os.environ.get("MINUTI", "300")) * 60
    # la nuvolosità media giornaliera c'è? (prova su un giorno solo)
    if scarica(43.95, 10.6, "2025-10-01", "2025-10-02", VAR) is None:
        VAR = VAR[:2]; print("nuvolosità media non disponibile: solo sole e radiazione", flush=True)
    print("variabili:", VAR, flush=True)

    # 1) casi della Lucchesia (pochi, prima)
    C = json.load(open(FILE_C)) if os.path.exists(FILE_C) else {"variabili": VAR, "casi": {}}
    S = json.load(open("data/validazione/serie.json"))["casi"]
    for c in S:
        k = str(c["ci"])
        if k in C["casi"] or not c["serie"]:
            continue
        C["casi"][k] = scarica(c["lat"], c["lon"], c["serie"][0]["d"], c["serie"][-1]["d"], VAR); time.sleep(0.3)
    os.makedirs(os.path.dirname(FILE_C), exist_ok=True)
    json.dump(C, open(FILE_C, "w"), separators=(",", ":"))
    print(f"casi della Lucchesia: {len(C['casi'])}/{len(S)}", flush=True)

    # 2) gruppi GBIF, stessi giorni del meteo dei punti
    M = {}
    for f in os.listdir("data/gbif/meteo"):
        M[f[:-5]] = json.load(open(f"data/gbif/meteo/{f}"))
    G = {}
    if os.path.isdir(DIR_G):
        for f in os.listdir(DIR_G):
            G[f[:-5]] = json.load(open(f"{DIR_G}/{f}"))

    def salva(msg=None):
        os.makedirs(DIR_G, exist_ok=True)
        for anno, v in G.items():
            json.dump(v, open(f"{DIR_G}/{anno}.json", "w"), separators=(",", ":"))
        if msg:
            commit(msg)

    fatti = sum(len(v) for v in G.values()); nuovi = 0; ultimo = time.time()
    tutti = [k for k, _ in gruppi() if k.split(",")[2] in M and k in M[k.split(",")[2]]]
    log(f"inizio: gruppi GBIF {len(tutti)}, già scaricati {fatti}")
    try:
        for k in tutti:
            la, lo, anno = k.split(",")
            if k in G.get(anno, {}):
                continue
            if time.time() - t0 > limite:
                print("tempo finito"); break
            m = M[anno][k]
            e = (date.fromisoformat(m["s"]) + timedelta(days=len(m["R"]) - 1)).isoformat()
            try:
                G.setdefault(anno, {})[k] = scarica(float(la), float(lo), m["s"], e, VAR); nuovi += 1
            except RuntimeError as ex:
                log(ex); continue
            time.sleep(0.25)
            if nuovi % 50 == 0:
                log(f"{nuovi} nuovi gruppi ({(time.time() - t0) / 60:.0f} min)")
            if time.time() - ultimo > 900:
                salva("Sole dei punti GBIF: salvataggio intermedio"); ultimo = time.time()
    except Basta as ex:
        log(ex)
    salva()
    log(f"fine: {nuovi} nuovi, totale {sum(len(v) for v in G.values())} su {len(tutti)}")


if __name__ == "__main__":
    sys.exit(main())
