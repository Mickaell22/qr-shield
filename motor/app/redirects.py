"""Trazabilidad de cadenas de redireccion (RF-009).

Resuelve la cadena de saltos HTTP de una URL hasta su destino terminal ANTES de
que corran las heuristicas. Motivo: el quishing esconde el destino detras de un
acortador, y una heuristica sobre `bit.ly/x8k2m` no ve nada anomalo mientras que
la URL terminal (`pagos-banc0.xyz`) si dispara.

No vive en `app/detectors/` a proposito: los detectores L1 son funciones puras
sin I/O, y este modulo hace peticiones de red. El invariante de `detectors/` se
mantiene intacto.

Limitacion conocida y declarada fuera de alcance: no se ejecuta JavaScript, asi
que las redirecciones por JS o por `<meta http-equiv="refresh">` no se siguen.
"""

import ipaddress
import socket
import time
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx

from app.config import (
    PRODUCT_NAME,
    REDIRECT_MAX_HOPS,
    REDIRECT_TIMEOUT_SECONDS,
    REDIRECT_TOTAL_TIMEOUT_SECONDS,
)

REDIRECT_STATUS = frozenset({301, 302, 303, 307, 308})

# Servidores que no soportan HEAD: los canonicos son 405 y 501, pero en la
# practica varios CDN responden 400 o 403 a un HEAD y sirven el GET sin drama.
HEAD_UNSUPPORTED_STATUS = frozenset({400, 403, 405, 501})

USER_AGENT = f"{PRODUCT_NAME}-Motor/1.0 (+deteccion de quishing)"


class _BlockedTarget(Exception):
    """El destino no es una URL publica alcanzable (esquema raro o IP interna)."""


@dataclass(frozen=True)
class RedirectTrace:
    """Cadena recorrida. `chain` incluye la URL inicial y todos los saltos.

    `resolved=False` significa que la cadena se corto (limite, timeout, bucle o
    error de red): el analisis continua igual sobre la ultima URL alcanzada, y
    `reason` explica por que quedo sin resolver.
    """

    chain: tuple[str, ...]
    resolved: bool
    reason: str = ""

    @property
    def final_url(self) -> str:
        return self.chain[-1]

    @property
    def hops(self) -> int:
        return len(self.chain) - 1

    @property
    def rewrote_url(self) -> bool:
        """Si el modulo cambio la URL que veran las capas siguientes."""
        return self.hops > 0

    @classmethod
    def identity(cls, url: str) -> "RedirectTrace":
        """Traza vacia, para cuando el modulo esta desactivado (corrida A/B)."""
        return cls(chain=(url,), resolved=True)


def _assert_public(url: str) -> None:
    """Rechaza esquemas no HTTP y destinos que apunten a la red interna.

    El motor hace peticiones salientes hacia una URL que viene de un QR
    desconocido: sin este filtro seria un SSRF que permite sondear la red del
    servidor. `is_global` cubre loopback, privadas, link-local y reservadas.

    ponytail: se resuelve el DNS aca y httpx lo resuelve otra vez al conectar,
    asi que queda una ventana TOCTOU (DNS rebinding). Techo aceptado: cerrarla
    exige conectar por IP y forzar el Host header o un transport propio. Camino
    de upgrade si el riesgo sube: transport custom que valide en el connect.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise _BlockedTarget(f"esquema no soportado: {parsed.scheme or 'ninguno'}")
    if not parsed.hostname:
        raise _BlockedTarget("URL sin host")
    try:
        infos = socket.getaddrinfo(parsed.hostname, None, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise _BlockedTarget(f"el host no resuelve: {parsed.hostname}") from exc
    for info in infos:
        if not ipaddress.ip_address(info[4][0]).is_global:
            raise _BlockedTarget(f"destino en red interna: {parsed.hostname}")


def _fetch(client: httpx.Client, url: str) -> httpx.Response:
    """Pide solo las cabeceras. HEAD primero; si el server no lo soporta, GET
    en streaming sin leer el cuerpo (no descarga la pagina)."""
    response = client.head(url)
    if response.status_code in HEAD_UNSUPPORTED_STATUS:
        with client.stream("GET", url) as streamed:
            return streamed
    return response


def resolve_chain(
    url: str,
    *,
    max_hops: int = REDIRECT_MAX_HOPS,
    timeout: float = REDIRECT_TIMEOUT_SECONDS,
    total_timeout: float = REDIRECT_TOTAL_TIMEOUT_SECONDS,
    client: httpx.Client | None = None,
    allow_private_hosts: bool = False,
) -> RedirectTrace:
    """Sigue la cadena de redirecciones y devuelve la traza completa.

    `allow_private_hosts` desactiva el filtro anti-SSRF y existe solo para los
    tests con transport simulado; nunca debe activarse sirviendo trafico real.
    """
    chain = [url]
    seen = {url}
    deadline = time.monotonic() + total_timeout
    owned = client is None
    client = client or httpx.Client(
        follow_redirects=False,
        timeout=timeout,
        headers={"User-Agent": USER_AGENT},
    )
    try:
        for _ in range(max_hops):
            if time.monotonic() >= deadline:
                return RedirectTrace(tuple(chain), False, "se agoto el tiempo total de la cadena")
            current = chain[-1]
            try:
                if not allow_private_hosts:
                    _assert_public(current)
                response = _fetch(client, current)
            except _BlockedTarget as exc:
                return RedirectTrace(tuple(chain), False, f"destino bloqueado: {exc}")
            except httpx.HTTPError as exc:
                return RedirectTrace(tuple(chain), False, f"error de red: {type(exc).__name__}")

            if response.status_code not in REDIRECT_STATUS:
                return RedirectTrace(tuple(chain), True)
            location = response.headers.get("location")
            if not location:
                # Redireccion sin Location: no hay a donde seguir, es el final.
                return RedirectTrace(tuple(chain), True)

            # `join` resuelve un Location relativo contra la URL actual.
            nxt = str(response.url.join(location))
            if nxt in seen:
                return RedirectTrace(tuple(chain), False, f"bucle de redirecciones hacia {nxt}")
            chain.append(nxt)
            seen.add(nxt)
        return RedirectTrace(tuple(chain), False, f"se supero el limite de {max_hops} saltos")
    finally:
        if owned:
            client.close()
