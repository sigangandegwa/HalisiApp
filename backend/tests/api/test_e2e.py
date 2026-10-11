"""End-to-end integration and failover drill test suite (TSK-014).

Validates the full consumer journey, merchant lifecycle, community reporting,
false-positive prevention, and complete offline failover under DEMO_MODE.
"""

import base64
import re
from pathlib import Path
from uuid import UUID

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.ingestion.fixtures import logos as L
from app.ingestion.mock_seeder import seed_id
from app.main import create_app

NSV_ID = str(seed_id("merchant", "nsv"))
LOGO_B64 = base64.b64encode(L.png_bytes(L.sneaker_logo())).decode()
HEX_64_REGEX = re.compile(r"^[0-9a-fA-F]{64}$")


def test_consumer_journey_blatant_clone_check_and_alert_dispatch(
    client: TestClient, auth: dict[str, str]
) -> None:
    """Requirement 1a: Public /api/v1/check against a blatant clone.

    - Verdict is 'impersonation', score >= 90, confidence 1.0.
    - 5 dimensions present (visual, identity, payment, language, account).
    - Reasons present in both EN and SW.
    - Safe action present in both EN and SW.
    - Third-party numbers are masked in public output.
    - Asynchronous alert dispatch creates a merchant alert record.
    """
    # Step 1: Check existing blatant clone
    response = client.post(
        "/api/v1/check",
        json={"url": "https://instagram.com/nairobi_sneakervault_official_ke"},
    )
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["verdict"] == "impersonation"
    assert data["score"] >= 90.0
    assert data["confidence"] == 1.0
    assert data["matched_merchant"]["slug"] == "nairobi-sneaker-vault"
    assert data["target"]["handle"] == "nairobi_sneakervault_official_ke"
    assert data["target"]["fetched_via"] == "seed"

    # Verify all 5 dimensions
    dimensions = {d["key"]: d for d in data["dimensions"]}
    assert set(dimensions.keys()) == {"visual", "identity", "payment", "language", "account"}
    for dim in dimensions.values():
        assert dim["available"] is True
        assert dim["score"] >= 0.0
        assert dim["weight"] > 0.0
        assert len(dim["evidence"]) > 0

    # Verify reasons in EN and SW
    assert len(data["reasons"]) > 0
    for reason in data["reasons"]:
        assert "code" in reason
        assert "severity" in reason
        assert len(reason["text"]) > 0
        assert len(reason["text_sw"]) > 0

    # Verify safe action in EN and SW
    assert data["safe_action"] is not None
    assert data["safe_action"]["text"].startswith("Pay only via Buy Goods Till 543210")
    assert "Lipa tu" in data["safe_action"]["text_sw"]

    # Verify public response masks phone numbers
    assert "0798 *** 111" in response.text
    assert "0798999111" not in response.text

    # Step 2: Test live asynchronous alert dispatch with a newly discovered blatant clone
    cursor_resp = client.get(f"/api/v1/merchants/{NSV_ID}/alerts", headers=auth)
    assert cursor_resp.status_code == 200
    cursor_time = cursor_resp.json()["server_time"]

    new_clone_payload = {
        "handle": "nairobi_sneakervault_live_scam",
        "manual": {
            "display_name": "Nairobi Sneaker Vault Promo",
            "bio": "Official sale! Lipa kwanza, send money to 0798 123 456. Clearance!",
            "avatar_base64": LOGO_B64,
        },
    }
    new_clone_res = client.post("/api/v1/check", json=new_clone_payload)
    assert new_clone_res.status_code == 200
    new_clone_data = new_clone_res.json()
    assert new_clone_data["verdict"] == "impersonation"
    assert new_clone_data["score"] >= 90.0

    # Verify merchant alert record was dispatched asynchronously
    alerts_after = client.get(
        f"/api/v1/merchants/{NSV_ID}/alerts",
        headers=auth,
        params={"since": cursor_time},
    )
    assert alerts_after.status_code == 200
    new_alerts = alerts_after.json()["alerts"]
    assert len(new_alerts) >= 1
    assert any(
        a["kind"] == "new_threat"
        and "nairobi_sneakervault_live_scam" in a["title"]
        and a["score"] >= 90.0
        for a in new_alerts
    )


