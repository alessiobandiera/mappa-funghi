#!/usr/bin/env python3
"""Analisi dei ritrovamenti GBIF: giorno del ritrovamento contro gli stessi giorni della settimana ±1-4 settimane, stesso punto.

AUC di strato: in quale frazione dei confronti il punteggio del giorno del ritrovamento è più alto di quello dei giorni di
confronto dello stesso punto (0,5 = il punteggio non dice niente, 1 = sempre più alto).
Modello: regressione logistica condizionata (stesso principio), validata tenendo fuori un paese alla volta.
Uso: python script/gbif_analisi.py   (dopo node script/gbif_confronti.js)
"""
import json, sys
import numpy as np

C = json.load(open("data/gbif/confronti.json"))
col = C["colonne"]; R = np.array(C["righe"], dtype=float)
S, Y = R[:, 0].astype(int), R[:, 1].astype(int)
meta = C["strati"]
paese = np.array([meta[s - 1][1] for s in S]); specie = np.array([meta[s - 1][2] for s in S])
mese = np.array([int(meta[s - 1][0][5:7]) for s in S]); anno = np.array([int(meta[s - 1][0][:4]) for s in S])
quota = np.array([meta[s - 1][5] or 0 for s in S], dtype=float)
lat = np.array([meta[s - 1][3] for s in S]); lon = np.array([meta[s - 1][4] for s in S])
PUNT = ["indice", "indice_quota_neutra", "indice_60mm", "fungaiolo"]
VAR = col[6:]
X = R[:, 6:]


def auc_strato(score, k=None):
    """Media sui confronti caso-riferimento dentro ogni strato (pareggi = 0,5)."""
    k = np.ones(len(S), bool) if k is None else k
    s, y, st = score[k], Y[k], S[k]
    ordine = np.argsort(st, kind="stable"); s, y, st = s[ordine], y[ordine], st[ordine]
    confini = np.flatnonzero(np.diff(st)) + 1
    tot = n = 0.0
    for a, b in zip(np.r_[0, confini], np.r_[confini, len(st)]):
        yy, ss = y[a:b], s[a:b]
        if yy.sum() != 1 or len(yy) < 2: continue
        c = ss[yy == 1][0]; r = ss[yy == 0]
        tot += (c > r).sum() + 0.5 * (c == r).sum(); n += len(r)
    return tot / n if n else float("nan"), int(n)


def ic(score, k=None, B=300, seme=1):
    """Intervallo al 90% ricampionando gli strati."""
    rng = np.random.default_rng(seme)
    k = np.ones(len(S), bool) if k is None else k
    strati = np.unique(S[k]); idx = {s: np.flatnonzero((S == s) & k) for s in strati}
    v = []
    for _ in range(B):
        pick = rng.choice(strati, len(strati))
        rows = np.concatenate([idx[s] for s in pick])
        # ristratifico con id nuovi per i duplicati
        nuovi = np.repeat(np.arange(len(pick)), [len(idx[s]) for s in pick])
        s2, y2, sc = nuovi, Y[rows], score[rows]
        tot = n = 0.0
        for j in range(len(pick)):
            m = s2 == j; yy, ss = y2[m], sc[m]
            if yy.sum() != 1: continue
            c = ss[yy == 1][0]; r = ss[yy == 0]; tot += (c > r).sum() + .5 * (c == r).sum(); n += len(r)
        v.append(tot / n)
    return np.percentile(v, [5, 95])


print(f"ritrovamenti (strati) {len(np.unique(S))}, giorni di confronto {int((Y == 0).sum())}")
print("per paese:", {p: int(((paese == p) & (Y == 1)).sum()) for p in ["IT", "FR", "CH", "AT", "ES", "SI", "HR", "DE", "PT"] if ((paese == p) & (Y == 1)).sum()})

print("\n1) PUNTEGGI: AUC di strato (0,5 = non dice niente)")
gruppi = [("tutti", None), ("Italia", paese == "IT"), ("Francia", paese == "FR"), ("Svizzera", paese == "CH"),
          ("Austria", paese == "AT"), ("Spagna", paese == "ES"), ("edulis", specie == "edulis"), ("aereus", specie == "aereus"),
          ("reticulatus (estivo)", specie == "reticulatus"), ("pinophilus", specie == "pinophilus"),
          ("giugno-luglio", mese <= 7), ("agosto-settembre", (mese >= 8) & (mese <= 9)), ("ottobre-dicembre", mese >= 10),
          ("cella sotto 600 m", quota < 600), ("cella 600-1200 m", (quota >= 600) & (quota < 1200)), ("cella sopra 1200 m", quota >= 1200)]
