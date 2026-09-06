from fastapi import APIRouter
from pydantic import BaseModel, HttpUrl

from app.config import REDIRECT_TRACING_ENABLED
from app.detectors.l1_heuristics import run_l1
from app.redirects import RedirectTrace, resolve_chain
from app.scoring import Verdict, evaluate

router = APIRouter()


class AnalyzeRequest(BaseModel):
    url: HttpUrl


class RedirectInfo(BaseModel):
    """Cadena recorrida. Se expone completa por requisito funcional (RF-009):
    el usuario y la validacion deben poder ver la traza, no solo el destino."""

    chain: list[str]
    hops: int
    resolved: bool
    rewrote_url: bool
    reason: str = ""


class AnalyzeResponse(BaseModel):
    verdict: Verdict
    score: int
    reasons: list[str]
    final_url: str
    redirects: RedirectInfo


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    url = str(req.url)
    # Las heuristicas corren sobre el destino terminal, no sobre el acortador.
    # Con la trazabilidad apagada (corrida A/B) se analiza la URL tal cual vino.
    trace = resolve_chain(url) if REDIRECT_TRACING_ENABLED else RedirectTrace.identity(url)
    hits = run_l1(trace.final_url)
    score, verdict = evaluate(hits)

    reasons = [h.reason for h in hits]
    if not trace.resolved:
        reasons.append(f"cadena de redirecciones no resuelta: {trace.reason}")

    return AnalyzeResponse(
        verdict=verdict,
        score=score,
        reasons=reasons,
        final_url=trace.final_url,
        redirects=RedirectInfo(
            chain=list(trace.chain),
            hops=trace.hops,
            resolved=trace.resolved,
            rewrote_url=trace.rewrote_url,
            reason=trace.reason,
        ),
    )
