"""Parse what a user pasted into the checker (docs/BACKEND.md section 7.1).

Accepts profile URLs for Instagram, Facebook, TikTok and X, ``wa.me`` links, raw ``@handle``
(Instagram by default), and raw phone / till numbers (routed to ``/verify/payment``). Query strings
and tracking parameters are dropped. Anything else raises :class:`UnsupportedInput`.
"""

import re
from dataclasses import dataclass
from typing import Literal
from urllib.parse import parse_qs, urlsplit

from app.engine.payment import canonical_phone, canonical_till
from app.schemas.common import HANDLE_PATTERN

MAX_INPUT_LENGTH = 2048
_HANDLE = re.compile(HANDLE_PATTERN)
_HOSTS: dict[str, str] = {
    "instagram.com": "instagram",
    "www.instagram.com": "instagram",
    "m.instagram.com": "instagram",
    "instagr.am": "instagram",
    "facebook.com": "facebook",
    "www.facebook.com": "facebook",
    "m.facebook.com": "facebook",
    "web.facebook.com": "facebook",
    "fb.com": "facebook",
    "www.fb.com": "facebook",
    "mbasic.facebook.com": "facebook",
    "tiktok.com": "tiktok",
    "www.tiktok.com": "tiktok",
    "m.tiktok.com": "tiktok",
    "x.com": "x",
    "www.x.com": "x",
    "twitter.com": "x",
    "www.twitter.com": "x",
    "mobile.twitter.com": "x",
    "wa.me": "whatsapp",
    "api.whatsapp.com": "whatsapp",
}
# First path segments that are not profiles.
_RESERVED: dict[str, frozenset[str]] = {
    "instagram": frozenset({"p", "reel", "reels", "tv", "explore", "accounts", "direct", "about", "legal"}),
    "facebook": frozenset(
        {
            "watch",
            "groups",
            "events",
            "marketplace",
            "login",
            "help",
            "pages",
            "share",
            "sharer",
            "story.php",
            "photo.php",
            "permalink.php",
            "people",
        }
    ),
    "tiktok": frozenset({"foryou", "discover", "tag", "music", "login"}),
    "x": frozenset({"i", "home", "explore", "search", "login", "intent", "share", "hashtag"}),
}
_PROFILE_URLS: dict[str, str] = {
    "instagram": "https://instagram.com/{h}",
    "facebook": "https://facebook.com/{h}",
    "tiktok": "https://tiktok.com/@{h}",
    "x": "https://x.com/{h}",
}


class UnsupportedInput(ValueError):
    """The input is not a supported profile link, handle, phone or till (API: 422 UNSUPPORTED_PLATFORM)."""


@dataclass(frozen=True, slots=True)
class ParsedInput:
    """A normalised checker input."""

    kind: Literal["url", "handle", "phone", "till"]
    value: str  # what the user submitted (trimmed)
    platform: str | None = None
    handle: str | None = None  # lowercase, no '@'
    url: str | None = None  # canonical profile URL
    number: str | None = None  # E.164 phone or till digits (kind phone/till)

    @property
    def is_payment(self) -> bool:
        """Phone / till inputs go to ``/verify/payment``, not ``/check``."""
        return self.kind in ("phone", "till")


def profile_url(platform: str, handle: str) -> str | None:
    """Canonical profile URL for a handle."""
    template = _PROFILE_URLS.get(platform)
    if template is None:
        return None
    if platform == "facebook" and handle.isdigit():
        return f"https://facebook.com/profile.php?id={handle}"
    return template.format(h=handle)


def normalize_handle_input(raw: str) -> str:
    """Lowercase, strip whitespace, a leading '@' and a trailing '/'."""
    return raw.strip().lower().lstrip("@").rstrip("/")


def _valid_handle(handle: str) -> str:
    if not _HANDLE.match(handle):
        raise UnsupportedInput("That doesn't look like a valid account name.")
    return handle


def _parse_url(raw: str) -> ParsedInput:
    text = raw if "://" in raw else "https://" + raw
    parts = urlsplit(text)
    host = (parts.hostname or "").lower()
    platform = _HOSTS.get(host)
    if platform is None:
        raise UnsupportedInput("Only Instagram, Facebook, TikTok, X and WhatsApp links are supported.")
    segments = [s for s in parts.path.split("/") if s]

    if platform == "whatsapp":
        from_query = (parse_qs(parts.query).get("phone") or [""])[0]
        digits = segments[0] if segments and segments[0] != "send" else from_query
        phone = canonical_phone(digits)
        if phone is None:
            raise UnsupportedInput("That WhatsApp link has no Kenyan phone number.")
        return ParsedInput(kind="phone", value=raw, platform="whatsapp", number=phone)

    if platform == "facebook" and segments and segments[0] == "profile.php":
        profile_id = (parse_qs(parts.query).get("id") or [""])[0]
        if not profile_id.isdigit():
            raise UnsupportedInput("That Facebook link has no profile id.")
        return ParsedInput(
            kind="url",
            value=raw,
            platform="facebook",
            handle=profile_id,
            url=profile_url("facebook", profile_id),
        )

    if platform == "instagram" and len(segments) >= 2 and segments[0] == "stories":
        segments = segments[1:]
    if not segments:
        raise UnsupportedInput("Paste a link to a profile, not the home page.")
    first = segments[0]
    if platform == "tiktok":
        if not first.startswith("@"):
            raise UnsupportedInput("TikTok profile links look like tiktok.com/@name.")
        first = first[1:]
    if first.lower() in _RESERVED.get(platform, frozenset()):
        raise UnsupportedInput("Paste a link to the profile itself, not to a post or page section.")
    handle = _valid_handle(normalize_handle_input(first))
    return ParsedInput(
        kind="url", value=raw, platform=platform, handle=handle, url=profile_url(platform, handle)
    )


def parse_input(raw: str, platform: str | None = None) -> ParsedInput:
    """Parse a URL, @handle, phone or till.

    Args:
        raw: user input (max 2048 chars).
        platform: explicit platform for a bare handle (defaults to instagram).

    Raises:
        UnsupportedInput: anything that isn't a supported profile link / handle / number.
    """
    value = (raw or "").strip()
    if not value:
        raise UnsupportedInput("Nothing to check.")
    if len(value) > MAX_INPUT_LENGTH:
        raise UnsupportedInput("Input is too long.")

    compact = re.sub(r"[\s\-()]", "", value)
    if re.fullmatch(r"\+?\d{5,13}", compact):
        phone = canonical_phone(compact)
        if phone:
            return ParsedInput(kind="phone", value=value, number=phone)
        till = canonical_till(compact)
        if till and not compact.startswith("+"):
            return ParsedInput(kind="till", value=value, number=till)
        raise UnsupportedInput("That number is not a Kenyan mobile number or a 5-7 digit till/paybill.")

    # "kilimani.glow" is a valid Instagram handle, so a dot alone doesn't make a URL.
    looks_like_url = "://" in value or "/" in value or value.lower().split("?")[0] in _HOSTS
    if looks_like_url and not value.startswith("@"):
        return _parse_url(value)

    target_platform = (platform or "instagram").lower()
    if target_platform not in _PROFILE_URLS:
        raise UnsupportedInput("Unsupported platform.")
    handle = _valid_handle(normalize_handle_input(value))
    return ParsedInput(
        kind="handle",
        value=value,
        platform=target_platform,
        handle=handle,
        url=profile_url(target_platform, handle),
    )
