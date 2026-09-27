"""Composite impersonation scorer (TSK-008, spec: docs/BACKEND.md section 6.8).

Two questions, answered separately:
  1. Resemblance: who is this page imitating?   visual (logo) + identity (handle/name)
  2. Malice: how dangerous is it?                payment + language + account

Pure functions: plain dataclasses in, a ScoreResult out. No network, no DB, no settings import.
The API layer converts repository records into MerchantProfile / TargetProfile and passes
thresholds through ScoringContext.
"""

from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from datetime import date
from typing import Literal

from app.engine.constants import (
    ACCOUNT_AGE_OLD,
    ACCOUNT_AGE_SCORES,
    LANGUAGE_REASON_MIN,
    LOGO_CONTRADICTS,
    LOW_FOLLOWER_COUNT,
    LOW_FOLLOWER_SCORE,
    LOW_POST_COUNT,
    LOW_POST_SCORE,
    MIN_CONFIDENCE_FOR_IMPERSONATION,
    NO_MATCH_CAP,
    PAYMENT_HIJACK_FLOOR,
    PAYMENT_RESEMBLANCE_MIN,
    REASON_HIGH_SEVERITY,
    REASON_MIN_SCORE,
    REPORTED_FLOOR,
    RESEMBLANCE_GATE,
    STRONG_IDENTITY,
    STRONG_VISUAL,
    SUSPICIOUS_THRESHOLD,
    THREAT_THRESHOLD,
    WEIGHTS,
)
from app.engine.hasher import ImageFeatures, VisualResult, visual_score
from app.engine.matcher import identity_score, language_score
from app.engine.payment import PaymentEvidence, PaymentResult, canonical_phone, payment_score

Verdict = Literal["official", "impersonation", "suspicious", "no_match"]
DimensionKey = Literal["visual", "identity", "payment", "language", "account"]

LABELS: dict[str, str] = {
    "visual": "Logo match",
    "identity": "Name & handle",
    "payment": "Payment details",
    "language": "Scam language",
    "account": "Account signals",
}


# --- inputs -------------------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class OfficialHandle:
    """One official account of a merchant. ``handle`` is stored lowercase without '@'."""

    platform: str
    handle: str


@dataclass(frozen=True, slots=True)
class MerchantProfile:
    """Everything the scorer needs to know about a verified merchant."""

    id: str
    business_name: str
    slug: str
    official_handles: Sequence[OfficialHandle] = ()
    aliases: Sequence[str] = ()
    logo: ImageFeatures | None = None
    phone_numbers: Sequence[str] = ()
    mpesa_type: Literal["till", "paybill", "pochi", "none"] = "none"
    mpesa_number: str | None = None
    mpesa_account_name: str | None = None
    established_on: date | None = None


@dataclass(frozen=True, slots=True)
class TargetProfile:
    """The page being checked. Unknown fields stay None: they lower confidence, never the score."""

    platform: str | None
    handle: str | None
    display_name: str | None = None
    bio: str | None = None
    avatar: ImageFeatures | None = None
    payment: PaymentEvidence = field(default_factory=PaymentEvidence)
    follower_count: int | None = None
    post_count: int | None = None
    account_created_on: date | None = None


@dataclass(frozen=True, slots=True)
class ScoringContext:
    """Per-request context. ``confirmed_reported`` holds phones/tills from confirmed community reports."""

    today: date
    confirmed_reported: frozenset[str] = frozenset()
    threat_threshold: float = THREAT_THRESHOLD
    suspicious_threshold: float = SUSPICIOUS_THRESHOLD


# --- outputs ------------------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class Dimension:
    """One of the five sub-scores. ``score`` is None when the signal was unavailable."""

    key: DimensionKey
    score: float | None
    evidence: str | None

    @property
    def weight(self) -> float:
        return WEIGHTS[self.key]

    @property
    def available(self) -> bool:
        return self.score is not None


@dataclass(frozen=True, slots=True)
class Reason:
    """A plain-language explanation shown to consumers (English + Swahili)."""

    code: str
    severity: Literal["high", "medium"]
    text: str
    text_sw: str


