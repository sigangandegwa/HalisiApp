<<<<<<< HEAD
import pytest
from app.ingestion.extractors import extract_payment_signals

@pytest.mark.parametrize("text, expected", [
    ("Call us on 0712345678", {"phones": ["+254712345678"], "tills": [], "paybills": [], "has_pochi": False}),
    ("WhatsApp +254 712 345 678", {"phones": ["+254712345678"], "tills": [], "paybills": [], "has_pochi": False}),
    ("wa.me/254712345678", {"phones": ["+254712345678"], "tills": [], "paybills": [], "has_pochi": False}),
    ("Till no 123456", {"phones": [], "tills": ["123456"], "paybills": [], "has_pochi": False}),
    ("Buy goods 123456", {"phones": [], "tills": ["123456"], "paybills": [], "has_pochi": False}),
    ("B.G. 123456", {"phones": [], "tills": ["123456"], "paybills": [], "has_pochi": False}),
    ("Paybill 987654", {"phones": [], "tills": [], "paybills": ["987654"], "has_pochi": False}),
    ("Send money to 0712 345 678", {"phones": ["+254712345678"], "tills": [], "paybills": [], "has_pochi": True}),
    ("Pochi la biashara", {"phones": [], "tills": [], "paybills": [], "has_pochi": True}),
    ("Tuma pesa kwa 0112345678", {"phones": ["+254112345678"], "tills": [], "paybills": [], "has_pochi": True}),
    ("Till: 12345, Call +254711222333", {"phones": ["+254711222333"], "tills": ["12345"], "paybills": [], "has_pochi": False}),
    ("No phone, no till", {"phones": [], "tills": [], "paybills": [], "has_pochi": False})
])
def test_payment_extractors(text, expected):
    res = extract_payment_signals(text)
    assert sorted(res["phones"]) == sorted(expected["phones"])
    assert sorted(res["tills"]) == sorted(expected["tills"])
    assert sorted(res["paybills"]) == sorted(expected["paybills"])
    assert res["has_pochi"] == expected["has_pochi"]
=======
"""Tests for app.engine.payment (payment-score half of TSK-021)."""

import pytest

from app.engine.payment import (
    PaymentEvidence,
    canonical_phone,
    canonical_till,
    mask_phone,
    payment_score,
)

OFFICIAL_PHONES = ["+254712345678"]
OFFICIAL_TILL = "543210"


def score(found: PaymentEvidence, *, close: bool = True, reported=(), mpesa=OFFICIAL_TILL):
    return payment_score(
        found,
        official_phones=OFFICIAL_PHONES,
        official_mpesa_number=mpesa,
        close_resemblance=close,
        confirmed_reported=reported,
    )


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("0712 345 678", "+254712345678"),
        ("+254-712-345678", "+254712345678"),
        ("254712345678", "+254712345678"),
        ("712345678", "+254712345678"),
        ("0112345678", "+254112345678"),
        ("0812345678", None),          # not a Kenyan mobile prefix
        ("12345", None),
        ("", None),
    ],
)
def test_canonical_phone(raw, expected):
    assert canonical_phone(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"), [("543 210", "543210"), ("12345", "12345"), ("1234", None), ("12345678", None)]
)
def test_canonical_till(raw, expected):
    assert canonical_till(raw) == expected


def test_mask_phone():
    assert mask_phone("+254798999111") == "0798 *** 111"
    assert mask_phone("0798999111") == "0798 *** 111"
    assert mask_phone("543210") == "543210"


def test_no_payment_details_is_unavailable_not_zero():
    assert score(PaymentEvidence()).score is None


def test_only_official_numbers_score_zero():
    result = score(PaymentEvidence(phones=["0712 345 678"], tills=["543210"]))
    assert result.score == 0.0
    assert result.reasons == ()
    assert "Only this business" in result.evidence


def test_pochi_merchant_number_counts_as_registered():
    result = score(PaymentEvidence(phones=["0700111222"], pochi_phrasing=True), mpesa="0700 111 222")
    assert result.score == 0.0
    assert not result.pochi_request


@pytest.mark.parametrize(("close", "expected"), [(True, 100.0), (False, 60.0)])
def test_unregistered_phone(close, expected):
    result = score(PaymentEvidence(phones=["0798999111"]), close=close)
    assert result.score == expected
    assert result.unregistered_phones == ("+254798999111",)
    assert result.reasons == ("PAYMENT_MISMATCH",)


@pytest.mark.parametrize(("close", "expected"), [(True, 50.0), (False, 25.0)])
def test_unregistered_till_is_weaker_than_a_personal_number(close, expected):
    """Tills need a registered business; a competitor's own till must not read as a hijack."""
    result = score(PaymentEvidence(tills=["889900"]), close=close)
    assert result.score == expected
    assert result.unregistered_tills == ("889900",)


def test_pochi_request_with_unregistered_number_is_maximal():
    result = score(PaymentEvidence(phones=["0711222333"], pochi_phrasing=True), close=False)
    assert result.score == 100.0
    assert result.pochi_request
    assert result.reasons == ("POCHI_REQUEST",)
    assert "personal number" in result.evidence


def test_confirmed_report_hit_is_maximal_even_without_resemblance():
    result = score(PaymentEvidence(phones=["0798999111"]), close=False, reported=["0798 999 111"])
    assert result.score == 100.0
    assert result.reported_hits == ("+254798999111",)
    assert "COMMUNITY_REPORTED" in result.reasons


def test_evidence_never_contains_a_full_third_party_number():
    result = score(PaymentEvidence(phones=["+254798999111", "0798999111"]))
    assert result.unregistered_phones == ("+254798999111",)          # de-duplicated
    assert "798999111" not in result.evidence
    assert "0798 *** 111" in result.evidence
>>>>>>> main
