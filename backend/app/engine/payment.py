"""Payment signal: do the numbers on a page belong to the business it resembles?

Spec: docs/BACKEND.md section 6.5.

Pure functions. The regex extraction of phones, tills and Pochi phrasing from page text lives in
``app.ingestion.extractors`` (TSK-021, Geoffrey). This module only scores what was extracted.

There is no M-Pesa API. "Registered" means registered with Halisi by the merchant (self-declared
phone numbers and M-Pesa number), never a Safaricom lookup.

Kenyan context: a Buy Goods till or Paybill needs a registered business behind it, while
"Send Money" to a personal line or Pochi la Biashara does not. Clone scams overwhelmingly collect
through personal lines. So an unregistered *phone* is scored far higher than an unregistered *till*.
Without that split, an honest competitor with a similar name and its own till reads as a hijack.
"""

import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field

from app.engine.constants import (
    PAYMENT_OFFICIAL_ONLY,
    PAYMENT_UNREGISTERED_PHONE,
    PAYMENT_UNREGISTERED_PHONE_LOW_RESEMBLANCE,
    PAYMENT_UNREGISTERED_TILL,
    PAYMENT_UNREGISTERED_TILL_LOW_RESEMBLANCE,
)

_DIGITS = re.compile(r"\D")


@dataclass(frozen=True, slots=True)
class PaymentEvidence:
    """What the extractors found on the target page."""

    phones: Sequence[str] = ()          # Kenyan mobiles, ideally E.164 (+2547XXXXXXXX)
    tills: Sequence[str] = ()           # Buy Goods till or Paybill numbers (5-7 digits)
    pochi_phrasing: bool = False        # "pochi la biashara", "send money to", "tuma pesa"


@dataclass(frozen=True, slots=True)
class PaymentResult:
    """Payment dimension outcome. ``score`` is None when the page shows no payment details."""

    score: float | None
    unregistered_phones: tuple[str, ...] = ()
    unregistered_tills: tuple[str, ...] = ()
    reported_hits: tuple[str, ...] = ()          # numbers found in confirmed community reports
    pochi_request: bool = False                  # personal-line payment request with an unregistered number
    evidence: str | None = None                  # public-safe: phone numbers are masked
    reasons: tuple[str, ...] = field(default=())  # PAYMENT_MISMATCH, POCHI_REQUEST, COMMUNITY_REPORTED


def canonical_phone(value: str) -> str | None:
    """Return a Kenyan mobile number as E.164 (``+2547XXXXXXXX`` / ``+2541XXXXXXXX``), or None.

    Accepts ``0712345678``, ``712345678``, ``254712345678``, ``+254 712 345 678`` and similar.
    """
    digits = _DIGITS.sub("", value or "")
    if digits.startswith("254"):
        digits = digits[3:]
    elif digits.startswith("0"):
        digits = digits[1:]
    if len(digits) == 9 and digits[0] in "17":
        return "+254" + digits
    return None


def canonical_till(value: str) -> str | None:
    """Return a till/paybill as a plain 5-7 digit string, or None."""
    digits = _DIGITS.sub("", value or "")
    return digits if 5 <= len(digits) <= 7 else None


def mask_phone(e164: str) -> str:
    """Public-safe display: ``+254798999111`` -> ``0798 *** 111``. Non-phones are returned unchanged."""
    phone = canonical_phone(e164)
    if phone is None:
        return e164
    local = "0" + phone[4:]
    return f"{local[:4]} *** {local[-3:]}"


def payment_score(
    found: PaymentEvidence,
    *,
    official_phones: Iterable[str],
    official_mpesa_number: str | None,
    close_resemblance: bool,
    confirmed_reported: Iterable[str] = (),
) -> PaymentResult:
    """Score the payment details on a page against the merchant it resembles.

    Args:
        found: numbers extracted from the target page.
        official_phones: the merchant's registered phone numbers.
        official_mpesa_number: the merchant's till / paybill / Pochi number, if any.
        close_resemblance: whether the page closely resembles this merchant (decided by the scorer).
            Unregistered numbers only become strong evidence on a page that closely resembles the merchant.
        confirmed_reported: phones/tills from ``confirmed`` community reports.

    Returns:
        PaymentResult with score None (no payment details), 0 (only official numbers), or higher.
    """
    phones = _unique(p for p in map(canonical_phone, found.phones) if p)
    tills = _unique(t for t in map(canonical_till, found.tills) if t)
    if not phones and not tills:
        return PaymentResult(score=None)

    official_mpesa = official_mpesa_number or ""
    registered_phones = {p for p in map(canonical_phone, [*official_phones, official_mpesa]) if p}
    registered_tills = {t for t in [canonical_till(official_mpesa)] if t}
    reported = {n for n in (canonical_phone(r) or canonical_till(r) for r in confirmed_reported) if n}

    bad_phones = tuple(p for p in phones if p not in registered_phones)
    bad_tills = tuple(t for t in tills if t not in registered_tills)
    reported_hits = tuple(n for n in (*phones, *tills) if n in reported)
    pochi_request = found.pochi_phrasing and bool(bad_phones)

    close = close_resemblance
    score = PAYMENT_OFFICIAL_ONLY
    if bad_tills:
        till_score = PAYMENT_UNREGISTERED_TILL if close else PAYMENT_UNREGISTERED_TILL_LOW_RESEMBLANCE
        score = max(score, till_score)
    if bad_phones:
        phone_score = PAYMENT_UNREGISTERED_PHONE if close else PAYMENT_UNREGISTERED_PHONE_LOW_RESEMBLANCE
        score = max(score, phone_score)
    if pochi_request or reported_hits:
        score = 100.0

    reasons: list[str] = []
    if reported_hits:
        reasons.append("COMMUNITY_REPORTED")
    if pochi_request:
        reasons.append("POCHI_REQUEST")
    elif bad_phones or bad_tills:
        reasons.append("PAYMENT_MISMATCH")

    return PaymentResult(
        score=score,
        unregistered_phones=bad_phones,
        unregistered_tills=bad_tills,
        reported_hits=reported_hits,
        pochi_request=pochi_request,
        evidence=_evidence(bad_phones, bad_tills, reported_hits, pochi_request),
        reasons=tuple(reasons),
    )


def _evidence(
    bad_phones: Sequence[str], bad_tills: Sequence[str], reported: Sequence[str], pochi: bool
) -> str:
    """Human-readable, masked summary of the payment findings."""
    parts: list[str] = []
    if bad_phones:
        kind = "personal number" if pochi else "number"
        shown = ", ".join(mask_phone(p) for p in bad_phones)
        parts.append(f"Asks for payment to {kind} {shown} (not registered to this business)")
    if bad_tills:
        parts.append(f"Till/Paybill {', '.join(bad_tills)} is not registered to this business")
    if reported:
        parts.append(f"{len(reported)} payment number(s) confirmed in community scam reports")
    return " · ".join(parts) or "Only this business's registered payment numbers appear"


def _unique(values: Iterable[str]) -> tuple[str, ...]:
    """De-duplicate while keeping first-seen order."""
    return tuple(dict.fromkeys(values))
