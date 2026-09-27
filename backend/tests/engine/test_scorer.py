"""Tests for app.engine.scorer (TSK-008). Required cases: docs/BACKEND.md section 6.8."""

from dataclasses import replace
from datetime import date

import pytest

from app.engine.hasher import ImageFeatures, compute_hashes
from app.engine.imaging import normalize
from app.engine.payment import PaymentEvidence
from app.engine.scorer import (
    MerchantProfile,
    OfficialHandle,
    ScoringContext,
    TargetProfile,
    find_official,
    safe_action,
    score_against_all,
    score_target,
)
from tests.engine import imagegen as gen

TODAY = date(2026, 9, 27)
CTX = ScoringContext(today=TODAY)


def features(img) -> ImageFeatures:
    hashes = compute_hashes(normalize(img))
    return ImageFeatures(phash=hashes.phash, dhash=hashes.dhash)


NSV_LOGO = gen.sneaker_logo()
NSV = MerchantProfile(
    id="nsv",
    business_name="Nairobi Sneaker Vault",
    slug="nairobi-sneaker-vault",
    official_handles=[OfficialHandle("instagram", "nairobisneakervault")],
    logo=features(NSV_LOGO),
    phone_numbers=["+254712345678"],
    mpesa_type="till",
    mpesa_number="543210",
    mpesa_account_name="NAIROBI SNEAKER VAULT",
    established_on=date(2021, 3, 1),
)
GLOW = MerchantProfile(
    id="glow",
    business_name="Kilimani Glow",
    slug="kilimani-glow",
    official_handles=[OfficialHandle("instagram", "kilimaniglow")],
    logo=features(gen.glow_logo()),
    mpesa_type="paybill",
    mpesa_number="400200",
)
MERCHANTS = [NSV, GLOW]

BLATANT = TargetProfile(
    platform="instagram",
    handle="nairobi_sneakervault_official_ke",
    display_name="Nairobi Sneaker Vault Official",
    bio="Lipa kwanza. Pay before delivery. Send money to 0798 999 111",
    avatar=features(gen.overlay_text(gen.jpeg(NSV_LOGO))),
    payment=PaymentEvidence(phones=["+254798999111"], pochi_phrasing=True),
    follower_count=212,
    post_count=9,
    account_created_on=date(2026, 9, 19),
)
SUBTLE = TargetProfile(
    platform="instagram",
    handle="nairobisneakervau1t",
    display_name="Nairobi Sneaker Vault",
    bio="Pochi la biashara 0711 222 333. Delivery countrywide",
    avatar=features(gen.crop(gen.recolor(NSV_LOGO))),
    payment=PaymentEvidence(phones=["+254711222333"], pochi_phrasing=True),
)
COMPETITOR = TargetProfile(
    platform="instagram",
    handle="nairobisneakerhub",
    display_name="Nairobi Sneaker Hub",
    bio="Nairobi sneaker plug since 2019. Delivery countrywide. Till 889900",
    avatar=features(gen.threads_logo()),
    payment=PaymentEvidence(tills=["889900"]),
    follower_count=5400,
    post_count=410,
)


# --- required cases (BACKEND.md section 6.8) ------------------------------------------------------

def test_blatant_clone_is_impersonation_at_90_plus():
    result = score_against_all(BLATANT, MERCHANTS, CTX)
    assert result.verdict == "impersonation"
    assert result.score >= 90
    assert result.merchant is NSV
    assert result.confidence == 1.0
    codes = [r.code for r in result.reasons]
    assert {"LOGO_COPY", "HANDLE_LOOKALIKE", "POCHI_REQUEST", "SCAM_LANGUAGE", "NEW_ACCOUNT"} <= set(codes)
    assert result.reasons[0].severity == "high"


def test_subtle_clone_is_impersonation_at_70_plus():
    """Homoglyph handle + cropped/recoloured logo + Pochi request, no account data."""
    result = score_against_all(SUBTLE, MERCHANTS, CTX)
    assert result.verdict == "impersonation"
    assert result.score >= 70
    assert "O2" in result.rules


def test_similar_named_competitor_is_no_match():
    """The false-positive proof for judges: similar name, own logo, own till."""
    result = score_against_all(COMPETITOR, MERCHANTS, CTX)
    assert result.verdict == "no_match"
    assert result.score < 40
    assert result.merchant is None
    assert "O2" not in result.rules


def test_exact_official_handle_is_official():
    target = TargetProfile(platform="instagram", handle="@NairobiSneakerVault/")
    result = score_against_all(target, MERCHANTS, CTX)
    assert result.verdict == "official"
    assert result.merchant is NSV
    assert result.rules == ("O1",)
    assert result.dimensions == ()


def test_logo_only_evidence_is_capped_at_suspicious():
    result = score_against_all(TargetProfile(platform=None, handle=None, avatar=NSV.logo), MERCHANTS, CTX)
    assert result.confidence == 0.30
    assert result.verdict == "suspicious"
    assert "O4" in result.rules


# --- false-positive regressions -------------------------------------------------------------------

def test_unrelated_shop_sharing_a_city_prefix_with_its_own_number_is_no_match():
    """Matcher prefix bias gives 'nairobi_bakery' ~78 identity vs 'nairobisneakervault'. A clearly
    different logo must stop its personal order number from reading as a payment hijack."""
    bakery = TargetProfile(
        platform="instagram",
        handle="nairobi_bakery",
        display_name="Nairobi Bakery",
        bio="Fresh cakes daily. Order on 0722 111 000",
        avatar=features(gen.threads_logo()),
        payment=PaymentEvidence(phones=["+254722111000"]),
        follower_count=1200,
        post_count=150,
    )
    result = score_against_all(bakery, MERCHANTS, CTX)
    assert result.verdict == "no_match", result.dimensions


