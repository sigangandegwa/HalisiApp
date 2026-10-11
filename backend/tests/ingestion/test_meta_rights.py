"""Unit tests for Meta Rights Manager API automated takedowns (TSK-038)."""

from datetime import UTC, datetime

import httpx
import pytest
import respx

from app.alerts.dispatcher import dispatch_threat_alert
from app.core.config import Settings
from app.core.repository import MemoryRepository
from app.ingestion.meta_rights import (
    META_GRAPH_API_DEFAULT_URL,
    META_TAKEDOWN_THRESHOLD,
    MetaRightsManagerClient,
    MetaRightsManagerError,
    TakedownResult,
    build_takedown_payload,
    compute_evidence_hash,
    maybe_submit_meta_takedown,
    submit_takedown,
)
from app.schemas.merchant import LogoFeatures, MerchantCreate, MerchantHandle
from app.schemas.threat import ThreatUpsert


def test_compute_evidence_hash() -> None:
    hash1 = compute_evidence_hash(
        handle="fake_vault",
        url="https://instagram.com/fake_vault",
        score=96.5,
        avatar_phash="1" * 16,
        phones=["+254711223344", "+254799000111"],
        tills=["543210"],
    )
    assert len(hash1) == 64
    assert isinstance(hash1, str)

    # Different order of phones/tills produces identical hash (sorted canonicalisation)
    hash2 = compute_evidence_hash(
        handle="fake_vault",
        url="https://instagram.com/fake_vault",
        score=96.5,
        avatar_phash="1" * 16,
        phones=["+254799000111", "+254711223344"],
        tills=["543210"],
    )
    assert hash1 == hash2

    # Different score alters hash
    hash3 = compute_evidence_hash(
        handle="fake_vault",
        url="https://instagram.com/fake_vault",
        score=95.0,
        avatar_phash="1" * 16,
        phones=["+254711223344"],
    )
    assert hash1 != hash3


def test_build_takedown_payload() -> None:
    payload = build_takedown_payload(
        threat_handle="@scam_store_ke",
        threat_url="https://instagram.com/scam_store_ke",
        merchant_name="Nairobi Sneaker Vault",
        score=97.2,
        evidence_hash="abcdef123456",
    )
    assert payload["target_handle"] == "scam_store_ke"
    assert payload["url"] == "https://instagram.com/scam_store_ke"
    assert payload["infringed_party"] == "Nairobi Sneaker Vault"
    assert payload["claim_type"] == "brand_impersonation"
    assert payload["confidence_score"] == 97.2
    assert payload["evidence_bundle_hash"] == "abcdef123456"
    assert "Halisi AI" in payload["reason"]


@pytest.mark.asyncio
async def test_unconfigured_fallback() -> None:
    settings = Settings(
        _env_file=None,
        demo_mode=False,
        meta_access_token="",
        meta_rights_manager_id="",
        meta_rights_manager_enabled=True,
    )
    client = MetaRightsManagerClient(settings=settings)
    assert client.is_configured is False

    result1 = await client.submit_takedown(
        threat_handle="fake_vault",
        threat_url="https://instagram.com/fake_vault",
        merchant_name="Nairobi Sneaker Vault",
        score=96.0,
        evidence_hash="hash_12345",
    )
    assert isinstance(result1, TakedownResult)
    assert result1.status == "simulated"
    assert result1.success is True
    assert result1.takedown_id.startswith("meta_sim_")
    assert result1.response_payload == {"simulated": True, "reason": "unconfigured"}

    # Deterministic simulation check: same inputs yield same simulated takedown_id
    result2 = await client.submit_takedown(
        threat_handle="fake_vault",
        threat_url="https://instagram.com/fake_vault",
        merchant_name="Nairobi Sneaker Vault",
        score=96.0,
        evidence_hash="hash_12345",
    )
    assert result1.takedown_id == result2.takedown_id


@pytest.mark.asyncio
async def test_demo_mode_fallback() -> None:
    settings = Settings(
        _env_file=None,
        demo_mode=True,
        meta_access_token="real_token_123",
        meta_rights_manager_id="123456",
        meta_rights_manager_enabled=True,
    )
    client = MetaRightsManagerClient(settings=settings)
    assert client.is_configured is False

    result = await client.submit_takedown(
        threat_handle="fake_glow",
        threat_url="https://facebook.com/fake_glow",
        merchant_name="Kilimani Glow",
        score=95.5,
        evidence_hash="hash_glow",
    )
    assert result.status == "simulated"
    assert result.success is True
    assert result.response_payload == {"simulated": True, "reason": "demo_mode"}


@pytest.mark.asyncio
async def test_disabled_feature_fallback() -> None:
    settings = Settings(
        _env_file=None,
        demo_mode=False,
        meta_access_token="real_token_123",
        meta_rights_manager_id="123456",
        meta_rights_manager_enabled=False,
    )
    client = MetaRightsManagerClient(settings=settings)
    assert client.is_configured is False

    result = await client.submit_takedown(
        threat_handle="fake_glow",
        threat_url="https://facebook.com/fake_glow",
        merchant_name="Kilimani Glow",
        score=95.5,
        evidence_hash="hash_glow",
    )
    assert result.status == "simulated"
    assert result.response_payload == {"simulated": True, "reason": "disabled"}


