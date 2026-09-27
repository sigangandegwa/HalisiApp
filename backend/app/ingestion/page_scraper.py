"""Tiered page-metadata acquisition (TSK-006, docs/BACKEND.md section 7.2).

1. Known targets: seeded / previously fetched ``target_profiles`` rows (instant; the demo path).
2. OpenGraph fetch with the shared httpx client: mobile User-Agent, 5 s timeout, manual redirects
   (max 3) each re-checked by the SSRF guard, login-wall detection.
3. Manual fallback: the user pastes the bio and uploads the avatar (handled by the check service).

Instagram/Facebook block unauthenticated datacenter traffic, so tier 2 is best-effort and the
demo never depends on it. Tier 1 and 3 live in ``app.services.check``; this module is the network part.
"""

import html
import re
from dataclasses import dataclass
from datetime import date
from urllib.parse import urljoin, urlsplit

import httpx
from bs4 import BeautifulSoup

from app.core.security import Resolver, is_public_url, system_resolver
from app.engine.constants import MAX_IMAGE_BYTES

MOBILE_UA = (
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0 Mobile Safari/537.36"
)
MAX_REDIRECTS = 3
MAX_HTML_BYTES = 2 * 1024 * 1024
_LOGIN_MARKERS = ("/accounts/login", "/login", "login.php", "checkpoint")
_GENERIC_TITLES = {
    "instagram",
    "facebook",
    "tiktok",
    "x",
    "log in",
    "login",
    "log into facebook",
    "page not found",
}
_COUNT = r"([\d.,]+\s*[kKmM]?)"
_IG_DESCRIPTION = re.compile(
    rf"{_COUNT}\s+Followers?,\s*{_COUNT}\s+Following,\s*{_COUNT}\s+Posts?"
    r"(?:\s*[-–]\s*See Instagram photos and videos from\s+(?P<name>.+?)\s*\(@(?P<handle>[\w.]+)\))?",
    re.I,
)
_TITLE_HANDLE = re.compile(r"^(?P<name>.*?)\s*\(@(?P<handle>[\w.]+)\)")


class FetchError(Exception):
    """A tier-2 fetch failed (blocked, login wall, SSRF-rejected, too large, not found...)."""

    def __init__(self, reason: str, status_code: int | None = None) -> None:
        super().__init__(reason)
        self.reason = reason
        self.status_code = status_code


@dataclass(frozen=True, slots=True)
class FetchedProfile:
    """Page metadata from any tier. ``avatar_bytes`` is set when the image was downloaded."""

    platform: str
    handle: str
    url: str | None = None
    display_name: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    avatar_bytes: bytes | None = None
    follower_count: int | None = None
    post_count: int | None = None
    account_created_on: date | None = None
    fetched_via: str = "opengraph"


def parse_count(value: str | None) -> int | None:
    """``"1,234"`` -> 1234, ``"5.4K"`` -> 5400, ``"1.2M"`` -> 1200000."""
    if not value:
        return None
    text = value.strip().replace(" ", "")
    multiplier = 1
    if text[-1:].lower() == "k":
        multiplier, text = 1_000, text[:-1]
    elif text[-1:].lower() == "m":
        multiplier, text = 1_000_000, text[:-1]
    text = text.replace(",", "") if multiplier == 1 or "." in text else text.replace(",", ".")
    try:
        return int(round(float(text) * multiplier))
    except ValueError:
        return None


def parse_opengraph(document: str) -> dict[str, str]:
    """``og:*`` / ``twitter:*`` meta tags plus ``<title>`` from an HTML document."""
    soup = BeautifulSoup(document, "html.parser")
    tags: dict[str, str] = {}
    for meta in soup.find_all("meta"):
        key = meta.get("property") or meta.get("name")
        content = meta.get("content")
        if key and content and (key.startswith("og:") or key.startswith("twitter:") or key == "description"):
            tags.setdefault(str(key), html.unescape(str(content)).strip())
    if soup.title and soup.title.string:
        tags.setdefault("title", soup.title.string.strip())
    return tags


def profile_from_opengraph(tags: dict[str, str], platform: str, handle: str, url: str) -> FetchedProfile:
    """Build a profile from OG tags. Instagram descriptions carry follower/post counts and the name."""
    title = tags.get("og:title") or tags.get("title") or ""
    description = tags.get("og:description") or tags.get("description") or ""
    display_name: str | None = None
    followers = posts = None
    bio: str | None = description or None

    match = _IG_DESCRIPTION.search(description)
    if match:
        followers, posts = parse_count(match.group(1)), parse_count(match.group(3))
        display_name = match.group("name")
        rest = description[match.end() :].strip(' :-–"')
        bio = rest or None
    title_match = _TITLE_HANDLE.match(title)
    if not display_name and title_match:
        display_name = title_match.group("name").strip() or None
    if not display_name and title and title.lower() not in _GENERIC_TITLES:
        display_name = re.split(r"\s+[|•·-]\s+", title)[0].strip() or None
    avatar = tags.get("og:image") or tags.get("twitter:image")
    return FetchedProfile(
        platform=platform,
        handle=handle,
        url=url,
        display_name=display_name,
        bio=bio,
        avatar_url=urljoin(url, avatar) if avatar else None,
        follower_count=followers,
        post_count=posts,
        fetched_via="opengraph",
    )


