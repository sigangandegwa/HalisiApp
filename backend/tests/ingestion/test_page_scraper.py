"""Tier-2 OpenGraph scraper (TSK-006) with respx, and the tiered check flow outside DEMO_MODE. No network."""

from pathlib import Path

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from app.ingestion.fixtures import logos as L
from app.ingestion.page_scraper import (
    FetchError,
    fetch_opengraph,
    is_login_wall,
    parse_count,
    parse_opengraph,
    profile_from_opengraph,
)
from app.main import create_app
from tests.conftest import make_settings


async def resolve_public(host: str) -> list[str]:
    return ["157.240.1.174"]


IG_HTML = (
    "<html><head>"
    '<meta property="og:title" content="Nairobi Sneaker Vault Deals (&#064;nsv_deals_ke) &#x2022; Instagram">'
    '<meta property="og:description" content="1,234 Followers, 56 Following, 7 Posts - '
    'See Instagram photos and videos from Nairobi Sneaker Vault Deals (@nsv_deals_ke)">'
    '<meta property="og:image" content="https://cdn.example.com/avatar.jpg">'
    "</head><body></body></html>"
)
LOGIN_HTML = "<html><head><title>Instagram</title></head><body>Log in</body></html>"


@pytest.mark.parametrize(
    ("raw", "value"),
    [
        ("1,234", 1234),
        ("5.4K", 5400),
        ("1.2M", 1_200_000),
        ("12", 12),
        ("1,2K", 1200),
        ("", None),
        ("abc", None),
    ],
)
def test_parse_count(raw: str, value: int | None) -> None:
    assert parse_count(raw) == value


def test_instagram_description_is_parsed() -> None:
    tags = parse_opengraph(IG_HTML)
    profile = profile_from_opengraph(tags, "instagram", "nsv_deals_ke", "https://instagram.com/nsv_deals_ke")
    assert profile.follower_count == 1234 and profile.post_count == 7
    assert profile.display_name == "Nairobi Sneaker Vault Deals"
    assert profile.avatar_url == "https://cdn.example.com/avatar.jpg"


def test_login_wall_detection() -> None:
    assert is_login_wall("https://www.instagram.com/accounts/login/?next=/x", parse_opengraph(IG_HTML))
    assert is_login_wall("https://instagram.com/x", parse_opengraph(LOGIN_HTML))
    assert not is_login_wall("https://instagram.com/x", parse_opengraph(IG_HTML))


@respx.mock
async def test_fetch_opengraph_downloads_the_avatar() -> None:
    respx.get("https://instagram.com/nsv_deals_ke").mock(return_value=httpx.Response(200, text=IG_HTML))
    respx.get("https://cdn.example.com/avatar.jpg").mock(
        return_value=httpx.Response(
            200, headers={"content-type": "image/png"}, content=L.png_bytes(L.sneaker_logo())
        )
    )
    async with httpx.AsyncClient() as http:
        profile = await fetch_opengraph(
            http, "https://instagram.com/nsv_deals_ke", "instagram", "nsv_deals_ke", resolver=resolve_public
        )
    assert profile.avatar_bytes and profile.follower_count == 1234 and profile.fetched_via == "opengraph"


@respx.mock
@pytest.mark.parametrize(
    ("response", "reason"),
    [
        (
            httpx.Response(302, headers={"location": "https://www.instagram.com/accounts/login/"}),
            "login_wall",
        ),
        (httpx.Response(200, text=LOGIN_HTML), "login_wall"),
        (httpx.Response(429), "blocked"),
        (httpx.Response(404), "not_found"),
    ],
)
async def test_fetch_failures(response: httpx.Response, reason: str) -> None:
    respx.get("https://instagram.com/someone").mock(return_value=response)
    respx.get("https://www.instagram.com/accounts/login/").mock(
        return_value=httpx.Response(200, text=LOGIN_HTML)
    )
    async with httpx.AsyncClient() as http:
        with pytest.raises(FetchError) as err:
            await fetch_opengraph(
                http, "https://instagram.com/someone", "instagram", "someone", resolver=resolve_public
            )
    assert err.value.reason == reason


@respx.mock
async def test_network_error_is_a_fetch_error() -> None:
    respx.get("https://instagram.com/someone").mock(side_effect=httpx.ConnectTimeout("slow"))
    async with httpx.AsyncClient() as http:
        with pytest.raises(FetchError):
            await fetch_opengraph(
                http, "https://instagram.com/someone", "instagram", "someone", resolver=resolve_public
            )


def test_live_tier_end_to_end_outside_demo_mode(tmp_path: Path) -> None:
    """Non-demo app, MemoryRepository, tier 2 via respx: fetched once, then served from the cache."""
    settings = make_settings(tmp_path, demo_mode=False)
    with respx.mock(assert_all_called=False) as mock:
        page = mock.get("https://instagram.com/nsv_deals_ke").mock(
            return_value=httpx.Response(
                200, text=IG_HTML.replace("7 Posts", "7 Posts - Lipa kwanza. Send money to 0798 555 444")
            )
        )
        mock.get("https://cdn.example.com/avatar.jpg").mock(
            return_value=httpx.Response(
                200, headers={"content-type": "image/png"}, content=L.png_bytes(L.jpeg(L.sneaker_logo()))
            )
        )
        blocked = mock.get("https://instagram.com/blocked_one").mock(return_value=httpx.Response(429))
        app = create_app(settings, resolver=resolve_public, seed=True)
        with TestClient(app) as client:
            first = client.post("/api/v1/check", json={"url": "https://instagram.com/nsv_deals_ke"}).json()
            assert first["target"]["fetched_via"] == "opengraph"
            assert first["target"]["follower_count"] == 1234
            assert first["verdict"] == "impersonation", first
            second = client.post("/api/v1/check", json={"handle": "nsv_deals_ke"}).json()
            assert second["score"] == first["score"]
            assert page.call_count == 1  # cached (tier 1 / TTL cache)
            unreachable = client.post("/api/v1/check", json={"handle": "blocked_one"})
            assert unreachable.status_code == 502 and blocked.called
            assert client.get("/health").json()["db"] == "memory"
