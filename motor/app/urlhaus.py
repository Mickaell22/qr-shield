"""Feed local de URLhaus (capa L3).

Tercera capa de la cascada: compara las URLs de la cadena de redirecciones
contra el volcado CSV de URLs activas que publica abuse.ch. El feed se descarga
en segundo plano y se guarda en memoria, asi que la consulta por analisis es
una busqueda en un conjunto, sin red: la capa no consume nada del SLA de 3s.

No vive en `app/detectors/` por la misma razon que `redirects.py`: descarga el
feed por red, y los detectores de ese paquete son funciones puras sin I/O.

Regla heredada de la cache L2: **el feed nunca puede tumbar el analisis**. Si
no esta configurado o no se pudo descargar todavia, la capa no corre y la
cascada sigue sin ella. Una descarga fallida conserva el ultimo feed bueno.
"""

import csv
import io
import logging
from urllib.parse import urlsplit, urlunsplit

import httpx

from app.config import URLHAUS_AUTH_KEY, URLHAUS_FEED_URL, URLHAUS_TIMEOUT_SECONDS
from app.detectors.l1_heuristics import HeuristicResult

logger = logging.getLogger("motor.urlhaus")

# Una URL listada en un feed de amenazas confirmadas es suficiente por si sola
# para el rojo: no es una sospecha que tenga que sumarse a otra senal.
SCORE_LISTED = 100

# Columna de la URL en el CSV: id,dateadded,url,url_status,...
_URL_COLUMN = 2

# ponytail: conjunto en memoria reemplazado entero en cada recarga. La
# asignacion de la referencia es atomica, asi que no hace falta lock entre el
# hilo que recarga y los que consultan. Techo conocido: cada worker descarga y
# guarda su propia copia (~14k URLs, unos MB). El camino de upgrade, si se
# escala a varios workers, es volcar el feed a una tabla de PostgreSQL.
_urls: frozenset[str] | None = None


def normalize(url: str) -> str:
    """Forma canonica para comparar URLs del feed contra las del analisis.

    Pydantic `HttpUrl` agrega la barra final a un host sin ruta
    (`http://a.com` -> `http://a.com/`) y el feed no; ademas el esquema y el
    host no distinguen mayusculas. El fragmento no viaja al servidor, asi que
    tampoco cambia el destino. La ruta y la query SI se respetan tal cual.
    """
    parts = urlsplit(url.strip())
    return urlunsplit(
        (parts.scheme.lower(), parts.netloc.lower(), parts.path or "/", parts.query, "")
    )


def parse_feed(text: str) -> frozenset[str]:
    """Extrae las URLs normalizadas del CSV, ignorando la cabecera comentada."""
    lines = (line for line in io.StringIO(text) if not line.startswith("#"))
    return frozenset(
        normalize(row[_URL_COLUMN]) for row in csv.reader(lines) if len(row) > _URL_COLUMN
    )


def enabled() -> bool:
    """Sin URLHAUS_FEED_URL la capa queda desactivada y la cascada la saltea."""
    return bool(URLHAUS_FEED_URL)


def ready() -> bool:
    """La capa solo corre con un feed cargado: medirla vacia la haria figurar
    como una capa que consulto y no encontro nada, y falsearia las metricas."""
    return _urls is not None


def refresh(client: httpx.Client | None = None) -> bool:
    """Descarga el feed y reemplaza el conjunto. Devuelve si se actualizo.

    Ante cualquier error se conserva el feed anterior: uno de hace 12 horas
    sigue siendo mucho mejor que ninguno.
    """
    global _urls
    if not enabled():
        return False
    headers = {"Auth-Key": URLHAUS_AUTH_KEY} if URLHAUS_AUTH_KEY else {}
    try:
        with client or httpx.Client(timeout=URLHAUS_TIMEOUT_SECONDS) as http:
            response = http.get(URLHAUS_FEED_URL, headers=headers)
            response.raise_for_status()
        urls = parse_feed(response.text)
    except Exception as exc:
        logger.warning("feed URLhaus no disponible: %s", type(exc).__name__)
        return False
    # Un 200 sin URLs (pagina de error, feed truncado) no puede vaciar la capa:
    # se trataria como si ninguna URL fuera maliciosa.
    if not urls:
        logger.warning("feed URLhaus descargado sin URLs; se conserva el anterior")
        return False
    _urls = urls
    logger.info("feed URLhaus cargado: %d URLs", len(urls))
    return True


def lookup(chain: tuple[str, ...] | list[str]) -> HeuristicResult | None:
    """Busca cada URL de la cadena de redirecciones en el feed.

    Se revisa la cadena completa y no solo el destino: un salto intermedio
    listado (un redirector comprometido) es evidencia aunque el destino final
    no figure todavia en el feed. El motivo no incluye la URL, porque termina
    guardado en la cache L2 y ahi no se guarda nada en claro.
    """
    urls = _urls
    if urls is None:
        return None
    ultimo = len(chain) - 1
    for i, url in enumerate(chain):
        if normalize(url) in urls:
            if i == ultimo:
                donde = "el destino final"
            elif i == 0:
                donde = "la URL leida del codigo"
            else:
                donde = f"el salto {i} de la cadena de redirecciones"
            return HeuristicResult(
                triggered=True,
                score=SCORE_LISTED,
                reason=f"{donde} figura en URLhaus (abuse.ch) como URL maliciosa activa",
            )
    return None
