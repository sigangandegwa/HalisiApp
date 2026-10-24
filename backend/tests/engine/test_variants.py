"""Tests for app.engine.variants (TSK-047)."""

from app.engine.matcher import identity_score
from app.engine.scorer import MerchantProfile, OfficialHandle
from app.engine.variants import handle_variants


def test_includes_what_scammers_actually_register():
    variants = handle_variants("nairobisneakervault", "Nairobi Sneaker Vault")
    assert "nairobisneakervau1t" in variants                      # look-alike character
    assert "nairobisneakervault_official" in variants             # affix on the real handle
    assert "nairobi_sneakervault_official_ke" in variants         # name split + stacked affix
    assert "nairobi_sneaker_vault" in variants                    # separators from the business name


def test_never_returns_the_real_handle_or_invalid_handles():
    variants = handle_variants("@KilimaniGlow", "Kilimani Glow")
    assert "kilimaniglow" not in variants
    assert all(v == v.lower() and " " not in v and "@" not in v for v in variants)
    assert len(variants) == len(set(variants))


def test_limit_and_garbage_input():
    assert len(handle_variants("nairobisneakervault", "Nairobi Sneaker Vault", limit=10)) == 10
    assert handle_variants("not a handle!") == []
    assert handle_variants("") == []


def test_most_variants_would_actually_be_caught_by_the_matcher():
    """The generator and the matcher must agree: what we probe for is what we can score."""
    merchant = MerchantProfile(
        id="m", business_name="Nairobi Sneaker Vault", slug="nsv",
        official_handles=[OfficialHandle("instagram", "nairobisneakervault")],
    )
    variants = handle_variants("nairobisneakervault", "Nairobi Sneaker Vault")
    caught = [v for v in variants if identity_score(v, None, merchant).score >= 70]
    assert len(caught) / len(variants) >= 0.75