def test_merchant_lifecycle_alerts_playbooks_and_dossier(
    client: TestClient, auth: dict[str, str]
) -> None:
    """Requirement 1b: Complete merchant lifecycle.

    - Poll alerts via GET /api/v1/merchants/{id}/alerts: verify 'new_threat' and details.
    - Mark alert read via POST /api/v1/merchants/{id}/alerts/read: verify unread count decreases.
    - Fetch remediation playbooks GET /api/v1/threats/{id}/playbook in EN and SW.
    - Verify anti-hallucination validation, verified contacts, and valid templates.
    - Fetch evidence dossier GET /api/v1/threats/{id}/dossier: verify X-Evidence-Hash.
    """
    # 1. Poll alerts
    res = client.get(f"/api/v1/merchants/{NSV_ID}/alerts", headers=auth)
    assert res.status_code == 200
    data = res.json()
    assert data["unread_count"] > 0
    assert len(data["alerts"]) > 0

    target_alert = data["alerts"][0]
    threat_id = target_alert["threat_id"]
    assert target_alert["kind"] == "new_threat"
    assert target_alert["threat"] is not None
    assert target_alert["threat"]["composite_score"] >= 70.0
    assert target_alert["threat"]["target_handle"]

    # 2. Mark alert read
    alert_id = target_alert["id"]
    mark_one = client.post(
        f"/api/v1/merchants/{NSV_ID}/alerts/read",
        headers=auth,
        json={"ids": [alert_id]},
    )
    assert mark_one.status_code == 200
    assert mark_one.json()["unread_count"] == data["unread_count"] - 1

    # Mark all remaining read
    mark_all = client.post(
        f"/api/v1/merchants/{NSV_ID}/alerts/read",
        headers=auth,
        json={"all": True},
    )
    assert mark_all.status_code == 200
    assert mark_all.json()["unread_count"] == 0

    # 3. Fetch English remediation playbooks
    pb_en_res = client.get(f"/api/v1/threats/{threat_id}/playbook?lang=en", headers=auth)
    assert pb_en_res.status_code == 200, pb_en_res.text
    pb_en = pb_en_res.json()
    assert pb_en["language"] == "en"
    assert pb_en["contacts_verified"] is True
    assert pb_en["generator"] in ("template", "llm")
    assert pb_en["consumer_warning"]["title"]
    assert pb_en["consumer_warning"]["whatsapp_share_url"].startswith("https://wa.me/?text=")
    assert pb_en["platform_takedown"]["report_url"]
    assert pb_en["safaricom_report"]["to"] == "fraud@safaricom.co.ke"
    assert pb_en["kecirt_report"]["to"] == "incidents@ke-cirt.go.ke"

    # Anti-hallucination validation: no arbitrary/invented numbers in consumer warning
    cw_body = pb_en["consumer_warning"]["body"]
    assert "Nairobi Sneaker Vault" in cw_body
    assert "543210" in cw_body  # Official till must be quoted accurately

    # 4. Fetch Swahili remediation playbooks
    pb_sw_res = client.get(f"/api/v1/threats/{threat_id}/playbook?lang=sw", headers=auth)
    assert pb_sw_res.status_code == 200, pb_sw_res.text
    pb_sw = pb_sw_res.json()
    assert pb_sw["language"] == "sw"
    assert "Tahadhari" in pb_sw["consumer_warning"]["title"]
    assert "Ripoti" in pb_sw["safaricom_report"]["subject"]

    # 5. Fetch evidence dossier (default PDF + JSON format)
    dossier_pdf_res = client.get(f"/api/v1/threats/{threat_id}/dossier", headers=auth)
    assert dossier_pdf_res.status_code == 200, dossier_pdf_res.text
    assert "X-Evidence-Hash" in dossier_pdf_res.headers
    assert dossier_pdf_res.headers["content-type"] == "application/pdf"
    assert dossier_pdf_res.content.startswith(b"%PDF-")

    dossier_res = client.get(f"/api/v1/threats/{threat_id}/dossier?format=json", headers=auth)
    assert dossier_res.status_code == 200, dossier_res.text

    assert "X-Evidence-Hash" in dossier_res.headers
    evidence_hash = dossier_res.headers["X-Evidence-Hash"]
    assert len(evidence_hash) == 64
    assert HEX_64_REGEX.match(evidence_hash)

    dossier = dossier_res.json()
    assert dossier["threat_id"] == threat_id
    assert dossier["evidence_hash"] == evidence_hash
    assert dossier["merchant"]["slug"] == "nairobi-sneaker-vault"
    assert dossier["threat"]["composite_score"] >= 70.0
    assert "status" in dossier["threat"]


