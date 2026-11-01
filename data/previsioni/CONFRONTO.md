# Previsioni di pioggia contro pioggia misurata (stazioni SIR)

Periodo 2025-04-15 – 2026-10-31. Stazioni: 15. Modelli: Open-Meteo automatico (usato fino al 9/10/2026), ECMWF AIFS (IA), ECMWF IFS, GFS (USA), ICON-D2 2 km, ICON (DWD), ICON-2I ItaliaMeteo 2 km, AROME France HD 1,5 km.
Giorno D = pioggia dalle 9 del giorno prima alle 9 di D (come l'archivio SIR). Ogni tabella usa gli stessi giorni e stazioni per tutti i modelli con quell'anticipo. CSI: 1 = perfetto, 0 = mai preso.

## Verdetto sulla scelta attuale (media AROME + ECMWF + AIFS + ICON-2I)

Pioggia utile per la buttata (≥13 mm in 3 giorni), CSI della scelta attuale e della migliore alternativa per anticipo:

- anticipo 0: 0.69 (migliore alternativa media di AROME, ECMWF, AIFS, ICON-2I, ICON, GFS 0.70)
- anticipo 1: 0.66 (migliore alternativa media di AROME, ECMWF, AIFS, ICON-2I, ICON, GFS 0.67)
- anticipo 2: 0.63 (migliore alternativa media dei modelli disponibili 0.64)
- anticipo 3: 0.58 (migliore alternativa media di AROME, ECMWF, AIFS, ICON-2I, ICON, GFS 0.59)
- anticipo 4: 0.57 (migliore alternativa ECMWF AIFS (IA) 0.58)
- anticipo 5: 0.57 (migliore alternativa ECMWF AIFS (IA) 0.57)
- anticipo 6: 0.51 (migliore alternativa ECMWF AIFS (IA) 0.51)
- anticipo 7: 0.46 (migliore alternativa ECMWF AIFS (IA) 0.47)

**La scelta attuale resta la migliore** (o entro 0,03 dalla migliore) a tutti gli anticipi.

## Anticipo 0 giorni (8274 giorni-stazione)

| modello | ≥3 mm CSI | presi | falsi allarmi | prev./oss. | ≥20 mm CSI | presi | falsi | pioggia utile 3 gg CSI | presi | falsi | errore mm | scarto mm |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| media AROME + ECMWF + ICON-2I + ICON | 0.65 | 0.86 | 0.28 | 1.20 | 0.51 | 0.60 | 0.23 | 0.69 | 0.85 | 0.21 | 2.51 | -0.42 |
| media di AROME, ECMWF, AIFS, ICON-2I, ICON, GFS | 0.64 | 0.88 | 0.30 | 1.27 | 0.50 | 0.59 | 0.22 | 0.70 | 0.87 | 0.22 | 2.57 | -0.41 |
| media dei modelli disponibili | 0.64 | 0.85 | 0.28 | 1.18 | 0.45 | 0.51 | 0.20 | 0.68 | 0.81 | 0.19 | 2.58 | -0.76 |
| media AROME + ECMWF + ICON-2I | 0.63 | 0.88 | 0.31 | 1.27 | 0.53 | 0.68 | 0.29 | 0.69 | 0.88 | 0.24 | 2.62 | +0.04 |
| media AROME + ECMWF + AIFS + ICON-2I + GFS | 0.63 | 0.89 | 0.32 | 1.32 | 0.52 | 0.64 | 0.27 | 0.70 | 0.89 | 0.23 | 2.65 | -0.13 |
| media AROME + ECMWF + AIFS + ICON-2I | 0.63 | 0.89 | 0.32 | 1.30 | 0.52 | 0.66 | 0.28 | 0.69 | 0.88 | 0.24 | 2.64 | -0.04 |
| AROME France HD 1,5 km | 0.62 | 0.84 | 0.30 | 1.20 | 0.53 | 0.76 | 0.37 | 0.68 | 0.88 | 0.25 | 3.04 | +0.88 |
| ECMWF AIFS (IA) | 0.58 | 0.88 | 0.38 | 1.41 | 0.42 | 0.54 | 0.35 | 0.63 | 0.83 | 0.27 | 3.06 | -0.30 |
| ECMWF IFS | 0.56 | 0.82 | 0.36 | 1.29 | 0.41 | 0.56 | 0.39 | 0.62 | 0.78 | 0.26 | 3.29 | -0.14 |
| GFS (USA) | 0.55 | 0.82 | 0.37 | 1.30 | 0.37 | 0.47 | 0.35 | 0.59 | 0.76 | 0.27 | 3.20 | -0.46 |
| ICON-2I ItaliaMeteo 2 km | 0.54 | 0.70 | 0.29 | 0.98 | 0.38 | 0.51 | 0.40 | 0.56 | 0.70 | 0.27 | 3.32 | -0.61 |
| Open-Meteo automatico (usato fino al 9/10/2026) | 0.49 | 0.57 | 0.22 | 0.72 | 0.29 | 0.34 | 0.33 | 0.47 | 0.53 | 0.20 | 3.26 | -1.79 |
| ICON-D2 2 km | 0.49 | 0.56 | 0.22 | 0.71 | 0.28 | 0.33 | 0.34 | 0.46 | 0.52 | 0.20 | 3.27 | -1.82 |
| ICON (DWD) | 0.49 | 0.56 | 0.22 | 0.71 | 0.28 | 0.33 | 0.34 | 0.46 | 0.52 | 0.20 | 3.27 | -1.82 |

## Anticipo 1 giorno (7764 giorni-stazione)

| modello | ≥3 mm CSI | presi | falsi allarmi | prev./oss. | ≥20 mm CSI | presi | falsi | pioggia utile 3 gg CSI | presi | falsi | errore mm | scarto mm |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| media AROME + ECMWF + ICON-2I + ICON | 0.63 | 0.82 | 0.27 | 1.12 | 0.48 | 0.57 | 0.25 | 0.64 | 0.77 | 0.20 | 2.74 | -0.85 |
| media dei modelli disponibili | 0.63 | 0.82 | 0.26 | 1.11 | 0.40 | 0.45 | 0.21 | 0.65 | 0.74 | 0.16 | 2.84 | -1.24 |
| media di AROME, ECMWF, AIFS, ICON-2I, ICON, GFS | 0.63 | 0.84 | 0.29 | 1.18 | 0.47 | 0.55 | 0.24 | 0.67 | 0.80 | 0.20 | 2.81 | -0.82 |
| media AROME + ECMWF + AIFS + ICON-2I + GFS | 0.62 | 0.86 | 0.31 | 1.24 | 0.49 | 0.60 | 0.28 | 0.66 | 0.83 | 0.23 | 2.85 | -0.49 |
| media AROME + ECMWF + ICON-2I | 0.62 | 0.83 | 0.29 | 1.17 | 0.50 | 0.64 | 0.30 | 0.65 | 0.81 | 0.24 | 2.82 | -0.30 |
| media AROME + ECMWF + AIFS + ICON-2I | 0.62 | 0.86 | 0.31 | 1.23 | 0.50 | 0.63 | 0.30 | 0.66 | 0.84 | 0.24 | 2.84 | -0.32 |
| AROME France HD 1,5 km | 0.60 | 0.78 | 0.28 | 1.09 | 0.48 | 0.65 | 0.35 | 0.64 | 0.79 | 0.22 | 3.15 | +0.16 |
| ECMWF IFS | 0.57 | 0.81 | 0.33 | 1.21 | 0.39 | 0.51 | 0.37 | 0.59 | 0.74 | 0.25 | 3.39 | -0.57 |
| ECMWF AIFS (IA) | 0.57 | 0.89 | 0.39 | 1.45 | 0.43 | 0.56 | 0.34 | 0.63 | 0.83 | 0.28 | 3.30 | -0.36 |
| ICON-2I ItaliaMeteo 2 km | 0.54 | 0.67 | 0.27 | 0.92 | 0.37 | 0.51 | 0.43 | 0.55 | 0.70 | 0.27 | 3.59 | -0.50 |
| GFS (USA) | 0.53 | 0.76 | 0.36 | 1.19 | 0.30 | 0.36 | 0.36 | 0.58 | 0.69 | 0.22 | 3.40 | -1.15 |
| Open-Meteo automatico (usato fino al 9/10/2026) | 0.40 | 0.46 | 0.24 | 0.60 | 0.22 | 0.24 | 0.33 | 0.38 | 0.41 | 0.17 | 3.60 | -2.48 |
| ICON-D2 2 km | 0.40 | 0.45 | 0.22 | 0.58 | 0.22 | 0.25 | 0.33 | 0.38 | 0.42 | 0.17 | 3.57 | -2.51 |
| ICON (DWD) | 0.40 | 0.45 | 0.22 | 0.58 | 0.22 | 0.25 | 0.33 | 0.38 | 0.42 | 0.17 | 3.57 | -2.51 |

## Anticipo 2 giorni (7824 giorni-stazione)

| modello | ≥3 mm CSI | presi | falsi allarmi | prev./oss. | ≥20 mm CSI | presi | falsi | pioggia utile 3 gg CSI | presi | falsi | errore mm | scarto mm |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| media dei modelli disponibili | 0.61 | 0.83 | 0.31 | 1.20 | 0.38 | 0.47 | 0.34 | 0.64 | 0.78 | 0.23 | 3.14 | -0.78 |
| media di AROME, ECMWF, AIFS, ICON-2I, ICON, GFS | 0.61 | 0.84 | 0.32 | 1.23 | 0.40 | 0.49 | 0.33 | 0.63 | 0.79 | 0.24 | 3.17 | -0.73 |
| media AROME + ECMWF + ICON-2I + ICON | 0.60 | 0.81 | 0.30 | 1.15 | 0.40 | 0.52 | 0.36 | 0.62 | 0.77 | 0.24 | 3.20 | -0.66 |
| media AROME + ECMWF + AIFS + ICON-2I + GFS | 0.59 | 0.84 | 0.33 | 1.26 | 0.39 | 0.49 | 0.34 | 0.63 | 0.79 | 0.25 | 3.27 | -0.65 |
| media AROME + ECMWF + AIFS + ICON-2I | 0.59 | 0.84 | 0.34 | 1.28 | 0.41 | 0.53 | 0.36 | 0.63 | 0.81 | 0.27 | 3.32 | -0.41 |
| Open-Meteo automatico (usato fino al 9/10/2026) | 0.57 | 0.72 | 0.27 | 0.99 | 0.34 | 0.43 | 0.37 | 0.58 | 0.68 | 0.21 | 3.32 | -1.05 |
| ICON (DWD) | 0.57 | 0.72 | 0.27 | 0.99 | 0.34 | 0.43 | 0.37 | 0.58 | 0.68 | 0.21 | 3.32 | -1.04 |
| media AROME + ECMWF + ICON-2I | 0.57 | 0.78 | 0.32 | 1.15 | 0.39 | 0.52 | 0.39 | 0.61 | 0.77 | 0.26 | 3.41 | -0.47 |
| ECMWF AIFS (IA) | 0.55 | 0.89 | 0.40 | 1.49 | 0.37 | 0.48 | 0.38 | 0.62 | 0.84 | 0.29 | 3.51 | -0.29 |
| ECMWF IFS | 0.55 | 0.76 | 0.33 | 1.13 | 0.36 | 0.49 | 0.42 | 0.60 | 0.75 | 0.25 | 3.56 | -0.48 |
| GFS (USA) | 0.51 | 0.71 | 0.35 | 1.10 | 0.26 | 0.32 | 0.39 | 0.54 | 0.65 | 0.25 | 3.61 | -1.36 |
| ICON-2I ItaliaMeteo 2 km | 0.50 | 0.64 | 0.31 | 0.93 | 0.33 | 0.47 | 0.48 | 0.53 | 0.67 | 0.28 | 3.97 | -0.47 |

## Anticipo 3 giorni (8319 giorni-stazione)

| modello | ≥3 mm CSI | presi | falsi allarmi | prev./oss. | ≥20 mm CSI | presi | falsi | pioggia utile 3 gg CSI | presi | falsi | errore mm | scarto mm |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| media dei modelli disponibili | 0.57 | 0.82 | 0.35 | 1.25 | 0.32 | 0.41 | 0.41 | 0.59 | 0.74 | 0.26 | 3.27 | -0.62 |
| media di AROME, ECMWF, AIFS, ICON-2I, ICON, GFS | 0.56 | 0.83 | 0.36 | 1.30 | 0.32 | 0.41 | 0.43 | 0.59 | 0.76 | 0.27 | 3.31 | -0.59 |
| media AROME + ECMWF + AIFS + ICON-2I + GFS | 0.55 | 0.84 | 0.38 | 1.35 | 0.31 | 0.41 | 0.44 | 0.57 | 0.75 | 0.29 | 3.44 | -0.55 |
| media AROME + ECMWF + ICON-2I + ICON | 0.55 | 0.76 | 0.34 | 1.15 | 0.35 | 0.48 | 0.44 | 0.58 | 0.74 | 0.28 | 3.33 | -0.56 |
| media AROME + ECMWF + AIFS + ICON-2I | 0.55 | 0.85 | 0.39 | 1.40 | 0.32 | 0.44 | 0.45 | 0.58 | 0.79 | 0.32 | 3.51 | -0.28 |
| Open-Meteo automatico (usato fino al 9/10/2026) | 0.53 | 0.70 | 0.32 | 1.02 | 0.34 | 0.45 | 0.43 | 0.56 | 0.68 | 0.25 | 3.47 | -0.72 |
| ICON (DWD) | 0.53 | 0.70 | 0.32 | 1.02 | 0.34 | 0.45 | 0.43 | 0.56 | 0.68 | 0.25 | 3.46 | -0.72 |
| ECMWF AIFS (IA) | 0.52 | 0.89 | 0.44 | 1.58 | 0.32 | 0.44 | 0.46 | 0.58 | 0.82 | 0.33 | 3.63 | -0.16 |
| ECMWF IFS | 0.52 | 0.77 | 0.38 | 1.24 | 0.30 | 0.42 | 0.50 | 0.56 | 0.73 | 0.30 | 3.64 | -0.40 |
| GFS (USA) | 0.47 | 0.68 | 0.40 | 1.13 | 0.21 | 0.27 | 0.51 | 0.48 | 0.58 | 0.27 | 3.75 | -1.10 |

## Anticipo 4 giorni (8109 giorni-stazione)

| modello | ≥3 mm CSI | presi | falsi allarmi | prev./oss. | ≥20 mm CSI | presi | falsi | pioggia utile 3 gg CSI | presi | falsi | errore mm | scarto mm |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| media AROME + ECMWF + AIFS + ICON-2I + GFS | 0.53 | 0.84 | 0.41 | 1.42 | 0.29 | 0.35 | 0.39 | 0.57 | 0.77 | 0.32 | 3.69 | -0.61 |
| media di AROME, ECMWF, AIFS, ICON-2I, ICON, GFS | 0.53 | 0.82 | 0.40 | 1.37 | 0.28 | 0.34 | 0.39 | 0.57 | 0.76 | 0.30 | 3.58 | -0.70 |
| media dei modelli disponibili | 0.53 | 0.80 | 0.39 | 1.32 | 0.29 | 0.36 | 0.39 | 0.58 | 0.75 | 0.29 | 3.55 | -0.77 |
| media AROME + ECMWF + AIFS + ICON-2I | 0.53 | 0.85 | 0.42 | 1.45 | 0.33 | 0.44 | 0.42 | 0.57 | 0.78 | 0.32 | 3.71 | -0.35 |
| ECMWF AIFS (IA) | 0.51 | 0.88 | 0.45 | 1.59 | 0.30 | 0.41 | 0.46 | 0.58 | 0.82 | 0.33 | 3.81 | -0.19 |
| media AROME + ECMWF + ICON-2I + ICON | 0.50 | 0.74 | 0.39 | 1.20 | 0.32 | 0.42 | 0.43 | 0.55 | 0.72 | 0.30 | 3.59 | -0.75 |
| ECMWF IFS | 0.50 | 0.74 | 0.40 | 1.23 | 0.33 | 0.45 | 0.45 | 0.52 | 0.70 | 0.33 | 3.86 | -0.50 |
| Open-Meteo automatico (usato fino al 9/10/2026) | 0.46 | 0.65 | 0.38 | 1.05 | 0.29 | 0.39 | 0.46 | 0.52 | 0.66 | 0.29 | 3.69 | -1.01 |
| ICON (DWD) | 0.46 | 0.65 | 0.38 | 1.06 | 0.29 | 0.39 | 0.46 | 0.52 | 0.66 | 0.29 | 3.69 | -1.00 |
| GFS (USA) | 0.43 | 0.65 | 0.44 | 1.17 | 0.18 | 0.24 | 0.56 | 0.46 | 0.60 | 0.34 | 4.11 | -1.12 |

## Anticipo 5 giorni (8229 giorni-stazione)

| modello | ≥3 mm CSI | presi | falsi allarmi | prev./oss. | ≥20 mm CSI | presi | falsi | pioggia utile 3 gg CSI | presi | falsi | errore mm | scarto mm |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| media AROME + ECMWF + AIFS + ICON-2I + GFS | 0.49 | 0.78 | 0.43 | 1.36 | 0.22 | 0.26 | 0.43 | 0.54 | 0.70 | 0.30 | 3.74 | -1.02 |
| media di AROME, ECMWF, AIFS, ICON-2I, ICON, GFS | 0.49 | 0.79 | 0.44 | 1.43 | 0.22 | 0.27 | 0.44 | 0.54 | 0.71 | 0.31 | 3.84 | -0.90 |
| media AROME + ECMWF + AIFS + ICON-2I | 0.48 | 0.82 | 0.47 | 1.53 | 0.29 | 0.39 | 0.48 | 0.57 | 0.79 | 0.33 | 3.92 | -0.25 |
| ECMWF AIFS (IA) | 0.47 | 0.86 | 0.49 | 1.68 | 0.26 | 0.38 | 0.54 | 0.57 | 0.83 | 0.35 | 4.06 | +0.07 |
| media dei modelli disponibili | 0.47 | 0.77 | 0.45 | 1.41 | 0.21 | 0.26 | 0.47 | 0.52 | 0.69 | 0.32 | 3.94 | -0.83 |
| ECMWF IFS | 0.44 | 0.69 | 0.45 | 1.25 | 0.28 | 0.38 | 0.48 | 0.52 | 0.69 | 0.33 | 4.09 | -0.56 |
| media AROME + ECMWF + ICON-2I + ICON | 0.44 | 0.71 | 0.47 | 1.35 | 0.27 | 0.35 | 0.48 | 0.52 | 0.70 | 0.34 | 4.14 | -0.55 |
| Open-Meteo automatico (usato fino al 9/10/2026) | 0.39 | 0.63 | 0.49 | 1.23 | 0.19 | 0.26 | 0.60 | 0.43 | 0.61 | 0.40 | 4.63 | -0.53 |
| ICON (DWD) | 0.39 | 0.63 | 0.49 | 1.23 | 0.19 | 0.26 | 0.60 | 0.43 | 0.61 | 0.40 | 4.63 | -0.53 |
| GFS (USA) | 0.33 | 0.45 | 0.43 | 0.78 | 0.05 | 0.05 | 0.63 | 0.29 | 0.33 | 0.27 | 3.99 | -2.58 |

## Anticipo 6 giorni (8274 giorni-stazione)

| modello | ≥3 mm CSI | presi | falsi allarmi | prev./oss. | ≥20 mm CSI | presi | falsi | pioggia utile 3 gg CSI | presi | falsi | errore mm | scarto mm |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| media AROME + ECMWF + AIFS + ICON-2I + GFS | 0.46 | 0.76 | 0.47 | 1.43 | 0.16 | 0.17 | 0.41 | 0.49 | 0.64 | 0.33 | 4.03 | -1.22 |
| media di AROME, ECMWF, AIFS, ICON-2I, ICON, GFS | 0.44 | 0.76 | 0.49 | 1.48 | 0.15 | 0.18 | 0.49 | 0.50 | 0.65 | 0.32 | 4.12 | -1.02 |
| media dei modelli disponibili | 0.44 | 0.74 | 0.49 | 1.44 | 0.17 | 0.20 | 0.51 | 0.49 | 0.65 | 0.33 | 4.22 | -0.90 |
| media AROME + ECMWF + AIFS + ICON-2I | 0.43 | 0.80 | 0.52 | 1.68 | 0.19 | 0.25 | 0.54 | 0.51 | 0.76 | 0.39 | 4.32 | -0.29 |
| ECMWF AIFS (IA) | 0.42 | 0.82 | 0.54 | 1.80 | 0.21 | 0.29 | 0.58 | 0.51 | 0.80 | 0.42 | 4.38 | +0.02 |
| media AROME + ECMWF + ICON-2I + ICON | 0.41 | 0.71 | 0.50 | 1.42 | 0.18 | 0.24 | 0.58 | 0.47 | 0.64 | 0.36 | 4.51 | -0.51 |
| ECMWF IFS | 0.38 | 0.64 | 0.51 | 1.31 | 0.19 | 0.26 | 0.58 | 0.44 | 0.60 | 0.38 | 4.57 | -0.60 |
| ICON (DWD) | 0.35 | 0.59 | 0.53 | 1.26 | 0.17 | 0.26 | 0.66 | 0.42 | 0.59 | 0.40 | 4.92 | -0.43 |
| Open-Meteo automatico (usato fino al 9/10/2026) | 0.35 | 0.59 | 0.53 | 1.26 | 0.17 | 0.26 | 0.66 | 0.42 | 0.59 | 0.40 | 4.91 | -0.43 |
| GFS (USA) | 0.27 | 0.34 | 0.43 | 0.59 | 0.01 | 0.01 | 0.33 | 0.17 | 0.18 | 0.21 | 4.03 | -3.08 |

## Anticipo 7 giorni (8229 giorni-stazione)

| modello | ≥3 mm CSI | presi | falsi allarmi | prev./oss. | ≥20 mm CSI | presi | falsi | pioggia utile 3 gg CSI | presi | falsi | errore mm | scarto mm |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| media AROME + ECMWF + AIFS + ICON-2I + GFS | 0.39 | 0.69 | 0.53 | 1.47 | 0.07 | 0.08 | 0.63 | 0.45 | 0.61 | 0.37 | 4.42 | -1.25 |
| media di AROME, ECMWF, AIFS, ICON-2I, ICON, GFS | 0.39 | 0.69 | 0.53 | 1.47 | 0.07 | 0.08 | 0.63 | 0.45 | 0.61 | 0.37 | 4.42 | -1.25 |
| media AROME + ECMWF + AIFS + ICON-2I | 0.38 | 0.75 | 0.56 | 1.68 | 0.15 | 0.20 | 0.62 | 0.46 | 0.69 | 0.43 | 4.77 | -0.35 |
| media dei modelli disponibili | 0.38 | 0.67 | 0.53 | 1.42 | 0.07 | 0.07 | 0.61 | 0.43 | 0.58 | 0.36 | 4.36 | -1.37 |
| ECMWF AIFS (IA) | 0.38 | 0.77 | 0.57 | 1.81 | 0.20 | 0.31 | 0.62 | 0.47 | 0.74 | 0.45 | 4.98 | +0.29 |
| ECMWF IFS | 0.32 | 0.57 | 0.57 | 1.34 | 0.09 | 0.13 | 0.76 | 0.37 | 0.53 | 0.45 | 4.94 | -0.98 |
| Open-Meteo automatico (usato fino al 9/10/2026) | 0.29 | 0.45 | 0.54 | 0.98 | 0.11 | 0.13 | 0.65 | 0.29 | 0.38 | 0.44 | 4.52 | -1.74 |
| GFS (USA) | 0.20 | 0.27 | 0.55 | 0.60 | 0.02 | 0.02 | 0.57 | 0.13 | 0.14 | 0.37 | 4.28 | -3.06 |