def is_login_wall(final_url: str, tags: dict[str, str]) -> bool:
    """Login walls redirect to a login path or serve a page with no profile metadata."""
    path = urlsplit(final_url).path.lower()
    if any(marker in path for marker in _LOGIN_MARKERS):
        return True
    title = (tags.get("og:title") or tags.get("title") or "").strip().lower()
    has_profile_data = bool(tags.get("og:description") or tags.get("og:image"))
    return not has_profile_data or title in _GENERIC_TITLES and not tags.get("og:description")


async def safe_get(
    client: httpx.AsyncClient,
    url: str,
    *,
    max_bytes: int,
    timeout: float,
    resolver: Resolver = system_resolver,
    headers: dict[str, str] | None = None,
) -> tuple[str, httpx.Response, bytes]:
    """GET with the SSRF guard on the first URL and after every redirect, streaming with a byte cap.

    Returns (final_url, response, body). Raises FetchError.
    """
    current = url
    for _ in range(MAX_REDIRECTS + 1):
        if not await is_public_url(current, resolver=resolver):
            raise FetchError("blocked_url")
        try:
            async with client.stream(
                "GET",
                current,
                headers={"User-Agent": MOBILE_UA, **(headers or {})},
                follow_redirects=False,
                timeout=timeout,
            ) as response:
                if response.is_redirect:
                    location = response.headers.get("location")
                    if not location:
                        raise FetchError("bad_redirect", response.status_code)
                    current = urljoin(current, location)
                    continue
                declared = response.headers.get("content-length")
                if declared and declared.isdigit() and int(declared) > max_bytes:
                    raise FetchError("too_large", response.status_code)
                body = bytearray()
                async for chunk in response.aiter_bytes():
                    body.extend(chunk)
                    if len(body) > max_bytes:
                        raise FetchError("too_large", response.status_code)
                return current, response, bytes(body)
        except httpx.HTTPError as exc:
            raise FetchError(f"network:{type(exc).__name__}") from exc
    raise FetchError("too_many_redirects")


async def fetch_image(
    client: httpx.AsyncClient, url: str, *, timeout: float = 8.0, resolver: Resolver = system_resolver
) -> bytes:
    """Download an avatar/logo: SSRF-guarded, <= 5 MB, ``content-type: image/*``. Raises FetchError."""
    _, response, body = await safe_get(
        client, url, max_bytes=MAX_IMAGE_BYTES, timeout=timeout, resolver=resolver
    )
    if response.status_code != 200:
        raise FetchError("image_status", response.status_code)
    if not response.headers.get("content-type", "").lower().startswith("image/"):
        raise FetchError("not_an_image", response.status_code)
    return body


async def fetch_opengraph(
    client: httpx.AsyncClient,
    url: str,
    platform: str,
    handle: str,
    *,
    timeout: float = 5.0,
    image_timeout: float = 8.0,
    resolver: Resolver = system_resolver,
) -> FetchedProfile:
    """Tier 2: fetch a profile page's OpenGraph tags and its avatar. Raises FetchError on any failure,
    including login walls, 404s and rate limiting (429)."""
    final_url, response, body = await safe_get(
        client,
        url,
        max_bytes=MAX_HTML_BYTES,
        timeout=timeout,
        resolver=resolver,
        headers={"Accept": "text/html,application/xhtml+xml", "Accept-Language": "en-KE,en;q=0.9"},
    )
    if response.status_code == 404:
        raise FetchError("not_found", 404)
    if response.status_code != 200:
        raise FetchError(
            "blocked" if response.status_code in (401, 403, 429) else "status", response.status_code
        )
    tags = parse_opengraph(body.decode(response.encoding or "utf-8", errors="replace"))
    if is_login_wall(final_url, tags):
        raise FetchError("login_wall", response.status_code)
    profile = profile_from_opengraph(tags, platform, handle, url)
    if profile.avatar_url:
        try:
            avatar = await fetch_image(client, profile.avatar_url, timeout=image_timeout, resolver=resolver)
        except FetchError:
            avatar = None
        if avatar:
            profile = FetchedProfile(**{**_as_dict(profile), "avatar_bytes": avatar})
    return profile


def _as_dict(profile: FetchedProfile) -> dict[str, object]:
    return {name: getattr(profile, name) for name in profile.__slots__}  # type: ignore[attr-defined]
