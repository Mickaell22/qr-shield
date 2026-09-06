"""Configuracion del motor leida del entorno.

Todo lo que cambia entre entornos (o entre corridas del benchmark) vive aca y
NO escrito en el codigo que lo consume. Los defaults son valores de referencia
para desarrollo, no secretos.
"""

import os

# El nombre del producto es provisional: se define en un unico lugar para que
# un cambio de nombre sea una sola linea y no un barrido por todo el codigo.
PRODUCT_NAME = os.getenv("PRODUCT_NAME", "Umbral")

FALSY = {"0", "false", "no", "off"}


def _flag(name: str, default: str) -> bool:
    return os.getenv(name, default).strip().lower() not in FALSY


# --- Trazabilidad de redirecciones (RF-009) ---

# Interruptor del modulo. Existe para poder correr el benchmark A/B sobre el
# mismo dataset con la trazabilidad activada y desactivada: esa comparacion es
# la evidencia del aporte del modulo, no una feature flag de conveniencia.
REDIRECT_TRACING_ENABLED = _flag("REDIRECT_TRACING_ENABLED", "true")

# Tope de saltos de la cadena. Referencia del documento de alcance: 10.
REDIRECT_MAX_HOPS = int(os.getenv("REDIRECT_MAX_HOPS", "10"))

# Timeout de CADA peticion. Alineado con el SLA: ninguna capa puede colgar mas
# de 1.5s sin devolver un veredicto parcial.
REDIRECT_TIMEOUT_SECONDS = float(os.getenv("REDIRECT_TIMEOUT_SECONDS", "1.5"))

# Presupuesto de la cadena COMPLETA. Se mantiene por debajo del SLA de 3s para
# dejar margen a las capas L2-L5 que corren despues.
REDIRECT_TOTAL_TIMEOUT_SECONDS = float(os.getenv("REDIRECT_TOTAL_TIMEOUT_SECONDS", "2.0"))

# --- Metricas por capa (RF-008) ---

# Registrar la URL completa en el log de metricas. Por defecto NO: RF-008 pide
# registro anonimo y en produccion se guarda solo un hash. Se activa para el
# benchmark, donde hace falta la URL para cruzar cada analisis con la etiqueta
# del dataset.
METRICS_LOG_URLS = _flag("METRICS_LOG_URLS", "false")
