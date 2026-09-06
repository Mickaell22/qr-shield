"""Cache de veredictos en PostgreSQL (capa L2).

Segunda capa de la cascada: si una URL ya se analizo y el veredicto sigue
vigente, se devuelve sin consultar las capas caras (L3 feed local, L4 Google
Safe Browsing, L5 VirusTotal, esta ultima con cuota de 4 req/min). Ese
cortocircuito es el motivo de la capa; sin el, cada escaneo repetido consume
cuota externa.

Regla de oro del modulo: **la cache nunca puede tumbar el analisis**. Si
PostgreSQL no esta configurado, esta caido o responde lento, el motor sigue
analizando como si la capa no existiera. Por eso todas las operaciones capturan
los errores y devuelven un miss en vez de propagar.
"""

import hashlib
import json
import logging
from dataclasses import dataclass

from psycopg_pool import ConnectionPool

from app.config import (
    CACHE_TTL_MALICIOUS_SECONDS,
    CACHE_TTL_SECONDS,
    DATABASE_URL,
)

logger = logging.getLogger("motor.cache")

# La clave es el hash de la URL terminal, no la URL: no obliga a indexar textos
# largos y evita guardar en claro lo que escaneo un usuario, igual que en el
# registro de metricas.
SCHEMA = """
CREATE TABLE IF NOT EXISTS verdict_cache (
    url_hash     text PRIMARY KEY,
    verdict      text NOT NULL,
    score        integer NOT NULL,
    reasons      jsonb NOT NULL DEFAULT '[]'::jsonb,
    source_layer text NOT NULL,
    created_at   timestamptz NOT NULL DEFAULT now(),
    expires_at   timestamptz NOT NULL
);
CREATE INDEX IF NOT EXISTS verdict_cache_expires_at_idx ON verdict_cache (expires_at);
"""

_pool: ConnectionPool | None = None


@dataclass(frozen=True)
class CachedVerdict:
    verdict: str
    score: int
    reasons: list[str]
    source_layer: str


def enabled() -> bool:
    """Sin DATABASE_URL la capa queda desactivada y la cascada la saltea."""
    return bool(DATABASE_URL)


def _key(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()


def _ttl_seconds(verdict: str) -> int:
    """TTL asimetrico: un veredicto rojo se guarda mas tiempo que el resto.

    Un dominio malicioso rara vez deja de serlo dentro del dia, mientras que uno
    limpio hoy puede quedar comprometido mañana. Servir un verde viejo es un
    falso negativo, que en deteccion cuesta mas caro que un falso positivo.
    """
    return CACHE_TTL_MALICIOUS_SECONDS if verdict == "red" else CACHE_TTL_SECONDS


def pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        # ponytail: pool global perezoso, de tamano fijo. Techo conocido: no se
        # dimensiona segun la carga. Alcanza para un worker; el camino de
        # upgrade, si la conexion escasea, es ajustar max_size por entorno.
        _pool = ConnectionPool(DATABASE_URL, min_size=1, max_size=4, open=True)
    return _pool


def init_schema() -> bool:
    """Crea la tabla si no existe. Devuelve si la cache quedo utilizable.

    ponytail: DDL idempotente al arrancar en vez de una herramienta de
    migraciones. Techo conocido: no versiona el esquema, asi que un cambio de
    columnas hay que aplicarlo a mano. Alcanza para una sola tabla; el camino de
    upgrade es Alembic cuando haya un modelo de datos de verdad.
    """
    if not enabled():
        logger.info("cache L2 desactivada: no hay DATABASE_URL configurada")
        return False
    try:
        with pool().connection() as conn:
            conn.execute(SCHEMA)
        return True
    except Exception as exc:
        logger.warning("cache L2 no disponible al crear el esquema: %s", type(exc).__name__)
        return False


def lookup(url: str) -> CachedVerdict | None:
    """Devuelve el veredicto vigente de la URL, o None si no hay o fallo la DB."""
    if not enabled():
        return None
    try:
        with pool().connection() as conn:
            row = conn.execute(
                "SELECT verdict, score, reasons, source_layer FROM verdict_cache "
                "WHERE url_hash = %s AND expires_at > now()",
                (_key(url),),
            ).fetchone()
    except Exception as exc:
        # Un miss degrada a analisis completo; propagar el error dejaria sin
        # veredicto a un usuario por un problema de infraestructura.
        logger.warning("cache L2 no disponible en lookup: %s", type(exc).__name__)
        return None
    if row is None:
        return None
    verdict, score, reasons, source_layer = row
    return CachedVerdict(verdict=verdict, score=score, reasons=reasons, source_layer=source_layer)


def store(url: str, *, verdict: str, score: int, reasons: list[str], source_layer: str) -> bool:
    """Guarda (o refresca) el veredicto. Devuelve si se llego a escribir.

    `expires_at` se calcula en el servidor de base de datos, no en el proceso:
    son dos relojes distintos y el del contenedor de la app puede derivar, lo
    que dejaria entradas vencidas al nacer o vivas de mas.
    """
    if not enabled():
        return False
    try:
        with pool().connection() as conn:
            conn.execute(
                "INSERT INTO verdict_cache "
                "  (url_hash, verdict, score, reasons, source_layer, expires_at) "
                "VALUES (%s, %s, %s, %s, %s, now() + make_interval(secs => %s)) "
                "ON CONFLICT (url_hash) DO UPDATE SET "
                "  verdict = EXCLUDED.verdict, score = EXCLUDED.score, "
                "  reasons = EXCLUDED.reasons, source_layer = EXCLUDED.source_layer, "
                "  created_at = now(), expires_at = EXCLUDED.expires_at",
                (
                    _key(url),
                    verdict,
                    score,
                    json.dumps(reasons, ensure_ascii=False),
                    source_layer,
                    _ttl_seconds(verdict),
                ),
            )
        return True
    except Exception as exc:
        logger.warning("cache L2 no disponible en store: %s", type(exc).__name__)
        return False


def close() -> None:
    """Cierra el pool al apagar el proceso.

    Sin esto psycopg no logra parar sus hilos y espera 5 segundos por cada uno
    antes de rendirse, con lo que cada reinicio del servicio se vuelve un
    apagado sucio de varios segundos.
    """
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None
