#!/usr/bin/env python3
"""Il sole conta a parità di indice? (dopo node script/sole_confronti.js)

Regressione logistica condizionata sugli strati ritrovamento / giorni di confronto dello stesso punto:
  caso ~ log(1+indice) + sole e pioggia del giorno e del giorno prima (quando la gente esce) + sole dei giorni prima (la domanda).
Coefficiente del sole per +10 punti di frazione di sole (es. dal 40% al 50% del sole possibile), intervallo al 95%, p del test
del rapporto di verosimiglianza. Poi: AUC di strato dell'indice e dell'indice corretto col sole, tarato su metà degli anni e
controllato sull'altra metà.
Uso: python script/sole_analisi.py
"""
import json, warnings
import numpy as np
from scipy import stats

warnings.filterwarnings("ignore")
C = json.load(open("data/gbif/sole_confronti.json"))
col = C["colonne"]; R = np.array(C["righe"], dtype=float); meta = C["strati"]
S, Y = R[:, 0].astype(int), R[:, 1].astype(int)
V = {c: R[:, k] for k, c in enumerate(col)}
paese = np.array([meta[s - 1][1] for s in S]); mese = np.array([int(meta[s - 1][0][5:7]) for s in S])
anno = np.array([int(meta[s - 1][0][:4]) for s in S]); specie = np.array([meta[s - 1][2] for s in S])
LI = np.log1p(V["indice"])
CORR = ["fr0", "fr1", "p0", "p1"]
FIN = [c for c in col if c.startswith("fr_")]


def auc(score, k):
    s, y, st = score[k], Y[k], S[k]
    o = np.argsort(st, kind="stable"); s, y, st = s[o], y[o], st[o]
    cf = np.flatnonzero(np.diff(st)) + 1; t = n = 0.0
    for a, b in zip(np.r_[0, cf], np.r_[cf, len(st)]):
        yy, ss = y[a:b], s[a:b]
        if yy.sum() != 1 or len(yy) < 2: continue
        c = ss[yy == 1][0]; r = ss[yy == 0]; t += (c > r).sum() + .5 * (c == r).sum(); n += len(r)
    return t / n if n else float("nan")


class Fit:
    pass


def fit(k, nomi):
    """Regressione logistica condizionata (un caso per strato), Newton-Raphson vettoriale."""
    X = np.column_stack([LI[k]] + [V[c][k] for c in nomi]); y, st = Y[k], S[k]
    o = np.argsort(st, kind="stable"); X, y, st = X[o], y[o], st[o]
    cf = np.flatnonzero(np.diff(st)) + 1; a0, a1 = np.r_[0, cf], np.r_[cf, len(st)]
    buoni = [(a, b) for a, b in zip(a0, a1) if y[a:b].sum() == 1 and b - a >= 2]
    m = max(b - a for a, b in buoni); G = len(buoni); p = X.shape[1]
    Z = np.zeros((G, m, p)); M = np.zeros((G, m), bool); xc = np.zeros((G, p))
    for g, (a, b) in enumerate(buoni):
        Z[g, :b - a] = X[a:b]; M[g, :b - a] = True; xc[g] = X[a:b][y[a:b] == 1][0]
    mu, sd = X.mean(0), X.std(0) + 1e-12; Z = (Z - mu) / sd; xc = (xc - mu) / sd
    beta = np.zeros(p)
    for _ in range(50):
        eta = np.where(M, Z @ beta, -np.inf); mx = eta.max(1, keepdims=True)
        w = np.exp(eta - mx); w /= w.sum(1, keepdims=True)
        xb = np.einsum("gm,gmp->gp", w, Z)
        grad = (xc - xb).sum(0)
        H = np.einsum("gm,gmp,gmq->pq", w, Z, Z) - np.einsum("gp,gq->pq", xb, xb)
        step = np.linalg.solve(H, grad); beta += step
        if np.abs(step).max() < 1e-8: break
    eta = np.where(M, Z @ beta, -np.inf); mx = eta.max(1)
    llf = float(((xc @ beta) - (mx + np.log(np.exp(eta - mx[:, None]).sum(1)))).sum())
    cov = np.linalg.inv(H)
    f = Fit(); f.params = beta / sd; f.bse = np.sqrt(np.diag(cov)) / sd; f.llf = llf
    return f


def prova(k, fin):
    base = fit(k, CORR); m = fit(k, CORR + [fin])
    b, se = m.params[-1], m.bse[-1]
    lr = 2 * (m.llf - base.llf); p = stats.chi2.sf(lr, 1)
    return b * .1, se * .1, p


GRUPPI = [("tutti", np.ones(len(S), bool)), ("Italia", paese == "IT"), ("Francia", paese == "FR"), ("Austria", paese == "AT"),
          ("Spagna", paese == "ES"), ("estate giu-ago", (mese >= 6) & (mese <= 8)), ("settembre", mese == 9), ("ott-dic", mese >= 10),
          ("anni pari", anno % 2 == 0), ("anni dispari", anno % 2 == 1), ("edulis", specie == "edulis")]
print(f"strati {len(np.unique(S))}, righe {len(S)}")
print("\nAUC di strato (0,5 = niente): indice e sole da solo")
for nome, k in GRUPPI:
    n = len(np.unique(S[k]))
    if n < 80: continue
    print(f"  {nome:15s} n={n:5d}  indice {auc(V['indice'], k):.3f}  sole del giorno {auc(V['fr0'], k):.3f}  sole 2-7 giorni prima "
          f"{auc(V['fr_2_7'], k):.3f}  8-14 {auc(V['fr_8_14'], k):.3f}  15-21 {auc(V['fr_15_21'], k):.3f}")

print("\nEffetto del sole a parità di indice (log odds per +10 punti di frazione di sole; >0 = il sole aiuta) — p")
print("  " + " " * 15 + "".join(f"{f:>22s}" for f in FIN))
for nome, k in GRUPPI:
    if len(np.unique(S[k])) < 80: continue
    riga = []
    for f in FIN:
        try:
            b, se, p = prova(k, f); riga.append(f"{b:+.3f}±{1.96 * se:.3f} p{p:.3f}")
        except Exception as e:
            riga.append("errore")
    print(f"  {nome:15s}" + "".join(f"{x:>22s}" for x in riga))

# Quanto cambierebbe la verifica: indice × correzione col sole, coefficiente stimato su metà anni e provato sull'altra metà
print("\nIndice corretto col sole (log(1+indice) + b·sole 2-14 giorni prima), tarato su metà degli anni e provato sull'altra metà")
for nome, tar, ver in [("pari → dispari", anno % 2 == 0, anno % 2 == 1), ("dispari → pari", anno % 2 == 1, anno % 2 == 0),
                       ("senza Italia → Italia", paese != "IT", paese == "IT")]:
    m0 = fit(tar, CORR); m1 = fit(tar, CORR + ["fr_2_14"])
    a, b = m1.params[0], m1.params[-1]
    s1 = a * LI + b * V["fr_2_14"]
    print(f"  {nome:22s} b={b * .1:+.3f} per +10 punti   AUC indice {auc(V['indice'], ver):.4f}  corretto {auc(s1, ver):.4f}")