@dataclass(frozen=True, slots=True)
class ScoreResult:
    """Scorer output. Serialise with :meth:`dimensions_payload` / :meth:`reasons_payload`."""

    verdict: Verdict
    score: float
    confidence: float
    merchant: MerchantProfile | None
    dimensions: tuple[Dimension, ...] = ()
    reasons: tuple[Reason, ...] = ()
    visual: VisualResult | None = None
    payment: PaymentResult | None = None
    rules: tuple[str, ...] = ()          # which gates/overrides fired: G1, O1, O2, O3, O4

    def dimensions_payload(self) -> list[dict[str, object]]:
        """Dimensions in the API contract shape (BACKEND.md section 5.2)."""
        return [
            {
                "key": d.key,
                "label": LABELS[d.key],
                "score": d.score if d.score is not None else 0.0,
                "weight": d.weight,
                "available": d.available,
                "evidence": d.evidence or "No data",
            }
            for d in self.dimensions
        ]

    def reasons_payload(self) -> list[dict[str, str]]:
        """Reasons in the API contract shape."""
        return [
            {"code": r.code, "severity": r.severity, "text": r.text, "text_sw": r.text_sw}
            for r in self.reasons
        ]


# --- public API ---------------------------------------------------------------------------------

def normalize_official_handle(handle: str) -> str:
    """Normalise a handle for the *exact* official check: lowercase, no '@', no trailing slash.

    Deliberately keeps '.', '_' and '-'. On Instagram ``nairobi.sneaker.vault`` is a different
    account from ``nairobisneakervault``, so the matcher's separator-stripping must never be
    used to decide that a page is official.
    """
    return handle.strip().lower().lstrip("@").rstrip("/")


def find_official(target: TargetProfile, merchants: Sequence[MerchantProfile]) -> MerchantProfile | None:
    """O1: return the merchant whose official handle on the same platform equals the target's, if any."""
    if not target.handle or not target.platform:
        return None
    handle = normalize_official_handle(target.handle)
    platform = target.platform.lower()
    for merchant in merchants:
        for official in merchant.official_handles:
            if official.platform.lower() == platform and normalize_official_handle(official.handle) == handle:
                return merchant
    return None


def score_against_all(
    target: TargetProfile, merchants: Sequence[MerchantProfile], ctx: ScoringContext
) -> ScoreResult:
    """Score a page against every merchant and return the verdict for the closest one.

    ``no_match`` results carry ``merchant=None`` and keep only merchant-independent reasons
    (scam language, community-reported numbers). A page can be a scam without imitating anyone.
    """
    official = find_official(target, merchants)
    if official is not None:
        return ScoreResult(verdict="official", score=0.0, confidence=1.0, merchant=official, rules=("O1",))

    if not merchants:
        return _no_match(score_target(target, _NOBODY, ctx))

    best = max(
        (score_target(target, merchant, ctx) for merchant in merchants),
        key=lambda r: (r.score, r.confidence),
    )
    return _no_match(best) if best.verdict == "no_match" else best


def score_target(target: TargetProfile, merchant: MerchantProfile, ctx: ScoringContext) -> ScoreResult:
    """Score one page against one merchant (no official short-circuit; see :func:`score_against_all`)."""
    visual = visual_score(target.avatar, merchant.logo) if target.avatar and merchant.logo else None
    visual_value = visual.score if visual else None

    identity_value: float | None = None
    identity_evidence: str | None = None
    if merchant is not _NOBODY and (target.handle or target.display_name):
        identity = identity_score(target.handle, target.display_name, merchant)
        identity_value, identity_evidence = identity.score, identity.evidence

    resemblance = max(visual_value or 0.0, identity_value or 0.0)

    payment = payment_score(
        target.payment,
        official_phones=merchant.phone_numbers,
        official_mpesa_number=merchant.mpesa_number,
        close_resemblance=_closely_resembles(visual_value, identity_value),
        confirmed_reported=ctx.confirmed_reported,
    )

    language = language_score(target.bio)
    language_value = language.score
    if language_value is None and target.bio and target.bio.strip():
        language_value = 0.0            # text present, no scam phrases: evidence of absence, not "unknown"

    account_value, account_evidence, account_code = _account_signal(target, resemblance, ctx.today)

    dimensions = (
        Dimension("visual", visual_value, visual.evidence if visual else None),
        Dimension("identity", identity_value, identity_evidence),
        Dimension("payment", payment.score, payment.evidence),
        Dimension("language", language_value, language.evidence),
        Dimension("account", account_value, account_evidence),
    )

    available = [d for d in dimensions if d.available]
    weight_sum = sum(d.weight for d in available)
    composite = sum(d.weight * d.score for d in available) / weight_sum if weight_sum else 0.0
    confidence = round(weight_sum, 2)

    rules: list[str] = []
    if resemblance < RESEMBLANCE_GATE:
        composite = min(composite, NO_MATCH_CAP)
        rules.append("G1")
    strong = (visual_value or 0.0) >= STRONG_VISUAL or (identity_value or 0.0) >= STRONG_IDENTITY
    if strong and payment.score == 100.0 and (payment.unregistered_phones or payment.reported_hits):
        composite = max(composite, PAYMENT_HIJACK_FLOOR)
        rules.append("O2")
    if payment.reported_hits and resemblance >= RESEMBLANCE_GATE:
        composite = max(composite, REPORTED_FLOOR)
        rules.append("O3")

    composite = round(composite, 2)
    verdict = _tier(composite, ctx)
    if verdict == "impersonation" and confidence < MIN_CONFIDENCE_FOR_IMPERSONATION:
        verdict = "suspicious"
        rules.append("O4")

    return ScoreResult(
        verdict=verdict,
        score=composite,
        confidence=confidence,
        merchant=None if merchant is _NOBODY else merchant,
        dimensions=dimensions,
        reasons=_reasons(dimensions, payment, account_code, merchant, target),
        visual=visual,
        payment=payment,
        rules=tuple(rules),
    )


