# Motor de deteccion

API REST para la deteccion de suplantacion en codigos QR mediante analisis en
cascada con trazabilidad de redirecciones. Backend central del sistema (NovaTools).

## Stack
- Python 3.11+
- FastAPI + Uvicorn
- PostgreSQL (capa de cache L2; opcional, el motor arranca sin ella)

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
# {"verdict":"green","score":0,"reasons":[],"final_url":"https://example.com/",
#  "redirects":{"chain":["https://example.com/"],"hops":0,"resolved":true,
#               "rewrote_url":false,"reason":""}}
#  "metrics":{"total_ms":1.4,"deciding_layer":"L1","layers":[...]}}
# Los ejemplos siguientes omiten "final_url", "redirects" y "metrics" por brevedad.
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

## Trazabilidad de redirecciones (RF-009)

Antes de aplicar las heuristicas, el motor resuelve la cadena de saltos HTTP de
la URL hasta su destino terminal, y **las capas analizan esa URL terminal**. Sin
esto, un acortador esconde el destino: `bit.ly/x8k2m` no dispara ninguna
heuristica (dominio conocido, sin caracteres raros, HTTPS valido) mientras que
su destino real `pagos-banc0.xyz` si.

La respuesta expone la cadena completa, no solo el destino:

| Campo | Significado |
|---|---|
| `final_url` | URL terminal sobre la que corrio el analisis |
| `redirects.chain` | Cadena completa recorrida, incluida la URL original |
| `redirects.hops` | Cantidad de saltos resueltos |
| `redirects.rewrote_url` | Si el modulo cambio la URL analizada |
| `redirects.resolved` | `false` si la cadena se corto antes de terminar |
| `redirects.reason` | Por que quedo sin resolver (limite, timeout, bucle, red) |

Comportamiento:
- Sigue `301`, `302`, `303`, `307`, `308` leyendo el header `Location`
  (resuelve tambien los `Location` relativos).
- Pide solo cabeceras: `HEAD`, con fallback a `GET` en streaming sin descargar
  el cuerpo si el servidor no soporta `HEAD`.
- Detecta bucles registrando las URLs ya visitadas.
- Si supera el limite de saltos o el presupuesto de tiempo, la reporta como **no
  resuelta** y sigue el analisis con la ultima URL alcanzada, agregando el motivo
  a `reasons`.
- Bloquea destinos hacia la red interna y esquemas que no sean HTTP/HTTPS: el
  motor hace peticiones salientes hacia una URL de origen desconocido, y sin ese
  filtro seria un vector de SSRF.

**Limitacion declarada:** no se ejecuta JavaScript, asi que las redirecciones por
JS o por `<meta http-equiv="refresh">` quedan fuera de alcance.

Todo se configura por entorno (ver `.env.example`): `REDIRECT_MAX_HOPS`,
`REDIRECT_TIMEOUT_SECONDS`, `REDIRECT_TOTAL_TIMEOUT_SECONDS` y el interruptor
`REDIRECT_TRACING_ENABLED`, que existe para correr el benchmark A/B con y sin el
modulo sobre el mismo dataset.

> Nota para los ejemplos de arriba: con la trazabilidad activada, una URL de
> acortador real se resuelve primero, asi que el veredicto correspondera a su
> destino y no al acortador.

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
la dispara igual. Las capas siguientes suman sus resultados al mismo score, sin
cambiar los umbrales: una URL listada en URLhaus (L3) aporta 100 y basta para el rojo.

## Metricas por capa (RF-008)

Cada analisis se instrumenta capa por capa. Es el insumo del **objetivo
especifico 4**: sin esto no se pueden calcular precision, exhaustividad ni
tiempos desglosados, ni comparar la deteccion con y sin trazabilidad.

La respuesta trae el desglose en `metrics`:

| Campo | Significado |
|---|---|
| `metrics.total_ms` | Tiempo total del analisis |
| `metrics.deciding_layer` | Capa responsable del veredicto: la ultima que aporto puntos; si ninguna aporto (verde), la ultima que corrio |
| `metrics.layers[].layer` | Identificador de la capa (`redirects`, `L1`, ...) |
| `metrics.layers[].duration_ms` | Tiempo de esa capa |
| `metrics.layers[].score` | Puntos que aporto al total |
| `metrics.layers[].hits` | Senales que disparo (en `redirects`, los saltos resueltos) |
| `metrics.layers[].service` | Servicio externo consultado; `null` en las capas locales |

Ademas, cada analisis se escribe como una linea JSON en el logger
`motor.metrics`, con el timestamp, el veredicto, la capa responsable, los
servicios consultados, los tiempos, los datos de la trazabilidad y el estado del
interruptor `tracing_enabled` (lo que separa la corrida A de la B del benchmark):