@respx.mock
@pytest.mark.asyncio
async def test_live_submission_success() -> None:
    settings = Settings(
        _env_file=None,
        demo_mode=False,
        meta_access_token="meta_secret_token",
        meta_rights_manager_id="100123456789",
        meta_rights_manager_enabled=True,
    )
    expected_url = f"{META_GRAPH_API_DEFAULT_URL}/100123456789/takedown_requests"
    mock_payload = {
        "id": "meta_takedown_request_789456",
        "status": "pending_review",
        "created_time": "2026-10-11T12:00:00+0000",
    }
    route = respx.post(expected_url).mock(
        return_value=httpx.Response(201, json=mock_payload)
    )

    client = MetaRightsManagerClient(settings=settings)
    assert client.is_configured is True
    assert client.get_endpoint_url() == expected_url

    result = await client.submit_takedown(
        threat_handle="@fake_sneakers",
        threat_url="https://instagram.com/fake_sneakers",
        merchant_name="Nairobi Sneaker Vault",
        score=97.5,
        evidence_hash="bundle_hash_999",
    )

    assert result.status == "submitted"
    assert result.success is True
    assert result.takedown_id == "meta_takedown_request_789456"
    assert result.response_payload == mock_payload
    assert route.called

    last_req = route.calls.last.request
    assert last_req.headers["Authorization"] == "Bearer meta_secret_token"
    assert last_req.headers["Content-Type"] == "application/json"
    req_json = httpx.Request(
        "POST", expected_url, content=last_req.content
    ).read()
    assert b"fake_sneakers" in req_json
    assert b"bundle_hash_999" in req_json


@respx.mock
@pytest.mark.asyncio
async def test_live_submission_api_error() -> None:
    settings = Settings(
        _env_file=None,
        demo_mode=False,
        meta_access_token="invalid_token",
        meta_rights_manager_id="100123456789",
        meta_rights_manager_enabled=True,
    )
    expected_url = f"{META_GRAPH_API_DEFAULT_URL}/100123456789/takedown_requests"
    respx.post(expected_url).mock(
        return_value=httpx.Response(400, text='{"error": {"message": "Invalid OAuth token"}}')
    )

    client = MetaRightsManagerClient(settings=settings)
    with pytest.raises(MetaRightsManagerError) as exc_info:
        await client.submit_takedown(
            threat_handle="fake_store",
            threat_url="https://instagram.com/fake_store",
            merchant_name="Test Store",
            score=98.0,
            evidence_hash="hash1",
        )
    assert "400" in str(exc_info.value)


@respx.mock
@pytest.mark.asyncio
async def test_live_submission_network_error() -> None:
    settings = Settings(
        _env_file=None,
        demo_mode=False,
        meta_access_token="valid_token",
        meta_rights_manager_id="100123456789",
        meta_rights_manager_enabled=True,
    )
    expected_url = f"{META_GRAPH_API_DEFAULT_URL}/100123456789/takedown_requests"
    respx.post(expected_url).mock(side_effect=httpx.ConnectError("Connection refused"))

    client = MetaRightsManagerClient(settings=settings)
    with pytest.raises(MetaRightsManagerError) as exc_info:
        await client.submit_takedown(
            threat_handle="fake_store",
            threat_url="https://instagram.com/fake_store",
            merchant_name="Test Store",
            score=98.0,
            evidence_hash="hash1",
        )
    assert "Network error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_score_threshold_check() -> None:
    repo = MemoryRepository()
    merchant = await repo.create_merchant(
        MerchantCreate(
            business_name="Nairobi Sneaker Vault",
            slug="nairobi-sneaker-vault",
            phone_numbers=["0711223344"],
            handles=[MerchantHandle(platform="instagram", handle="nairobisneakervault")],
        ),
        LogoFeatures(phash="0" * 16, dhash="0" * 16),
    )

    settings = Settings(
        _env_file=None,
        demo_mode=True,
        meta_rights_manager_enabled=True,
    )

    # 1. Threat below threshold (94.9 < 95.0) -> takedown skipped
    threat_sub = await repo.upsert_threat(
        ThreatUpsert(
            merchant_id=merchant.id,
            platform="instagram",
            target_handle="nsv_almost_clone",
            target_url="https://instagram.com/nsv_almost_clone",
            composite_score=94.9,
            reasons=[],
        )
    )
    result_sub = await maybe_submit_meta_takedown(repo, threat_sub, settings=settings)
    assert result_sub is None

    threat_sub_after = await repo.get_threat(threat_sub.id)
    assert threat_sub_after is not None
    assert threat_sub_after.status == "detected"
    remediations_sub = await repo.list_remediations(threat_sub.id)
    assert len(remediations_sub) == 0

    # 2. Threat at exact threshold (95.0) -> takedown submitted/simulated, status updated
    assert META_TAKEDOWN_THRESHOLD == 95.0
    threat_exact = await repo.upsert_threat(
        ThreatUpsert(
            merchant_id=merchant.id,
            platform="instagram",
            target_handle="nsv_exact_clone",
            target_url="https://instagram.com/nsv_exact_clone",
            composite_score=95.0,
            reasons=[],
        )
    )
    result_exact = await maybe_submit_meta_takedown(repo, threat_exact, settings=settings)
    assert result_exact is not None
    assert result_exact.status == "simulated"
    assert result_exact.score == 95.0

    threat_exact_after = await repo.get_threat(threat_exact.id)
    assert threat_exact_after is not None
    assert threat_exact_after.status == "takedown_filed"

    remediations_exact = await repo.list_remediations(threat_exact.id)
    assert len(remediations_exact) == 1
    assert remediations_exact[0].playbook_type == "platform_takedown"
    assert remediations_exact[0].dispatched_to == "meta_rights_manager"
    assert "Takedown ID:" in remediations_exact[0].generated_content

    # 3. Threat above threshold (98.5) -> takedown submitted/simulated
    threat_high = await repo.upsert_threat(
        ThreatUpsert(
            merchant_id=merchant.id,
            platform="instagram",
            target_handle="nsv_high_clone",
            target_url="https://instagram.com/nsv_high_clone",
            composite_score=98.5,
            reasons=[],
        )
    )
    result_high = await maybe_submit_meta_takedown(repo, threat_high, settings=settings)
    assert result_high is not None
    assert result_high.status == "simulated"

    threat_high_after = await repo.get_threat(threat_high.id)
    assert threat_high_after is not None
    assert threat_high_after.status == "takedown_filed"


