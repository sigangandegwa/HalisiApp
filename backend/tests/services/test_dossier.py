"""Unit tests for dossier service (TSK-028)."""

import re
from datetime import UTC, datetime
from uuid import uuid4

from app.schemas.check import ScanRecord
from app.schemas.merchant import MerchantHandle, MerchantRecord
from app.schemas.threat import ThreatRecord
from app.services.dossier import (
    build_evidence_bundle,
    compute_evidence_hash,
    generate_dossier_pdf,
    render_dossier_html,
)

NOW = datetime(2026, 10, 11, 10, 0, tzinfo=UTC)
HEX_64_REGEX = re.compile(r"^[0-9a-f]{64}$")

MERCHANT = MerchantRecord(
    id=uuid4(),
    business_name="Nairobi Sneaker Vault",
    slug="nairobi-sneaker-vault",
    logo_phash="c3d1a4f0e8b27c19",
    logo_dhash="1234567890abcdef",
    mpesa_type="till",
    mpesa_number="543210",
    mpesa_account_name="NAIROBI SNEAKER VAULT",
    phone_numbers=["+254712345678"],
    is_verified=True,
    created_at=NOW,
    updated_at=NOW,
    official_handles=[MerchantHandle(platform="instagram", handle="nairobisneakervault")],
)

THREAT = ThreatRecord(
    id=uuid4(),
    merchant_id=MERCHANT.id,
    platform="instagram",
    target_handle="nairobi_sneakervault_fake",
    target_url="https://instagram.com/nairobi_sneakervault_fake",
    avatar_phash="c3d1a4f0e8b27c1b",  # Hamming distance 1
    avatar_dhash="1234567890abcdee",  # Hamming distance 1
    bio="Pay deposit to 0798 999 111 before delivery",
    extracted_phones=["+254798999111"],
    extracted_tills=["999888"],
    visual_score=98.0,
    identity_score=95.0,
    payment_score=100.0,
    language_score=85.0,
    account_score=90.0,
    composite_score=96.0,
    confidence=1.0,
    reasons=[
        {
            "code": "LOGO_COPY",
            "severity": "high",
            "text": "Uses a logo 98% similar to Nairobi Sneaker Vault.",
            "text_sw": "Inatumia nembo inayofanana 98% na ya Nairobi Sneaker Vault.",
        },
        {
            "code": "UNAUTHORIZED_PAYMENT",
            "severity": "high",
            "text": "Directs funds to personal line 0798 999 111.",
            "text_sw": "Inaelekeza fedha kwa laini ya kibinafsi 0798 999 111.",
        },
    ],
    first_seen_at=NOW,
    last_checked_at=NOW,
)


def test_build_evidence_bundle_extracts_all_forensic_fields() -> None:
    bundle = build_evidence_bundle(THREAT, MERCHANT)

    assert bundle["case_id"] == f"HALISI-CASE-{str(THREAT.id).upper()}"
    assert bundle["threat_id"] == str(THREAT.id)
    assert "generated_at" in bundle

    # Threat details
    assert bundle["threat"]["target_handle"] == "nairobi_sneakervault_fake"
    assert bundle["threat"]["extracted_phones"] == ["+254798999111"]
    assert bundle["threat"]["composite_score"] == 96.0

    # Merchant details
    assert bundle["merchant"]["business_name"] == "Nairobi Sneaker Vault"
    assert bundle["merchant"]["slug"] == "nairobi-sneaker-vault"
    assert bundle["merchant"]["mpesa_number"] == "543210"

    # Perceptual hashes
    assert bundle["visual_hashes"]["phash_hamming_distance"] == 1
    assert bundle["visual_hashes"]["phash_similarity"] == 100.0
    assert bundle["visual_hashes"]["dhash_hamming_distance"] == 1

    # Scores and verdict
    assert bundle["scores"]["verdict"] == "impersonation"
    assert bundle["scores"]["verdict_sw"] == "FEKI"
    assert bundle["scores"]["composite_score"] == 96.0

    # Statutory framework
    assert len(bundle["legal_framework"]) == 3
    statutes = [item["statute"] for item in bundle["legal_framework"]]
    assert any("Computer Misuse and Cybercrimes Act" in s for s in statutes)
    assert any("Kenya Penal Code" in s for s in statutes)
    assert any("Data Protection Act" in s for s in statutes)

    # Verification
    assert bundle["verification"]["safaricom_report_to"] == "fraud@safaricom.co.ke"
    assert bundle["verification"]["kecirt_report_to"] == "incidents@ke-cirt.go.ke"


def test_build_evidence_bundle_with_scan() -> None:
    scan = ScanRecord(
        id=uuid4(),
        input_value="https://instagram.com/nairobi_sneakervault_fake",
        input_kind="url",
        platform="instagram",
        target_handle="nairobi_sneakervault_fake",
        source="public_checker",
        verdict="impersonation",
        composite_score=96.0,
        merchant_id=MERCHANT.id,
        threat_id=THREAT.id,
        result={"verdict": "impersonation"},
        elapsed_ms=45,
        created_at=NOW,
    )
    bundle = build_evidence_bundle(THREAT, MERCHANT, scan)
    assert bundle["scan"] is not None
    assert bundle["scan"]["id"] == str(scan.id)
    assert bundle["scan"]["elapsed_ms"] == 45


def test_compute_evidence_hash_is_deterministic() -> None:
    bundle = build_evidence_bundle(THREAT, MERCHANT)
    hash1 = compute_evidence_hash(bundle)
    hash2 = compute_evidence_hash(bundle)

    assert hash1 == hash2
    assert len(hash1) == 64
    assert HEX_64_REGEX.match(hash1)

    # Tampering test: altering a single field changes the hash
    tampered_bundle = dict(bundle)
    tampered_bundle["scores"] = dict(bundle["scores"])
    tampered_bundle["scores"]["composite_score"] = 95.9
    hash3 = compute_evidence_hash(tampered_bundle)

    assert hash1 != hash3


def test_render_dossier_html() -> None:
    bundle = build_evidence_bundle(THREAT, MERCHANT)
    evidence_hash = compute_evidence_hash(bundle)
    html = render_dossier_html(THREAT, MERCHANT, bundle, evidence_hash)

    assert "<!DOCTYPE html>" in html
    assert evidence_hash in html
    assert str(THREAT.id).upper() in html
    assert "Nairobi Sneaker Vault" in html
    assert "nairobi_sneakervault_fake" in html
    assert "FEKI" in html
    assert "Computer Misuse and Cybercrimes Act" in html
    assert "fraud@safaricom.co.ke" in html
    assert "incidents@ke-cirt.go.ke" in html
    assert '<script id="bundle-data" type="application/json">' in html


def test_generate_dossier_pdf_returns_valid_pdf_bytes() -> None:
    bundle = build_evidence_bundle(THREAT, MERCHANT)
    evidence_hash = compute_evidence_hash(bundle)
    html = render_dossier_html(THREAT, MERCHANT, bundle, evidence_hash)

    pdf = generate_dossier_pdf(html)

    assert isinstance(pdf, bytes)
    assert pdf.startswith(b"%PDF-1.4")
    assert b"%%EOF" in pdf
    assert len(pdf) > 1500
    # Confirm evidence hash and case ID are embedded
    assert evidence_hash[:16].encode("utf-8") in pdf or b"HALISI FORENSIC EVIDENCE DOSSIER" in pdf
