"""Convert repository records to engine inputs and to API contract shapes (docs/BACKEND.md section 5)."""

from app.engine.hasher import ImageFeatures
from app.engine.payment import mask_phone
from app.engine.scorer import MerchantProfile, OfficialHandle
from app.schemas.check import CheckResult, ReasonOut
from app.schemas.common import Verdict
from app.schemas.merchant import MatchedMerchant, MerchantPayment, MerchantRecord, PublicMerchant
from app.schemas.remediation import RemediationRecord
from app.schemas.threat import PlaybookLogEntry, ThreatDetail, ThreatRecord, ThreatSummary


def merchant_profile(record: MerchantRecord) -> MerchantProfile:
    """Repository merchant -> scorer input."""
    logo = None
    if record.logo_phash and record.logo_dhash:
        logo = ImageFeatures(
            phash=record.logo_phash.strip(), dhash=record.logo_dhash.strip(), embedding=record.logo_embedding
        )
    return MerchantProfile(
        id=str(record.id),
        business_name=record.business_name,
        slug=record.slug,
        official_handles=tuple(OfficialHandle(h.platform, h.handle) for h in record.official_handles),
        aliases=tuple(record.aliases),
        logo=logo,
        phone_numbers=tuple(record.phone_numbers),
        mpesa_type=record.mpesa_type,
        mpesa_number=record.mpesa_number,
        mpesa_account_name=record.mpesa_account_name,
        established_on=record.established_on,
    )


def merchant_payment(record: MerchantRecord) -> MerchantPayment:
    """The merchant's official payment channel (public by design)."""
    return MerchantPayment(
        type=record.mpesa_type, number=record.mpesa_number, account_name=record.mpesa_account_name
    )


def matched_merchant(record: MerchantRecord) -> MatchedMerchant:
    """``CheckResult.matched_merchant``."""
    return MatchedMerchant(
        id=record.id,
        business_name=record.business_name,
        slug=record.slug,
        logo_url=record.logo_url,
        official_handles=record.official_handles,
        payment=merchant_payment(record),
    )


def public_merchant(record: MerchantRecord) -> PublicMerchant:
    """``GET /merchants/{slug}``."""
    return PublicMerchant(
        id=record.id,
        business_name=record.business_name,
        slug=record.slug,
        logo_url=record.logo_url,
        category=record.category,
        location=record.location,
        established_on=record.established_on,
        is_verified=record.is_verified,
        official_handles=record.official_handles,
        payment=merchant_payment(record),
        verified_since=record.created_at if record.is_verified else None,
    )


def threat_verdict(threat: ThreatRecord, threshold: float, suspicious: float) -> Verdict:
    """Verdict band for a stored threat (O4: low confidence caps at suspicious)."""
    if threat.composite_score >= threshold:
        return "impersonation" if threat.confidence >= 0.5 else "suspicious"
    return "suspicious" if threat.composite_score >= suspicious else "no_match"


def threat_summary(threat: ThreatRecord, threshold: float, suspicious: float) -> ThreatSummary:
    """Dashboard feed row."""
    top = ReasonOut.model_validate(threat.reasons[0]) if threat.reasons else None
    return ThreatSummary(
        id=threat.id,
        platform=threat.platform,
        target_handle=threat.target_handle,
        target_url=threat.target_url,
        avatar_url=threat.avatar_url,
        composite_score=threat.composite_score,
        verdict=threat_verdict(threat, threshold, suspicious),
        status=threat.status,
        first_seen_at=threat.first_seen_at,
        top_reason=top,
    )


def threat_detail(
    threat: ThreatRecord,
    latest: CheckResult | None,
    merchant: MerchantRecord | None,
    playbooks: list[RemediationRecord],
    threshold: float,
    suspicious: float,
) -> ThreatDetail:
    """``GET /threats/{id}``: the latest check result for this page plus workflow state (unmasked numbers).

    Without a stored scan, the dimensions are rebuilt from the threat's sub-scores.
    """
    if latest is not None:
        base = latest.model_dump()
    else:
        from app.engine.scorer import LABELS, WEIGHTS

        dims = []
        for key in ("visual", "identity", "payment", "language", "account"):
            value = getattr(threat, f"{key}_score")
            dims.append(
                {
                    "key": key,
                    "label": LABELS[key],
                    "score": value or 0.0,
                    "weight": WEIGHTS[key],
                    "available": value is not None,
                    "evidence": "No data" if value is None else "Stored score",
                }
            )
        base = {
            "scan_id": None,
            "verdict": threat_verdict(threat, threshold, suspicious),
            "score": threat.composite_score,
            "confidence": threat.confidence,
            "target": {
                "platform": threat.platform,
                "handle": threat.target_handle,
                "display_name": threat.display_name,
                "url": threat.target_url,
                "avatar_url": threat.avatar_url,
                "follower_count": threat.follower_count,
                "post_count": threat.post_count,
                "account_created_on": threat.account_created_on,
                "fetched_via": "seed",
            },
            "matched_merchant": matched_merchant(merchant).model_dump() if merchant else None,
            "dimensions": dims,
            "reasons": threat.reasons,
            "hashes": None,
            "safe_action": None,
            "elapsed_ms": None,
        }
    base.update(
        threat_id=threat.id,
        status=threat.status,
        status_history=threat.status_history,
        extracted_phones=threat.extracted_phones,
        extracted_tills=threat.extracted_tills,
        playbooks_generated=[
            PlaybookLogEntry(
                playbook_type=p.playbook_type,
                language=p.language,
                generator=p.generator,
                prompt_id=p.prompt_id,
                model=p.model,
                created_at=p.created_at,
            )
            for p in playbooks
        ],
        first_seen_at=threat.first_seen_at,
        last_checked_at=threat.last_checked_at,
        resolved_at=threat.resolved_at,
    )
    return ThreatDetail.model_validate(base)


def display_number(number: str, *, official: bool) -> str:
    """Official merchant numbers are public; third-party numbers are masked (``0798 *** 111``)."""
    if not number.startswith("+"):
        return number
    if official:
        local = "0" + number[4:]
        return f"{local[:4]} {local[4:7]} {local[7:]}"
    return mask_phone(number)
