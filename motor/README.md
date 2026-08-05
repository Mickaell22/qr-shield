# Motor QR Shield

API REST de deteccion de QR maliciosos. Backend central de QR Shield (NovaTools).

## Stack
- Python 3.11+
- FastAPI + Uvicorn
- PostgreSQL (desde v0.2.0, capa de cache L2)

## Setup local

```bash
cd motor
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Correr en dev

```bash
uvicorn app.main:app --reload --port 8000
```

Endpoints disponibles:
- `GET  http://localhost:8000/health` — health check
- `POST http://localhost:8000/v1/analyze` — analiza una URL
- `http://localhost:8000/docs` — Swagger UI interactiva

Ejemplo de request — URL segura (veredicto verde):
```bash
curl -X POST http://localhost:8000/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
# {"verdict":"green","score":0,"reasons":[]}
```

Ejemplo de request — URL larga sospechosa (veredicto amarillo, heuristica L1):
```bash
curl -X POST http://localhost:8000/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/'"$(printf 'x%.0s' {1..200})"'"}'
# {"verdict":"yellow","score":30,"reasons":["URL excede 100 caracteres (longitud ...)"]}
```

Ejemplo de request — host es una IP literal (veredicto amarillo, heuristica L1):
```bash
curl -X POST http://localhost:8000/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"url": "http://192.168.1.1/login"}'
# {"verdict":"yellow","score":40,"reasons":["El host es una IP literal (192.168.1.1) en vez de un dominio"]}
```

Ejemplo de request — host es un acortador conocido (veredicto amarillo, heuristica L1):
```bash
curl -X POST http://localhost:8000/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"url": "https://bit.ly/abc123"}'
# {"verdict":"yellow","score":25,"reasons":["El host es un acortador de URLs conocido (bit.ly)"]}
```

Ejemplo de request — TLD con alta tasa de abuso (veredicto amarillo, heuristica L1):
```bash
curl -X POST http://localhost:8000/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"url": "http://pagos-uni.tk/login"}'
# {"verdict":"yellow","score":35,"reasons":["El dominio usa un TLD con alta tasa de abuso (.tk)"]}
```

Ejemplo de request — host punycode / homografo (veredicto amarillo, heuristica L1):
```bash
curl -X POST http://localhost:8000/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"url": "https://xn--pple-43d.com/login"}'
# {"verdict":"yellow","score":50,"reasons":["El host usa caracteres internacionales / punycode (xn--pple-43d.com), posible ataque homografo"]}
```

Ejemplo de request — dos senales acumuladas (veredicto rojo):
```bash
curl -X POST http://localhost:8000/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"url": "https://xn--80ak6aa92e.tk/login"}'
# {"verdict":"red","score":85,"reasons":["El dominio usa un TLD con alta tasa de abuso (.tk)","El host usa caracteres internacionales / punycode (...), posible ataque homografo"]}
```

## Scoring y veredicto

Cada heuristica que dispara aporta su peso; el motor los suma y topa el total en 100.
El veredicto sale de ese score:

| Score | Veredicto | Lectura |
|---|---|---|
| `0` | `green` | Ninguna senal |
| `1` – `59` | `yellow` | Sospechosa: al menos una senal, ninguna concluyente |
| `60` – `100` | `red` | Peligrosa |

Pesos actuales por heuristica: punycode 50, IP literal 40, TLD sospechoso 35,
URL larga 30, acortador 25.

El corte en 60 exige **dos senales acumuladas** para llegar a rojo: la heuristica
L1 mas fuerte (punycode, 50) no basta por si sola, porque un dominio IDN legitimo
la dispara igual. Cuando entren las capas L2-L5 sus resultados se suman al mismo
score, sin cambiar los umbrales.

## Tests

```bash
pytest
```

## Roadmap de versiones
- `v0.1.0` (actual): scaffold + heuristicas L1 + scoring ponderado
- `v0.2.0`: cache L2 (PostgreSQL)
- `v0.3.0`: L3 (feed local de URLhaus)
- `v0.4.0`: L4 (Google Safe Browsing)
- `v0.5.0`: L5 (VirusTotal) + deploy Railway
