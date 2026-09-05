from fastapi import APIRouter
from pydantic import BaseModel, HttpUrl

from app.detectors.l1_heuristics import run_l1
from app.scoring import Verdict, evaluate

router = APIRouter()


class AnalyzeRequest(BaseModel):
    url: HttpUrl


class AnalyzeResponse(BaseModel):
    verdict: Verdict
    score: int
    reasons: list[str]


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    hits = run_l1(str(req.url))
    score, verdict = evaluate(hits)
    return AnalyzeResponse(
        verdict=verdict,
        score=score,
        reasons=[h.reason for h in hits],
    )
