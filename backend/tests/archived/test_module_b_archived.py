"""Archived Module 3.B cases (TC-B09..TC-B13): USSD, SMS, Telegram, Daraja, Meta Rights Manager.

These features were archived on 2026-10-22 (docs/PRODUCT_V2.md section 9). The tests are kept green
so the code can return on the roadmap; the routers are mounted on a throwaway app here and are NOT
part of the live API.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.archived.alerts.sms import send_threat_sms
from app.archived.ingestion.daraja import DarajaClient
from app.archived.ingestion.meta_rights import (
    MetaRightsManagerClient,
    compute_evidence_hash,
)
from app.main import create_app
from tests.archived.conftest import mount_archived_routers
from tests.conftest import make_settings


def archived_client(tmp_path: Path, **overrides: object) -> TestClient:
    """A seeded app with the archived channel routers mounted (they are not in the live router)."""
    return TestClient(mount_archived_routers(create_app(make_settings(tmp_path, **overrides))))

# ==============================================================================
# TC-B09: Africa's Talking USSD Handler (POST /api/v1/channels/ussd)
# ==============================================================================
def test_tc_b09_ussd_menu_navigation(tmp_path: Path) -> None:
    """TC-B09: POST /api/v1/channels/ussd responds per Africa's Talking USSD protocol."""
    with archived_client(tmp_path) as client:
        _ussd_flow(client)


def _ussd_flow(client: TestClient) -> None:
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
    with archived_client(tmp_path, telegram_bot_token="test-token-secret") as test_client:
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