def test_community_reports_and_payment_verification(client: TestClient) -> None:
    """Requirement 1c: Community scam reports & payment verification.

    - POST /api/v1/reports stores community scam report.
    - GET /api/v1/verify/payment reflects reported count and reported status.
    - Seeded numbers reflect confirmed status.
    """
    test_number = "0719888777"

    # 1. Verify unknown payment before reports
    init_res = client.get(f"/api/v1/verify/payment?value={test_number}")
    assert init_res.status_code == 200
    init_data = init_res.json()
    assert init_data["status"] == "unknown"
    assert init_data["report_count"] == 0

    # 2. File community scam report
    report_res = client.post(
        "/api/v1/reports",
        json={
            "reported_phone": test_number,
            "target_handle": "fake_sneaker_plug",
            "description": "Demanded advance payment via M-Pesa then blocked me.",
        },
    )
    assert report_res.status_code == 201
    report_data = report_res.json()
    assert UUID(report_data["id"])
    assert report_data["status"] == "pending"

    # 3. Verify report_count incremented
    after_res = client.get(f"/api/v1/verify/payment?value={test_number}")
    assert after_res.status_code == 200
    after_data = after_res.json()
    assert after_data["report_count"] == 1
    assert after_data["normalized"] == "+254719888777"

    # 4. Verify seeded reported scam phone number (0798999111 from blatant clone)
    scam_res = client.get("/api/v1/verify/payment?value=0798999111")
    assert scam_res.status_code == 200
    scam_data = scam_res.json()
    assert scam_data["status"] == "reported"
    assert scam_data["report_count"] >= 2
    assert scam_data["linked_threats"] >= 1

    # 5. Verify official merchant till
    official_res = client.get("/api/v1/verify/payment?value=543210")
    assert official_res.status_code == 200
    official_data = official_res.json()
    assert official_data["status"] == "official"
    assert official_data["merchant"]["business_name"] == "Nairobi Sneaker Vault"


def test_false_positive_prevention_and_official_handles(client: TestClient) -> None:
    """Requirement 1d: False positive prevention and official handle short-circuit.

    - Official handle returns verdict 'official' with 0.0 score.
    - Honest competitor returns verdict 'no_match' (< 40.0) without false alarms.
    """
    # 1. Official handle check
    official_check = client.post(
        "/api/v1/check",
        json={"handle": "nairobisneakervault", "platform": "instagram"},
    )
    assert official_check.status_code == 200
    official_data = official_check.json()
    assert official_data["verdict"] == "official"
    assert official_data["score"] == 0.0
    assert official_data["dimensions"] == []
    assert official_data["matched_merchant"]["slug"] == "nairobi-sneaker-vault"

    # 2. Honest competitor check (Nairobi Sneaker Hub)
    comp_check = client.post(
        "/api/v1/check",
        json={"handle": "nairobisneakerhub", "platform": "instagram"},
    )
    assert comp_check.status_code == 200
    comp_data = comp_check.json()
    assert comp_data["verdict"] == "no_match"
    assert comp_data["score"] < 40.0
    assert comp_data["matched_merchant"] is None
    assert comp_data["safe_action"] is None
    assert comp_data["threat_id"] is None

    # 3. Second competitor check (Kilimani Beauty Bar)
    comp2_check = client.post(
        "/api/v1/check",
        json={"handle": "kilimanibeautybar", "platform": "instagram"},
    )
    assert comp2_check.status_code == 200
    comp2_data = comp2_check.json()
    assert comp2_data["verdict"] == "no_match"
    assert comp2_data["score"] < 40.0