print(f"  {'':24s}" + "".join(f"{p:>22s}" for p in PUNT))
for nome, k in gruppi:
    kk = np.ones(len(S), bool) if k is None else k
    if (Y[kk] == 1).sum() < 15: continue
    print(f"  {nome:24s}" + "".join(f"{auc_strato(R[:, col.index(p)], kk)[0]:22.3f}" for p in PUNT) + f"   n={(Y[kk] == 1).sum()}")
lo, hi = ic(R[:, col.index("indice_quota_neutra")]); print(f"  indice (quota neutra), tutti: intervallo 90% {lo:.3f}-{hi:.3f}")
if (paese == "IT").sum():
    lo, hi = ic(R[:, col.index("indice_quota_neutra")], paese == "IT"); print(f"  indice (quota neutra), Italia: intervallo 90% {lo:.3f}-{hi:.3f}")

print("\n2) VARIABILI UNA PER UNA (AUC di strato; sopra 0,5 = più alta il giorno del ritrovamento)")
for j, n in enumerate(VAR):
    a = auc_strato(X[:, j])[0]; ai = auc_strato(X[:, j], paese == "IT")[0] if (paese == "IT").sum() else float("nan")
    print(f"  {n:16s} tutti {a:.3f}   Italia {ai:.3f}")

# ---------------------------------------------------------------- regressione logistica condizionata
try:
    from statsmodels.discrete.conditional_models import ConditionalLogit
except ImportError:
    print("\n(statsmodels non installato: niente modello)"); sys.exit()

def base(Xr):
    """Variabili del modello: le grezze più qualche forma non lineare semplice (pioggia in radice, temperature al quadrato)."""
    v = {n: Xr[:, j] for j, n in enumerate(VAR)}
    cols = {
        "rad_p_0_3": np.sqrt(v["p_0_3"]), "rad_p_4_7": np.sqrt(v["p_4_7"]), "rad_p_8_14": np.sqrt(v["p_8_14"]),
        "rad_p_15_21": np.sqrt(v["p_15_21"]), "rad_p_22_35": np.sqrt(v["p_22_35"]), "rad_max3_35": np.sqrt(v["max3_35"]),
        "giorni_da_20mm": v["giorni_da_20mm"], "tmin7": v["tmin7"], "tmin7_q": (v["tmin7"] - 10) ** 2,
        "tmax7": v["tmax7"], "tmax7_q": (v["tmax7"] - 20) ** 2, "calo": v["calo"], "suolo_u7": v["suolo_u7"],
        "suolo_u_rel": v["suolo_u_rel"], "suolo_prof7": v["suolo_prof7"], "suolo_t7": v["suolo_t7"],
        "suolo_t7_q": (v["suolo_t7"] - 14) ** 2, "umid5": v["umid5"], "vento_max5": v["vento_max5"]}
    return list(cols), np.column_stack(list(cols.values()))

nomi_m, M = base(X)
mu, sd = M.mean(0), M.std(0) + 1e-9
Z = (M - mu) / sd

def adatta(k):
    m = ConditionalLogit(Y[k], Z[k], groups=S[k]).fit(disp=0, method="bfgs", maxiter=400)
    return np.asarray(m.params)

print("\n3) MODELLO (regressione logistica condizionata), validato su dati mai visti")
paesi = [p for p in ["IT", "FR", "CH", "AT", "ES"] if ((paese == p) & (Y == 1)).sum() >= 20]
pr = np.full(len(S), np.nan)
for p in paesi:
    w = adatta(paese != p); pr[paese == p] = Z[paese == p] @ w
    print(f"  addestrato senza {p}, verificato su {p}: modello {auc_strato(Z @ w, paese == p)[0]:.3f}   indice {auc_strato(R[:, col.index('indice_quota_neutra')], paese == p)[0]:.3f}")
anni_v = anno >= 2022
w = adatta(~anni_v)
print(f"  addestrato fino al 2021, verificato 2022-2026: modello {auc_strato(Z @ w, anni_v)[0]:.3f}   indice {auc_strato(R[:, col.index('indice_quota_neutra')], anni_v)[0]:.3f}")

w = adatta(np.ones(len(S), bool))
print("\n4) PESI DEL MODELLO SU TUTTI I DATI (variabili standardizzate; + = più probabile trovarli)")
for n, b in sorted(zip(nomi_m, w), key=lambda t: -abs(t[1])):
    print(f"  {n:16s} {b:+.2f}")
json.dump({"variabili": nomi_m, "media": mu.tolist(), "dev": sd.tolist(), "pesi": w.tolist()},
          open("data/gbif/modello.json", "w"), indent=1)
