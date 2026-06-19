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

## Tests

```bash
pytest
```

## Roadmap de versiones
- `v0.1.0` (actual): scaffold + heuristicas L1
- `v0.2.0`: cache L2 (PostgreSQL)
- `v0.3.0`: L3 (PhishTank local)
- `v0.4.0`: L4 (Google Safe Browsing)
- `v0.5.0`: L5 (VirusTotal) + deploy Railway
