import httpx
import pytest

from app.redirects import RedirectTrace, resolve_chain


def _client(routes: dict[str, tuple[int, dict[str, str]]]) -> httpx.Client:
    """Cliente con transport simulado: mapea URL -> (status, headers)."""

    def handler(request: httpx.Request) -> httpx.Response:
        status, headers = routes[str(request.url)]
        return httpx.Response(status, headers=headers)

    return httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=False)


def _chain_routes(urls: list[str], status: int = 302) -> dict:
    """Encadena urls[0] -> urls[1] -> ... y deja la ultima en 200."""
    routes = {u: (status, {"location": nxt}) for u, nxt in zip(urls, urls[1:], strict=False)}
    routes[urls[-1]] = (200, {})
    return routes


def test_url_sin_redireccion_queda_igual():
    url = "https://example.com/"
    trace = resolve_chain(url, client=_client({url: (200, {})}), allow_private_hosts=True)
    assert trace.chain == (url,)
    assert trace.final_url == url
    assert trace.hops == 0
    assert trace.resolved
    assert not trace.rewrote_url


def test_resuelve_cadena_de_cinco_saltos():
    # Criterio de aceptacion de RF-009: al menos 5 saltos, traza completa.
    urls = [f"https://hop{i}.example/" for i in range(5)] + ["https://pagos-banc0.xyz/"]
    trace = resolve_chain(
        urls[0], client=_client(_chain_routes(urls)), allow_private_hosts=True
    )
    assert trace.resolved
    assert trace.hops == 5
    assert trace.chain == tuple(urls)
    assert trace.final_url == "https://pagos-banc0.xyz/"
    assert trace.rewrote_url


@pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
def test_sigue_todos_los_codigos_de_redireccion(status):
    urls = ["https://a.example/", "https://b.example/"]
    trace = resolve_chain(
        urls[0], client=_client(_chain_routes(urls, status)), allow_private_hosts=True
    )
    assert trace.final_url == "https://b.example/"


def test_resuelve_location_relativo():
    routes = {
        "https://a.example/ir": (302, {"location": "/destino"}),
        "https://a.example/destino": (200, {}),
    }
    trace = resolve_chain(
        "https://a.example/ir", client=_client(routes), allow_private_hosts=True
    )
    assert trace.final_url == "https://a.example/destino"


def test_detecta_bucle_y_no_queda_colgado():
    routes = {
        "https://a.example/": (302, {"location": "https://b.example/"}),
        "https://b.example/": (302, {"location": "https://a.example/"}),
    }
    trace = resolve_chain(
        "https://a.example/", client=_client(routes), allow_private_hosts=True
    )
    assert not trace.resolved
    assert "bucle" in trace.reason
    assert trace.final_url == "https://b.example/"


def test_corta_al_superar_el_limite_de_saltos():
    urls = [f"https://hop{i}.example/" for i in range(12)]
    trace = resolve_chain(
        urls[0],
        client=_client(_chain_routes(urls)),
        max_hops=3,
        allow_private_hosts=True,
    )
    assert not trace.resolved
    assert "limite" in trace.reason
    assert trace.hops == 3


def test_corta_al_agotar_el_presupuesto_total():
    url = "https://a.example/"
    trace = resolve_chain(
        url, client=_client({url: (200, {})}), total_timeout=0, allow_private_hosts=True
    )
    assert not trace.resolved
    assert "tiempo total" in trace.reason


def test_hace_fallback_a_get_si_el_server_rechaza_head():
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.method)
        if request.method == "HEAD":
            return httpx.Response(405)
        return httpx.Response(302, headers={"location": "https://final.example/"})

    client = httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=False)
    trace = resolve_chain(
        "https://a.example/", client=client, max_hops=1, allow_private_hosts=True
    )
    assert calls[:2] == ["HEAD", "GET"]
    assert trace.chain[-1] == "https://final.example/"


def test_error_de_red_deja_la_cadena_sin_resolver():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("sin conexion")

    client = httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=False)
    trace = resolve_chain("https://a.example/", client=client, allow_private_hosts=True)
    assert not trace.resolved
    assert "error de red" in trace.reason


def test_bloquea_destinos_en_la_red_interna():
    # Sin allow_private_hosts: el filtro anti-SSRF debe cortar antes de pedir.
    trace = resolve_chain("http://localhost/admin")
    assert not trace.resolved
    assert "bloqueado" in trace.reason


def test_bloquea_esquemas_que_no_son_http():
    trace = resolve_chain("file:///etc/passwd")
    assert not trace.resolved
    assert "esquema" in trace.reason


def test_identity_no_toca_la_url():
    trace = RedirectTrace.identity("https://example.com/")
    assert trace.resolved
    assert trace.hops == 0
    assert not trace.rewrote_url
    assert trace.final_url == "https://example.com/"