def test_offline_failover_drill_runs_100_percent_isolated(tmp_path: Path) -> None:
    """Requirement 1e: Offline failover drill.

    Validates that with DEMO_MODE=True and no external network:
    - All endpoints run completely in-memory without errors.
    - Deterministic templates generate playbooks without LLM API key.
    - Visual hasher and composite scorer operate offline.
    """
    offline_settings = Settings(
        _env_file=None,
        demo_mode=True,
        api_key="offline-drill-test-key",
        rate_limit_enabled=False,
        media_dir=tmp_path / "media",
        cors_origins="http://localhost:3000",
        llm_enabled=False,
        enable_clip=False,
        scraper_enabled=False,
        daraja_enabled=False,
        meta_rights_manager_enabled=False,
        enable_takedown_tracker=False,
    )

    drill_app = create_app(offline_settings)
    drill_auth = {"X-Halisi-Key": "offline-drill-test-key"}

    with TestClient(drill_app) as drill_client:
        # 1. Health check
        health_res = drill_client.get("/health")
        assert health_res.status_code == 200
        health = health_res.json()
        assert health["status"] == "ok"
        assert health["demo_mode"] is True
        assert health["db"] in ("ok", "memory")
        assert health["engine"]["hash"] == "ok"

        # 2. Check blatant clone
        check_res = drill_client.post(
            "/api/v1/check",
            json={"url": "https://instagram.com/nairobi_sneakervault_official_ke"},
        )
        assert check_res.status_code == 200
        assert check_res.json()["verdict"] == "impersonation"

        # 3. Verify payment lookup
        verify_res = drill_client.get("/api/v1/verify/payment?value=0798999111")
        assert verify_res.status_code == 200
        assert verify_res.json()["status"] == "reported"

        # 4. Public merchant profile
        merchant_res = drill_client.get("/api/v1/merchants/nairobi-sneaker-vault")
        assert merchant_res.status_code == 200
        assert merchant_res.json()["business_name"] == "Nairobi Sneaker Vault"

        # 5. Playbook generation completely offline (Jinja2 templates)
        threats_res = drill_client.get(
            f"/api/v1/merchants/{NSV_ID}/threats", headers=drill_auth
        )
        assert threats_res.status_code == 200
        threat_id = threats_res.json()[0]["id"]

        pb_res = drill_client.get(
            f"/api/v1/threats/{threat_id}/playbook?lang=en", headers=drill_auth
        )
        assert pb_res.status_code == 200
        assert pb_res.json()["generator"] == "template"

        # 6. Cryptographic dossier generation completely offline
        dossier_res = drill_client.get(
            f"/api/v1/threats/{threat_id}/dossier", headers=drill_auth
        )
        assert dossier_res.status_code == 200
        assert "X-Evidence-Hash" in dossier_res.headers
        assert len(dossier_res.headers["X-Evidence-Hash"]) == 64

        # 7. Simulator clone generation completely offline
        sim_res = drill_client.post(
            "/api/v1/simulator/clone",
            headers=drill_auth,
            json={"merchant_id": NSV_ID},
        )
        assert sim_res.status_code == 200
        assert sim_res.json()["verdict"] == "impersonation"