def safe_action(merchant: MerchantProfile, platform: str | None = None) -> tuple[str, str]:
    """The "what to do instead" line for a merchant: (English, Swahili)."""
    handle = _display_handle(merchant, platform)
    account = f" ({merchant.mpesa_account_name})" if merchant.mpesa_account_name else ""
    number = merchant.mpesa_number or ""
    if merchant.mpesa_type == "till" and number:
        en_pay, sw_pay = f"Buy Goods Till {number}{account}", f"Till {number}{account}"
    elif merchant.mpesa_type == "paybill" and number:
        en_pay, sw_pay = f"Paybill {number}{account}", f"Paybill {number}{account}"
    elif merchant.mpesa_type == "pochi" and number:
        shown = _format_phone(number)
        en_pay, sw_pay = f"Pochi la Biashara {shown}{account}", f"Pochi la Biashara {shown}{account}"
    else:
        return (
            f"Contact {merchant.business_name} only through {handle}.",
            f"Wasiliana na {merchant.business_name} kupitia {handle} pekee.",
        )
    return (
        f"Pay only via {en_pay} through {handle}.",
        f"Lipa tu kwa {sw_pay}. Ukurasa rasmi ni {handle}.",
    )


# --- internals ----------------------------------------------------------------------------------

_NOBODY = MerchantProfile(id="", business_name="", slug="")   # sentinel: "no merchants registered"


def _closely_resembles(visual: float | None, identity: float | None) -> bool:
    """Whether unregistered payment numbers on this page should count as a hijack of this merchant.

    A clearly different logo (visual <= LOGO_CONTRADICTS) is counter-evidence, so name similarity
    alone must then be near-identical. Without this, an unrelated shop whose handle merely starts
    with the same city ("nairobi_bakery" vs "nairobisneakervault") and lists its own personal order
    number reads as a payment hijack.
    """
    if (visual or 0.0) >= PAYMENT_RESEMBLANCE_MIN:
        return True
    logo_contradicts = visual is not None and visual <= LOGO_CONTRADICTS
    needed = STRONG_IDENTITY if logo_contradicts else PAYMENT_RESEMBLANCE_MIN
    return (identity or 0.0) >= needed


def _tier(score: float, ctx: ScoringContext) -> Verdict:
    """Map a composite score to a verdict band."""
    if score >= ctx.threat_threshold:
        return "impersonation"
    if score >= ctx.suspicious_threshold:
        return "suspicious"
    return "no_match"


def _no_match(result: ScoreResult) -> ScoreResult:
    """Strip merchant attribution from a no-match result, keeping merchant-independent reasons."""
    keep = {"SCAM_LANGUAGE", "COMMUNITY_REPORTED"}
    return replace(
        result,
        verdict="no_match",
        merchant=None,
        reasons=tuple(r for r in result.reasons if r.code in keep),
    )


def _account_signal(
    target: TargetProfile, resemblance: float, today: date
) -> tuple[float | None, str | None, str | None]:
    """Account-age and activity signal: (score, evidence, reason code).

    None when no account data is known. When data is known but nothing is unusual, the score is
    ACCOUNT_AGE_OLD, so an established-looking account counts as evidence rather than as missing.
    """
    known = False
    scored: list[tuple[float, str]] = []
    evidence: list[str] = []

    if target.account_created_on is not None:
        known = True
        age = max(0, (today - target.account_created_on).days)
        score = next((s for max_days, s in ACCOUNT_AGE_SCORES if age < max_days), ACCOUNT_AGE_OLD)
        scored.append((score, "NEW_ACCOUNT"))
        evidence.append(f"Account is {age} days old")
    if target.post_count is not None:
        known = True
        evidence.append(f"{target.post_count} posts")
        if target.post_count < LOW_POST_COUNT:
            scored.append((LOW_POST_SCORE, "LOW_ACTIVITY"))
    if target.follower_count is not None:
        known = True
        evidence.append(f"{target.follower_count} followers")
        if target.follower_count < LOW_FOLLOWER_COUNT and resemblance >= STRONG_VISUAL:
            scored.append((LOW_FOLLOWER_SCORE, "LOW_ACTIVITY"))

    if not known:
        return None, None, None
    best_score, best_code = max(scored, default=(ACCOUNT_AGE_OLD, None))
    return best_score, " · ".join(evidence), best_code


