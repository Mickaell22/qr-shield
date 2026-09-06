from fastapi import FastAPI

from app.api.v1 import analyze
from app.config import PRODUCT_NAME

app = FastAPI(
    title=f"{PRODUCT_NAME} Motor",
    # Se bumpea junto con pyproject.toml en cada release. No se lee de la
    # metadata del paquete: con un install editable esa metadata queda
    # congelada en la version con la que se instalo, y la API reportaria
    # una version vieja sin que nadie lo note.
    version="0.1.1",
    description="API de deteccion de QR maliciosos (quishing) - NovaTools",
)

app.include_router(analyze.router, prefix="/v1", tags=["analyze"])


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
