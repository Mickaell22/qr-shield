import httpx
import pytest

from app import urlhaus

FEED = """################################################################
# abuse.ch URLhaus Database Dump (CSV - online URLs only)      #
################################################################
#
# id,dateadded,url,url_status,last_online,threat,tags,urlhaus_link,reporter
"1","2026-09-12 20:26:32","http://42.230.29.94:38010/i","online","2026-09-12 20:26:32","malware_download","32-bit,elf,mips,Mozi","https://urlhaus.abuse.ch/url/1/","geenensp"
"2","2026-09-12 20:23:25","http://Pagos-Banc0.xyz","online","2026-09-12 20:23:25","malware_download","exe","https://urlhaus.abuse.ch/url/2/","anon"
"""


@pytest.fixture(autouse=True)
def feed_configurado(monkeypatch):
    monkeypatch.setattr(urlhaus, "URLHAUS_FEED_URL", "https://feed.example/csv_online/")
    monkeypatch.setattr(urlhaus, "_urls", None)


def _client(status: int = 200, text: str = FEED) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(lambda _r: httpx.Response(status, text=text)))


def test_normaliza_barra_final_mayusculas_y_fragmento():
    assert urlhaus.normalize("HTTP://Pagos-Banc0.xyz#x") == "http://pagos-banc0.xyz/"
    # La ruta y la query distinguen: son otro recurso.
    assert urlhaus.normalize("http://a.com/Bin?x=1") == "http://a.com/Bin?x=1"


def test_parsea_el_csv_ignorando_la_cabecera_y_las_comas_entre_comillas():
    urls = urlhaus.parse_feed(FEED)
    assert urls == {"http://42.230.29.94:38010/i", "http://pagos-banc0.xyz/"}


def test_sin_feed_cargado_la_capa_no_esta_lista():
    assert not urlhaus.ready()
    assert urlhaus.lookup(("http://42.230.29.94:38010/i",)) is None


def test_sin_url_de_feed_la_capa_queda_desactivada(monkeypatch):
    monkeypatch.setattr(urlhaus, "URLHAUS_FEED_URL", "")
    assert not urlhaus.enabled()
    assert not urlhaus.refresh(client=_client())
    assert not urlhaus.ready()


def test_una_recarga_exitosa_deja_la_capa_lista():
    assert urlhaus.refresh(client=_client())
    assert urlhaus.ready()


def test_una_descarga_fallida_conserva_el_feed_anterior():
    urlhaus.refresh(client=_client())
    assert not urlhaus.refresh(client=_client(status=503))
    assert urlhaus.lookup(("http://42.230.29.94:38010/i",)) is not None


def test_un_200_sin_urls_no_vacia_la_capa():
    urlhaus.refresh(client=_client())
    assert not urlhaus.refresh(client=_client(text="<html>mantenimiento</html>"))
    assert urlhaus.lookup(("http://42.230.29.94:38010/i",)) is not None


def test_detecta_el_destino_final_con_la_forma_de_pydantic():
    urlhaus.refresh(client=_client())
    hit = urlhaus.lookup(("https://bit.ly/abc", "http://pagos-banc0.xyz/"))
    assert hit is not None
    assert hit.score == urlhaus.SCORE_LISTED
    assert "destino final" in hit.reason


def test_detecta_un_salto_intermedio_aunque_el_destino_no_figure():
    urlhaus.refresh(client=_client())
    hit = urlhaus.lookup(
        ("https://bit.ly/abc", "http://42.230.29.94:38010/i", "https://ok.example/")
    )
    assert hit is not None
    assert "salto 1" in hit.reason
    # El motivo termina en la cache L2: no puede llevar la URL en claro.
    assert "42.230" not in hit.reason


def test_una_url_no_listada_es_un_miss():
    urlhaus.refresh(client=_client())
    assert urlhaus.lookup(("https://example.com/",)) is None
