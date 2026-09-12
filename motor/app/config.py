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

# --- Cache de veredictos (L2) ---

# Cadena de conexion a PostgreSQL. Vacia = capa L2 desactivada: el motor arranca
# y analiza igual, solo sin cache. No lleva default con host ni credenciales.
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Vigencia de un veredicto no concluyente (verde o amarillo). 6 horas: un
# dominio limpio hoy puede quedar comprometido, asi que no se sirve indefinido.
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", str(6 * 3600)))

# Vigencia de un veredicto rojo. 24 horas: un dominio malicioso rara vez deja
# de serlo dentro del dia, y servir de mas un rojo es mucho menos grave que
# servir de mas un verde.
CACHE_TTL_MALICIOUS_SECONDS = int(os.getenv("CACHE_TTL_MALICIOUS_SECONDS", str(24 * 3600)))

# --- Feed local de URLhaus (L3) ---

# URL del volcado CSV de abuse.ch. Vacia = capa L3 desactivada: el motor analiza
# igual sin ella. No lleva default con host, igual que DATABASE_URL.
URLHAUS_FEED_URL = os.getenv("URLHAUS_FEED_URL", "")

# Clave de abuse.ch. Opcional: los volcados CSV hoy son libres, pero si se
# define se envia en la cabecera Auth-Key.
URLHAUS_AUTH_KEY = os.getenv("URLHAUS_AUTH_KEY", "")

# Cada cuanto se recarga el feed. 12 horas: abuse.ch pide no descargar el
# volcado mas de una vez cada 5 minutos, y el alcance fija el refresco en 12h.
URLHAUS_REFRESH_SECONDS = int(os.getenv("URLHAUS_REFRESH_SECONDS", str(12 * 3600)))

# Reintento tras una descarga fallida. Mas corto que el refresco para que un
# fallo al arrancar no deje la capa apagada 12 horas; no menos de 5 minutos por
# la politica de uso de abuse.ch.
URLHAUS_RETRY_SECONDS = int(os.getenv("URLHAUS_RETRY_SECONDS", "300"))

# Timeout de la descarga. Corre en segundo plano, fuera del SLA del analisis, y
# el volcado pesa algunos MB: no se alinea con los 1.5s por capa.
URLHAUS_TIMEOUT_SECONDS = float(os.getenv("URLHAUS_TIMEOUT_SECONDS", "30"))
