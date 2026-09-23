# Benchmark A/B del motor 0.3.0

- Fecha: 2026-09-13T17:55:19+00:00
- Dataset: `dataset-2026-09-13.csv` (sha256 `c963688ec96538f6`), malicious: 500, legit: 500
- Capas: L1, L3; cache L2 desactivada; workers: 8; duracion: 115.4 s

## Deteccion, criterio estricto (red)

| Corrida | Precision | Recall | F1 | FPR | TP | FP | TN | FN |
|---|---|---|---|---|---|---|---|---|
| Con trazabilidad | 100.0% | 0.8% | 1.6% | 0.0% | 4 | 0 | 500 | 496 |
| Sin trazabilidad | 100.0% | 0.8% | 1.6% | 0.0% | 4 | 0 | 500 | 496 |

- Maliciosas marcadas solo con trazabilidad: 0; solo sin ella: 0 (McNemar p = 1.0)
- Legitimas marcadas solo con trazabilidad: 0; solo sin ella: 0
- Maliciosas cuyo destino difiere de la URL del QR (n = 58): recall 0.0% con trazabilidad, 0.0% sin ella

## Deteccion, criterio amplio (red o yellow)

| Corrida | Precision | Recall | F1 | FPR | TP | FP | TN | FN |
|---|---|---|---|---|---|---|---|---|
| Con trazabilidad | 94.9% | 18.6% | 31.1% | 1.0% | 93 | 5 | 495 | 407 |
| Sin trazabilidad | 98.9% | 18.0% | 30.5% | 0.2% | 90 | 1 | 499 | 410 |

- Maliciosas marcadas solo con trazabilidad: 11; solo sin ella: 8 (McNemar p = 0.647606)
- Legitimas marcadas solo con trazabilidad: 4; solo sin ella: 0
- Maliciosas cuyo destino difiere de la URL del QR (n = 58): recall 29.3% con trazabilidad, 24.1% sin ella

## Latencia (ms)

| Corrida | Medida | p50 | p95 |
|---|---|---|---|
| Con trazabilidad | total | 676.257 | 2269.856 |
| Con trazabilidad | redirects | 676.065 | 2269.726 |
| Con trazabilidad | L1 | 0.105 | 0.183 |
| Con trazabilidad | L3 | 0.036 | 0.072 |
| Sin trazabilidad | total | 0.038 | 0.117 |
| Sin trazabilidad | redirects | 0.001 | 0.004 |
| Sin trazabilidad | L1 | 0.02 | 0.05 |
| Sin trazabilidad | L3 | 0.006 | 0.013 |

## Capa responsable de las detecciones (criterio amplio)

- Con trazabilidad: {'L1': 93}; errores: 0
- Sin trazabilidad: {'L1': 90}; errores: 0
