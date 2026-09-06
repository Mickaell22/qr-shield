"""Tests de la capa L2.

Los de integracion corren contra un PostgreSQL real y se saltan si no hay uno:
el SQL (make_interval, ON CONFLICT, jsonb) no lo valida ningun doble de prueba.
Para correrlos: TEST_DATABASE_URL=postgresql://... pytest
"""

import os

import pytest

from app import cache

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "")


@pytest.fixture
def cache_apagada(monkeypatch):
    monkeypatch.setattr(cache, "DATABASE_URL", "")


@pytest.fixture
def cache_rota(monkeypatch):
    """Cache configurada pero con la base inalcanzable."""
    monkeypatch.setattr(cache, "DATABASE_URL", "postgresql://nadie@127.0.0.1:1/nada")

    def _revienta():
        raise OSError("conexion rechazada")

    monkeypatch.setattr(cache, "pool", _revienta)


def test_sin_database_url_la_capa_queda_desactivada(cache_apagada):
    assert cache.enabled() is False
    assert cache.lookup("https://example.com/") is None
    guardado = cache.store(
        "https://example.com/", verdict="green", score=0, reasons=[], source_layer="L1"
    )
    assert guardado is False


def test_una_base_caida_devuelve_miss_en_vez_de_reventar(cache_rota):
    # La deteccion no puede depender de la cache: un fallo de infraestructura
    # degrada a analisis completo, nunca a un error para el usuario.
    assert cache.lookup("https://example.com/") is None
    guardado = cache.store(
        "https://example.com/", verdict="red", score=70, reasons=[], source_layer="L1"
    )
    assert guardado is False
    assert cache.init_schema() is False


def test_el_veredicto_rojo_se_guarda_mas_tiempo_que_el_resto():
    assert cache._ttl_seconds("red") > cache._ttl_seconds("green")
    assert cache._ttl_seconds("yellow") == cache._ttl_seconds("green")


def test_la_clave_es_un_hash_de_la_url_no_la_url():
    clave = cache._key("https://pagos-banc0.xyz/login")
    assert "pagos-banc0" not in clave
    assert len(clave) == 64
    assert clave == cache._key("https://pagos-banc0.xyz/login")


# --- Integracion contra PostgreSQL real ---

pytestmark_integracion = pytest.mark.skipif(
    not TEST_DATABASE_URL, reason="requiere TEST_DATABASE_URL apuntando a un PostgreSQL"
)


@pytest.fixture
def base(monkeypatch):
    monkeypatch.setattr(cache, "DATABASE_URL", TEST_DATABASE_URL)
    monkeypatch.setattr(cache, "_pool", None)
    assert cache.init_schema() is True
    with cache.pool().connection() as conn:
        conn.execute("TRUNCATE verdict_cache")
    yield
    monkeypatch.setattr(cache, "_pool", None)


@pytestmark_integracion
def test_guarda_y_recupera_el_veredicto(base):
    url = "http://pagos-banc0.xyz/login"
    assert cache.store(
        url, verdict="red", score=70, reasons=["IP literal"], source_layer="L1"
    ) is True

    guardado = cache.lookup(url)
    assert guardado.verdict == "red"
    assert guardado.score == 70
    assert guardado.reasons == ["IP literal"]
    assert guardado.source_layer == "L1"


@pytestmark_integracion
def test_una_url_no_analizada_es_un_miss(base):
    assert cache.lookup("https://nunca-vista.example/") is None


@pytestmark_integracion
def test_reanalizar_refresca_la_entrada_en_vez_de_duplicarla(base):
    url = "https://example.com/"
    cache.store(url, verdict="green", score=0, reasons=[], source_layer="L1")
    cache.store(url, verdict="red", score=70, reasons=["cambio"], source_layer="L1")

    with cache.pool().connection() as conn:
        (filas,) = conn.execute("SELECT count(*) FROM verdict_cache").fetchone()
    assert filas == 1
    assert cache.lookup(url).verdict == "red"


@pytestmark_integracion
def test_una_entrada_vencida_no_se_sirve(base, monkeypatch):
    url = "https://example.com/"
    # TTL negativo: nace vencida, que es lo mismo que ver una de ayer sin
    # tener que esperar el TTL real.
    monkeypatch.setattr(cache, "_ttl_seconds", lambda _verdict: -1)
    cache.store(url, verdict="green", score=0, reasons=[], source_layer="L1")
    assert cache.lookup(url) is None


@pytestmark_integracion
def test_el_vencimiento_lo_marca_el_reloj_de_la_base(base):
    # expires_at se calcula con now() del servidor, no con el reloj del proceso:
    # si derivan entre si, la entrada vence antes o despues de lo previsto.
    url = "https://example.com/"
    cache.store(url, verdict="green", score=0, reasons=[], source_layer="L1")
    with cache.pool().connection() as conn:
        (segundos,) = conn.execute(
            "SELECT extract(epoch FROM expires_at - now()) FROM verdict_cache"
        ).fetchone()
    assert 0 < segundos <= cache.CACHE_TTL_SECONDS
