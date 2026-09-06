from fastapi import APIRouter
from pydantic import BaseModel, HttpUrl

from app import cache
from app.config import REDIRECT_TRACING_ENABLED
from app.detectors.l1_heuristics import run_l1
from app.redirects import RedirectTrace, resolve_chain
from app.scoring import Verdict, evaluate
from app.telemetry import AnalysisMetrics

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


class LayerMetricInfo(BaseModel):
    layer: str
    duration_ms: float
    score: int
    hits: int
    service: str | None = None
    short_circuited: bool = False


class MetricsInfo(BaseModel):
    """Desglose por capa del analisis (RF-008). Va en la respuesta ademas del
    log: la validacion necesita el tiempo por capa y la capa responsable del
    veredicto, y desde el cliente es lo que permite auditar una deteccion."""

    total_ms: float
    deciding_layer: str
    layers: list[LayerMetricInfo]


class AnalyzeResponse(BaseModel):
    verdict: Verdict
    score: int
    reasons: list[str]
    final_url: str
    redirects: RedirectInfo
    metrics: MetricsInfo


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    url = str(req.url)
    metrics = AnalysisMetrics()

    # Las heuristicas corren sobre el destino terminal, no sobre el acortador.
    # Con la trazabilidad apagada (corrida A/B) se analiza la URL tal cual vino.
    with metrics.measure("redirects") as medicion:
        trace = resolve_chain(url) if REDIRECT_TRACING_ENABLED else RedirectTrace.identity(url)
        medicion.hits = trace.hops

    # L1 corre siempre, incluso si despues la cache resuelve: es local e
    # instantanea, su resultado es el que vale si la cache falla, y registrar su
    # score en las metricas permite contrastar la senal local contra el
    # veredicto consolidado.
    with metrics.measure("L1") as medicion:
        hits = run_l1(trace.final_url)
        medicion.hits = len(hits)
        medicion.score = sum(h.score for h in hits)

    # Se resuelve el veredicto en vivo antes de tocar la cache: la capa
    # responsable se lee ahora, cuando solo corrieron las capas que evaluan. Si
    # se leyera despues, la propia L2 figuraria como origen del veredicto que
    # ella misma va a guardar.
    score_vivo, verdict_vivo = evaluate(hits)
    capa_responsable = metrics.deciding_layer

    # La capa solo se mide si existe en esta configuracion: registrar una L2
    # desactivada la haria figurar como responsable de todo veredicto verde,
    # y falsearia la proporcion de detecciones por capa del reporte.
    cached = None
    if cache.enabled():
        with metrics.measure("L2") as medicion:
            cached = cache.lookup(trace.final_url)
            medicion.short_circuited = cached is not None

    if cached is not None:
        score, verdict = cached.score, cached.verdict
        origen = "veredicto servido desde la cache L2 (analisis previo)"
        reasons = [*cached.reasons, origen]
    else:
        score, verdict = score_vivo, verdict_vivo
        reasons = [h.reason for h in hits]
        # Una cadena sin resolver deja el analisis sobre una URL intermedia: ese
        # veredicto es parcial y no se cachea, o se serviria como definitivo.
        if trace.resolved:
            cache.store(
                trace.final_url,
                verdict=verdict,
                score=score,
                reasons=reasons,
                source_layer=capa_responsable,
            )

    if not trace.resolved:
        reasons.append(f"cadena de redirecciones no resuelta: {trace.reason}")

    registro = metrics.emit(
        url=url,
        verdict=verdict,
        score=score,
        redirect_hops=trace.hops,
        redirect_rewrote_url=trace.rewrote_url,
        redirect_resolved=trace.resolved,
    )

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
        metrics=MetricsInfo(
            total_ms=registro["total_ms"],
            deciding_layer=registro["deciding_layer"],
            layers=registro["layers"],
        ),
    )
