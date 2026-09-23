# Benchmark A/B del motor 0.3.0

- Fecha: 2026-09-13T18:05:46+00:00
- Dataset: `dataset-2026-09-13.csv` (sha256 `c963688ec96538f6`), malicious: 500, legit: 500
- Capas: L1, L3; cache L2 desactivada; workers: 8; duracion: 103.3 s

## Deteccion, criterio estricto (red)

| Corrida | Precision | Recall | F1 | FPR | TP | FP | TN | FN |
|---|---|---|---|---|---|---|---|---|
| Con trazabilidad | 100.0% | 1.0% | 2.0% | 0.0% | 5 | 0 | 500 | 495 |
| Sin trazabilidad | 100.0% | 0.8% | 1.6% | 0.0% | 4 | 0 | 500 | 496 |

- Maliciosas marcadas solo con trazabilidad: 1; solo sin ella: 0 (McNemar p = 1.0)
- Legitimas marcadas solo con trazabilidad: 0; solo sin ella: 0
- Maliciosas cuyo destino difiere de la URL del QR (n = 58): recall 1.7% con trazabilidad, 0.0% sin ella

## Deteccion, criterio amplio (red o yellow)

| Corrida | Precision | Recall | F1 | FPR | TP | FP | TN | FN |
|---|---|---|---|---|---|---|---|---|
| Con trazabilidad | 99.4% | 33.0% | 49.5% | 0.2% | 165 | 1 | 499 | 335 |
| Sin trazabilidad | 99.4% | 32.8% | 49.3% | 0.2% | 164 | 1 | 499 | 336 |

- Maliciosas marcadas solo con trazabilidad: 1; solo sin ella: 0 (McNemar p = 1.0)
- Legitimas marcadas solo con trazabilidad: 0; solo sin ella: 0
- Maliciosas cuyo destino difiere de la URL del QR (n = 58): recall 27.6% con trazabilidad, 25.9% sin ella

## Latencia (ms)

| Corrida | Medida | p50 | p95 |
|---|---|---|---|
| Con trazabilidad | total | 657.193 | 2000.384 |
| Con trazabilidad | redirects | 656.967 | 2000.152 |
| Con trazabilidad | L1 | 0.108 | 0.208 |
| Con trazabilidad | L3 | 0.027 | 0.06 |
| Sin trazabilidad | total | 0.04 | 0.128 |
| Sin trazabilidad | redirects | 0.001 | 0.004 |
| Sin trazabilidad | L1 | 0.022 | 0.066 |
| Sin trazabilidad | L3 | 0.006 | 0.015 |

## Capa responsable de las detecciones (criterio amplio)

- Con trazabilidad: {'L1': 165}; errores: 0
- Sin trazabilidad: {'L1': 164}; errores: 0
