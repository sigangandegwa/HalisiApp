"""Unit tests for Safaricom Daraja API integration (TSK-039). No external network."""

from pathlib import Path

import httpx
import pytest
import respx

from app.core.config import Settings
from app.core.repository import MemoryRepository
from app.ingestion.daraja import (
    DarajaAuthError,
    DarajaClient,
)
from app.schemas.merchant import MerchantCreate, MerchantHandle
from app.services.payments import verify_payment
from tests.conftest import make_settings


def make_daraja_settings(
    tmp_path: Path,
    *,
    live: bool = False,
    demo_mode: bool = False,
    **overrides: object,
) -> Settings:
    """Helper to configure test settings with or without Daraja credentials."""
    data: dict[str, object] = {
        "demo_mode": demo_mode,
        "daraja_enabled": True,
        "daraja_env": "sandbox",
        "daraja_consumer_key": "test_consumer_key" if live else "",
        "daraja_consumer_secret": "test_consumer_secret" if live else "",
        "daraja_base_url": "https://sandbox.safaricom.co.ke",
        "daraja_shortcode": "600000",
        "daraja_initiator_name": "HalisiTest",
        "daraja_security_credential": "test_credential",
        "daraja_timeout_seconds": 2.0,
    }
    data.update(overrides)
    return make_settings(tmp_path, **data)


# --- 1. Fallback & Demo Mode Tests (Zero Network) -----------------------------


def test_mock_validate_official_merchants(tmp_path: Path) -> None:
    settings = make_daraja_settings(tmp_path, live=False)
    client = DarajaClient(settings)

    # Nairobi Sneaker Vault Till
    till = client.mock_validate("543210")
    assert till.is_valid is True
    assert till.account_name == "NAIROBI SNEAKER VAULT"
    assert till.account_type == "till"
    assert till.kyc_status == "verified"
    assert till.source == "simulated"

    # Kilimani Glow Paybill
    paybill = client.mock_validate("400200", kind="paybill")
    assert paybill.is_valid is True
    assert paybill.account_name == "KILIMANI GLOW"
    assert paybill.account_type == "paybill"
    assert paybill.kyc_status == "verified"

    # Collins Kimanzi Pochi/phone
    phone = client.mock_validate("+254 700 111 222")
    assert phone.is_valid is True
    assert phone.account_name == "COLLINS KIMANZI"
    assert phone.account_type == "phone"
    assert phone.kyc_status == "verified"


def test_mock_validate_competitor_and_scam_clones(tmp_path: Path) -> None:
    settings = make_daraja_settings(tmp_path, live=False)
    client = DarajaClient(settings)

    # Competitor Till
    comp = client.mock_validate("889900")
    assert comp.is_valid is True
    assert comp.account_name == "KICKS KENYA LIMITED"
    assert comp.account_type == "till"

    # Known NSV clone reported phone (local format)
    scam = client.mock_validate("0798 999 111")
    assert scam.is_valid is True
    assert scam.account_name == "JOHN KAMAU NJOROGE"
    assert scam.account_type == "phone"
    assert scam.kyc_status == "active"

    # Another clone target
    scam2 = client.mock_validate("+254798555444")
    assert scam2.is_valid is True
    assert scam2.account_name == "DENNIS OCHIENG"


def test_mock_validate_arbitrary_valid_numbers(tmp_path: Path) -> None:
    settings = make_daraja_settings(tmp_path, live=False)
    client = DarajaClient(settings)

    # Deterministic phone lookup
    res_phone = client.mock_validate("0712345678")
    assert res_phone.is_valid is True
    assert res_phone.account_type == "phone"
    assert res_phone.account_name is not None
    assert len(res_phone.account_name.split()) == 2
    # Determinism: same phone yields exact same name
    assert client.mock_validate("+254712345678").account_name == res_phone.account_name

    # Arbitrary till
    res_till = client.mock_validate("654321")
    assert res_till.is_valid is True
    assert res_till.account_type == "till"
    assert res_till.account_name == "ENTERPRISE 654321"


def test_mock_validate_invalid_inputs(tmp_path: Path) -> None:
    settings = make_daraja_settings(tmp_path, live=False)
    client = DarajaClient(settings)

    for invalid in ("not_a_number", "123", "+12025550199", ""):
        res = client.mock_validate(invalid)
        assert res.is_valid is False
        assert res.kyc_status == "not_found"
        assert res.error_message is not None


@pytest.mark.asyncio
async def test_demo_mode_or_missing_keys_never_makes_network_calls(tmp_path: Path) -> None:
    settings = make_daraja_settings(tmp_path, live=False, demo_mode=True)
    client = DarajaClient(settings)

    # Getting token returns simulated without HTTP request
    token = await client.get_access_token()
    assert token == "simulated_daraja_access_token"

    # validate_account returns simulated without HTTP request
    res = await client.validate_account("543210")
    assert res.is_valid is True
    assert res.account_name == "NAIROBI SNEAKER VAULT"
    assert res.source == "simulated"


# --- 2. Live-Mocked Tests with respx (OAuth & API endpoints) ------------------


@respx.mock
@pytest.mark.asyncio
async def test_oauth_token_success_and_caching(tmp_path: Path) -> None:
    settings = make_daraja_settings(tmp_path, live=True)
    oauth_route = respx.get(
        "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    ).mock(
        return_value=httpx.Response(
            200,
            json={"access_token": "live_test_access_token_xyz", "expires_in": "3599"},
        )
    )

    async with httpx.AsyncClient() as http:
        client = DarajaClient(settings, http=http)
        token1 = await client.get_access_token()
        assert token1 == "live_test_access_token_xyz"
        assert oauth_route.call_count == 1

        # Second call should use cached token
        token2 = await client.get_access_token()
        assert token2 == "live_test_access_token_xyz"
        assert oauth_route.call_count == 1