@pytest.mark.asyncio
async def test_skip_already_filed_or_resolved_threats() -> None:
    repo = MemoryRepository()
    merchant = await repo.create_merchant(
        MerchantCreate(
            business_name="Kilimani Glow",
            slug="kilimani-glow",
            phone_numbers=["0722334455"],
            handles=[MerchantHandle(platform="instagram", handle="kilimaniglow")],
        ),
        LogoFeatures(phash="0" * 16, dhash="0" * 16),
    )
    settings = Settings(_env_file=None, demo_mode=True, meta_rights_manager_enabled=True)

    threat = await repo.upsert_threat(
        ThreatUpsert(
            merchant_id=merchant.id,
            platform="instagram",
            target_handle="fake_glow_1",
            target_url="https://instagram.com/fake_glow_1",
            composite_score=97.0,
            reasons=[],
        )
    )

    # First run succeeds and marks takedown_filed
    res1 = await maybe_submit_meta_takedown(repo, threat, settings=settings)
    assert res1 is not None

    threat_filed = await repo.get_threat(threat.id)
    assert threat_filed is not None
    assert threat_filed.status == "takedown_filed"

    # Second run skips since status is already takedown_filed
    res2 = await maybe_submit_meta_takedown(repo, threat_filed, settings=settings)
    assert res2 is None

    # Resolved threats also skip
    await repo.update_threat_status(threat.id, "resolved")
    threat_resolved = await repo.get_threat(threat.id)
    assert threat_resolved is not None
    res3 = await maybe_submit_meta_takedown(repo, threat_resolved, settings=settings)
    assert res3 is None


@pytest.mark.asyncio
async def test_dispatcher_integration_with_meta_takedown() -> None:
    repo = MemoryRepository()
    merchant = await repo.create_merchant(
        MerchantCreate(
            business_name="Test Brand",
            slug="test-brand",
            phone_numbers=["0700112233"],
            handles=[MerchantHandle(platform="instagram", handle="testbrand")],
        ),
        LogoFeatures(phash="0" * 16, dhash="0" * 16),
    )
    settings = Settings(_env_file=None, demo_mode=True, meta_rights_manager_enabled=True)

    # 1. Threat with composite score 96.0 triggers alert AND takedown
    threat = await repo.upsert_threat(
        ThreatUpsert(
            merchant_id=merchant.id,
            platform="instagram",
            target_handle="fake_testbrand",
            target_url="https://instagram.com/fake_testbrand",
            composite_score=96.0,
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

    threat_after = await repo.get_threat(threat.id)
    assert threat_after is not None
    assert threat_after.status == "takedown_filed"

    rems = await repo.list_remediations(threat.id)
    assert len(rems) == 1
    assert rems[0].dispatched_to == "meta_rights_manager"


@pytest.mark.asyncio
async def test_functional_submit_takedown_wrapper() -> None:
    settings = Settings(_env_file=None, demo_mode=True, meta_rights_manager_enabled=True)
    res = await submit_takedown(
        threat_handle="@direct_handle",
        threat_url="https://instagram.com/direct_handle",
        merchant_name="Direct Brand",
        score=99.0,
        evidence_hash="ev_12345",
        settings=settings,
    )
    assert res.status == "simulated"
    assert res.threat_handle == "direct_handle"
    assert res["status"] == "simulated"
    assert res["takedown_id"].startswith("meta_sim_")