```json
{"timestamp": "2026-09-06T22:55:11+00:00", "url": "sha256:fadd71a0eb835709",
 "verdict": "red", "score": 70, "deciding_layer": "L1", "services": [],
 "total_ms": 0.251,
 "layers": [{"layer": "redirects", "duration_ms": 0.013, "score": 0, "hits": 0, "service": null},
            {"layer": "L1", "duration_ms": 0.143, "score": 70, "hits": 2, "service": null}],
 "redirects": {"hops": 0, "rewrote_url": false, "resolved": true},
 "tracing_enabled": false}
```

**La URL se registra anonimizada** (hash truncado): el requisito pide registro
anonimo y la URL que escaneo un usuario no tiene por que quedar en el log. Para
el benchmark, donde hace falta cruzar cada analisis con la etiqueta del dataset,
se activa con `METRICS_LOG_URLS=true`.

## Cache de veredictos (L2)

Segunda capa de la cascada: si la URL terminal ya se analizo y su veredicto
sigue vigente, se devuelve sin consultar las capas caras (L3 feed local, L4
Google Safe Browsing, L5 VirusTotal, esta ultima con cuota de 4 req/min). En
medicion local, un analisis completo tarda ~40 ms y el mismo servido desde la
cache, ~2 ms.

Se configura con `DATABASE_URL`. **Sin esa variable la capa queda desactivada**
y el motor analiza igual, sin cache: la deteccion no depende de PostgreSQL. Lo
mismo si la base esta caida o lenta — un error de la cache degrada a analisis
completo, nunca a un error para quien consulta.

| Comportamiento | Detalle |
|---|---|
| Clave | Hash SHA-256 de la URL terminal; no se guarda la URL en claro |
| TTL verde / amarillo | `CACHE_TTL_SECONDS`, por defecto 6 h |
| TTL rojo | `CACHE_TTL_MALICIOUS_SECONDS`, por defecto 24 h |
| Vencimiento | Se calcula con el reloj de PostgreSQL, no con el del proceso |
| Que no se cachea | Los analisis cuya cadena de redirecciones quedo sin resolver: el veredicto es parcial |
| Esquema | Se crea al arrancar si falta (`CREATE TABLE IF NOT EXISTS`) |

El TTL es asimetrico a proposito: servir de mas un verde es un falso negativo, y
en deteccion cuesta mas caro que servir de mas un rojo.

> **Al agregar una capa nueva a la cascada, purgar la cache**
> (`TRUNCATE verdict_cache`). Las entradas guardadas antes se calcularon con
> menos capas, y se seguirian sirviendo como si fueran veredictos completos.

La columna `source_layer` guarda que capa emitio el veredicto: `cascade`
significa que ninguna capa lo emitio, la cascada se agoto sin senales.

## Feed local de URLhaus (L3)

Tercera capa: compara las URLs de la cadena de redirecciones contra el volcado
CSV de URLs maliciosas activas de abuse.ch. El feed se descarga en segundo plano
al arrancar y cada 12 h, y se consulta en memoria: la capa no hace red por
analisis (~0.2 ms medidos).

Se configura con `URLHAUS_FEED_URL` (valor de referencia en `.env.example`).
**Sin esa variable la capa queda desactivada**, y mientras el feed no termine de
descargarse la capa no corre ni figura en las metricas. Una descarga fallida, o
una respuesta sin URLs, conserva el ultimo feed bueno.

| Comportamiento | Detalle |
|---|---|
| Que revisa | La cadena completa: tambien detecta un salto intermedio listado |
| Comparacion | URL exacta normalizada (esquema y host en minusculas, barra final, sin fragmento). No por host: URLhaus lista URLs de servicios de alojamiento compartido |
| Peso | 100 puntos y cortocircuito: una URL confirmada basta para el rojo |
| Recarga | `URLHAUS_REFRESH_SECONDS`, por defecto 12 h |
| Reintento tras fallo | `URLHAUS_RETRY_SECONDS`, por defecto 5 min (minimo que pide abuse.ch) |
| Timeout de descarga | `URLHAUS_TIMEOUT_SECONDS`, por defecto 30 s (fuera del SLA) |
| Clave | `URLHAUS_AUTH_KEY`, opcional; si existe se envia en `Auth-Key` |

Como L2 va antes que L3, un verde cacheado se sigue sirviendo aunque la URL entre
al feed despues, hasta que vence su TTL de 6 h.

## Tests

```bash
pytest
```

Los tests de la capa L2 contra PostgreSQL real se saltan si no hay base. Para
correrlos, apuntar a una de pruebas (la tabla se trunca en cada test):

```bash
TEST_DATABASE_URL=postgresql://USUARIO:CLAVE@localhost:5432/BASE_TEST pytest
```

## Roadmap de versiones
- `v0.1.0`: scaffold + heuristicas L1 + scoring ponderado
- `v0.1.1`: trazabilidad de redirecciones + metricas por capa
- `v0.2.0` (actual): cache L2 (PostgreSQL)
- `v0.3.0`: L3 (feed local de URLhaus)
- `v0.4.0`: L4 (Google Safe Browsing)
- `v0.5.0`: L5 (VirusTotal) + deploy Railway
