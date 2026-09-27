"""Security checklist (TSK-019, docs/BACKEND.md section 11). No network: DNS and HTTP are faked."""

from pathlib import Path

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from app.core.security import check_api_key, client_ip, is_public_ip, is_public_url
from app.ingestion.mock_seeder import seed_id
from app.ingestion.page_scraper import FetchError, fetch_image, safe_get
from app.main import create_app
from tests.conftest import AUTH, make_settings

NSV = str(seed_id("merchant", "nsv"))


def resolver_for(mapping: dict[str, list[str]]):
    async def resolve(host: str) -> list[str]:
        if host not in mapping:
            raise OSError("no such host")
        return mapping[host]

    return resolve


PUBLIC = resolver_for(
    {
        "cdn.example.com": ["93.184.216.34"],
        "instagram.com": ["157.240.1.174"],
        "evil.example.com": ["127.0.0.1"],
        "rebind.example.com": ["93.184.216.34", "10.0.0.5"],
        "meta.example.com": ["169.254.169.254"],
    }
)


# --- SSRF guard ----------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "url",
    [
        "https://127.0.0.1/x",
        "https://169.254.169.254/latest/meta-data/",
        "https://[::1]/",
        "https://10.1.2.3/",
        "https://192.168.0.10/",
        "https://localhost/",
        "https://0.0.0.0/",
        "https://100.64.0.1/",
        "https://[::ffff:127.0.0.1]/",
        "http://cdn.example.com/a.png",
        "file:///etc/passwd",
        "ftp://cdn.example.com/",
        "https://user:pass@cdn.example.com/",
        "https://evil.example.com/",
        "https://rebind.example.com/",
        "https://meta.example.com/",
        "https://unknown.example.com/",
        "https:///nohost",
    ],
)
async def test_ssrf_guard_rejects(url: str) -> None:
    assert await is_public_url(url, resolver=PUBLIC) is False


async def test_ssrf_guard_accepts_public_https() -> None:
    assert await is_public_url("https://cdn.example.com/a.png", resolver=PUBLIC)
    assert await is_public_url("https://93.184.216.34/a.png", resolver=PUBLIC)


def test_is_public_ip() -> None:
    assert is_public_ip("8.8.8.8")
    assert not is_public_ip("fe80::1") and not is_public_ip("224.0.0.1") and not is_public_ip("garbage")


@respx.mock
async def test_redirect_to_private_address_is_blocked() -> None:
    respx.get("https://cdn.example.com/a.png").mock(
        return_value=httpx.Response(302, headers={"location": "https://169.254.169.254/latest/meta-data/"})
    )
    async with httpx.AsyncClient() as http:
        with pytest.raises(FetchError) as err:
            await fetch_image(http, "https://cdn.example.com/a.png", resolver=PUBLIC)
    assert err.value.reason == "blocked_url"


@respx.mock
async def test_too_many_redirects() -> None:
    respx.get("https://cdn.example.com/loop").mock(
        return_value=httpx.Response(302, headers={"location": "https://cdn.example.com/loop"})
    )
    async with httpx.AsyncClient() as http:
        with pytest.raises(FetchError) as err:
            await safe_get(http, "https://cdn.example.com/loop", max_bytes=1000, timeout=1, resolver=PUBLIC)
    assert err.value.reason == "too_many_redirects"


@respx.mock
async def test_image_size_and_type_limits() -> None:
    respx.get("https://cdn.example.com/big.png").mock(
        return_value=httpx.Response(
            200, headers={"content-type": "image/png"}, content=b"\x89PNG" + b"0" * (5 * 1024 * 1024 + 10)
        )
    )
    respx.get("https://cdn.example.com/page.html").mock(
        return_value=httpx.Response(200, headers={"content-type": "text/html"}, content=b"<html></html>")
    )
    async with httpx.AsyncClient() as http:
        with pytest.raises(FetchError) as big:
            await fetch_image(http, "https://cdn.example.com/big.png", resolver=PUBLIC)
        with pytest.raises(FetchError) as html:
            await fetch_image(http, "https://cdn.example.com/page.html", resolver=PUBLIC)
    assert big.value.reason == "too_large"
    assert html.value.reason == "not_an_image"


# --- API key -------------------------------------------------------------------------------------


def test_api_key_comparison() -> None:
    assert check_api_key("abc", "abc")
    assert not check_api_key("abd", "abc")
    assert not check_api_key(None, "abc")
    assert not check_api_key("", "")  # an empty configured key never matches


@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("get", f"/api/v1/merchants/{NSV}/threats", None),
        ("get", f"/api/v1/merchants/{NSV}/alerts", None),
        ("post", f"/api/v1/merchants/{NSV}/alerts/read", {"all": True}),
        ("get", "/api/v1/threats/00000000-0000-0000-0000-000000000000", None),
        ("patch", "/api/v1/threats/00000000-0000-0000-0000-000000000000", {"status": "resolved"}),
        ("post", "/api/v1/threats/00000000-0000-0000-0000-000000000000/playbooks", None),
        ("post", "/api/v1/simulator/clone", {"merchant_id": NSV}),
        ("get", f"/api/v1/stats?merchant_id={NSV}", None),
    ],
)
def test_key_protected_endpoints(client: TestClient, method: str, path: str, body: object) -> None:
    kwargs = {"json": body} if body is not None else {}
    missing = getattr(client, method)(path, **kwargs)
    assert missing.status_code == 401
    assert missing.json()["error"]["code"] == "UNAUTHORIZED"
    wrong = getattr(client, method)(path, headers={"X-Halisi-Key": "nope"}, **kwargs)
    assert wrong.status_code == 401