def test_dotted_variant_of_official_handle_is_not_official():
    """On Instagram 'nairobi.sneaker.vault' is a different account; the matcher strips dots, O1 must not."""
    target = TargetProfile(platform="instagram", handle="nairobi.sneaker.vault")
    assert find_official(target, MERCHANTS) is None
    assert score_against_all(target, MERCHANTS, CTX).verdict != "official"


def test_official_handle_on_another_platform_is_not_official():
    assert find_official(TargetProfile(platform="tiktok", handle="nairobisneakervault"), MERCHANTS) is None


# --- mechanics ------------------------------------------------------------------------------------

def test_unavailable_signals_are_renormalised_out():
    target = TargetProfile(platform="instagram", handle="nairobisneakervau1t", bio="New stock this week")
    result = score_target(target, NSV, CTX)
    by_key = {d.key: d for d in result.dimensions}
    assert by_key["visual"].score is None and by_key["payment"].score is None
    assert by_key["language"].score == 0.0                     # text present, no scam phrases
    identity = by_key["identity"].score
    assert result.score == pytest.approx(round(0.25 * identity / 0.35, 2))
    assert result.confidence == 0.35


def test_resemblance_gate_caps_unrelated_scammy_pages():
    target = TargetProfile(
        platform="instagram",
        handle="mombasa_fashion_house",
        bio="Lipa kwanza! Pay before delivery. Send money to 0798 999 111",
        payment=PaymentEvidence(phones=["+254798999111"], pochi_phrasing=True),
    )
    result = score_against_all(target, MERCHANTS, CTX)
    assert result.verdict == "no_match"
    assert result.score <= 39
    assert result.merchant is None
    assert [r.code for r in result.reasons] == ["SCAM_LANGUAGE"]     # merchant-independent reasons only


def test_community_confirmed_number_sets_a_floor():
    ctx = replace(CTX, confirmed_reported=frozenset({"+254733000111"}))
    target = TargetProfile(
        platform="instagram",
        handle="nairobisneakervault_ke",
        payment=PaymentEvidence(phones=["0733 000 111"]),
    )
    result = score_against_all(target, MERCHANTS, ctx)
    assert result.score >= 85
    assert "O3" in result.rules
    reported = next(r for r in result.reasons if r.code == "COMMUNITY_REPORTED")
    assert reported.severity == "high"


def test_best_matching_merchant_wins():
    target = TargetProfile(platform="instagram", handle="kilimaniglow_official", avatar=GLOW.logo)
    assert score_against_all(target, MERCHANTS, CTX).merchant is GLOW


def test_no_registered_merchants_is_no_match():
    assert score_against_all(BLATANT, [], CTX).verdict == "no_match"


def test_thresholds_come_from_context():
    strict = replace(CTX, threat_threshold=99.5)
    assert score_against_all(BLATANT, MERCHANTS, strict).verdict == "suspicious"


def test_established_account_data_counts_as_evidence():
    result = score_target(COMPETITOR, NSV, CTX)
    account = next(d for d in result.dimensions if d.key == "account")
    assert account.score == 10.0
    assert account.evidence == "410 posts · 5400 followers"


# --- serialisation --------------------------------------------------------------------------------

def test_payloads_match_the_api_contract_and_mask_numbers():
    result = score_against_all(BLATANT, MERCHANTS, CTX)
    dims = result.dimensions_payload()
    assert [d["key"] for d in dims] == ["visual", "identity", "payment", "language", "account"]
    assert set(dims[0]) == {"key", "label", "score", "weight", "available", "evidence"}
    reasons = result.reasons_payload()
    assert all(r["text"] and r["text_sw"] for r in reasons)
    flat = str(dims) + str(reasons)
    assert "798999111" not in flat and "0798 *** 111" in flat


def test_unavailable_dimension_payload():
    result = score_target(TargetProfile(platform="instagram", handle="nairobisneakervau1t"), NSV, CTX)
    visual = result.dimensions_payload()[0]
    assert visual == {"key": "visual", "label": "Logo match", "score": 0.0, "weight": 0.30,
                      "available": False, "evidence": "No data"}


@pytest.mark.parametrize(
    ("merchant", "en", "sw"),
    [
        (NSV, "Pay only via Buy Goods Till 543210 (NAIROBI SNEAKER VAULT) through @nairobisneakervault.",
         "Lipa tu kwa Till 543210 (NAIROBI SNEAKER VAULT). Ukurasa rasmi ni @nairobisneakervault."),
        (replace(NSV, mpesa_type="pochi", mpesa_number="+254700111222", mpesa_account_name=None),
         "Pay only via Pochi la Biashara 0700 111 222 through @nairobisneakervault.",
         "Lipa tu kwa Pochi la Biashara 0700 111 222. Ukurasa rasmi ni @nairobisneakervault."),
        (replace(NSV, mpesa_type="none", mpesa_number=None),
         "Contact Nairobi Sneaker Vault only through @nairobisneakervault.",
         "Wasiliana na Nairobi Sneaker Vault kupitia @nairobisneakervault pekee."),
    ],
)
def test_safe_action(merchant, en, sw):
    assert safe_action(merchant, "instagram") == (en, sw)
