"""Tests for app.engine.matcher (TSK-016). Golden table: docs/BACKEND.md section 6.4 (never loosen)."""

from dataclasses import dataclass, field

import pytest

from app.engine.matcher import (
    distinctive_similarity,
    fold_homoglyphs,
    identity_score,
    language_score,
    normalize_handle,
    strip_affixes,
)


@dataclass
class _Handle:
    handle: str
    platform: str = "instagram"


@dataclass
class _Merchant:
    official_handles: list[_Handle]
    business_name: str = ""
    aliases: list[str] = field(default_factory=list)


def merchant(*handles: str, name: str = "", aliases: tuple[str, ...] = ()) -> _Merchant:
    return _Merchant([_Handle(h) for h in handles], name, list(aliases))


# --- golden table (spec values, BACKEND.md 6.4) -------------------------------------------------


@pytest.mark.parametrize(
    ("official", "target", "lo", "hi"),
    [
        ("nairobisneakervault", "nairobi_sneakervault_official_ke", 90, 100),
        ("nairobisneakervault", "nairobisneakervau1t", 90, 100),
        ("nairobisneakervault", "nairobi.sneaker.vault", 95, 100),
        ("kilimaniglow", "kiIimaniglow_ke", 90, 100),  # capital i
        ("nairobisneakervault", "nairobi_bakery", 0, 49.99),
        ("nairobisneakervault", "nairobisneakerhub", 0, 69.99),  # real competitor
        ("pwanithreads", "mombasa_fashion_house", 0, 29.99),
    ],
)
def test_identity_golden(official: str, target: str, lo: float, hi: float) -> None:
    result = identity_score(target, None, merchant(official))
    assert lo <= result.score <= hi, f"{target!r} vs {official!r}: {result.score} ({result.evidence})"


# --- extra must-hit cases (typosquats) ----------------------------------------------------------


@pytest.mark.parametrize(
    ("official", "target"),
    [
        ("nairobisneakervault", "nairobisneakervualt"),  # transposition
        ("nairobisneakervault", "nairobisneekervault"),  # one substitution mid-word
        ("nairobisneakervault", "nairobisneakervaul"),  # truncation by one letter
        ("nairobisneakervault", "official_nairobisneakervault"),  # prefix affix
        ("nairobisneakervault", "nairobisneakervault.shop"),
        ("kilimaniglow", "klimaniglow"),
        ("kilimaniglow", "kilimaniglow.official"),
        ("pwanithreads", "pwanlthreads"),
        ("pwanithreads", "pwani_threadz"),
        ("pwanithreads", "pwanithreads_ke"),
        ("pwanithreads", "pwanithreads254"),
        ("nairobisneakervault", "nairobisneakervau1t_ke"),
        ("kilimaniglow", "ki1imanig1ow"),
        ("nairobisneakervault", "nairobisneakervau|t"),
    ],
)
def test_identity_catches_typosquats(official: str, target: str) -> None:
    result = identity_score(target, None, merchant(official))
    assert result.score >= 90, f"{target!r}: {result.score} ({result.evidence})"


# --- extra must-miss cases (shared city / category words) ---------------------------------------


@pytest.mark.parametrize(
    ("official", "target", "hi"),
    [
        ("nairobisneakervault", "nairobi", 60),
        ("kilimaniglow", "kilimanibeauty", 50),
        ("nairobisneakervault", "kicks_nairobi", 50),
        ("pwanithreads", "pwani_fish_market", 50),
    ],
)
def test_identity_ignores_shared_generic_prefixes(official: str, target: str, hi: float) -> None:
    assert identity_score(target, None, merchant(official)).score < hi


def test_display_name_against_business_name() -> None:
    nsv = merchant("nairobisneakervault", name="Nairobi Sneaker Vault")
    assert identity_score("nairobisneakerhub", "Nairobi Sneaker Hub", nsv).score < 70
    assert identity_score("nsv_ke_deals", "Nairobi Sneaker Vault Official", nsv).score >= 90


def test_best_of_multiple_handles_and_aliases() -> None:
    m = merchant("nairobisneakervault", "nsv.kicks", name="Nairobi Sneaker Vault", aliases=("NSV Kicks",))
    assert identity_score("nsvkicks_official", None, m).score >= 90


def test_evidence_names_the_trick() -> None:
    result = identity_score("nairobi_sneakervault_official_ke", None, merchant("nairobisneakervault"))
    assert "nairobisneakervault" in result.evidence and "'official'" in result.evidence
    dotted = identity_score("nairobi.sneaker.vault", None, merchant("nairobisneakervault"))
    assert "separators" in dotted.evidence
    glyph = identity_score("nairobisneakervau1t", None, merchant("nairobisneakervault"))
    assert "look-alike" in glyph.evidence


def test_no_inputs_is_zero() -> None:
    assert identity_score(None, None, merchant("abc")).score == 0.0
    assert identity_score("abc", None, merchant()).score == 0.0


def test_helpers() -> None:
    assert normalize_handle("@Nairobi.Sneaker_Vault/") == "nairobisneakervault"
    assert fold_homoglyphs("rn0b1l3") == "moblle"
    assert strip_affixes(["nairobi", "official", "ke"]) == ["nairobi"]
    assert distinctive_similarity("abc", "abc") == 100.0
    assert distinctive_similarity("", "abc") == 0.0


# --- language (BACKEND.md 6.6) -------------------------------------------------------------------


def test_language_score_weights() -> None:
    res = language_score("Welcome to our shop. Pay before delivery and get 10% off. Offer ends today!")
    assert res.score == 65.0
    assert "pay before delivery" in res.evidence and "offer ends today" in res.evidence


def test_language_score_capped_at_100() -> None:
    assert (
        language_score("Pay before delivery. Lipa kwanza. No refunds. Strictly delivery. Order now.").score
        == 100.0
    )


def test_language_text_without_phrases_is_zero_not_none() -> None:
    res = language_score("Just a normal bio")
    assert res.score == 0.0
    assert res.phrases == ()


def test_language_no_text_is_none() -> None:
    assert language_score(None).score is None
    assert language_score("   ").score is None


def test_language_uses_word_boundaries() -> None:
    assert language_score("Leo tunauza viatu mpya").score == 0.0  # "leo tu" inside "Leo tunauza"
    assert language_score("Offer leo tu!").score == 25.0
    assert language_score("Order nowhere else").score == 0.0


def test_language_tolerates_extra_whitespace_and_case() -> None:
    assert language_score("LIPA   KWANZA").score == 40.0
