"""Automated test execution suite for Module 3.B of E2E_TESTING_GUIDE.md.

Covers all 14 test cases assigned to Geoffrey:
- TC-B01: FastAPI Server Health & OpenAPI Docs
- TC-B02: Public Scan Endpoint (POST /api/v1/check)
- TC-B03: API Security & SSRF Protection
- TC-B04: API Rate Limiting Enforcement
- TC-B05: Merchant Data & Threat Endpoints
- TC-B06: Payment Verification Endpoint (GET /api/v1/verify/payment)
- TC-B07: Community Report Intake (POST /api/v1/reports)
- TC-B08: In-App Alert Dispatcher & De-duplication
- TC-B09: Africa's Talking USSD Handler (POST /api/v1/channels/ussd)
- TC-B10: Africa's Talking SMS Dispatcher (app/alerts/sms.py)
- TC-B11: Telegram Consumer Checker Bot (POST /api/v1/channels/telegram/webhook)
- TC-B12: Safaricom Daraja API Validation (app/ingestion/daraja.py)
- TC-B13: Meta Rights Manager Automated Takedown (app/ingestion/meta_rights.py)
- TC-B14: 3-Tier Page Scraper Fallback (app/ingestion/page_scraper.py)
"""

from __future__ import annotations

import base64
from pathlib import Path
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.alerts.sms import send_threat_sms
from app.core.repository import MemoryRepository
from app.core.security import RateLimiter
from app.ingestion.daraja import DarajaClient
from app.ingestion.fixtures import logos as L
from app.ingestion.meta_rights import (
    MetaRightsManagerClient,
    compute_evidence_hash,
)
from app.ingestion.mock_seeder import seed_id
from app.ingestion.page_scraper import parse_opengraph, profile_from_opengraph
from app.main import create_app
from tests.conftest import make_settings

LOGO_B64 = base64.b64encode(L.png_bytes(L.sneaker_logo())).decode()
NSV_ID = str(seed_id("merchant", "nsv"))


# ==============================================================================
# TC-B01: FastAPI Server Health & OpenAPI Docs
# ==============================================================================
def test_tc_b01_health_and_docs(client: TestClient) -> None:
    """TC-B01: GET /health returns status: ok, GET /docs loads Swagger UI."""
    health_resp = client.get("/health")
    assert health_resp.status_code == 200, health_resp.text
    health_data = health_resp.json()
    assert health_data["status"] == "ok"
    assert health_data["version"] == "0.2.0"
    assert "engine" in health_data
    assert "db" in health_data

    docs_resp = client.get("/docs")
    assert docs_resp.status_code == 200
    assert "swagger-ui" in docs_resp.text.lower() or "openapi" in docs_resp.text.lower()


