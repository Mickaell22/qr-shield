"""Instrumentacion de metricas por capa (RF-008 / Objetivo Especifico 4).

Cada analisis emite un registro con timestamp, veredicto, capa responsable del
veredicto, servicios externos consultados, tiempo por capa y total, y los datos
de la trazabilidad. Con eso el reporte de validacion calcula precision,
exhaustividad y tiempos desglosados por capa, la proporcion de detecciones
resueltas localmente (L1-L3) frente a las externas (L4-L5), y la variacion de la
tasa de deteccion con y sin trazabilidad sobre el mismo dataset.

Se instrumenta ahora, con una sola capa viva, a proposito: medir la cascada
cuando ya tiene cinco capas obliga a tocarlas todas.
"""

import hashlib
import json
import logging
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime

from app import cache
from app.config import METRICS_LOG_URLS, REDIRECT_TRACING_ENABLED

# Logger con nombre tecnico, no el del producto: PRODUCT_NAME es configurable y
# un rename no debe cambiar la clave por la que se filtran los logs.
logger = logging.getLogger("motor.metrics")


@dataclass
class LayerMetric:
    """Medicion de una capa de la cascada.

    `score` es lo que la capa aporto al total (sin el tope de 100, que se aplica
    al sumar), `hits` cuantas senales disparo y `service` nombra el servicio
    externo consultado: queda en None en las capas locales.

    `short_circuited` marca la capa que corto la cascada: es el dato con el que
    el reporte de validacion mide cuantas detecciones se resolvieron localmente
    (L1-L3) frente a las que llegaron a consultar un servicio externo (L4-L5).
    """

    layer: str
    duration_ms: float = 0.0
    score: int = 0
    hits: int = 0
    service: str | None = None
    short_circuited: bool = False


def _anonymize(url: str) -> str:
    """Devuelve la URL tal cual solo si se pidio explicitamente registrarla.

    RF-008 exige un registro anonimo: la URL que escaneo un usuario no se
    escribe al log en produccion. El benchmark si necesita la URL para cruzar
    cada analisis con la etiqueta del dataset, y para eso esta METRICS_LOG_URLS.
    El hash conserva lo unico que hace falta sin la URL: poder agrupar los
    analisis de una misma URL entre corridas.
    """
    if METRICS_LOG_URLS:
        return url
    return "sha256:" + hashlib.sha256(url.encode()).hexdigest()[:16]


@dataclass
class AnalysisMetrics:
    """Recolector de un analisis. Se crea uno por request y se emite al final."""

    layers: list[LayerMetric] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    _start: float = field(default_factory=time.monotonic)

    @contextmanager
    def measure(self, layer: str, service: str | None = None) -> Iterator[LayerMetric]:
        """Cronometra una capa. El bloque recibe la medicion para completar
        `score` y `hits`; la duracion se registra aunque el bloque falle."""
        metric = LayerMetric(layer=layer, service=service)
        start = time.monotonic()
        try:
            yield metric
        finally:
            metric.duration_ms = round((time.monotonic() - start) * 1000, 3)
            self.layers.append(metric)

    @property
    def deciding_layer(self) -> str:
        """Capa responsable del veredicto.

        Manda la capa que corto la cascada: si un hit de cache resuelve el
        analisis, la responsable es esa aunque no haya sumado puntos propios.
        Sin cortocircuito, responde la ultima capa que aporto puntos.

        Si nadie corto ni sumo, el veredicto (un verde) no lo emitio ninguna
        capa sino la cascada al agotarse: `cascade`. Atribuirselo a la ultima
        que corrio contaria como resuelta en L2 una consulta que fue un miss, y
        falsearia la proporcion de detecciones por capa del reporte. `none` es
        el caso distinto de que no haya corrido ninguna capa.
        """
        for metrica in self.layers:
            if metrica.short_circuited:
                return metrica.layer
        con_puntos = [m.layer for m in self.layers if m.score > 0]
        if con_puntos:
            return con_puntos[-1]
        return "cascade" if self.layers else "none"

    @property
    def services(self) -> list[str]:
        return [m.service for m in self.layers if m.service]

    def record(
        self,
        *,
        url: str,
        verdict: str,
        score: int,
        redirect_hops: int,
        redirect_rewrote_url: bool,
        redirect_resolved: bool,
    ) -> dict:
        """Arma el registro del analisis. `total_ms` se congela aca."""
        return {
            "timestamp": self.timestamp,
            "url": _anonymize(url),
            "verdict": verdict,
            "score": score,
            "deciding_layer": self.deciding_layer,
            "services": self.services,
            "total_ms": round((time.monotonic() - self._start) * 1000, 3),
            "layers": [asdict(m) for m in self.layers],
            "redirects": {
                "hops": redirect_hops,
                "rewrote_url": redirect_rewrote_url,
                "resolved": redirect_resolved,
            },
            # Separa la corrida A de la B: sin esta marca los dos conjuntos de
            # registros del benchmark quedan mezclados y la comparacion no se
            # puede reconstruir.
            "tracing_enabled": REDIRECT_TRACING_ENABLED,
        }

    def emit(self, **kwargs) -> dict:
        """Registra el analisis como una linea JSON y devuelve el registro.

        La linea de log es sincrona pero va a stdout, que no frena. La escritura
        lenta, la de PostgreSQL, no se hace aca: el endpoint la agenda con
        `persist` para despues de enviar la respuesta.
        """
        registro = self.record(**kwargs)
        logger.info(json.dumps(registro, ensure_ascii=False))
        return registro


# --- Persistencia de los registros (fuente del panel de RF-008) ---

# El registro se guarda entero como jsonb: el panel y el reporte de validacion
# lo consultan con operadores jsonb, y un campo nuevo de las metricas no obliga
# a migrar columnas. La URL ya viene anonimizada desde `record`.
SCHEMA = """
CREATE TABLE IF NOT EXISTS analysis_metrics (
    id         bigserial PRIMARY KEY,
    created_at timestamptz NOT NULL DEFAULT now(),
    record     jsonb NOT NULL
);
CREATE INDEX IF NOT EXISTS analysis_metrics_created_at_idx ON analysis_metrics (created_at);
"""


def init_schema() -> bool:
    """Crea la tabla si hay base configurada. Devuelve si quedo utilizable.

    Comparte base y pool con la cache L2: no hay una segunda conexion que
    configurar. Igual que la cache, un fallo no impide arrancar el motor.
    """
    if not cache.enabled():
        return False
    try:
        with cache.pool().connection() as conn:
            conn.execute(SCHEMA)
        return True
    except Exception as exc:
        logger.warning("persistencia de metricas no disponible: %s", type(exc).__name__)
        return False


def persist(registro: dict) -> bool:
    """Guarda el registro. Devuelve si se llego a escribir.

    Corre como tarea de fondo del endpoint, despues de enviar la respuesta: un
    PostgreSQL lento no puede comerse el SLA de 3s. Y como la cache, perder un
    registro de metricas nunca puede costarle el veredicto al usuario, asi que
    los errores se loguean y no suben.
    """
    if not cache.enabled():
        return False
    try:
        with cache.pool().connection() as conn:
            conn.execute(
                "INSERT INTO analysis_metrics (record) VALUES (%s)",
                (json.dumps(registro, ensure_ascii=False),),
            )
        return True
    except Exception as exc:
        logger.warning("no se pudo persistir el registro de metricas: %s", type(exc).__name__)
        return False
