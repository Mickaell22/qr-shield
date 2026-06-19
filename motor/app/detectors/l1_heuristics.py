from dataclasses import dataclass

URL_LENGTH_THRESHOLD = 100
URL_LENGTH_SCORE = 30


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


def run_l1(url: str) -> list[HeuristicResult]:
    checks = [check_url_length(url)]
    return [r for r in checks if r.triggered]
