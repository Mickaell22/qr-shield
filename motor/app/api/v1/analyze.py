from fastapi import APIRouter
from pydantic import BaseModel, HttpUrl

router = APIRouter()


class AnalyzeRequest(BaseModel):
    url: HttpUrl


class AnalyzeResponse(BaseModel):
    verdict: str
    score: int
    reasons: list[str]


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    return AnalyzeResponse(verdict="green", score=0, reasons=[])
