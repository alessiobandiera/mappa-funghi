#!/usr/bin/env python3
"""Sentieri, forestali e accessi al bosco per le tessere a 20 m.

Gira su GitHub Actions (serve la rete: OpenStreetMap con Overpass e altimetria Terrarium).
Per ogni tessera di docs/terreno/tessere.json:
  - scarica da OpenStreetMap strade, forestali, sentieri, parcheggi e le relazioni dei sentieri escursionistici (numero CAI);
  - trova gli ACCESSI: punti dove un sentiero o una forestale entra nel bosco (bosco per almeno 60 m), entro 1 km da una
    strada carrozzabile o da un parcheggio; per ognuno distanza dall'auto, parcheggio vicino, pendenza dei primi 200 m nel bosco;
  - scrive docs/terreno/s/<id>.json:
      {"linee": [[tipo, numero, [lat, lon, lat, lon, ...]], ...],
       "accessi": [[lat, lon, tipo, numero, auto_m, pendenza_%, quota, parcheggio_m, comodita_0_100], ...],
       "parcheggi": [[lat, lon], ...]}
    tipo: 1 forestale percorribile in auto, 2 forestale o carrareccia, 3 sentiero CAI (o segnato), 4 altro sentiero
e docs/terreno/sentieri.json con data, fonte e conteggi.
Le tessere già fatte si saltano (RIFAI=1 per rifarle), così il lavoro riprende se si interrompe.
"""
import io, json, math, os, sys, time, urllib.parse, urllib.request
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(__file__))
import terreno_tessere as T          # altimetria (mosaico Terrarium) e server Overpass, gli stessi delle tessere

OUT = "docs/terreno/s"
IDX = json.load(open("docs/terreno/tessere.json"))
DLAT, DLON = IDX["dlat"], IDX["dlon"]
MARG = 50                                            # 50 celle = 1 km attorno alla tessera per strade e parcheggi
AUTO = {"motorway", "trunk", "primary", "secondary", "tertiary", "unclassified", "residential", "living_street", "service",
        "motorway_link", "trunk_link", "primary_link", "secondary_link", "tertiary_link"}
PIEDI = {"track", "path", "footway", "bridleway", "steps"}
VIETATO = {"no", "private"}
AUTO_VIETATO = {"no", "private", "forestry", "agricultural", "agricultural;forestry", "permit", "delivery"}


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def overpass(S, W, N, E):
    q = f"""[out:json][timeout:180];
(way["highway"]({S},{W},{N},{E}); node["amenity"="parking"]({S},{W},{N},{E}); way["amenity"="parking"]({S},{W},{N},{E}););
out tags geom;
relation["route"~"^(hiking|foot)$"]({S},{W},{N},{E});
out body;"""
    for t in range(8):
        srv = T.SERVER[t % len(T.SERVER)]
        try:
            t0 = time.time()
            el = json.loads(T.get(srv, urllib.parse.urlencode({"data": q}).encode(), timeout=240)).get("elements", [])
            log(f"   OSM {srv.split('/')[2]}: {len(el)} elementi in {time.time() - t0:.0f} s")
            return el
        except Exception as e:
            log(f"   OSM {srv.split('/')[2]}: {e}"); time.sleep(10 + 10 * t)
    raise RuntimeError("OpenStreetMap non risponde")


def classifica(els):
    """Divide gli elementi in linee per l'auto, linee a piedi (con tipo e numero CAI) e parcheggi."""
    numero, cai = {}, set()
    for e in els:
        if e["type"] != "relation":
            continue
        tg = e.get("tags", {})
        ref = (tg.get("ref") or "").strip()[:12]
        segnato = "CAI" in (tg.get("operator", "") + tg.get("network", "") + tg.get("name", "")).upper() or bool(ref) \
                  or tg.get("network") in ("lwn", "rwn", "nwn", "iwn")
        for m in e.get("members", []):
            if m.get("type") == "way":
                if segnato: cai.add(m["ref"])
                if ref and m["ref"] not in numero: numero[m["ref"]] = ref
    auto, piedi, park = [], [], []
    for e in els:
        tg = e.get("tags", {})
        if e["type"] == "node" and tg.get("amenity") == "parking":
            park.append((e["lat"], e["lon"])); continue
        if e["type"] != "way" or not e.get("geometry"):
            continue
        g = [(p["lat"], p["lon"]) for p in e["geometry"]]
        if tg.get("amenity") == "parking":
            park.append((sum(p[0] for p in g) / len(g), sum(p[1] for p in g) / len(g))); continue
        hw = tg.get("highway")
        acc, mv = tg.get("access", ""), tg.get("motor_vehicle", tg.get("motorcar", ""))
        in_auto = (hw in AUTO and acc not in VIETATO and mv not in AUTO_VIETATO and not (hw == "service" and tg.get("service") == "driveway")) or \
                  (hw == "track" and tg.get("tracktype") in ("grade1", "grade2") and acc not in AUTO_VIETATO and mv not in AUTO_VIETATO)
        if in_auto:
            auto.append(g)
        if hw in PIEDI and acc not in VIETATO and tg.get("foot") not in VIETATO:
            if e["id"] in cai or tg.get("sac_scale") or tg.get("cai_scale"):
                tipo = 3
            elif hw == "track":
                tipo = 1 if in_auto else 2
            else:
                tipo = 4
            piedi.append((tipo, numero.get(e["id"], ""), g))
    return auto, piedi, park