# ==============================================================================
# TC-B02: Public Scan Endpoint (POST /api/v1/check)
# ==============================================================================
def test_tc_b02_public_scan_endpoint(client: TestClient) -> None:
    """TC-B02: POST /api/v1/check against a clone returns FEKI / impersonation >= 70 score."""
    resp = client.post(
        "/api/v1/check",
        json={"url": "https://instagram.com/nairobi_sneakervault_official_ke"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["verdict"] in ("impersonation", "suspicious")
    assert data["score"] >= 70.0
    assert "scan_id" in data
    assert "dimensions" in data
    assert len(data["dimensions"]) >= 4

    # Verify localized reasons (each reason item carries English 'text' and Swahili 'text_sw')
    assert "reasons" in data
    assert len(data["reasons"]) > 0
    first_reason = data["reasons"][0]
    assert "text" in first_reason
    assert "text_sw" in first_reason


# ==============================================================================
# TC-B03: API Security & SSRF Protection
# ==============================================================================
def test_tc_b03_ssrf_protection(client: TestClient) -> None:
    """TC-B03: Scanning cloud metadata IP (169.254.169.254) or localhost is blocked."""
    resp = client.post(
        "/api/v1/check",
        json={"url": "http://169.254.169.254/latest/meta-data"},
    )
    assert resp.status_code in (400, 422), resp.text
    err = resp.json()
    assert "error" in err or "detail" in err


# ==============================================================================
# TC-B04: API Rate Limiting Enforcement
# ==============================================================================
def test_tc_b04_rate_limiting_enforcement() -> None:
    """TC-B04: Rate limiter blocks requests exceeding configured limit."""
    rate_limiter = RateLimiter()
    client_ip = "192.168.1.100"

    assert rate_limiter.hit("check", "3/minute", client_ip) is True
    assert rate_limiter.hit("check", "3/minute", client_ip) is True
    assert rate_limiter.hit("check", "3/minute", client_ip) is True
    # 4th request in the same minute is blocked
    assert rate_limiter.hit("check", "3/minute", client_ip) is False


# ==============================================================================
# TC-B05: Merchant Data & Threat Endpoints
# ==============================================================================
def test_tc_b05_merchants_and_threats_endpoints(client: TestClient, auth: dict[str, str]) -> None:
    """TC-B05: GET /api/v1/merchants/{slug}, threats feed, and single threat detail work."""
    # 1. Get verified merchant public profile
    merchant_resp = client.get("/api/v1/merchants/nairobi-sneaker-vault")
    assert merchant_resp.status_code == 200, merchant_resp.text
    merchant = merchant_resp.json()
    assert merchant["slug"] == "nairobi-sneaker-vault"
    assert merchant["business_name"] == "Nairobi Sneaker Vault"
    assert merchant["payment"]["number"] == "543210"

    # 2. Get merchant threats feed (SOC dashboard)
    threats_resp = client.get(f"/api/v1/merchants/{NSV_ID}/threats", headers=auth)
    assert threats_resp.status_code == 200, threats_resp.text
    threats = threats_resp.json()
    assert isinstance(threats, list)
    assert len(threats) >= 1

    # 3. Get single threat detail (Evidence Board)
    threat_id = threats[0]["id"]
    threat_resp = client.get(f"/api/v1/threats/{threat_id}", headers=auth)
    assert threat_resp.status_code == 200, threat_resp.text
    threat_data = threat_resp.json()
    assert threat_data["threat_id"] == threat_id
    assert "score" in threat_data
    assert "status" in threat_data


# ==============================================================================
# TC-B06: Payment Verification Endpoint (GET /api/v1/verify/payment)
# ==============================================================================
def test_tc_b06_verify_payment_endpoint(client: TestClient) -> None:
    """TC-B06: GET /api/v1/verify/payment distinguishes official tills from reported scam numbers."""
    # 1. Seeded official till for Nairobi Sneaker Vault (543210)
    official_resp = client.get("/api/v1/verify/payment?value=543210")
    assert official_resp.status_code == 200, official_resp.text
    off_data = official_resp.json()
    assert off_data["status"] == "official"
    assert off_data["merchant"]["business_name"] == "Nairobi Sneaker Vault"

    # 2. Seeded reported scam number (0798999111)
    scam_resp = client.get("/api/v1/verify/payment?value=0798999111")
    assert scam_resp.status_code == 200, scam_resp.text
    scam_data = scam_resp.json()
    assert scam_data["status"] == "reported"
    assert scam_data["report_count"] >= 1


# ==============================================================================
# TC-B07: Community Report Intake (POST /api/v1/reports)
# ==============================================================================
def test_tc_b07_community_report_intake(client: TestClient) -> None:
    """TC-B07: POST /api/v1/reports creates pending community report and returns report UUID."""
    payload = {
        "target_handle": "scam_shoe_store",
        "reported_phone": "+254711999888",
        "reported_till": "499120",
        "description": "Seller took payment via M-Pesa but blocked my number afterwards.",
    }
    resp = client.post("/api/v1/reports", json=payload)
    assert resp.status_code in (200, 201), resp.text
    data = resp.json()
    assert "id" in data
    assert UUID(data["id"])
    assert data.get("status") == "pending"


# ==============================================================================
# TC-B08: In-App Alert Dispatcher & De-duplication
# ==============================================================================
def test_tc_b08_alert_dispatcher_deduplication(client: TestClient, auth: dict[str, str]) -> None:
    """TC-B08: Alert dispatcher creates alerts and suppresses duplicates within dedup window."""
    initial_alerts = client.get(f"/api/v1/merchants/{NSV_ID}/alerts", headers=auth).json()
    cursor = initial_alerts["server_time"]

    body = {
        "handle": "nairobisneakervault_module_b_test",
        "manual": {"bio": "Send money to 0798 555 444", "avatar_base64": LOGO_B64},
    }
    check_resp = client.post("/api/v1/check", json=body)
    assert check_resp.status_code == 200
    assert check_resp.json()["verdict"] == "impersonation"

    # Verify alert created
    new_alerts = client.get(
        f"/api/v1/merchants/{NSV_ID}/alerts", headers=auth, params={"since": cursor}
    ).json()
    assert len(new_alerts["alerts"]) >= 1
    assert any("nairobisneakervault_module_b_test" in a["title"] for a in new_alerts["alerts"])

    # Trigger same page again with identical score
    next_cursor = new_alerts["server_time"]
    client.post("/api/v1/check", json=body)
    dup_alerts = client.get(
        f"/api/v1/merchants/{NSV_ID}/alerts", headers=auth, params={"since": next_cursor}
    ).json()
    assert dup_alerts["alerts"] == []


# ==============================================================================
# TC-B09: Africa's Talking USSD Handler (POST /api/v1/channels/ussd)
# ==============================================================================
def test_tc_b09_ussd_menu_navigation(client: TestClient) -> None:
    """TC-B09: POST /api/v1/channels/ussd responds per Africa's Talking USSD protocol."""
    # 1. Level 0 Welcome Menu
    resp0 = client.post(
        "/api/v1/channels/ussd",
        data={"sessionId": "s1", "serviceCode": "*384*100#", "phoneNumber": "+254712345678", "text": ""},
    )
    assert resp0.status_code == 200
    assert resp0.text.startswith("CON ")
    assert "Karibu Halisi" in resp0.text

    # 2. Level 1 Option 1 (Prompt for Till/Phone)
    resp1 = client.post(
        "/api/v1/channels/ussd",
        data={"sessionId": "s1", "serviceCode": "*384*100#", "phoneNumber": "+254712345678", "text": "1"},
    )
    assert resp1.status_code == 200
    assert resp1.text.startswith("CON ")
    assert "Enter Till" in resp1.text

    # 3. Level 2 Official Till Check (543210)
    resp2 = client.post(
        "/api/v1/channels/ussd",
        data={
            "sessionId": "s1",
            "serviceCode": "*384*100#",
            "phoneNumber": "+254712345678",
            "text": "1*543210",
        },
    )
    assert resp2.status_code == 200
    assert resp2.text.startswith("END ")
    assert "VERIFIED OFFICIAL" in resp2.text


# ==============================================================================
# TC-B10: Africa's Talking SMS Dispatcher (app/alerts/sms.py)
# ==============================================================================
@pytest.mark.asyncio
async def test_tc_b10_sms_dispatcher(tmp_path: Path) -> None:
    """TC-B10: Africa's Talking SMS dispatcher formats and sends simulated alert cleanly."""
    settings = make_settings(tmp_path, demo_mode=True)
    result = await send_threat_sms(
        phone_number="+254712345678",
        merchant_name="Nairobi Sneaker Vault",
        threat_handle="@nairobi_sneaker_vault_ke",
        score=94.5,
        settings=settings,
    )
    assert result.success is True
    assert result.simulated is True
    assert "HALISI TAHADHARI" in result.message
    assert "Risk:" in result.message


# ==============================================================================
# TC-B11: Telegram Consumer Checker Bot (POST /api/v1/channels/telegram/webhook)
# ==============================================================================
def test_tc_b11_telegram_checker_webhook(tmp_path: Path) -> None:
    """TC-B11: POST /api/v1/channels/telegram/webhook parses handle and returns Forensic Verdict."""
    settings = make_settings(tmp_path, telegram_bot_token="test-token-secret")
    with TestClient(create_app(settings)) as test_client:
        webhook_payload = {
            "update_id": 999123,
            "message": {
                "message_id": 1,
                "date": 1700000000,
                "chat": {"id": 123456789, "type": "private"},
                "from": {"id": 123456789, "is_bot": False, "first_name": "TestUser"},
                "text": "/check @nairobi_sneakervault_official_ke",
            },
        }
        resp = test_client.post("/api/v1/channels/telegram/webhook", json=webhook_payload)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["ok"] is True
        reply = data.get("text") or ""
        assert ("HALISI" in reply) or ("FEKI" in reply) or ("Verdict" in reply)


# ==============================================================================
# TC-B12: Safaricom Daraja API Validation (app/ingestion/daraja.py)
# ==============================================================================
def test_tc_b12_daraja_api_validation(tmp_path: Path) -> None:
    """TC-B12: DarajaClient resolves till validation in sandbox/demo mode without network crash."""
    settings = make_settings(tmp_path, daraja_enabled=True, demo_mode=True)
    client = DarajaClient(settings)
    res = client.mock_validate("543210")
    assert res.is_valid is True
    assert res.account_name == "NAIROBI SNEAKER VAULT"
    assert res.account_type == "till"
    assert res.kyc_status == "verified"


# ==============================================================================
# TC-B13: Meta Rights Manager Automated Takedown (app/ingestion/meta_rights.py)
# ==============================================================================
@pytest.mark.asyncio
async def test_tc_b13_meta_rights_manager_automated_takedown(tmp_path: Path) -> None:
    """TC-B13: MetaRightsManagerClient submits takedown for 95+ score threat with SHA-256 evidence hash."""
    settings = make_settings(tmp_path, meta_rights_manager_enabled=True, demo_mode=True)
    client = MetaRightsManagerClient(settings=settings)
    evidence_hash = compute_evidence_hash(
        handle="nairobi_sneakervault_clone",
        url="https://instagram.com/nairobi_sneakervault_clone",
        score=96.0,
    )
    assert len(evidence_hash) == 64

    res = await client.submit_takedown(
        threat_handle="@nairobi_sneakervault_clone",
        threat_url="https://instagram.com/nairobi_sneakervault_clone",
        merchant_name="Nairobi Sneaker Vault",
        score=96.0,
        evidence_hash=evidence_hash,
    )
    assert res.success is True
    assert res.status == "simulated"
    assert res.score == 96.0
    assert res.evidence_hash == evidence_hash
    assert res.takedown_id is not None


# ==============================================================================
# TC-B14: 3-Tier Page Scraper Fallback (app/ingestion/page_scraper.py)
# ==============================================================================
@pytest.mark.asyncio
async def test_tc_b14_tiered_page_scraper_fallback(client: TestClient) -> None:
    """TC-B14: 3-tier page scraper fallback: seeded lookup, OpenGraph parsing, and manual fallback."""
    repo: MemoryRepository = client.app.state.repo

    # Tier 1: Seeded / known profile lookup from repository
    seeded = await repo.get_target_profile("instagram", "nairobi_sneakervault_official_ke")
    assert seeded is not None
    assert seeded.handle == "nairobi_sneakervault_official_ke"
    assert seeded.fetched_via == "seed"

    # Tier 2: OpenGraph parser extraction from HTML
    sample_html = (
        "<html><head>"
        '<meta property="og:title" content="Sneaker Store Official (@sample_store)">'
        '<meta property="og:description" '
        'content="500 Followers, 50 Following, 20 Posts - Best kicks in Kenya">'
        '<meta property="og:image" content="https://example.com/logo.png">'
        "</head></html>"
    )
    tags = parse_opengraph(sample_html)
    profile = profile_from_opengraph(tags, "instagram", "sample_store", "https://instagram.com/sample_store")
    assert profile.handle == "sample_store"
    assert profile.display_name == "Sneaker Store Official"
    assert profile.follower_count == 500
    assert profile.post_count == 20
    assert profile.fetched_via == "opengraph"

    # Tier 3: Manual fallback check via API (user provides bio/avatar directly)
    manual_resp = client.post(
        "/api/v1/check",
        json={
            "handle": "unreachable_profile_123",
            "manual": {
                "display_name": "Unreachable Profile",
                "bio": "DM for inquiries. Call 0712345678",
            },
        },
    )
    assert manual_resp.status_code == 200, manual_resp.text
    manual_data = manual_resp.json()
    assert manual_data["target"]["fetched_via"] == "manual"
