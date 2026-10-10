# Previsioni di pioggia contro pioggia misurata (stazioni SIR)

Periodo 2025-04-15 – 2026-10-09. Stazioni: 15. Modelli: Open-Meteo automatico (usato fino al 9/10/2026), ECMWF AIFS (IA), ECMWF IFS, GFS (USA), ICON-D2 2 km, ICON (DWD), ICON-2I ItaliaMeteo 2 km, AROME France HD 1,5 km.
Giorno D = pioggia dalle 9 del giorno prima alle 9 di D (come l'archivio SIR). Ogni tabella usa gli stessi giorni e stazioni per tutti i modelli con quell'anticipo. CSI: 1 = perfetto, 0 = mai preso.

## Verdetto sulla scelta attuale (media AROME + ECMWF + AIFS + ICON-2I)

Pioggia utile per la buttata (≥13 mm in 3 giorni), CSI della scelta attuale e della migliore alternativa per anticipo:

- anticipo 0: 0.68 (migliore alternativa media di AROME, ECMWF, AIFS, ICON-2I, ICON, GFS 0.69)
- anticipo 1: 0.65 (migliore alternativa media di AROME, ECMWF, AIFS, ICON-2I, ICON, GFS 0.66)
- anticipo 2: 0.62 (migliore alternativa media dei modelli disponibili 0.62)
- anticipo 3: 0.57 (migliore alternativa media di AROME, ECMWF, AIFS, ICON-2I, ICON, GFS 0.58)
- anticipo 4: 0.56 (migliore alternativa ECMWF AIFS (IA) 0.57)
- anticipo 5: 0.56 (migliore alternativa ECMWF AIFS (IA) 0.56)
- anticipo 6: 0.50 (migliore alternativa ECMWF AIFS (IA) 0.50)
- anticipo 7: 0.46 (migliore alternativa ECMWF AIFS (IA) 0.46)

**La scelta attuale resta la migliore** (o entro 0,03 dalla migliore) a tutti gli anticipi.

## Anticipo 0 giorni (7929 giorni-stazione)

| modello | ≥3 mm CSI | presi | falsi allarmi | prev./oss. | ≥20 mm CSI | presi | falsi | pioggia utile 3 gg CSI | presi | falsi | errore mm | scarto mm |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| media AROME + ECMWF + ICON-2I + ICON | 0.65 | 0.86 | 0.28 | 1.19 | 0.50 | 0.59 | 0.24 | 0.69 | 0.85 | 0.22 | 2.54 | -0.45 |
| media di AROME, ECMWF, AIFS, ICON-2I, ICON, GFS | 0.64 | 0.88 | 0.30 | 1.26 | 0.49 | 0.57 | 0.23 | 0.69 | 0.86 | 0.22 | 2.60 | -0.45 |
| media dei modelli disponibili | 0.64 | 0.85 | 0.28 | 1.18 | 0.44 | 0.50 | 0.21 | 0.67 | 0.81 | 0.20 | 2.62 | -0.77 |
| media AROME + ECMWF + ICON-2I | 0.63 | 0.88 | 0.31 | 1.26 | 0.52 | 0.67 | 0.30 | 0.68 | 0.87 | 0.24 | 2.64 | -0.01 |
| media AROME + ECMWF + AIFS + ICON-2I + GFS | 0.63 | 0.89 | 0.32 | 1.31 | 0.50 | 0.63 | 0.28 | 0.69 | 0.88 | 0.24 | 2.67 | -0.18 |
| media AROME + ECMWF + AIFS + ICON-2I | 0.62 | 0.88 | 0.32 | 1.30 | 0.52 | 0.65 | 0.29 | 0.68 | 0.87 | 0.24 | 2.67 | -0.09 |
| AROME France HD 1,5 km | 0.62 | 0.84 | 0.30 | 1.19 | 0.52 | 0.75 | 0.38 | 0.67 | 0.87 | 0.26 | 3.04 | +0.82 |
| ECMWF AIFS (IA) | 0.57 | 0.88 | 0.38 | 1.42 | 0.40 | 0.52 | 0.36 | 0.62 | 0.83 | 0.28 | 3.09 | -0.32 |
| ECMWF IFS | 0.56 | 0.82 | 0.36 | 1.28 | 0.40 | 0.55 | 0.39 | 0.61 | 0.77 | 0.26 | 3.28 | -0.22 |
| GFS (USA) | 0.55 | 0.82 | 0.37 | 1.28 | 0.36 | 0.46 | 0.37 | 0.59 | 0.75 | 0.27 | 3.18 | -0.55 |
| ICON-2I ItaliaMeteo 2 km | 0.54 | 0.70 | 0.30 | 0.99 | 0.36 | 0.49 | 0.42 | 0.55 | 0.70 | 0.28 | 3.38 | -0.62 |
| Open-Meteo automatico (usato fino al 9/10/2026) | 0.49 | 0.57 | 0.22 | 0.73 | 0.28 | 0.33 | 0.35 | 0.46 | 0.53 | 0.21 | 3.27 | -1.74 |
| ICON-D2 2 km | 0.49 | 0.56 | 0.22 | 0.72 | 0.28 | 0.33 | 0.35 | 0.46 | 0.52 | 0.21 | 3.28 | -1.77 |
| ICON (DWD) | 0.49 | 0.56 | 0.22 | 0.72 | 0.28 | 0.33 | 0.35 | 0.46 | 0.52 | 0.21 | 3.28 | -1.77 |

## Anticipo 1 giorno (7419 giorni-stazione)

| modello | ≥3 mm CSI | presi | falsi allarmi | prev./oss. | ≥20 mm CSI | presi | falsi | pioggia utile 3 gg CSI | presi | falsi | errore mm | scarto mm |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| media AROME + ECMWF + ICON-2I + ICON | 0.63 | 0.81 | 0.26 | 1.10 | 0.47 | 0.56 | 0.25 | 0.63 | 0.76 | 0.21 | 2.78 | -0.93 |
| media dei modelli disponibili | 0.63 | 0.81 | 0.26 | 1.10 | 0.38 | 0.43 | 0.22 | 0.63 | 0.73 | 0.16 | 2.88 | -1.28 |
| media di AROME, ECMWF, AIFS, ICON-2I, ICON, GFS | 0.62 | 0.84 | 0.29 | 1.18 | 0.46 | 0.53 | 0.23 | 0.66 | 0.79 | 0.20 | 2.84 | -0.88 |
| media AROME + ECMWF + AIFS + ICON-2I + GFS | 0.62 | 0.86 | 0.30 | 1.23 | 0.47 | 0.58 | 0.28 | 0.65 | 0.82 | 0.24 | 2.88 | -0.56 |
| media AROME + ECMWF + AIFS + ICON-2I | 0.62 | 0.85 | 0.30 | 1.22 | 0.48 | 0.62 | 0.31 | 0.65 | 0.83 | 0.24 | 2.87 | -0.40 |
| media AROME + ECMWF + ICON-2I | 0.62 | 0.83 | 0.29 | 1.16 | 0.49 | 0.63 | 0.30 | 0.64 | 0.80 | 0.24 | 2.83 | -0.40 |
| AROME France HD 1,5 km | 0.59 | 0.78 | 0.28 | 1.08 | 0.47 | 0.64 | 0.36 | 0.63 | 0.78 | 0.23 | 3.16 | +0.06 |
| ECMWF IFS | 0.57 | 0.80 | 0.33 | 1.19 | 0.39 | 0.49 | 0.35 | 0.59 | 0.73 | 0.25 | 3.33 | -0.75 |
| ECMWF AIFS (IA) | 0.56 | 0.89 | 0.39 | 1.46 | 0.42 | 0.55 | 0.35 | 0.62 | 0.82 | 0.28 | 3.33 | -0.39 |
| ICON-2I ItaliaMeteo 2 km | 0.53 | 0.67 | 0.27 | 0.92 | 0.36 | 0.50 | 0.45 | 0.54 | 0.68 | 0.28 | 3.65 | -0.52 |
| GFS (USA) | 0.53 | 0.75 | 0.36 | 1.18 | 0.29 | 0.35 | 0.38 | 0.56 | 0.68 | 0.23 | 3.44 | -1.20 |
| Open-Meteo automatico (usato fino al 9/10/2026) | 0.40 | 0.46 | 0.25 | 0.61 | 0.20 | 0.23 | 0.35 | 0.36 | 0.39 | 0.19 | 3.61 | -2.48 |
| ICON-D2 2 km | 0.40 | 0.45 | 0.23 | 0.58 | 0.21 | 0.24 | 0.35 | 0.37 | 0.40 | 0.18 | 3.58 | -2.51 |
| ICON (DWD) | 0.40 | 0.45 | 0.23 | 0.58 | 0.21 | 0.24 | 0.35 | 0.37 | 0.40 | 0.18 | 3.58 | -2.51 |

## Anticipo 2 giorni (7479 giorni-stazione)

| modello | ≥3 mm CSI | presi | falsi allarmi | prev./oss. | ≥20 mm CSI | presi | falsi | pioggia utile 3 gg CSI | presi | falsi | errore mm | scarto mm |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| media dei modelli disponibili | 0.61 | 0.83 | 0.31 | 1.20 | 0.37 | 0.46 | 0.34 | 0.62 | 0.77 | 0.24 | 3.18 | -0.82 |
| media di AROME, ECMWF, AIFS, ICON-2I, ICON, GFS | 0.61 | 0.84 | 0.31 | 1.23 | 0.39 | 0.48 | 0.33 | 0.62 | 0.78 | 0.25 | 3.21 | -0.78 |
| media AROME + ECMWF + ICON-2I + ICON | 0.60 | 0.80 | 0.29 | 1.14 | 0.39 | 0.50 | 0.37 | 0.61 | 0.77 | 0.25 | 3.23 | -0.71 |
| media AROME + ECMWF + AIFS + ICON-2I + GFS | 0.59 | 0.83 | 0.33 | 1.25 | 0.38 | 0.48 | 0.35 | 0.62 | 0.78 | 0.26 | 3.31 | -0.70 |
| media AROME + ECMWF + AIFS + ICON-2I | 0.58 | 0.84 | 0.34 | 1.28 | 0.39 | 0.51 | 0.37 | 0.62 | 0.81 | 0.27 | 3.36 | -0.46 |
| Open-Meteo automatico (usato fino al 9/10/2026) | 0.57 | 0.72 | 0.27 | 0.99 | 0.34 | 0.42 | 0.38 | 0.57 | 0.67 | 0.22 | 3.35 | -1.06 |
| ICON (DWD) | 0.57 | 0.72 | 0.27 | 0.99 | 0.34 | 0.42 | 0.38 | 0.57 | 0.67 | 0.22 | 3.35 | -1.06 |
| media AROME + ECMWF + ICON-2I | 0.57 | 0.77 | 0.32 | 1.14 | 0.37 | 0.50 | 0.40 | 0.60 | 0.76 | 0.26 | 3.46 | -0.53 |
| ECMWF AIFS (IA) | 0.55 | 0.89 | 0.41 | 1.50 | 0.36 | 0.47 | 0.39 | 0.61 | 0.83 | 0.30 | 3.55 | -0.32 |
| ECMWF IFS | 0.55 | 0.75 | 0.33 | 1.11 | 0.34 | 0.47 | 0.44 | 0.59 | 0.74 | 0.25 | 3.56 | -0.58 |
| GFS (USA) | 0.51 | 0.70 | 0.35 | 1.09 | 0.25 | 0.30 | 0.41 | 0.52 | 0.64 | 0.26 | 3.65 | -1.42 |
| ICON-2I ItaliaMeteo 2 km | 0.50 | 0.64 | 0.31 | 0.93 | 0.31 | 0.45 | 0.50 | 0.52 | 0.67 | 0.29 | 4.04 | -0.49 |

## Anticipo 3 giorni (7974 giorni-stazione)

| modello | ≥3 mm CSI | presi | falsi allarmi | prev./oss. | ≥20 mm CSI | presi | falsi | pioggia utile 3 gg CSI | presi | falsi | errore mm | scarto mm |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| media dei modelli disponibili | 0.57 | 0.81 | 0.35 | 1.25 | 0.31 | 0.40 | 0.42 | 0.58 | 0.74 | 0.27 | 3.29 | -0.67 |
| media di AROME, ECMWF, AIFS, ICON-2I, ICON, GFS | 0.56 | 0.83 | 0.36 | 1.30 | 0.30 | 0.40 | 0.44 | 0.58 | 0.75 | 0.28 | 3.32 | -0.65 |
| media AROME + ECMWF + AIFS + ICON-2I + GFS | 0.55 | 0.83 | 0.38 | 1.34 | 0.30 | 0.39 | 0.45 | 0.56 | 0.74 | 0.30 | 3.44 | -0.63 |
| media AROME + ECMWF + ICON-2I + ICON | 0.55 | 0.76 | 0.34 | 1.14 | 0.34 | 0.46 | 0.45 | 0.57 | 0.73 | 0.28 | 3.34 | -0.62 |
| media AROME + ECMWF + AIFS + ICON-2I | 0.55 | 0.85 | 0.39 | 1.39 | 0.31 | 0.43 | 0.46 | 0.57 | 0.78 | 0.32 | 3.51 | -0.34 |
| Open-Meteo automatico (usato fino al 9/10/2026) | 0.52 | 0.69 | 0.32 | 1.01 | 0.33 | 0.44 | 0.44 | 0.55 | 0.68 | 0.26 | 3.50 | -0.72 |
| ICON (DWD) | 0.52 | 0.69 | 0.32 | 1.01 | 0.33 | 0.44 | 0.44 | 0.55 | 0.68 | 0.26 | 3.50 | -0.72 |
| ECMWF AIFS (IA) | 0.52 | 0.89 | 0.44 | 1.58 | 0.30 | 0.42 | 0.48 | 0.57 | 0.81 | 0.34 | 3.66 | -0.17 |
| ECMWF IFS | 0.52 | 0.76 | 0.38 | 1.22 | 0.29 | 0.40 | 0.50 | 0.55 | 0.72 | 0.30 | 3.61 | -0.52 |
| GFS (USA) | 0.47 | 0.68 | 0.40 | 1.13 | 0.20 | 0.26 | 0.53 | 0.47 | 0.57 | 0.29 | 3.74 | -1.20 |

## Anticipo 4 giorni (7764 giorni-stazione)

| modello | ≥3 mm CSI | presi | falsi allarmi | prev./oss. | ≥20 mm CSI | presi | falsi | pioggia utile 3 gg CSI | presi | falsi | errore mm | scarto mm |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| media AROME + ECMWF + AIFS + ICON-2I + GFS | 0.53 | 0.84 | 0.41 | 1.41 | 0.27 | 0.33 | 0.40 | 0.56 | 0.77 | 0.33 | 3.72 | -0.68 |
| media di AROME, ECMWF, AIFS, ICON-2I, ICON, GFS | 0.53 | 0.82 | 0.40 | 1.37 | 0.27 | 0.33 | 0.40 | 0.56 | 0.75 | 0.31 | 3.61 | -0.76 |
| media AROME + ECMWF + AIFS + ICON-2I | 0.53 | 0.85 | 0.42 | 1.45 | 0.32 | 0.42 | 0.44 | 0.56 | 0.77 | 0.33 | 3.73 | -0.41 |
| media dei modelli disponibili | 0.53 | 0.80 | 0.39 | 1.32 | 0.28 | 0.34 | 0.40 | 0.57 | 0.74 | 0.30 | 3.58 | -0.81 |
| ECMWF AIFS (IA) | 0.50 | 0.88 | 0.46 | 1.62 | 0.29 | 0.39 | 0.47 | 0.57 | 0.81 | 0.34 | 3.85 | -0.18 |
| media AROME + ECMWF + ICON-2I + ICON | 0.50 | 0.73 | 0.39 | 1.19 | 0.31 | 0.41 | 0.43 | 0.54 | 0.71 | 0.30 | 3.60 | -0.82 |
| ECMWF IFS | 0.50 | 0.73 | 0.39 | 1.21 | 0.32 | 0.43 | 0.45 | 0.51 | 0.68 | 0.33 | 3.84 | -0.64 |
| Open-Meteo automatico (usato fino al 9/10/2026) | 0.46 | 0.64 | 0.39 | 1.05 | 0.29 | 0.38 | 0.46 | 0.51 | 0.66 | 0.31 | 3.71 | -1.01 |
| ICON (DWD) | 0.46 | 0.64 | 0.39 | 1.05 | 0.29 | 0.38 | 0.46 | 0.51 | 0.66 | 0.31 | 3.71 | -1.01 |
| GFS (USA) | 0.43 | 0.65 | 0.44 | 1.16 | 0.17 | 0.23 | 0.58 | 0.45 | 0.59 | 0.35 | 4.11 | -1.22 |

## Anticipo 5 giorni (7884 giorni-stazione)

| modello | ≥3 mm CSI | presi | falsi allarmi | prev./oss. | ≥20 mm CSI | presi | falsi | pioggia utile 3 gg CSI | presi | falsi | errore mm | scarto mm |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| media AROME + ECMWF + AIFS + ICON-2I + GFS | 0.49 | 0.77 | 0.43 | 1.36 | 0.20 | 0.24 | 0.44 | 0.53 | 0.70 | 0.31 | 3.76 | -1.06 |
| media di AROME, ECMWF, AIFS, ICON-2I, ICON, GFS | 0.48 | 0.79 | 0.45 | 1.43 | 0.20 | 0.25 | 0.46 | 0.53 | 0.70 | 0.32 | 3.86 | -0.91 |
| media AROME + ECMWF + AIFS + ICON-2I | 0.47 | 0.81 | 0.47 | 1.53 | 0.27 | 0.37 | 0.48 | 0.56 | 0.79 | 0.34 | 3.93 | -0.29 |
| ECMWF AIFS (IA) | 0.47 | 0.86 | 0.49 | 1.69 | 0.25 | 0.37 | 0.55 | 0.56 | 0.83 | 0.37 | 4.10 | +0.07 |
| media dei modelli disponibili | 0.46 | 0.77 | 0.46 | 1.42 | 0.19 | 0.24 | 0.50 | 0.51 | 0.69 | 0.33 | 3.97 | -0.82 |
| ECMWF IFS | 0.44 | 0.68 | 0.45 | 1.24 | 0.27 | 0.36 | 0.49 | 0.51 | 0.68 | 0.33 | 4.06 | -0.65 |
| media AROME + ECMWF + ICON-2I + ICON | 0.43 | 0.71 | 0.47 | 1.35 | 0.25 | 0.33 | 0.49 | 0.51 | 0.69 | 0.34 | 4.15 | -0.56 |
| Open-Meteo automatico (usato fino al 9/10/2026) | 0.38 | 0.62 | 0.50 | 1.23 | 0.18 | 0.25 | 0.62 | 0.42 | 0.60 | 0.41 | 4.69 | -0.47 |
| ICON (DWD) | 0.38 | 0.62 | 0.50 | 1.23 | 0.18 | 0.25 | 0.62 | 0.42 | 0.60 | 0.41 | 4.69 | -0.47 |
| GFS (USA) | 0.33 | 0.44 | 0.43 | 0.77 | 0.03 | 0.03 | 0.77 | 0.28 | 0.31 | 0.29 | 4.01 | -2.60 |

## Anticipo 6 giorni (7929 giorni-stazione)

| modello | ≥3 mm CSI | presi | falsi allarmi | prev./oss. | ≥20 mm CSI | presi | falsi | pioggia utile 3 gg CSI | presi | falsi | errore mm | scarto mm |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| media AROME + ECMWF + AIFS + ICON-2I + GFS | 0.45 | 0.76 | 0.47 | 1.43 | 0.16 | 0.18 | 0.41 | 0.48 | 0.64 | 0.34 | 4.00 | -1.19 |
| media di AROME, ECMWF, AIFS, ICON-2I, ICON, GFS | 0.44 | 0.76 | 0.49 | 1.48 | 0.16 | 0.19 | 0.49 | 0.49 | 0.65 | 0.33 | 4.11 | -0.97 |
| media dei modelli disponibili | 0.43 | 0.74 | 0.49 | 1.44 | 0.17 | 0.21 | 0.51 | 0.48 | 0.64 | 0.34 | 4.21 | -0.83 |
| media AROME + ECMWF + AIFS + ICON-2I | 0.42 | 0.80 | 0.52 | 1.68 | 0.20 | 0.26 | 0.53 | 0.50 | 0.75 | 0.40 | 4.29 | -0.26 |
| ECMWF AIFS (IA) | 0.41 | 0.82 | 0.55 | 1.81 | 0.21 | 0.29 | 0.58 | 0.50 | 0.80 | 0.43 | 4.39 | +0.08 |
| media AROME + ECMWF + ICON-2I + ICON | 0.41 | 0.71 | 0.50 | 1.42 | 0.19 | 0.26 | 0.58 | 0.46 | 0.63 | 0.36 | 4.49 | -0.46 |
| ECMWF IFS | 0.38 | 0.64 | 0.51 | 1.30 | 0.20 | 0.27 | 0.56 | 0.44 | 0.59 | 0.37 | 4.51 | -0.61 |
| ICON (DWD) | 0.35 | 0.59 | 0.54 | 1.27 | 0.18 | 0.28 | 0.66 | 0.43 | 0.61 | 0.40 | 4.94 | -0.30 |
| Open-Meteo automatico (usato fino al 9/10/2026) | 0.35 | 0.59 | 0.54 | 1.27 | 0.18 | 0.28 | 0.66 | 0.43 | 0.61 | 0.40 | 4.94 | -0.30 |
| GFS (USA) | 0.26 | 0.33 | 0.44 | 0.59 | 0.01 | 0.01 | 0.33 | 0.18 | 0.19 | 0.21 | 4.02 | -3.05 |

## Anticipo 7 giorni (7884 giorni-stazione)

| modello | ≥3 mm CSI | presi | falsi allarmi | prev./oss. | ≥20 mm CSI | presi | falsi | pioggia utile 3 gg CSI | presi | falsi | errore mm | scarto mm |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| media dei modelli disponibili | 0.39 | 0.68 | 0.52 | 1.43 | 0.07 | 0.08 | 0.60 | 0.43 | 0.58 | 0.38 | 4.33 | -1.31 |
| media AROME + ECMWF + AIFS + ICON-2I + GFS | 0.39 | 0.69 | 0.53 | 1.48 | 0.07 | 0.08 | 0.63 | 0.45 | 0.61 | 0.38 | 4.39 | -1.19 |
| media di AROME, ECMWF, AIFS, ICON-2I, ICON, GFS | 0.39 | 0.69 | 0.53 | 1.48 | 0.07 | 0.08 | 0.63 | 0.45 | 0.61 | 0.38 | 4.39 | -1.19 |
| media AROME + ECMWF + AIFS + ICON-2I | 0.39 | 0.75 | 0.56 | 1.70 | 0.15 | 0.20 | 0.63 | 0.46 | 0.70 | 0.43 | 4.77 | -0.24 |
| ECMWF AIFS (IA) | 0.38 | 0.78 | 0.58 | 1.84 | 0.21 | 0.32 | 0.62 | 0.46 | 0.76 | 0.45 | 4.99 | +0.42 |
| ECMWF IFS | 0.33 | 0.58 | 0.57 | 1.35 | 0.09 | 0.13 | 0.76 | 0.37 | 0.54 | 0.46 | 4.93 | -0.89 |
| Open-Meteo automatico (usato fino al 9/10/2026) | 0.30 | 0.46 | 0.54 | 0.99 | 0.11 | 0.14 | 0.65 | 0.29 | 0.39 | 0.45 | 4.51 | -1.67 |
| GFS (USA) | 0.20 | 0.26 | 0.53 | 0.56 | 0.01 | 0.01 | 0.47 | 0.10 | 0.11 | 0.42 | 4.21 | -3.09 |

