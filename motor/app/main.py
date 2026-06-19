from fastapi import FastAPI

from app.api.v1 import analyze

app = FastAPI(
    title="QR Shield Motor",
    version="0.1.0",
    description="API de deteccion de QR maliciosos (quishing) - NovaTools",
)

app.include_router(analyze.router, prefix="/v1", tags=["analyze"])


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
