#!/usr/bin/env python3
"""Ricostruisce docs/bosco.html copiando le regole dell'indice da docs/index.html (una sola fonte delle regole).
Uso: python script/costruisci_bosco.py  (dopo ogni modifica alle specie in index.html)"""
import re
src = open("docs/index.html", encoding="utf-8").read()
i = src.index("const SPECIE = [")
j = src.index("function boscoStimato(")
j = src.index("\n}\n", j) + 3
blocco = src[i:j]
p = open("docs/bosco.html", encoding="utf-8").read()
a = p.index("/* regole dell'indice: copiate dalla mappa principale (index.html) */\n")
b = p.index("/* ---------------- dati ---------------- */")
p = p[:a] + "/* regole dell'indice: copiate dalla mappa principale (index.html) */\n" + blocco + "\n" + p[b:]
open("docs/bosco.html", "w", encoding="utf-8").write(p)
print("bosco.html aggiornato")
