import asyncio
import contextlib
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import cache, urlhaus
from app.api.v1 import analyze
from app.config import PRODUCT_NAME, URLHAUS_REFRESH_SECONDS, URLHAUS_RETRY_SECONDS


async def _refrescar_urlhaus() -> None:
    # La descarga corre en un hilo para no bloquear el event loop, y en una
    # tarea aparte para no demorar el arranque: mientras no haya feed, la capa
    # L3 simplemente no corre.
    while True:
        ok = await asyncio.to_thread(urlhaus.refresh)
        await asyncio.sleep(URLHAUS_REFRESH_SECONDS if ok else URLHAUS_RETRY_SECONDS)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    # Crea la tabla de la cache si falta. Si la base no esta configurada o no
    # responde, el motor arranca igual con la capa L2 desactivada: la deteccion
    # no depende de la cache.
    cache.init_schema()
    tarea = asyncio.create_task(_refrescar_urlhaus()) if urlhaus.enabled() else None
    yield
    if tarea is not None:
        tarea.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await tarea
    cache.close()


app = FastAPI(
    title=f"{PRODUCT_NAME} Motor",
    # Se bumpea junto con pyproject.toml en cada release. No se lee de la
    # metadata del paquete: con un install editable esa metadata queda
    # congelada en la version con la que se instalo, y la API reportaria
    # una version vieja sin que nadie lo note.
    version="0.3.0",
    description="API de deteccion de QR maliciosos (quishing) - NovaTools",
    lifespan=lifespan,
)

app.include_router(analyze.router, prefix="/v1", tags=["analyze"])


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
