"""Unit tests for Telegram consumer checker bot channel (TSK-042)."""

from collections.abc import Iterator
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from app.channels.telegram import (
    extract_target,
    format_help_message,
    format_welcome_message,
    send_telegram_message,
)
from app.main import create_app
from tests.conftest import make_settings


@pytest.fixture
def client_with_token(tmp_path: Path) -> Iterator[TestClient]:
    """Test client with TELEGRAM_BOT_TOKEN configured."""
    settings = make_settings(tmp_path, telegram_bot_token="test-bot-token-secret-123")
    with TestClient(create_app(settings)) as test_client:
        yield test_client


def test_webhook_fallback_when_token_not_configured(client: TestClient) -> None:
    """When TELEGRAM_BOT_TOKEN is empty, return graceful fallback response."""
    payload = {
        "update_id": 1,
        "message": {"chat": {"id": 12345}, "text": "/start"},
    }
    response = client.post("/api/v1/channels/telegram/webhook", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
    assert data["status"] == "disabled"
    assert "TELEGRAM_BOT_TOKEN is not configured" in data["description"]


def test_webhook_ignored_empty_or_non_message_updates(client_with_token: TestClient) -> None:
    """Updates without an actionable message or chat id are ignored gracefully."""
    # Empty update
    res1 = client_with_token.post("/api/v1/channels/telegram/webhook", json={})
    assert res1.status_code == 200
    assert res1.json()["status"] == "ignored"

    # Update with message but no chat
    res2 = client_with_token.post(
        "/api/v1/channels/telegram/webhook",
        json={"update_id": 2, "message": {"text": "hello"}},
    )
    assert res2.status_code == 200
    assert res2.json()["status"] == "ignored"


def test_webhook_start_command(client_with_token: TestClient) -> None:
    """Handle /start command with welcome greeting."""
    payload = {
        "update_id": 100,
        "message": {"chat": {"id": 555}, "text": "/start"},
    }
    response = client_with_token.post("/api/v1/channels/telegram/webhook", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["method"] == "sendMessage"
    assert data["chat_id"] == 555
    assert "Karibu Halisi Bot" in data["text"]


def test_webhook_help_command(client_with_token: TestClient) -> None:
    """Handle /help command with forensic verdict guide."""
    payload = {
        "update_id": 101,
        "message": {"chat": {"id": 555}, "text": "/help"},
    }
    response = client_with_token.post("/api/v1/channels/telegram/webhook", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["method"] == "sendMessage"
    assert data["chat_id"] == 555
    assert "HALISI" in data["text"]
    assert "FEKI" in data["text"]
    assert "TAHADHARI" in data["text"]


def test_webhook_invalid_input(client_with_token: TestClient) -> None:
    """Handle unsupported message text with helpful guidance."""
    payload = {
        "update_id": 102,
        "message": {"chat": {"id": 555}, "text": "just chatting about the weather"},
    }
    response = client_with_token.post("/api/v1/channels/telegram/webhook", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["chat_id"] == 555
    assert "couldn't find a valid link" in data["text"]


def test_webhook_official_profile_check(client_with_token: TestClient) -> None:
    """Verified official profile link returns HALISI verdict."""
    payload = {
        "update_id": 103,
        "message": {
            "chat": {"id": 555},
            "text": "https://instagram.com/NairobiSneakerVault",
        },
    }
    response = client_with_token.post("/api/v1/channels/telegram/webhook", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["chat_id"] == 555
    text = data["text"]
    assert "HALISI (Official Account)" in text
    assert "Nairobi Sneaker Vault" in text
    assert "0 / 100" in text


def test_webhook_blatant_clone_impersonation(client_with_token: TestClient) -> None:
    """Blatant clone returns FEKI verdict with high risk score and advice."""
    payload = {
        "update_id": 104,
        "message": {
            "chat": {"id": 555},
            "text": "https://www.instagram.com/nairobi_sneakervault_official_ke/?igsh=abc123",
        },
    }
    response = client_with_token.post("/api/v1/channels/telegram/webhook", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["chat_id"] == 555
    text = data["text"]
    assert "FEKI (Impersonation / Clone)" in text
    assert "Nairobi Sneaker Vault" in text
    assert "Risk Indicators:" in text
    assert "Official Advice:" in text


def test_webhook_embedded_url_in_message(client_with_token: TestClient) -> None:
    """Extract embedded URL inside longer conversational text."""
    payload = {
        "update_id": 105,
        "message": {
            "chat": {"id": 777},
            "text": (
                "Is this shop safe? "
                "https://www.instagram.com/nairobi_sneakervault_official_ke/ please check"
            ),
        },
    }
    response = client_with_token.post("/api/v1/channels/telegram/webhook", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["chat_id"] == 777
    assert "FEKI (Impersonation / Clone)" in data["text"]


def test_webhook_bare_handle_input(client_with_token: TestClient) -> None:
    """Bare handle like @nairobi_sneakervault_official_ke is parsed and checked."""
    payload = {
        "update_id": 106,
        "message": {
            "chat": {"id": 888},
            "text": "@nairobi_sneakervault_official_ke",
        },
    }
    response = client_with_token.post("/api/v1/channels/telegram/webhook", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["chat_id"] == 888
    assert "FEKI (Impersonation / Clone)" in data["text"]


def test_webhook_payment_verification_official_till(client_with_token: TestClient) -> None:
    """Sending a registered till number returns HALISI payment status."""
    payload = {
        "update_id": 107,
        "message": {"chat": {"id": 999}, "text": "543210"},
    }
    response = client_with_token.post("/api/v1/channels/telegram/webhook", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["chat_id"] == 999
    text = data["text"]
    assert "Payment Verification" in text
    assert "HALISI (Official Payment Channel)" in text
    assert "Nairobi Sneaker Vault" in text


def test_webhook_payment_verification_unknown(client_with_token: TestClient) -> None:
    """Sending an unregistered till number returns TAHADHARI / unknown status."""
    payload = {
        "update_id": 108,
        "message": {"chat": {"id": 999}, "text": "987654"},
    }
    response = client_with_token.post("/api/v1/channels/telegram/webhook", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    text = data["text"]
    assert "Payment Verification" in text
    assert "TAHADHARI (Unknown / Unregistered)" in text


def test_extract_target_helper() -> None:
    """Unit tests for extract_target pattern recognition."""
    assert extract_target("") is None
    assert extract_target("random words without link") is None

    # Prefix command stripping
    p1 = extract_target("/check https://instagram.com/kilimaniglow")
    assert p1 is not None and p1.handle == "kilimaniglow"

    p2 = extract_target("/verify 543210")
    assert p2 is not None and p2.is_payment and p2.number == "543210"

    # Embedded handle
    p3 = extract_target("Look at @kilimaniglow")
    assert p3 is not None and p3.handle == "kilimaniglow"

    # Embedded Kenyan phone
    p4 = extract_target("Contact them on +254712345678 please")
    assert p4 is not None and p4.is_payment and p4.number == "+254712345678"


def test_format_helpers() -> None:
    """Sanity checks on message format templates."""
    welcome = format_welcome_message()
    assert "Karibu Halisi Bot" in welcome

    help_msg = format_help_message()
    assert "HALISI" in help_msg
    assert "FEKI" in help_msg


@pytest.mark.asyncio
async def test_send_telegram_message_helper() -> None:
    """Test send_telegram_message with mock transport and empty token fallback."""
    # Empty token returns None
    assert await send_telegram_message("", 12345, "hello") is None

    # Mocked HTTP call
    def handler(request: httpx.Request) -> httpx.Response:
        assert "botmock-token/sendMessage" in str(request.url)
        return httpx.Response(200, json={"ok": True, "result": {"message_id": 42}})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http:
        res = await send_telegram_message(
            "mock-token", 12345, "test message", http_client=http
        )
        assert res is not None
        assert res["ok"] is True
        assert res["result"]["message_id"] == 42
