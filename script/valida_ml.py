#!/usr/bin/env python3
"""Indice attuale contro un primo modello statistico, sui casi di verifica.

Dati: data/validazione/variabili_om.json (indice, Fungaiolo e variabili meteo per caso, da Open-Meteo)
      data/validazione/casi.json (fonte e zona dei casi)
Validazione: un anno alla volta fuori (leave-one-year-out): casi dello stesso evento non finiscono sia
nell'addestramento sia nella verifica.
Uso: python script/valida_ml.py [file_casi_originali.json]   (facoltativo: per separare i casi vecchi dai nuovi)
"""
import json, sys
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import roc_auc_score

V = json.load(open("data/validazione/variabili_om.json"))
CASI = json.load(open("data/validazione/casi.json"))
nomi = V["fonte"].split("colonne: ")[1].split(",")[4:]
R = np.array(V["righe"], dtype=float)
ci, y, indice, fung, X = R[:, 0].astype(int), R[:, 1].astype(int), R[:, 2], R[:, 3], R[:, 4:]
anni = np.array([int(CASI[i][0][:4]) for i in ci])
url = [CASI[i][6] for i in ci]
lat, lon = np.array([CASI[i][2] for i in ci]), np.array([CASI[i][3] for i in ci])
forum = np.array([("fungodiborgotaro.com/forum" in u or "funghiemicologia" in u) for u in url])
vecchi = None
if len(sys.argv) > 1:
    orig = {(c[0], c[6]) for c in json.load(open(sys.argv[1]))}
    vecchi = np.array([(CASI[i][0], CASI[i][6]) in orig for i in ci])

auc = lambda s, k=None: roc_auc_score(y if k is None else y[k], s if k is None else s[k])
rng = np.random.default_rng(1)
def ic(s, k=None):
    k = np.arange(len(y)) if k is None else np.where(k)[0]
    a = []
    for _ in range(1000):
        b = rng.choice(k, len(k))
        if len(set(y[b])) == 2: a.append(roc_auc_score(y[b], s[b]))
    return np.percentile(a, [5, 95])

print(f"casi {len(y)}: positivi (A, D) {y.sum()}, negativi (S, N) {len(y) - y.sum()}")
print("\n1) INDICE ATTUALE (nessun addestramento) — AUC: 0,5 = a caso, 1 = perfetto")
gruppi = [("tutti", None), ("da giornali e blog", ~forum), ("dai forum", forum)]
if vecchi is not None:
    gruppi += [("casi originali (su cui era tarato)", vecchi), ("casi nuovi di oggi", ~vecchi)]
zona_lu = (lat >= 43.7) & (lat <= 44.45) & (lon >= 9.85) & (lon <= 11.0)
gruppi += [("Lucchesia, Garfagnana, Lunigiana, Abetone", zona_lu), ("Val Taro e Parma ovest", (lat > 44.36) & (lon < 10.0))]
for nome, k in gruppi:
    kk = np.ones(len(y), bool) if k is None else k
    if len(set(y[kk])) < 2: continue
    lo, hi = ic(indice, kk)
    print(f"  {nome:42s} n={kk.sum():3d}  indice {auc(indice, kk):.3f} ({lo:.2f}-{hi:.2f})   Fungaiolo {auc(fung, kk):.3f}")

print("\n2) MODELLI STATISTICI (un anno alla volta tenuto fuori)")
modelli = {
    "regressione logistica": lambda: make_pipeline(StandardScaler(), LogisticRegression(C=0.3, max_iter=3000)),
    "gradient boosting, alberi piccoli": lambda: HistGradientBoostingClassifier(max_depth=2, learning_rate=0.05, max_iter=150,
                                                                               min_samples_leaf=12, l2_regularization=1.0),
}
prev = {}
for nome, mk in modelli.items():
    pr = np.zeros(len(y))
    for a in sorted(set(anni)):
        tr, te = anni != a, anni == a
        m = mk().fit(X[tr], y[tr]); pr[te] = m.predict_proba(X[te])[:, 1]
    prev[nome] = pr
    lo, hi = ic(pr)
    print(f"  {nome:42s} AUC {auc(pr):.3f} ({lo:.2f}-{hi:.2f})")
rk = lambda v: np.argsort(np.argsort(v)) / (len(v) - 1)
for nome, pr in prev.items():
    comb = (rk(indice) + rk(pr)) / 2
    print(f"  indice + {nome:33s} AUC {auc(comb):.3f}")

# regressione con l'indice tra le variabili
Xi = np.column_stack([X, indice])
pr = np.zeros(len(y))
for a in sorted(set(anni)):
    tr, te = anni != a, anni == a
    pr[te] = modelli["regressione logistica"]().fit(Xi[tr], y[tr]).predict_proba(Xi[te])[:, 1]
print(f"  {'regressione con l indice come variabile':42s} AUC {auc(pr):.3f}")

print("\n3) COSA CONTA DI PIÙ (regressione su tutti i casi, variabili standardizzate; + = più funghi)")
m = modelli["regressione logistica"]().fit(X, y)
for n, w in sorted(zip(nomi, m[-1].coef_[0]), key=lambda t: -abs(t[1])):
    print(f"  {n:20s} {w:+.2f}")

print("\n4) VARIABILI UNA PER UNA (AUC; sotto 0,5 = più alta, meno funghi)")
for j, n in enumerate(nomi):
    print(f"  {n:20s} {auc(X[:, j]):.3f}")

print("\n5) INDICE ATTUALE PER ANNO")
for a in sorted(set(anni)):
    k = anni == a
    if len(set(y[k])) == 2 and k.sum() >= 6:
        print(f"  {a}: n={k.sum():3d}  AUC {auc(indice, k):.2f}")
