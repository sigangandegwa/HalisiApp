"""Authentication tests (POST /api/v1/auth/login and /logout)."""

from pathlib import Path
from uuid import UUID

from fastapi.testclient import TestClient

from app.main import create_app
from tests.conftest import make_settings


def test_login_success_by_slug(client: TestClient) -> None:
    res = client.post(
        "/api/v1/auth/login",
        json={"identifier": "nairobi-sneaker-vault", "passcode": "halisi-demo"},
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["ok"] is True
    assert data["merchant_slug"] == "nairobi-sneaker-vault"
    assert data["business_name"] == "Nairobi Sneaker Vault"
    assert UUID(data["merchant_id"])


def test_login_success_by_official_handle(client: TestClient) -> None:
    # Handle with '@'
    res = client.post(
        "/api/v1/auth/login",
        json={"identifier": "@nairobisneakervault", "passcode": "halisi-demo"},
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["ok"] is True
    assert data["merchant_slug"] == "nairobi-sneaker-vault"

    # Handle without '@'
    res_no_at = client.post(
        "/api/v1/auth/login",
        json={"identifier": "kilimaniglow", "passcode": "halisi-demo"},
    )
    assert res_no_at.status_code == 200
    assert res_no_at.json()["merchant_slug"] == "kilimani-glow"

    # Mixed case handle with '@'
    res_mixed = client.post(
        "/api/v1/auth/login",
        json={"identifier": "@NairobiSneakerVault", "passcode": "halisi-demo"},
    )
    assert res_mixed.status_code == 200
    assert res_mixed.json()["merchant_slug"] == "nairobi-sneaker-vault"


def test_login_success_by_business_name(client: TestClient) -> None:
    # Exact case
    res = client.post(
        "/api/v1/auth/login",
        json={"identifier": "Nairobi Sneaker Vault", "passcode": "halisi-demo"},
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["ok"] is True
    assert data["business_name"] == "Nairobi Sneaker Vault"
    assert data["merchant_slug"] == "nairobi-sneaker-vault"

    # Lowercase case-insensitive
    res_lower = client.post(
        "/api/v1/auth/login",
        json={"identifier": "nairobi sneaker vault", "passcode": "halisi-demo"},
    )
    assert res_lower.status_code == 200
    assert res_lower.json()["merchant_slug"] == "nairobi-sneaker-vault"

    # With surrounding whitespace and uppercase
    res_spaces = client.post(
        "/api/v1/auth/login",
        json={"identifier": "  PWANI THREADS  ", "passcode": "halisi-demo"},
    )
    assert res_spaces.status_code == 200
    assert res_spaces.json()["merchant_slug"] == "pwani-threads"


def test_login_invalid_passcode(client: TestClient) -> None:
    res = client.post(
        "/api/v1/auth/login",
        json={"identifier": "nairobi-sneaker-vault", "passcode": "wrong-passcode"},
    )
    assert res.status_code == 401
    body = res.json()
    assert body["error"]["code"] == "INVALID_PASSCODE"
    assert body["error"]["message"] == "Invalid merchant passcode."


def test_login_nonexistent_merchant(client: TestClient) -> None:
    res = client.post(
        "/api/v1/auth/login",
        json={"identifier": "non-existent-merchant", "passcode": "halisi-demo"},
    )
    assert res.status_code == 404
    body = res.json()
    assert body["error"]["code"] == "NOT_FOUND"
    assert body["error"]["message"] == "No registered business found matching that identifier."


def test_login_empty_identifier(client: TestClient) -> None:
    res = client.post(
        "/api/v1/auth/login",
        json={"identifier": "   ", "passcode": "halisi-demo"},
    )
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "NOT_FOUND"


def test_logout(client: TestClient) -> None:
    res = client.post("/api/v1/auth/logout")
    assert res.status_code == 200
    assert res.json() == {"ok": True, "message": "Logged out successfully"}


def test_custom_dashboard_passcode(tmp_path: Path) -> None:
    custom_settings = make_settings(tmp_path, dashboard_passcode="custom-secret-key-999")
    with TestClient(create_app(custom_settings)) as custom_client:
        # Default passcode fails
        res_fail = custom_client.post(
            "/api/v1/auth/login",
            json={"identifier": "nairobi-sneaker-vault", "passcode": "halisi-demo"},
        )
        assert res_fail.status_code == 401

        # Custom passcode succeeds
        res_ok = custom_client.post(
            "/api/v1/auth/login",
            json={"identifier": "nairobi-sneaker-vault", "passcode": "custom-secret-key-999"},
        )
        assert res_ok.status_code == 200
        assert res_ok.json()["ok"] is True
