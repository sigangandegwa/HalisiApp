import base64
import re
from dataclasses import dataclass
from datetime import date

import httpx
from bs4 import BeautifulSoup

from app.core.repository import Repository
from app.core.security import is_public_url
from app.main import DomainException
from app.schemas.check import ManualTarget

# Mobile User-Agent used for OG fetches so social platforms return full meta tags.
_MOBILE_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
    "Version/16.6 Mobile/15E148 Safari/604.1"
)


@dataclass
class ScrapedProfile:
    """Normalised profile data returned by all three scraping tiers."""

    platform: str | None
    handle: str | None
    display_name: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    avatar_bytes: bytes | None = None
    follower_count: int | None = None
    post_count: int | None = None
    account_created_on: date | None = None
    fetched_via: str | None = None  # "seed" | "live" | "manual"


class TargetUnreachable(DomainException):
    """Raised when the target URL cannot be fetched (login wall, network error, etc.)."""

    def __init__(self, message: str = "Target unreachable") -> None:
        super().__init__(code="TARGET_UNREACHABLE", message=message, status_code=502)


async def scrape_profile(
    platform: str,
    handle: str,
    repo: Repository,
    http_client: httpx.AsyncClient,
    manual: ManualTarget | None = None,
) -> ScrapedProfile:
    """Fetch a social-media profile using a three-tier strategy.

    Tier 1 – Seed / known target (DB lookup, instant):
        Returns immediately if the handle was previously seen as a threat.

    Tier 2a – Manual fallback (user-supplied data):
        If *manual* is provided, bypass network fetch entirely and return
        whatever the user pasted.  This is a real product feature, not a hack
        — it works for any platform including WhatsApp catalogues.

    Tier 2b – OpenGraph fetch (live httpx with mobile User-Agent):
        Parses og:title / og:description / og:image.  Instagram OG descriptions
        typically read: "1,234 Followers, 56 Following, 78 Posts - See …".
        Counts and display name are extracted with tolerant regexes.
        Any login-wall response raises TargetUnreachable so the API returns 502
        and the frontend shows the manual fallback form.
    """
    # ── Tier 1: Seeded / previously seen targets (instant, demo path) ────────
    threat = await repo.find_threat_by_target(platform, handle)
    if threat is not None:
        return ScrapedProfile(
            platform=threat.platform,
            handle=threat.target_handle,
            display_name=getattr(threat, "display_name", None),
            bio=getattr(threat, "bio", None),
            avatar_url=getattr(threat, "avatar_url", None),
            follower_count=getattr(threat, "follower_count", None),
            post_count=getattr(threat, "post_count", None),
            account_created_on=getattr(threat, "account_created_on", None),
            fetched_via="seed",
        )

    # ── Tier 2a: Manual fallback (user-pasted data, no network needed) ────────
    if manual is not None:
        avatar_bytes: bytes | None = None
        if manual.avatar_base64:
            b64 = manual.avatar_base64
            # Strip data-URI prefix if present (e.g. "data:image/png;base64,…")
            if "," in b64:
                b64 = b64.split(",", 1)[1]
            try:
                avatar_bytes = base64.b64decode(b64)
            except Exception:  # noqa: BLE001 – malformed base64 is non-fatal
                pass
        return ScrapedProfile(
            platform=platform,
            handle=handle,
            display_name=manual.display_name,
            bio=manual.bio,
            avatar_bytes=avatar_bytes,
            fetched_via="manual",
        )

    # ── Tier 2b: OpenGraph live fetch ─────────────────────────────────────────
    url = f"https://{platform}.com/{handle}"

    if not is_public_url(url):
        raise TargetUnreachable("Invalid or non-public target URL")

    try:
        response = await http_client.get(
            url,
            headers={"User-Agent": _MOBILE_UA},
            timeout=5.0,
            follow_redirects=True,
        )
        response.raise_for_status()
    except httpx.HTTPError as err:
        raise TargetUnreachable() from err

    # Treat any login-wall redirect or page content as a failure.
    if "Login" in response.text or "login" in str(response.url).lower():
        raise TargetUnreachable("Login wall detected")

    soup = BeautifulSoup(response.text, "html.parser")

    title = ""
    description = ""
    image_url = ""

    og_title = soup.find("meta", property="og:title")
    if og_title:
        title = og_title.get("content", "")  # type: ignore[arg-type]

    og_desc = soup.find("meta", property="og:description")
    if og_desc:
        description = og_desc.get("content", "")  # type: ignore[arg-type]

    og_image = soup.find("meta", property="og:image")
    if og_image:
        candidate = og_image.get("content", "")  # type: ignore[arg-type]
        # SSRF guard: re-validate the image URL (attacker controls the page).
        if candidate and is_public_url(candidate):
            image_url = candidate

    # ── Instagram-specific metadata extraction ────────────────────────────────
    follower_count: int | None = None
    post_count: int | None = None
    display_name: str | None = title or None

    if platform.lower() == "instagram":
        # OG description: "1,234 Followers, 56 Following, 78 Posts - See …"
        followers_match = re.search(r"([\d,]+[kKmM]?)\s+Followers", description)
        if followers_match:
            f_str = followers_match.group(1).replace(",", "").lower()
            if "k" in f_str:
                follower_count = int(float(f_str.replace("k", "")) * 1_000)
            elif "m" in f_str:
                follower_count = int(float(f_str.replace("m", "")) * 1_000_000)
            else:
                follower_count = int(f_str)

        posts_match = re.search(r"([\d,]+)\s+Posts", description)
        if posts_match:
            post_count = int(posts_match.group(1).replace(",", ""))

        # Strip the " (@handle) • Instagram photos and videos" suffix from title.
        name_match = re.search(r"^(.*?)\s*\(", title)
        if name_match:
            display_name = name_match.group(1).strip() or display_name

    return ScrapedProfile(
        platform=platform,
        handle=handle,
        display_name=display_name,
        bio=description or None,
        avatar_url=image_url or None,
        follower_count=follower_count,
        post_count=post_count,
        fetched_via="live",
    )
