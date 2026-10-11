"""API integration tests for dossier endpoints (TSK-028)."""

import re
from uuid import uuid4

from fastapi.testclient import TestClient

from app.ingestion.mock_seeder import seed_id

NSV_ID = str(seed_id("merchant", "nsv"))
HEX_64_REGEX = re.compile(r"^[0-9a-f]{64}$")


def _get_first_threat_id(client: TestClient, auth: dict[str, str]) -> str:
    res = client.get(f"/api/v1/merchants/{NSV_ID}/threats", headers=auth)
    assert res.status_code == 200
    threats = res.json()
    assert len(threats) > 0
    return str(threats[0]["id"])


def test_dossier_requires_api_key(client: TestClient) -> None:
    res = client.get(f"/api/v1/threats/{uuid4()}/dossier")
    assert res.status_code == 401


def test_dossier_not_found(client: TestClient, auth: dict[str, str]) -> None:
    fake_id = str(uuid4())
    res = client.get(f"/api/v1/threats/{fake_id}/dossier", headers=auth)
    assert res.status_code == 404


def test_threat_dossier_default_pdf(client: TestClient, auth: dict[str, str]) -> None:
    threat_id = _get_first_threat_id(client, auth)
    res = client.get(f"/api/v1/threats/{threat_id}/dossier", headers=auth)

    assert res.status_code == 200
    assert "X-Evidence-Hash" in res.headers
    assert HEX_64_REGEX.match(res.headers["X-Evidence-Hash"])
    assert res.headers["content-type"] == "application/pdf"
    assert f'inline; filename="halisi-dossier-{threat_id}.pdf"' in res.headers["content-disposition"]
    assert res.content.startswith(b"%PDF-1.4")
    assert b"%%EOF" in res.content


def test_threat_dossier_html(client: TestClient, auth: dict[str, str]) -> None:
    threat_id = _get_first_threat_id(client, auth)
    res = client.get(f"/api/v1/threats/{threat_id}/dossier?format=html", headers=auth)

    assert res.status_code == 200
    assert "X-Evidence-Hash" in res.headers
    assert HEX_64_REGEX.match(res.headers["X-Evidence-Hash"])
    assert "text/html" in res.headers["content-type"]
    assert f'inline; filename="halisi-dossier-{threat_id}.html"' in res.headers["content-disposition"]
    html_text = res.text
    assert "<!DOCTYPE html>" in html_text
    assert "Halisi Forensic Evidence Dossier" in html_text
    assert res.headers["X-Evidence-Hash"] in html_text


def test_threat_dossier_json(client: TestClient, auth: dict[str, str]) -> None:
    threat_id = _get_first_threat_id(client, auth)
    res = client.get(f"/api/v1/threats/{threat_id}/dossier?format=json", headers=auth)

    assert res.status_code == 200
    assert "X-Evidence-Hash" in res.headers
    assert HEX_64_REGEX.match(res.headers["X-Evidence-Hash"])
    assert res.headers["content-type"] == "application/json"
    assert f'inline; filename="halisi-dossier-{threat_id}.json"' in res.headers["content-disposition"]

    data = res.json()
    assert data["threat_id"] == threat_id
    assert data["evidence_hash"] == res.headers["X-Evidence-Hash"]
    assert "scores" in data
    assert "merchant" in data
    assert "legal_framework" in data
    assert data["merchant"]["slug"] == "nairobi-sneaker-vault"


def test_merchant_scoped_threat_dossier(client: TestClient, auth: dict[str, str]) -> None:
    threat_id = _get_first_threat_id(client, auth)

    # Success with correct merchant_id
    res = client.get(
        f"/api/v1/merchants/{NSV_ID}/threats/{threat_id}/dossier?format=json",
        headers=auth,
    )
    assert res.status_code == 200
    assert res.json()["threat_id"] == threat_id

    # 404 with mismatched merchant_id
    wrong_merchant = str(seed_id("merchant", "glow"))
    bad_res = client.get(
        f"/api/v1/merchants/{wrong_merchant}/threats/{threat_id}/dossier",
        headers=auth,
    )
    assert bad_res.status_code == 404
