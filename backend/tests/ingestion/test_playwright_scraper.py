"""Tests for the Playwright headless scraper upgrade and fallback pipelines (TSK-040)."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import respx

from app.ingestion.fixtures import logos as L
from app.ingestion.page_scraper import FetchedProfile
from app.ingestion.playwright_scraper import (
    PlaywrightScraper,
    PlaywrightScrapeResult,
    _dismiss_modals,
    extract_profile_from_html,
    scrape_with_playwright,
    simulate_target_profile,
)
from tests.conftest import make_settings


async def resolve_public(host: str) -> list[str]:
    return ["157.240.1.174"]


SAMPLE_OG_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta property="og:title" content="Sample Merchant (@sample_merchant) &#x2022; Instagram">
    <meta property="og:description"
          content="1,200 Followers, 45 Following, 30 Posts - Official shop page. Orders via DM.">
    <meta property="og:image" content="https://cdn.example.com/avatar.jpg">
</head>
<body>
</body>
</html>
"""

SAMPLE_DOM_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Instagram</title>
</head>
<body>
    <button>Allow all cookies</button>
    <h1 class="profile-header">Sample Brand Official</h1>
    <div class="profile-bio">Verified authentic goods in Nairobi CBD. Till 123456.</div>
    <div class="stats">5.4K followers &bull; 80 posts</div>
    <img class="profile-avatar" alt="profile photo" src="/images/avatar.png">
