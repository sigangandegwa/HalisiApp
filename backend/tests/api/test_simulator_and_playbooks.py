"""Simulator (TSK-031), playbooks endpoint (TSK-009) and /health (section 5.1)."""

import itertools
import time

import pytest
from fastapi.testclient import TestClient

from app.ingestion.mock_seeder import seed_id

NSV = str(seed_id("merchant", "nsv"))
KG = str(seed_id("merchant", "kg"))


@pytest.mark.parametrize("merchant_id", [NSV, KG, str(seed_id("merchant", "pt"))])
def test_every_tweak_combination_scores_for_real_within_budget(
    client: TestClient, auth: dict[str, str], merchant_id: str
) -> None:
    combos = itertools.product(
        ("suffix", "homoglyph", "underscore"),
        ("exact", "recolor", "crop", "jpeg"),
        ("phone", "pochi", "none"),
        (True, False),
    )
    for style, logo, payment, tokens in combos:
        started = time.perf_counter()
        response = client.post(
            "/api/v1/simulator/clone",
            headers=auth,
            json={
                "merchant_id": merchant_id,
                "tweaks": {"handle_style": style, "logo": logo, "payment": payment, "bio_tokens": tokens},
            },
        )
        assert time.perf_counter() - started < 1.5
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["target"]["fetched_via"] == "simulator"
        assert data["verdict"] in ("impersonation", "suspicious")
        if payment != "none" and logo in ("exact", "jpeg"):
            assert data["verdict"] == "impersonation" and data["score"] >= 90, (
                style,
                logo,
                payment,
                data["score"],
            )


def test_simulator_clone_is_persisted_and_alerts(client: TestClient, auth: dict[str, str]) -> None:
    cursor = client.get(f"/api/v1/merchants/{NSV}/alerts", headers=auth).json()["server_time"]
    data = client.post("/api/v1/simulator/clone", headers=auth, json={"merchant_id": NSV}).json()
    assert data["target"]["handle"] == "nairobisneakervault_official"
    assert data["target"]["avatar_url"].startswith("data:image/png;base64,")
    assert client.get(f"/api/v1/check/{data['scan_id']}").status_code == 200
    alerts = client.get(f"/api/v1/merchants/{NSV}/alerts", headers=auth, params={"since": cursor}).json()[
        "alerts"
    ]
    assert [a["kind"] for a in alerts] == ["new_threat"]


def test_simulator_unknown_merchant(client: TestClient, auth: dict[str, str]) -> None:
    response = client.post(
        "/api/v1/simulator/clone", headers=auth, json={"merchant_id": "00000000-0000-0000-0000-000000000000"}
    )
    assert response.status_code == 404


@pytest.mark.parametrize("lang", ["en", "sw"])
def test_playbooks_offline_templates(client: TestClient, auth: dict[str, str], lang: str) -> None:
    threat = client.get(f"/api/v1/merchants/{NSV}/threats", headers=auth).json()[0]
    response = client.post(f"/api/v1/threats/{threat['id']}/playbooks?lang={lang}", headers=auth)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["generator"] == "template" and data["model"] is None and data["language"] == lang
    assert data["prompt_ids"] == [
        "PROMPT_CONSUMER_DEFENSE_V2",
        "PROMPT_PLATFORM_TAKEDOWN_V2",
        "PROMPT_SAFARICOM_REPORT_V2",
        "PROMPT_KECIRT_REPORT_V1",
    ]
    warning = data["consumer_warning"]
    assert "0798 999 111" in warning["body"] and "@nairobisneakervault" in warning["body"]
    assert len(warning["body"]) <= 700
    assert warning["whatsapp_share_url"].startswith("https://wa.me/?text=")
    assert data["platform_takedown"]["platform"] == "instagram"
    assert data["contacts_verified"] is False and data["safaricom_report"]["to"].startswith("<")
    if lang == "sw":
        assert warning["body"].startswith("Tahadhari")
    detail = client.get(f"/api/v1/threats/{threat['id']}", headers=auth).json()
    assert {p["playbook_type"] for p in detail["playbooks_generated"]} == {
        "consumer_warning",
        "platform_takedown",
        "safaricom_report",
        "kecirt_report",
    }


def test_playbooks_lang_validation(client: TestClient, auth: dict[str, str]) -> None:
    threat = client.get(f"/api/v1/merchants/{NSV}/threats", headers=auth).json()[0]
    assert client.post(f"/api/v1/threats/{threat['id']}/playbooks?lang=fr", headers=auth).status_code == 422


def test_health_reports_real_state(client: TestClient) -> None:
    data = client.get("/health").json()
    assert data == {
        "status": "ok",
        "version": "0.2.0",
        "demo_mode": True,
        "engine": {"clip": "disabled", "hash": "ok"},
        "llm": "templates (demo mode)",
        "db": "memory",
    }


def test_seed_assets_are_served(client: TestClient) -> None:
    response = client.get("/seed/nsv_logo.png")
    assert response.status_code == 200 and response.headers["content-type"] == "image/png"