def test_onboarding_requires_key(client: TestClient) -> None:
    response = client.post(
        "/api/v1/merchants", data={"data": "{}"}, files={"logo": ("l.png", b"x", "image/png")}
    )
    assert response.status_code == 401


# --- rate limits ---------------------------------------------------------------------------------


def test_rate_limits(tmp_path: Path) -> None:
    settings = make_settings(
        tmp_path,
        rate_limit_enabled=True,
        public_check_rate_limit="3/minute",
        verify_payment_rate_limit="2/minute",
        report_rate_limit="1/minute",
    )
    with TestClient(create_app(settings)) as client:
        codes = [client.post("/api/v1/check", json={"handle": "kilimaniglow"}).status_code for _ in range(4)]
        assert codes == [200, 200, 200, 429]
        limited = client.post("/api/v1/check", json={"handle": "kilimaniglow"})
        assert limited.json()["error"]["code"] == "RATE_LIMITED"
        verify = [
            client.get("/api/v1/verify/payment", params={"value": "543210"}).status_code for _ in range(3)
        ]
        assert verify == [200, 200, 429]
        reports = [
            client.post("/api/v1/reports", json={"reported_phone": "0798999111"}).status_code
            for _ in range(2)
        ]
        assert reports == [201, 429]
        assert client.get("/health").status_code == 200  # unlimited


def test_forwarded_for_is_trusted_only_from_loopback_when_enabled(tmp_path: Path) -> None:
    class _Req:
        def __init__(self, peer: str, trust: bool) -> None:
            self.client = type("C", (), {"host": peer})()
            self.headers = {"x-forwarded-for": "41.90.1.2, 10.0.0.1"}
            self.app = type(
                "A",
                (),
                {"state": type("S", (), {"settings": make_settings(tmp_path, trust_forwarded_for=trust)})},
            )

    assert client_ip(_Req("127.0.0.1", True)) == "41.90.1.2"  # through the ngrok tunnel
    assert client_ip(_Req("203.0.113.9", True)) == "203.0.113.9"  # spoofed header from the internet
    assert client_ip(_Req("127.0.0.1", False)) == "127.0.0.1"


# --- CORS, errors, input limits, data minimisation -----------------------------------------------


def test_cors_is_explicit(client: TestClient) -> None:
    ok = client.options(
        "/api/v1/check", headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "POST"}
    )
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:3000"
    evil = client.options(
        "/api/v1/check", headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"}
    )
    assert evil.headers.get("access-control-allow-origin") is None


def test_star_origin_is_ignored(tmp_path: Path) -> None:
    assert make_settings(tmp_path, cors_origins="*, http://localhost:3000").cors_origins_list == [
        "http://localhost:3000"
    ]


def test_errors_are_generic_json(client: TestClient) -> None:
    response = client.get("/api/v1/nope")
    assert response.status_code == 404
    assert response.json() == {"error": {"code": "NOT_FOUND", "message": "Not Found"}}


def test_oversized_body_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/v1/check",
        content=b"x" * 10,
        headers={"content-type": "application/json", "content-length": str(9 * 1024 * 1024)},
    )
    assert response.status_code == 413


def test_report_limits_and_reporter_contact_never_returned(client: TestClient) -> None:
    long = client.post("/api/v1/reports", json={"reported_phone": "0798999111", "description": "x" * 1001})
    assert long.status_code == 422
    created = client.post(
        "/api/v1/reports", json={"reported_phone": "0798999111", "reporter_contact": "me@x.co"}
    )
    assert created.status_code == 201
    assert "reporter_contact" not in created.text and "me@x.co" not in created.text


def test_openapi_lists_every_route_with_a_response_model(client: TestClient) -> None:
    spec = client.get("/openapi.json").json()
    paths = spec["paths"]
    expected = {
        ("get", "/health"),
        ("post", "/api/v1/check"),
        ("get", "/api/v1/check/{scan_id}"),
        ("get", "/api/v1/verify/payment"),
        ("get", "/api/v1/merchants/{slug}"),
        ("post", "/api/v1/merchants"),
        ("get", "/api/v1/merchants/{merchant_id}/threats"),
        ("get", "/api/v1/merchants/{merchant_id}/alerts"),
        ("post", "/api/v1/merchants/{merchant_id}/alerts/read"),
        ("get", "/api/v1/threats/{threat_id}"),
        ("patch", "/api/v1/threats/{threat_id}"),
        ("post", "/api/v1/threats/{threat_id}/playbooks"),
        ("post", "/api/v1/reports"),
        ("get", "/api/v1/stats"),
        ("post", "/api/v1/simulator/clone"),
    }
    present = {(m, p) for p, ops in paths.items() for m in ops}
    assert expected <= present
    for method, path in expected:
        responses = paths[path][method]["responses"]
        ok = next(v for k, v in responses.items() if k.startswith("2"))
        assert "$ref" in str(ok) or "items" in str(ok), (method, path)


def test_auth_header_value_is_not_logged(client: TestClient, capsys: pytest.CaptureFixture[str]) -> None:
    client.get(f"/api/v1/merchants/{NSV}/threats", headers=AUTH)
    assert AUTH["X-Halisi-Key"] not in capsys.readouterr().out
