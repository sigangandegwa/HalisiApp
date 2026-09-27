"""Tests for app.ingestion.extractors (extractor half of TSK-021)."""

import pytest

from app.engine.payment import PaymentEvidence
from app.ingestion.extractors import (
    extract_payment_evidence,
    extract_payment_signals,
    extract_phones,
)

_NONE = {"phones": [], "tills": [], "paybills": [], "has_pochi": False}


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Call us on 0712345678", {**_NONE, "phones": ["+254712345678"]}),
        ("WhatsApp +254 712 345 678", {**_NONE, "phones": ["+254712345678"]}),
        ("wa.me/254712345678", {**_NONE, "phones": ["+254712345678"]}),
        ("Till no 123456", {**_NONE, "tills": ["123456"]}),
        ("Buy goods 123456", {**_NONE, "tills": ["123456"]}),
        ("B.G. 123456", {**_NONE, "tills": ["123456"]}),
        ("Paybill 987654", {**_NONE, "paybills": ["987654"]}),
        ("Send money to 0712 345 678", {**_NONE, "phones": ["+254712345678"], "has_pochi": True}),
        ("Pochi la biashara", {**_NONE, "has_pochi": True}),
        ("Tuma pesa kwa 0112345678", {**_NONE, "phones": ["+254112345678"], "has_pochi": True}),
        ("Till: 12345, Call +254711222333", {**_NONE, "phones": ["+254711222333"], "tills": ["12345"]}),
        ("No phone, no till", _NONE),
    ],
)
def test_payment_extractors(text: str, expected: dict) -> None:
    res = extract_payment_signals(text)
    assert sorted(res["phones"]) == sorted(expected["phones"])
    assert sorted(res["tills"]) == sorted(expected["tills"])
    assert sorted(res["paybills"]) == sorted(expected["paybills"])
    assert res["has_pochi"] == expected["has_pochi"]


# Real-world Kenyan formats seen in shop bios and captions (all numbers here are fictional).
@pytest.mark.parametrize(
    ("text", "phones", "tills", "pochi"),
    [
        ("Order: 0712 345 678", ["+254712345678"], [], False),
        ("Call/WhatsApp 0712-345-678", ["+254712345678"], [], False),
        ("📞 +254-712-345678", ["+254712345678"], [], False),
        ("Reach us 254712345678 anytime", ["+254712345678"], [], False),
        ("Safaricom 0112 345 678 / Airtel 0733 000 111", ["+254112345678", "+254733000111"], [], False),
        ("DM or chat wa.me/+254798999111", ["+254798999111"], [], False),
        ("Lipa na M-Pesa Till No. 543210", [], ["543210"], False),
        ("BUY GOODS TILL NUMBER: 889900", [], ["889900"], False),
        ("Paybill 400200 Acc: KGLOW", [], ["400200"], False),
        ("Pay bill no: 247247 account 0712345678", ["+254712345678"], ["247247"], False),
        ("Pochi la Biashara 0711 222 333", ["+254711222333"], [], True),
        ("Tuma pesa 0798 999 111 kisha tuma screenshot", ["+254798999111"], [], True),
        ("SEND MONEY TO 0798999111 before delivery", ["+254798999111"], [], True),
        ("BG 55432 | Delivery countrywide", [], ["55432"], False),
        ("Till#123456", [], ["123456"], False),
        ("Est. 2019 · 5,400 followers · 410 posts", [], [], False),  # counts are not phone numbers
        ("Order 10712345678 is ready", [], [], False),  # embedded in a longer number
    ],
)
def test_extract_payment_evidence_real_world_formats(
    text: str, phones: list[str], tills: list[str], pochi: bool
) -> None:
    evidence = extract_payment_evidence(text)
    assert list(evidence.phones) == phones
    assert list(evidence.tills) == tills
    assert evidence.pochi_phrasing is pochi


def test_evidence_is_deduplicated_in_first_seen_order() -> None:
    text = "Call 0733 000 111 or 0712 345 678. Again: +254733000111, wa.me/254712345678"
    assert extract_phones(text) == ["+254733000111", "+254712345678"]
    assert extract_payment_evidence(text).phones == ("+254733000111", "+254712345678")


def test_tills_and_paybills_share_one_list() -> None:
    ev = extract_payment_evidence("Till 543210 or Paybill 400200, till 543210")
    assert ev.tills == ("543210", "400200")


def test_empty_input() -> None:
    assert extract_payment_evidence(None) == PaymentEvidence()
    assert extract_payment_evidence("") == PaymentEvidence()
    assert extract_payment_signals(None) == _NONE