def campiona(g, passo=10.0):
    """Punti lungo la linea ogni `passo` metri."""
    out = [g[0]]
    for (a, b), (c, d) in zip(g[:-1], g[1:]):
        dy = (c - a) * 111320; dx = (d - b) * 111320 * math.cos(math.radians(a))
        L = math.hypot(dx, dy); n = max(1, int(L // passo))
        for k in range(1, n + 1):
            t = k / n; out.append((a + (c - a) * t, b + (d - b) * t))
    return out


def semplifica(g, tol=6.0):
    """Douglas-Peucker in metri."""
    if len(g) < 3:
        return g
    lat0 = math.radians(g[0][0])
    P = np.array([((p[1] - g[0][1]) * 111320 * math.cos(lat0), (p[0] - g[0][0]) * 111320) for p in g])
    keep = np.zeros(len(g), bool); keep[0] = keep[-1] = True
    pila = [(0, len(g) - 1)]
    while pila:
        i, j = pila.pop()
        if j <= i + 1: continue
        a, b = P[i], P[j]; ab = b - a; L = np.hypot(*ab)
        seg = P[i + 1:j]
        d = np.abs(ab[0] * (seg[:, 1] - a[1]) - ab[1] * (seg[:, 0] - a[0])) / L if L > 0 else np.hypot(*(seg - a).T)
        k = int(np.argmax(d))
        if d[k] > tol:
            keep[i + 1 + k] = True; pila += [(i, i + 1 + k), (i + 1 + k, j)]
    return [p for p, k in zip(g, keep) if k]


def tessera(m):
    ny, nx = m["righe"], m["colonne"]
    N, Wc = m["nord"], m["ovest"]
    b = np.asarray(Image.open(f"docs/terreno/t/{m['id']}_b.png").convert("RGB"))
    bosco = b[..., 2] > 0
    pad = MARG * max(DLAT, DLON) * 1.05
    els = overpass(m["sud"] - pad, m["ovest"] - pad, m["nord"] + pad, m["est"] + pad)
    auto, piedi, park = classifica(els)

    # distanza dalla strada carrozzabile più vicina (o da un parcheggio), su una griglia con 1 km di margine
    H, W = ny + 2 * MARG, nx + 2 * MARG
    img = Image.new("L", (W, H), 0); dr = ImageDraw.Draw(img)
    xy = lambda la, lo: ((lo - Wc) / DLON + MARG, (N - la) / DLAT + MARG)
    for g in auto:
        dr.line([xy(*p) for p in g], fill=1, width=1)
    for la, lo in park:
        x, y = xy(la, lo); dr.ellipse([x - 1, y - 1, x + 1, y + 1], fill=1)
    strada = np.asarray(img) > 0
    dist_auto = ndimage.distance_transform_edt(~strada) * T.RES if strada.any() else np.full((H, W), 1e6)
    imgp = Image.new("L", (W, H), 0); drp = ImageDraw.Draw(imgp)
    for la, lo in park:
        x, y = xy(la, lo); drp.ellipse([x - 1, y - 1, x + 1, y + 1], fill=1)
    pk = np.asarray(imgp) > 0
    dist_park = ndimage.distance_transform_edt(~pk) * T.RES if pk.any() else np.full((H, W), 1e6)

    def cella(la, lo):
        r = int((N - la) / DLAT); c = int((lo - Wc) / DLON)
        return r, c

    def nel_bosco(la, lo):
        r, c = cella(la, lo)
        return bosco[r, c] if 0 <= r < ny and 0 <= c < nx else None

    cand = []
    for tipo, ref, g in piedi:
        pts = campiona(g)
        F = [nel_bosco(*p) for p in pts]
        n = len(pts)
        def ingresso(k, verso):
            """k = primo punto nel bosco; verso = +1 o -1: il bosco deve continuare per almeno 60 m in quel verso."""
            seq = [F[k + verso * j] for j in range(0, 7) if 0 <= k + verso * j < n]
            return len(seq) == 7 and all(x is not None and bool(x) for x in seq)
        def aperto(k, verso):
            """prima dell'ingresso almeno 60 m fuori dal bosco (o l'inizio del percorso): è un margine vero, non una radura"""
            seq = [F[k + verso * j] for j in range(0, 7) if 0 <= k + verso * j < n]
            return all(x is not None and not bool(x) for x in seq)
        for k in range(1, n):
            a, b_ = F[k - 1], F[k]
            if a is None or b_ is None:
                continue
            if not a and b_ and ingresso(k, +1) and aperto(k - 1, -1):
                cand.append((tipo, ref, pts, k, +1))
            if a and not b_ and ingresso(k - 1, -1) and aperto(k, +1):
                cand.append((tipo, ref, pts, k - 1, -1))
        # linea che parte già nel bosco vicino a una strada (es. forestale che si stacca dalla provinciale nel bosco)
        for k, verso in ((0, +1), (n - 1, -1)):
            if F[k] and ingresso(k, verso):
                r, c = cella(*pts[k])
                if dist_auto[r + MARG, c + MARG] <= 60:
                    cand.append((tipo, ref, pts, k, verso))

    acc = []
    per_linea = {}
    for tipo, ref, pts, k, verso in cand:
        la, lo = pts[k]
        r, c = cella(la, lo)
        da = float(dist_auto[r + MARG, c + MARG])
        if da > 1000:
            continue
        dp = float(dist_park[r + MARG, c + MARG])
        tratto = [pts[k + verso * j] for j in range(0, 21) if 0 <= k + verso * j < len(pts)]
        z = T.quota(np.array([p[0] for p in tratto]), np.array([p[1] for p in tratto]))
        dz = np.abs(np.diff(z)).sum(); lun = 10.0 * (len(tratto) - 1)
        pend = float(100 * dz / lun) if lun else 0.0
        fa = min(1, max(.3, 1 - (da - 100) / 1400)); fp = min(1, max(.3, 1 - (pend - 10) / 30))
        per_linea.setdefault(id(pts), []).append([round(la, 5), round(lo, 5), tipo, ref, int(round(da)), round(pend, 1),
                    int(round(float(z[0]))), int(round(min(dp, 9999))), int(round(100 * fa * fp))])
    # per ogni percorso: gli ingressi entro 300 m dall'auto, oppure solo il più vicino all'auto
    for v in per_linea.values():
        vicini = [a for a in v if a[4] <= 300]
        acc += vicini if vicini else [min(v, key=lambda a: a[4])]
    # un accesso ogni ~120 m: si tiene il più comodo
    acc.sort(key=lambda a: -a[8])
    scelti = []
    for a in acc:
        if all((a[0] - s[0]) ** 2 + ((a[1] - s[1]) * 0.72) ** 2 > (120 / 111320) ** 2 for s in scelti):
            scelti.append(a)

    dentro = lambda g: any(m["sud"] <= p[0] <= m["nord"] and m["ovest"] <= p[1] <= m["est"] for p in g)
    linee = []
    for tipo, ref, g in piedi:
        if not dentro(g): continue
        s = semplifica(g)
        linee.append([tipo, ref, [round(v, 5) for p in s for v in p]])
    parcheggi = [[round(la, 5), round(lo, 5)] for la, lo in park if m["sud"] <= la <= m["nord"] and m["ovest"] <= lo <= m["est"]]
    return {"linee": linee, "accessi": scelti, "parcheggi": parcheggi}


def main():
    os.makedirs(OUT, exist_ok=True)
    T.log = log                                       # non sovrascrivere il registro delle tessere
    T.prepara_mosaico()
    t0, limite = time.time(), float(os.environ.get("MINUTI_MAX", "100")) * 60
    solo = os.environ.get("SOLO_TESSERE")
    conta = {}
    for m in IDX["tessere"]:
        if solo and m["id"] not in solo.split(","): continue
        f = f"{OUT}/{m['id']}.json"
        if os.path.exists(f) and not os.environ.get("RIFAI"):
            d = json.load(open(f)); conta[m["id"]] = [len(d["linee"]), len(d["accessi"])]; continue
        if time.time() - t0 > limite:
            log("tempo finito, si riprende al prossimo avvio"); break
        log(f"tessera {m['id']}")
        try:
            d = tessera(m)
        except Exception as e:
            log(f"   {m['id']}: {e}"); continue
        json.dump(d, open(f, "w"), separators=(",", ":"))
        conta[m["id"]] = [len(d["linee"]), len(d["accessi"])]
        log(f"   {len(d['linee'])} percorsi, {len(d['accessi'])} accessi, {len(d['parcheggi'])} parcheggi, {os.path.getsize(f) // 1024} KB")
        time.sleep(2)
    json.dump({"aggiornato": time.strftime("%Y-%m-%d"), "fonte": "© contributori OpenStreetMap (ODbL)",
               "tessere": conta}, open("docs/terreno/sentieri.json", "w"), indent=1)
    log("fatte", len(conta), "tessere su", len(IDX["tessere"]))


if __name__ == "__main__":
    main()
