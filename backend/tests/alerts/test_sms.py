"""Unit tests for Africa's Talking SMS integration (TSK-041)."""

from datetime import UTC, datetime

import httpx
import pytest
import respx

from app.alerts.dispatcher import dispatch_threat_alert
from app.alerts.sms import (
    AT_LIVE_URL,
    AT_SANDBOX_URL,
    AfricasTalkingClient,
    format_threat_sms,
    get_messaging_url,
    normalize_phone,
    send_threat_sms,
)
from app.core.config import Settings
from app.core.repository import MemoryRepository
from app.schemas.merchant import LogoFeatures, MerchantCreate, MerchantHandle
from app.schemas.threat import ThreatUpsert


def test_format_threat_sms() -> None:
    text = format_threat_sms("Nairobi Sneaker Vault", "nsv_deals_ke", 96.0)
    assert "@nsv_deals_ke" in text
    assert "Nairobi Sneaker Vault" in text
    assert "96%" in text
    assert "HALISI TAHADHARI / ALERT:" in text
    assert "Akaunti feki imegunduliwa" in text

    # Pre-existing @ handle
    text_with_at = format_threat_sms("Kilimani Glow", "@fake_glow", 91.4)
    assert "@fake_glow" in text_with_at
    assert "@@" not in text_with_at
    assert "91%" in text_with_at


@pytest.mark.parametrize(
    ("input_phone", "expected"),
    [
        ("0712345678", "+254712345678"),
        ("0112345678", "+254112345678"),
        ("+254 712 345 678", "+254712345678"),
        ("254712345678", "+254712345678"),
        ("+254799000111", "+254799000111"),
        ("+14155552671", "+14155552671"),
    ],
)
def test_normalize_phone(input_phone: str, expected: str) -> None:
    assert normalize_phone(input_phone) == expected


def test_get_messaging_url() -> None:
    assert get_messaging_url("sandbox") == AT_SANDBOX_URL
    assert get_messaging_url("Sandbox") == AT_SANDBOX_URL
    assert get_messaging_url("halisi_live") == AT_LIVE_URL


@pytest.mark.asyncio
async def test_send_threat_sms_unconfigured_fallback() -> None:
    settings = Settings(
        _env_file=None,
        demo_mode=False,
        africastalking_username="",
        africastalking_api_key="",
    )
    result = await send_threat_sms(
        "0712345678",
        "Nairobi Sneaker Vault",
        "fake_vault",
        95.0,
        settings=settings,
    )
    assert result.success is True
    assert result.simulated is True
    assert result.recipient == "+254712345678"
    assert result.response == {"status": "simulated", "reason": "unconfigured"}


@pytest.mark.asyncio
async def test_send_threat_sms_demo_mode_fallback() -> None:
    settings = Settings(
        _env_file=None,
        demo_mode=True,
        africastalking_username="sandbox",
        africastalking_api_key="some_key",
    )
    result = await send_threat_sms(
        "0712345678",
        "Nairobi Sneaker Vault",
        "fake_vault",
        95.0,
        settings=settings,
    )
    assert result.success is True
    assert result.simulated is True
    assert result.response == {"status": "simulated", "reason": "demo_mode"}


@respx.mock
@pytest.mark.asyncio
async def test_send_threat_sms_sandbox_success() -> None:
    settings = Settings(
        _env_file=None,
        demo_mode=False,
        africastalking_username="sandbox",
        africastalking_api_key="atsk_test_key_123",
    )
    mock_payload = {
        "SMSMessageData": {
            "Message": "Sent to 1/1 Total Cost: KES 0.8000",
            "Recipients": [
                {
                    "cost": "KES 0.8000",
                    "messageId": "ATXid_12345",
                    "number": "+254712345678",
                    "status": "Success",
                    "statusCode": 101,
                }
            ],
        }
    }
    route = respx.post(AT_SANDBOX_URL).mock(return_value=httpx.Response(201, json=mock_payload))

    result = await send_threat_sms(
        "0712345678",
        "Nairobi Sneaker Vault",
        "fake_vault",
        96.0,
        settings=settings,
    )
    assert route.called
    assert result.success is True
    assert result.simulated is False
    assert result.recipient == "+254712345678"
    assert result.response == mock_payload

    request = route.calls.last.request
    assert request.headers["apiKey"] == "atsk_test_key_123"
    content = request.content.decode("utf-8")
    assert "username=sandbox" in content
    assert "to=%2B254712345678" in content