</body>
</html>
"""


def test_playwright_scrape_result_properties() -> None:
    result = PlaywrightScrapeResult(
        platform="instagram",
        handle="sample_brand",
        url="https://instagram.com/sample_brand",
        display_name="Sample Brand",
        bio="Official account",
        avatar_url="https://example.com/pic.png",
        follower_count=5000,
        post_count=100,
        screenshot_bytes=b"\x89PNG\r\n\x1a\nfake_image_data",
        html="<html></html>",
    )

    assert result.has_screenshot is True
    assert result.platform == "instagram"
    assert result.handle == "sample_brand"

    # Profile conversion
    profile = result.profile
    assert isinstance(profile, FetchedProfile)
    assert profile.platform == "instagram"
    assert profile.handle == "sample_brand"
    assert profile.display_name == "Sample Brand"
    assert profile.bio == "Official account"
    assert profile.avatar_url == "https://example.com/pic.png"
    assert profile.follower_count == 5000
    assert profile.post_count == 100
    assert profile.fetched_via == "playwright"

    # Factory wrapping from FetchedProfile
    wrapped = PlaywrightScrapeResult.from_fetched_profile(
        profile,
        screenshot_bytes=b"screenshot_bytes",
        html="<html></html>",
    )
    assert wrapped.display_name == "Sample Brand"
    assert wrapped.screenshot_bytes == b"screenshot_bytes"
    assert wrapped.has_screenshot is True


def test_playwright_scrape_result_no_screenshot() -> None:
    result = PlaywrightScrapeResult(
        platform="instagram",
        handle="sample_brand",
        screenshot_bytes=None,
    )
    assert result.has_screenshot is False


def test_extract_profile_from_html_opengraph() -> None:
    profile = extract_profile_from_html(
        SAMPLE_OG_HTML,
        platform="instagram",
        handle="sample_merchant",
        url="https://instagram.com/sample_merchant",
    )
    assert profile.platform == "instagram"
    assert profile.handle == "sample_merchant"
    assert profile.display_name == "Sample Merchant"
    assert profile.follower_count == 1200
    assert profile.post_count == 30
    assert profile.avatar_url == "https://cdn.example.com/avatar.jpg"
    assert profile.fetched_via == "playwright"


def test_extract_profile_from_html_dom_fallback() -> None:
    profile = extract_profile_from_html(
        SAMPLE_DOM_HTML,
        platform="instagram",
        handle="sample_brand",
        url="https://instagram.com/sample_brand",
    )
    assert profile.display_name == "Sample Brand Official"
    assert profile.bio == "Verified authentic goods in Nairobi CBD. Till 123456."
    assert profile.follower_count == 5400
    assert profile.post_count == 80
    assert profile.avatar_url == "https://instagram.com/images/avatar.png"
    assert profile.fetched_via == "playwright"


def test_simulate_target_profile_seeded() -> None:
    profile = simulate_target_profile("instagram", "nairobi_sneakervault_official_ke")
    assert profile.platform == "instagram"
    assert profile.handle == "nairobi_sneakervault_official_ke"
    assert profile.display_name == "Nairobi Sneaker Vault Official"
    assert profile.follower_count == 212
    assert profile.post_count == 9
    assert profile.avatar_bytes is not None
    assert profile.fetched_via == "simulated"


def test_simulate_target_profile_unknown() -> None:
    profile = simulate_target_profile("instagram", "random_unseeded_handle")
    assert profile.platform == "instagram"
    assert profile.handle == "random_unseeded_handle"
    assert profile.display_name == "Random Unseeded Handle"
    assert profile.follower_count == 1000
    assert profile.fetched_via == "simulated"


@pytest.mark.asyncio
async def test_scrape_with_playwright_demo_mode(tmp_path: Path) -> None:
    """In DEMO_MODE, it returns simulated/seeded profiles without attempting browser or network."""
    settings = make_settings(tmp_path, demo_mode=True, playwright_scraper_enabled=True)

    result = await scrape_with_playwright(
        "https://instagram.com/nairobi_sneakervault_official_ke",
        settings=settings,
        resolver=resolve_public,
    )

    assert result.platform == "instagram"
    assert result.handle == "nairobi_sneakervault_official_ke"
    assert result.display_name == "Nairobi Sneaker Vault Official"
    assert result.fetched_via == "simulated"
    assert result.screenshot_bytes is None


@pytest.mark.asyncio
async def test_scrape_with_playwright_fallback_when_disabled(tmp_path: Path) -> None:
    """When playwright_scraper_enabled is False, falls back to tier-2 OpenGraph fetch."""
    settings = make_settings(
        tmp_path,
        demo_mode=False,
        scraper_enabled=True,
        playwright_scraper_enabled=False,
    )

    with respx.mock(assert_all_called=False) as mock:
        mock.get("https://instagram.com/sample_merchant").mock(
            return_value=httpx.Response(200, text=SAMPLE_OG_HTML)
        )
        mock.get("https://cdn.example.com/avatar.jpg").mock(
            return_value=httpx.Response(
                200,
                headers={"content-type": "image/png"},
                content=L.png_bytes(L.sneaker_logo()),
            )
        )

        async with httpx.AsyncClient() as http:
            result = await scrape_with_playwright(
                "https://instagram.com/sample_merchant",
                settings=settings,
                http_client=http,
                resolver=resolve_public,
            )

        assert result.display_name == "Sample Merchant"
        assert result.follower_count == 1200
        assert result.fetched_via == "opengraph"
        assert result.avatar_bytes is not None


@pytest.mark.asyncio
async def test_scrape_with_playwright_fallback_when_uninstalled(tmp_path: Path) -> None:
    """When Playwright is not installed, it falls back to OpenGraph fetch."""
    settings = make_settings(
        tmp_path,
        demo_mode=False,
        scraper_enabled=True,
        playwright_scraper_enabled=True,
    )

    with patch("app.ingestion.playwright_scraper.is_playwright_available", return_value=False):
        with respx.mock(assert_all_called=False) as mock:
            mock.get("https://instagram.com/sample_merchant").mock(
                return_value=httpx.Response(200, text=SAMPLE_OG_HTML)
            )
            mock.get("https://cdn.example.com/avatar.jpg").mock(
                return_value=httpx.Response(
                    200,
                    headers={"content-type": "image/png"},
                    content=L.png_bytes(L.sneaker_logo()),
                )
            )

            async with httpx.AsyncClient() as http:
                result = await scrape_with_playwright(
                    "https://instagram.com/sample_merchant",
                    settings=settings,
                    http_client=http,
                    resolver=resolve_public,
                )

            assert result.display_name == "Sample Merchant"
            assert result.fetched_via == "opengraph"


@pytest.mark.asyncio
async def test_scrape_with_playwright_fallback_when_opengraph_fails(tmp_path: Path) -> None:
    """When Playwright is unavailable and OpenGraph returns an error, falls back to simulation."""
    settings = make_settings(
        tmp_path,
        demo_mode=False,
        scraper_enabled=True,
        playwright_scraper_enabled=False,
    )

    with respx.mock(assert_all_called=False) as mock:
        mock.get("https://instagram.com/nonexistent_store").mock(
            return_value=httpx.Response(404)
        )

        async with httpx.AsyncClient() as http:
            result = await scrape_with_playwright(
                "https://instagram.com/nonexistent_store",
                settings=settings,
                http_client=http,
                resolver=resolve_public,
            )

        assert result.handle == "nonexistent_store"
        assert result.fetched_via == "simulated"
        assert result.display_name == "Nonexistent Store"


@pytest.mark.asyncio
async def test_scrape_with_playwright_headless_mocked(tmp_path: Path) -> None:
    """When Playwright is enabled and available, headless browser runs, captures screenshot and metadata."""
    settings = make_settings(
        tmp_path,
        demo_mode=False,
        scraper_enabled=True,
        playwright_scraper_enabled=True,
    )

    fake_png = b"\x89PNG\r\n\x1a\nfake_fullpage_screenshot"

    mock_locator = MagicMock()
    mock_locator.is_visible = AsyncMock(return_value=True)
    mock_locator.click = AsyncMock()

    mock_locators_first = MagicMock()
    mock_locators_first.first = mock_locator

    mock_page = MagicMock()
    mock_page.goto = AsyncMock()
    mock_page.locator = MagicMock(return_value=mock_locators_first)
    mock_page.content = AsyncMock(return_value=SAMPLE_DOM_HTML)
    mock_page.screenshot = AsyncMock(return_value=fake_png)

    mock_context = MagicMock()
    mock_context.new_page = AsyncMock(return_value=mock_page)

    mock_browser = MagicMock()
    mock_browser.new_context = AsyncMock(return_value=mock_context)
    mock_browser.close = AsyncMock()

    mock_chromium = MagicMock()
    mock_chromium.launch = AsyncMock(return_value=mock_browser)

    mock_playwright = MagicMock()
    mock_playwright.chromium = mock_chromium

    class MockAsyncPlaywrightContext:
        async def __aenter__(self) -> MagicMock:
            return mock_playwright

        async def __aexit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
            pass

    mock_playwright_module = MagicMock()
    mock_async_api_module = MagicMock()
    mock_async_api_module.async_playwright = MagicMock(return_value=MockAsyncPlaywrightContext())
    mock_playwright_module.async_api = mock_async_api_module

    with (
        patch("app.ingestion.playwright_scraper.is_playwright_available", return_value=True),
        patch.dict(
            "sys.modules",
            {
                "playwright": mock_playwright_module,
                "playwright.async_api": mock_async_api_module,
            },
        ),
    ):
        scraper = PlaywrightScraper(settings=settings, resolver=resolve_public)
        result = await scraper.scrape("https://instagram.com/sample_brand")

        assert result.platform == "instagram"
        assert result.handle == "sample_brand"
        assert result.display_name == "Sample Brand Official"
        assert result.bio == "Verified authentic goods in Nairobi CBD. Till 123456."
        assert result.fetched_via == "playwright"
        assert result.screenshot_bytes == fake_png
        assert result.has_screenshot is True

        mock_chromium.launch.assert_called_once()
        mock_page.goto.assert_called_once()
        mock_page.screenshot.assert_called_once()
        mock_browser.close.assert_called_once()


@pytest.mark.asyncio
async def test_scrape_with_playwright_browser_launch_failure_falls_back(tmp_path: Path) -> None:
    """When Playwright launch raises an exception, it logs and falls back gracefully."""
    settings = make_settings(
        tmp_path,
        demo_mode=False,
        scraper_enabled=True,
        playwright_scraper_enabled=True,
    )

    class MockFailingPlaywrightContext:
        async def __aenter__(self) -> MagicMock:
            mock = MagicMock()
            mock.chromium.launch = AsyncMock(side_effect=RuntimeError("Executable doesn't exist"))
            return mock

        async def __aexit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
            pass

    mock_playwright_module = MagicMock()
    mock_async_api_module = MagicMock()
    mock_async_api_module.async_playwright = MagicMock(return_value=MockFailingPlaywrightContext())
    mock_playwright_module.async_api = mock_async_api_module

    with (
        patch("app.ingestion.playwright_scraper.is_playwright_available", return_value=True),
        patch.dict(
            "sys.modules",
            {
                "playwright": mock_playwright_module,
                "playwright.async_api": mock_async_api_module,
            },
        ),
    ):
        with respx.mock(assert_all_called=False) as mock:
            mock.get("https://instagram.com/sample_merchant").mock(
                return_value=httpx.Response(200, text=SAMPLE_OG_HTML)
            )
            mock.get("https://cdn.example.com/avatar.jpg").mock(
                return_value=httpx.Response(
                    200,
                    headers={"content-type": "image/png"},
                    content=L.png_bytes(L.sneaker_logo()),
                )
            )

            async with httpx.AsyncClient() as http:
                result = await scrape_with_playwright(
                    "https://instagram.com/sample_merchant",
                    settings=settings,
                    http_client=http,
                    resolver=resolve_public,
                )

            assert result.display_name == "Sample Merchant"
            assert result.fetched_via == "opengraph"


@pytest.mark.asyncio
async def test_modal_dismissal_ignores_errors() -> None:
    """_dismiss_modals attempts clicks on selectors and handles visibility/click errors without crashing."""
    mock_loc = MagicMock()
    mock_loc.is_visible = AsyncMock(side_effect=TimeoutError("timed out"))
    mock_loc.click = AsyncMock()

    mock_loc_container = MagicMock()
    mock_loc_container.first = mock_loc

    mock_page = MagicMock()
    mock_page.locator = MagicMock(return_value=mock_loc_container)

    # Should complete without error
    await _dismiss_modals(mock_page)
    assert mock_page.locator.called
