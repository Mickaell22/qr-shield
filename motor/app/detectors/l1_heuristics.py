import ipaddress
from dataclasses import dataclass
from urllib.parse import urlparse

URL_LENGTH_THRESHOLD = 100
URL_LENGTH_SCORE = 30
IP_LITERAL_SCORE = 40
SHORTENER_SCORE = 25

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


def run_l1(url: str) -> list[HeuristicResult]:
    checks = [check_url_length(url), check_ip_literal(url), check_shortener(url)]
    return [r for r in checks if r.triggered]
