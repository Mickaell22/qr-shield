from fastapi import APIRouter
from pydantic import BaseModel, HttpUrl

from app.detectors.l1_heuristics import run_l1

router = APIRouter()


class AnalyzeRequest(BaseModel):
    url: HttpUrl


class AnalyzeResponse(BaseModel):
    verdict: str
    score: int
    reasons: list[str]


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    hits = run_l1(str(req.url))
    score = sum(h.score for h in hits)
    verdict = "yellow" if hits else "green"
    return AnalyzeResponse(
        verdict=verdict,
        score=score,
        reasons=[h.reason for h in hits],
    )