def _reasons(
    dimensions: Sequence[Dimension],
    payment: PaymentResult,
    account_code: str | None,
    merchant: MerchantProfile,
    target: TargetProfile,
) -> tuple[Reason, ...]:
    """Plain-language reasons for every strong signal, most severe first."""
    by_key = {d.key: d for d in dimensions}
    name = merchant.business_name or "a verified business"
    handle = _display_handle(merchant, target.platform)
    out: list[tuple[float, Reason]] = []

    def add(code: str, value: float, text: str, text_sw: str) -> None:
        severity = "high" if value >= REASON_HIGH_SEVERITY else "medium"
        out.append((value, Reason(code, severity, text, text_sw)))

    visual = by_key["visual"].score
    if visual is not None and visual >= REASON_MIN_SCORE:
        add("LOGO_COPY", visual,
            f"Uses a logo {visual:.0f}% similar to {name}'s.",
            f"Inatumia nembo inayofanana {visual:.0f}% na ya {name}.")

    identity = by_key["identity"].score
    if identity is not None and identity >= REASON_MIN_SCORE:
        add("HANDLE_LOOKALIKE", identity,
            f"Its name imitates {name}'s official account {handle}.",
            f"Jina lake linaiga akaunti rasmi ya {name}, {handle}.")

    if payment.score is not None:
        if "COMMUNITY_REPORTED" in payment.reasons:
            add("COMMUNITY_REPORTED", 100.0,
                "The payment number on this page has been reported by other customers.",
                "Namba ya malipo kwenye ukurasa huu imeripotiwa na wateja wengine.")
        if payment.score >= REASON_MIN_SCORE and "POCHI_REQUEST" in payment.reasons:
            add("POCHI_REQUEST", payment.score,
                f"Asks for payment to a personal number, not {name}'s official payment channel.",
                f"Inaomba malipo kwa namba ya binafsi, si njia rasmi ya malipo ya {name}.")
        elif payment.score >= REASON_MIN_SCORE and "PAYMENT_MISMATCH" in payment.reasons:
            add("PAYMENT_MISMATCH", payment.score,
                f"Asks you to pay a number that is not registered to {name}.",
                f"Inakuomba ulipe namba ambayo haijasajiliwa na {name}.")

    language = by_key["language"]
    if language.score is not None and language.score >= LANGUAGE_REASON_MIN:
        add("SCAM_LANGUAGE", language.score,
            f"Uses pressure phrases common in scams: {language.evidence}.",
            f"Inatumia maneno ya shinikizo yanayotumiwa na matapeli: {language.evidence}.")

    account = by_key["account"].score
    if account is not None and account >= REASON_MIN_SCORE and account_code:
        if account_code == "NEW_ACCOUNT" and target.account_created_on is not None:
            add("NEW_ACCOUNT", account,
                f"The account was created recently ({by_key['account'].evidence}).",
                "Akaunti hii imefunguliwa hivi karibuni.")
        else:
            add("LOW_ACTIVITY", account,
                f"Very little activity for an established business ({by_key['account'].evidence}).",
                "Shughuli chache sana kwa biashara inayojulikana.")

    out.sort(key=lambda item: (item[1].severity != "high", -item[0]))
    return tuple(reason for _, reason in out)


def _display_handle(merchant: MerchantProfile, platform: str | None) -> str:
    """The merchant's official handle on ``platform`` (or its first handle) as '@handle'."""
    handles = list(merchant.official_handles)
    if not handles:
        return merchant.business_name
    same = [h for h in handles if platform and h.platform.lower() == platform.lower()]
    return "@" + normalize_official_handle((same or handles)[0].handle)


def _format_phone(value: str) -> str:
    """Official merchant numbers are public by design: show them in full as 0712 345 678."""
    phone = canonical_phone(value)
    if phone is None:
        return value
    local = "0" + phone[4:]
    return f"{local[:4]} {local[4:7]} {local[7:]}"
