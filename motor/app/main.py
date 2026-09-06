from fastapi import FastAPI

from app.api.v1 import analyze
from app.config import PRODUCT_NAME

app = FastAPI(
    title=f"{PRODUCT_NAME} Motor",
    version="0.1.0",
    description="API de deteccion de QR maliciosos (quishing) - NovaTools",
)

app.include_router(analyze.router, prefix="/v1", tags=["analyze"])


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
