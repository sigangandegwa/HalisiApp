"""Kenyan payment-detail extractors (extractor half of TSK-021, docs/BACKEND.md section 6.5).

Run on bios, captions and link-in-bio text. Output feeds ``app.engine.payment.payment_score``.
Every list is de-duplicated in first-seen order so results (and fixtures) are deterministic.
"""

import re
from typing import TypedDict

from app.engine.payment import PaymentEvidence, canonical_phone, canonical_till

# Kenyan mobiles: 07xx / 01xx / +254 7xx / 254-1xx, digits optionally split by spaces or dashes.
KE_PHONE = re.compile(r"(?<![\d+])(?:\+?254[\s-]?|0)([17](?:[\s-]?\d){8})(?!\d)")
TILL = re.compile(
    r"(?:\btill|\bbuy\s*goods|\bb\.?g\.(?!\w)|\bbg\b)\s*(?:no\.?|number|num\.?|#|:)?\s*[:#-]?\s*(\d{5,7})(?!\d)",
    re.I,
)
PAYBILL = re.compile(r"\bpay\s*-?\s*bill\s*(?:no\.?|number|num\.?|#|:)?\s*[:#-]?\s*(\d{5,7})(?!\d)", re.I)
WA_LINK = re.compile(r"wa\.me/\+?(\d{10,13})", re.I)
POCHI = re.compile(r"pochi\s*la\s*biashara|send\s*money\s*to|tuma\s*pesa", re.I)


class PaymentSignals(TypedDict):
    """Legacy dict shape returned by :func:`extract_payment_signals`."""

    phones: list[str]
    tills: list[str]
    paybills: list[str]
    has_pochi: bool


def _unique(values: list[str]) -> list[str]:
    """De-duplicate while keeping first-seen order."""
    return list(dict.fromkeys(values))


def extract_phones(text: str) -> list[str]:
    """All Kenyan mobile numbers in ``text`` (including ``wa.me`` links) as E.164, in order of appearance."""
    if not text:
        return []
    found: list[tuple[int, str]] = []
    for match in KE_PHONE.finditer(text):
        phone = canonical_phone(match.group(0))
        if phone:
            found.append((match.start(), phone))
    for match in WA_LINK.finditer(text):
        phone = canonical_phone(match.group(1))
        if phone:
            found.append((match.start(), phone))
    return _unique([phone for _, phone in sorted(found)])


def extract_tills(text: str) -> list[str]:
    """Buy Goods till numbers (``Till No. 543210``, ``Buy goods 123456``, ``B.G. 123456``)."""
    if not text:
        return []
    return _unique([t for t in (canonical_till(m) for m in TILL.findall(text)) if t])


def extract_paybills(text: str) -> list[str]:
    """Paybill numbers (``Paybill 400200``, ``Pay bill no: 247247``)."""
    if not text:
        return []
    return _unique([t for t in (canonical_till(m) for m in PAYBILL.findall(text)) if t])


def has_pochi(text: str) -> bool:
    """Whether the text asks for a personal-line payment (Pochi / "send money to" / "tuma pesa")."""
    return bool(text) and bool(POCHI.search(text))


def extract_payment_evidence(text: str | None) -> PaymentEvidence:
    """Extract everything the payment scorer needs from free text.

    Tills and paybills both go into ``tills`` (the scorer treats them alike: both need a
    registered business). ``pochi_phrasing`` comes from the POCHI regex.
    """
    if not text:
        return PaymentEvidence()
    tills = _unique([*extract_tills(text), *extract_paybills(text)])
    return PaymentEvidence(
        phones=tuple(extract_phones(text)), tills=tuple(tills), pochi_phrasing=has_pochi(text)
    )


def extract_payment_signals(text: str | None) -> PaymentSignals:
    """Legacy dict form (kept for existing callers/tests): phones, tills, paybills, has_pochi."""
    if not text:
        return {"phones": [], "tills": [], "paybills": [], "has_pochi": False}
    return {
        "phones": extract_phones(text),
        "tills": extract_tills(text),
        "paybills": extract_paybills(text),
        "has_pochi": has_pochi(text),
    }
