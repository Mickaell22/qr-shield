import ipaddress
from collections.abc import Sequence
from dataclasses import dataclass
from urllib.parse import urlparse, urlunparse

URL_LENGTH_THRESHOLD = 100
URL_LENGTH_SCORE = 30
IP_LITERAL_SCORE = 40
SHORTENER_SCORE = 25
SUSPICIOUS_TLD_SCORE = 35
PUNYCODE_SCORE = 50

PUNYCODE_PREFIX = "xn--"

# ponytail: lista estatica de acortadores conocidos. Techo: no es exhaustiva y
# no se autoactualiza; el camino de upgrade es una fuente mantenida (feed) si la
# cobertura se queda corta. Para el alcance de la tesis, una lista curada basta.
SHORTENER_DOMAINS = frozenset(
    {
        "bit.ly",
        "t.co",
        "goo.gl",
        "tinyurl.com",
        "ow.ly",
        "is.gd",
        "buff.ly",
        "cutt.ly",
        "rebrand.ly",
        "bl.ink",
        "shorturl.at",
        "rb.gy",
        "t.ly",
        "tiny.cc",
        "shorte.st",
        # Redirectores de QR dinamicos (QR Code Generator): el QR impreso apunta
        # aca y el destino se cambia despues sin reimprimir. Esconden el destino
        # igual que un acortador. Son 74 de las 500 URLs maliciosas del
        # benchmark de 2026-09-13.
        "qrco.de",
        "q-r.to",
        "l.ead.me",
    }
)

# ponytail: lista estatica de TLDs con tasa de abuso alta (los gratuitos de
# Freenom, gTLD nuevos de registro barato y los que colisionan con extensiones
# de archivo). Techo: es una foto del panorama actual y no se autoactualiza; el
# camino de upgrade es un ranking de abuso mantenido (ej. Spamhaus) si la
# precision se queda corta. Se excluyen ccTLD de paises grandes a proposito:
# el volumen legitimo genera demasiados falsos positivos para el peso que lleva.
SUSPICIOUS_TLDS = frozenset(
    {
        "tk",
        "ml",
        "ga",
        "cf",
        "gq",
        "top",
        "xyz",
        "buzz",
        "click",
        "link",
        "work",
        "rest",
        "country",
        "kim",
        "zip",
        "mov",
    }
)


@dataclass(frozen=True)
class HeuristicResult:
    triggered: bool
    score: int
    reason: str


def check_url_length(url: str) -> HeuristicResult:
    length = len(url)
    if length > URL_LENGTH_THRESHOLD:
        return HeuristicResult(
            triggered=True,
            score=URL_LENGTH_SCORE,
            reason=f"URL excede {URL_LENGTH_THRESHOLD} caracteres (longitud {length})",
        )
    return HeuristicResult(triggered=False, score=0, reason="")


def check_ip_literal(url: str) -> HeuristicResult:
    host = urlparse(url).hostname
    if host is None:
        return HeuristicResult(triggered=False, score=0, reason="")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        return HeuristicResult(triggered=False, score=0, reason="")
    return HeuristicResult(
        triggered=True,
        score=IP_LITERAL_SCORE,
        reason=f"El host es una IP literal ({host}) en vez de un dominio",
    )


def check_shortener(url: str) -> HeuristicResult:
    host = urlparse(url).hostname
    if host is None:
        return HeuristicResult(triggered=False, score=0, reason="")
    host = host.lower()
    if host.startswith("www."):
        host = host[len("www.") :]
    if host not in SHORTENER_DOMAINS:
        return HeuristicResult(triggered=False, score=0, reason="")
    return HeuristicResult(
        triggered=True,
        score=SHORTENER_SCORE,
        reason=f"El host es un acortador de URLs conocido ({host})",
    )


def check_suspicious_tld(url: str) -> HeuristicResult:
    host = urlparse(url).hostname
    if host is None:
        return HeuristicResult(triggered=False, score=0, reason="")
    tld = host.rpartition(".")[2]
    if tld not in SUSPICIOUS_TLDS:
        return HeuristicResult(triggered=False, score=0, reason="")
    return HeuristicResult(
        triggered=True,
        score=SUSPICIOUS_TLD_SCORE,
        reason=f"El dominio usa un TLD con alta tasa de abuso (.{tld})",
    )


def check_punycode(url: str) -> HeuristicResult:
    host = urlparse(url).hostname
    if host is None:
        return HeuristicResult(triggered=False, score=0, reason="")
    # urlparse no convierte un host IDN unicode a punycode: se deja tal cual. Un
    # host no ASCII es la misma senal de homografo que el prefijo xn--, asi que
    # la heuristica cubre las dos formas de escribir el mismo dominio.
    is_idn = not host.isascii() or any(
        label.startswith(PUNYCODE_PREFIX) for label in host.split(".")
    )
    if not is_idn:
        return HeuristicResult(triggered=False, score=0, reason="")
    return HeuristicResult(
        triggered=True,
        score=PUNYCODE_SCORE,
        reason=(
            f"El host usa caracteres internacionales / punycode ({host}), posible ataque homografo"
        ),
    )


def _without_query(url: str) -> str:
    return urlunparse(urlparse(url)._replace(query="", fragment=""))


def run_l1(url: str, chain: Sequence[str] = ()) -> list[HeuristicResult]:
    """Corre las heuristicas sobre el destino terminal `url`.

    `chain` es la cadena de redirecciones completa (con `url` al final). Los
    checks siguen siendo funciones puras de una URL; lo que decide la cadena es
    a que URL se aplica cada uno, por dos senales que el destino solo pierde:

    - **Acortador**: se revisa cada salto. Tras resolver `bit.ly/x` el destino ya
      no es un acortador, y sin esto la trazabilidad borraba la senal de que el
      QR escondia su destino (8 maliciosas del benchmark se detectaban solo sin
      trazabilidad).
    - **Longitud**: la URL del QR se mide completa, pero un destino alcanzado por
      redireccion se mide sin query. La query de un salto la genera el servidor
      (tokens de SSO, `state`, `continue=`), no quien imprimio el QR: medida
      entera, cualquier portada que redirige a un login disparaba la heuristica
      (4 falsos positivos del benchmark sobre sitios legitimos).
    """
    chain = tuple(chain) or (url,)
    redirigida = len(chain) > 1
    acortador = next((r for r in map(check_shortener, chain) if r.triggered), None)
    longitud = check_url_length(chain[0])
    if not longitud.triggered and redirigida:
        longitud = check_url_length(_without_query(url))
    checks = [
        longitud,
        check_ip_literal(url),
        acortador or check_shortener(url),
        check_suspicious_tld(url),
        check_punycode(url),
    ]
    return [r for r in checks if r.triggered]