@respx.mock
@pytest.mark.asyncio
async def test_oauth_token_failure_raises_error(tmp_path: Path) -> None:
    settings = make_daraja_settings(tmp_path, live=True)
    respx.get(
        "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    ).mock(return_value=httpx.Response(401, text="Invalid consumer key or secret"))

    async with httpx.AsyncClient() as http:
        client = DarajaClient(settings, http=http)
        with pytest.raises(DarajaAuthError, match="HTTP 401"):
            await client.get_access_token()


@respx.mock
@pytest.mark.asyncio
async def test_live_account_query_success(tmp_path: Path) -> None:
    settings = make_daraja_settings(tmp_path, live=True)
    respx.get(
        "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    ).mock(
        return_value=httpx.Response(
            200, json={"access_token": "valid_token", "expires_in": "3599"}
        )
    )
    query_route = respx.post("https://sandbox.safaricom.co.ke/mpesa/accountname/v1/query").mock(
        return_value=httpx.Response(
            200,
            json={
                "ResponseCode": "0",
                "ResponseDescription": "Success",
                "AccountName": "SAFARICOM BUSINESS RETAIL",
                "KYCStatus": "Active",
            },
        )
    )

    async with httpx.AsyncClient() as http:
        client = DarajaClient(settings, http=http)
        result = await client.validate_account("554433", kind="till")
        assert result.is_valid is True
        assert result.account_name == "SAFARICOM BUSINESS RETAIL"
        assert result.kyc_status == "active"
        assert result.source == "live"
        assert query_route.call_count == 1


@respx.mock
@pytest.mark.asyncio
async def test_live_account_query_rejection(tmp_path: Path) -> None:
    settings = make_daraja_settings(tmp_path, live=True)
    respx.get(
        "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    ).mock(
        return_value=httpx.Response(
            200, json={"access_token": "valid_token", "expires_in": "3599"}
        )
    )
    respx.post("https://sandbox.safaricom.co.ke/mpesa/accountname/v1/query").mock(
        return_value=httpx.Response(
            200,
            json={
                "ResponseCode": "1",
                "ResponseDescription": "The target identifier does not exist",
            },
        )
    )

    async with httpx.AsyncClient() as http:
        client = DarajaClient(settings, http=http)
        result = await client.validate_account("999999", kind="till")
        assert result.is_valid is False
        assert result.kyc_status == "not_found"
        assert result.source == "live"
        assert "target identifier does not exist" in (result.error_message or "")


@respx.mock
@pytest.mark.asyncio
async def test_live_account_query_network_error_graceful_fallback(tmp_path: Path) -> None:
    settings = make_daraja_settings(tmp_path, live=True)
    respx.get(
        "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    ).mock(
        return_value=httpx.Response(
            200, json={"access_token": "valid_token", "expires_in": "3599"}
        )
    )
    # Simulate network failure on query
    respx.post("https://sandbox.safaricom.co.ke/mpesa/accountname/v1/query").mock(
        side_effect=httpx.ConnectTimeout("Connection to Daraja gateway timed out")
    )

    async with httpx.AsyncClient() as http:
        client = DarajaClient(settings, http=http)
        # Should gracefully fall back to simulated resolver without raising exception
        result = await client.validate_account("+254798999111")
        assert result.is_valid is True
        assert result.account_name == "JOHN KAMAU NJOROGE"
        assert result.source == "fallback"
        assert "Live API error" in (result.error_message or "")


# --- 3. Integration with verify_payment Service -------------------------------


@pytest.mark.asyncio
async def test_verify_payment_enriches_with_daraja_validation(tmp_path: Path) -> None:
    settings = make_daraja_settings(tmp_path, live=False)
    repo = MemoryRepository()
    from app.schemas.merchant import LogoFeatures

    # Create merchant
    await repo.create_merchant(
        MerchantCreate(
            business_name="Nairobi Sneaker Vault",
            slug="nairobi-sneaker-vault",
            mpesa_type="till",
            mpesa_number="543210",
            mpesa_account_name="NAIROBI SNEAKER VAULT",
            handles=[MerchantHandle(platform="instagram", handle="nairobisneakervault")],
            phone_numbers=["+254700111222"],
        ),
        LogoFeatures(phash="c3d1a4f0e8b27c19", dhash="1a2b3c4d5e6f7a8b"),
    )

    client = DarajaClient(settings)
    # 1. Verify official till
    res_official = await verify_payment(repo, "543210", daraja=client)
    assert res_official.status == "official"
    assert res_official.daraja is not None
    assert res_official.daraja.is_valid is True
    assert res_official.daraja.account_name == "NAIROBI SNEAKER VAULT"
    assert res_official.daraja.source == "simulated"

    # 2. Verify reported clone phone
    res_reported = await verify_payment(repo, "0798999111", daraja=client)
    assert res_reported.daraja is not None
    assert res_reported.daraja.is_valid is True
    assert res_reported.daraja.account_name == "JOHN KAMAU NJOROGE"
    assert res_reported.daraja.account_type == "phone"

    # 3. Verify unknown competitor till
    res_comp = await verify_payment(repo, "889900", daraja=client)
    assert res_comp.status == "unknown"
    assert res_comp.daraja is not None
    assert res_comp.daraja.is_valid is True
    assert res_comp.daraja.account_name == "KICKS KENYA LIMITED"
