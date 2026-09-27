"""URL / handle / number parsing (docs/BACKEND.md section 7.1)."""

import pytest

from app.ingestion.url_parser import UnsupportedInput, parse_input


@pytest.mark.parametrize(
    ("raw", "platform", "handle", "url"),
    [
        (
            "https://instagram.com/nairobi_sneakervault_official_ke",
            "instagram",
            "nairobi_sneakervault_official_ke",
            "https://instagram.com/nairobi_sneakervault_official_ke",
        ),
        (
            "https://www.instagram.com/NairobiSneakerVault/?igsh=MWx0bXBx&utm_source=qr",
            "instagram",
            "nairobisneakervault",
            "https://instagram.com/nairobisneakervault",
        ),
        ("instagram.com/kilimani.glow", "instagram", "kilimani.glow", "https://instagram.com/kilimani.glow"),
        (
            "https://www.instagram.com/stories/pwanithreads/3123/",
            "instagram",
            "pwanithreads",
            "https://instagram.com/pwanithreads",
        ),
        (
            "https://facebook.com/kilimaniglow",
            "facebook",
            "kilimaniglow",
            "https://facebook.com/kilimaniglow",
        ),
        (
            "https://m.facebook.com/kilimaniglow?mibextid=ZbWKwL",
            "facebook",
            "kilimaniglow",
            "https://facebook.com/kilimaniglow",
        ),
        (
            "https://www.facebook.com/profile.php?id=100089123456789&ref=share",
            "facebook",
            "100089123456789",
            "https://facebook.com/profile.php?id=100089123456789",
        ),
        ("fb.com/pwanithreads", "facebook", "pwanithreads", "https://facebook.com/pwanithreads"),
        (
            "https://www.tiktok.com/@pwani.threads?lang=en",
            "tiktok",
            "pwani.threads",
            "https://tiktok.com/@pwani.threads",
        ),
        ("https://x.com/NairobiSV", "x", "nairobisv", "https://x.com/nairobisv"),
        ("https://twitter.com/nairobisv/status/123", "x", "nairobisv", "https://x.com/nairobisv"),
    ],
)
def test_profile_urls(raw: str, platform: str, handle: str, url: str) -> None:
    parsed = parse_input(raw)
    assert (parsed.kind, parsed.platform, parsed.handle, parsed.url) == ("url", platform, handle, url)


def test_raw_handles_default_to_instagram() -> None:
    parsed = parse_input("@Kilimani.Glow")
    assert (parsed.kind, parsed.platform, parsed.handle) == ("handle", "instagram", "kilimani.glow")
    assert parse_input("kilimani.glow").kind == "handle"  # a dot alone is not a URL
    assert parse_input("pwanithreads", platform="tiktok").url == "https://tiktok.com/@pwanithreads"


@pytest.mark.parametrize(
    ("raw", "kind", "number"),
    [
        ("0798 999 111", "phone", "+254798999111"),
        ("+254-798-999111", "phone", "+254798999111"),
        ("(0112) 345-678", "phone", "+254112345678"),
        ("543210", "till", "543210"),
        ("https://wa.me/254798999111?text=hi", "phone", "+254798999111"),
        ("wa.me/+254798999111", "phone", "+254798999111"),
        ("https://api.whatsapp.com/send?phone=254798999111", "phone", "+254798999111"),
    ],
)
def test_numbers_go_to_payment_check(raw: str, kind: str, number: str) -> None:
    parsed = parse_input(raw)
    assert (parsed.kind, parsed.number, parsed.is_payment) == (kind, number, True)


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "   ",
        "https://example.com/shop",
        "https://instagram.com/",
        "https://instagram.com/p/Cxyz/",
        "https://instagram.com/reel/abc",
        "https://tiktok.com/pwanithreads",
        "https://facebook.com/profile.php",
        "https://wa.me/12345",
        "not a handle!",
        "+1 202 555 0100",
        "https://instagram.com/" + "a" * 61,
        "x" * 2049,
    ],
)
def test_rejects(raw: str) -> None:
    with pytest.raises(UnsupportedInput):
        parse_input(raw)