@respx.mock
@pytest.mark.asyncio
async def test_send_threat_sms_live_with_sender_id() -> None:
    settings = Settings(
        _env_file=None,
        demo_mode=False,
        africastalking_username="halisi_prod",
        africastalking_api_key="live_secret_key",
        africastalking_sender_id="HALISI",
    )
    mock_payload = {
        "SMSMessageData": {
            "Message": "Sent to 1/1 Total Cost: KES 0.8000",
            "Recipients": [
                {
                    "cost": "KES 0.8000",
                    "messageId": "ATXid_live_999",
                    "number": "+254722000000",
                    "status": "Sent",
                    "statusCode": 101,
                }
            ],
        }
    }
    route = respx.post(AT_LIVE_URL).mock(return_value=httpx.Response(200, json=mock_payload))

    client = AfricasTalkingClient(settings=settings)
    result = await client.send_threat_sms(
        "+254722000000",
        "Kilimani Glow",
        "fake_glow",
        99.0,
    )
    assert route.called
    assert result.success is True
    assert result.simulated is False

    request = route.calls.last.request
    content = request.content.decode("utf-8")
    assert "from=HALISI" in content
    assert "username=halisi_prod" in content


@respx.mock
@pytest.mark.asyncio
async def test_send_threat_sms_recipient_rejected() -> None:
    settings = Settings(
        _env_file=None,
        demo_mode=False,
        africastalking_username="sandbox",
        africastalking_api_key="test_key",
    )
    mock_payload = {
        "SMSMessageData": {
            "Message": "Sent to 0/1 Total Cost: KES 0",
            "Recipients": [
                {
                    "cost": "0",
                    "number": "+254712345678",
                    "status": "InvalidPhoneNumber",
                    "statusCode": 403,
                }
            ],
        }
    }
    respx.post(AT_SANDBOX_URL).mock(return_value=httpx.Response(200, json=mock_payload))

    result = await send_threat_sms(
        "0712345678",
        "Nairobi Sneaker Vault",
        "fake_vault",
        95.0,
        settings=settings,
    )
    assert result.success is False
    assert result.simulated is False
    assert "failed" in (result.error or "").lower()


@respx.mock
@pytest.mark.asyncio
async def test_send_threat_sms_http_error() -> None:
    settings = Settings(
        _env_file=None,
        demo_mode=False,
        africastalking_username="sandbox",
        africastalking_api_key="bad_key",
    )
    respx.post(AT_SANDBOX_URL).mock(return_value=httpx.Response(401, text="Unauthorized"))

    result = await send_threat_sms(
        "0712345678",
        "Nairobi Sneaker Vault",
        "fake_vault",
        95.0,
        settings=settings,
    )
    assert result.success is False
    assert result.simulated is False
    assert "401" in (result.error or "")


@respx.mock
@pytest.mark.asyncio
async def test_send_threat_sms_connection_failure() -> None:
    settings = Settings(
        _env_file=None,
        demo_mode=False,
        africastalking_username="sandbox",
        africastalking_api_key="test_key",
    )
    respx.post(AT_SANDBOX_URL).mock(side_effect=httpx.ConnectError("Connection refused"))

    result = await send_threat_sms(
        "0712345678",
        "Nairobi Sneaker Vault",
        "fake_vault",
        95.0,
        settings=settings,
    )
    assert result.success is False
    assert result.simulated is False
    assert "connection refused" in (result.error or "").lower()


@respx.mock
@pytest.mark.asyncio
async def test_dispatcher_sends_sms_for_critical_threat() -> None:
    repo = MemoryRepository()
    merchant = await repo.create_merchant(
        MerchantCreate(
            business_name="Test Store",
            slug="test-store",
            phone_numbers=["0711223344"],
            handles=[MerchantHandle(platform="instagram", handle="test_store")],
        ),
        LogoFeatures(phash="0" * 16, dhash="0" * 16),
    )

    settings = Settings(
        _env_file=None,
        demo_mode=False,
        africastalking_username="sandbox",
        africastalking_api_key="atsk_key",
    )
    mock_payload = {
        "SMSMessageData": {
            "Message": "Sent to 1/1",
            "Recipients": [{"status": "Success", "statusCode": 101, "number": "+254711223344"}],
        }
    }
    route = respx.post(AT_SANDBOX_URL).mock(return_value=httpx.Response(200, json=mock_payload))

    threat = await repo.upsert_threat(
        ThreatUpsert(
            merchant_id=merchant.id,
            platform="instagram",
            target_handle="fake_store_ke",
            target_url="https://instagram.com/fake_store_ke",
            composite_score=94.0,
            reasons=[],
        )
    )

    alert = await dispatch_threat_alert(
        repo,
        None,
        threat,
        threshold=70.0,
        dedup_hours=6.0,
        now=datetime.now(UTC),
        settings=settings,
    )
    assert alert is not None
    assert route.called
    assert "fake_store_ke" in route.calls.last.request.content.decode("utf-8")
