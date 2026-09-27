"""Repository contract (docs/BACKEND.md section 4): Memory and Supabase must pass the same tests.

The SupabaseRepository runs against ``tests.fakes.FakeSupabase`` (a query-builder stand-in), so
serialisation (UUIDs, datetimes, pgvector strings) and query composition are exercised offline.
"""

from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

import pytest

from app.core.repository import (
    Conflict,
    MemoryRepository,
    NotFound,
    Repository,
    SupabaseRepository,
    compute_stats,
)
from app.schemas.alert import AlertCreate
from app.schemas.check import ScanCreate, TargetProfileRecord
from app.schemas.merchant import LogoFeatures, MerchantCreate, MerchantHandle
from app.schemas.remediation import RemediationCreate
from app.schemas.report import ReportCreate
from app.schemas.threat import ThreatUpsert
from tests.fakes import FakeSupabase

HASHES = LogoFeatures(phash="c3d1a4f0e8b27c19", dhash="0f0f0f0f0f0f0f0f", embedding=[0.5, 0.25, 0.125])


@pytest.fixture(params=["memory", "supabase"])
def repo(request: pytest.FixtureRequest) -> Repository:
    return MemoryRepository() if request.param == "memory" else SupabaseRepository(FakeSupabase())


def merchant_data(slug: str = "test-shop", handle: str = "testshop") -> MerchantCreate:
    return MerchantCreate(
        business_name="Test Shop",
        slug=slug,
        mpesa_type="till",
        mpesa_number="123456",
        mpesa_account_name="TEST SHOP",
        phone_numbers=["0712 000 111"],
        handles=[MerchantHandle(platform="instagram", handle=handle)],
    )


def threat_data(merchant_id, handle: str = "testshop_official", score: float = 91.5) -> ThreatUpsert:
    return ThreatUpsert(
        merchant_id=merchant_id,
        platform="instagram",
        target_handle=handle,
        target_url=f"https://instagram.com/{handle}",
        composite_score=score,
        confidence=1.0,
        extracted_phones=["+254798999111"],
        extracted_tills=["654321"],
        visual_score=None,
        identity_score=100.0,
        avatar_embedding=[0.1, 0.2],
        reasons=[{"code": "HANDLE_LOOKALIKE", "severity": "high", "text": "t", "text_sw": "s"}],
    )


async def test_merchants_round_trip(repo: Repository) -> None:
    created = await repo.create_merchant(merchant_data(), HASHES, logo_url="/media/x.png")
    assert created.phone_numbers == ["+254712000111"]
    assert created.official_handles[0].url == "https://instagram.com/testshop"
    got = await repo.get_merchant(created.id)
    assert got is not None and got.logo_embedding == [0.5, 0.25, 0.125]
    assert (await repo.get_merchant_by_slug("test-shop")).id == created.id
    assert (await repo.find_official_handle("instagram", "@TestShop/")).id == created.id
    assert await repo.find_official_handle("tiktok", "testshop") is None
    assert [m.slug for m in await repo.list_merchants()] == ["test-shop"]
    again = await repo.create_merchant(merchant_data(), HASHES, merchant_id=created.id)  # idempotent
    assert again.id == created.id and len(await repo.list_merchants()) == 1


async def test_merchant_conflicts(repo: Repository) -> None:
    await repo.create_merchant(merchant_data(), HASHES)
    with pytest.raises(Conflict) as slug:
        await repo.create_merchant(merchant_data(handle="other"), HASHES)
    assert slug.value.code == "SLUG_TAKEN"
    with pytest.raises(Conflict) as handle:
        await repo.create_merchant(merchant_data(slug="other-shop"), HASHES)
    assert handle.value.code == "HANDLE_TAKEN"


async def test_threat_upsert_and_status(repo: Repository) -> None:
    merchant = await repo.create_merchant(merchant_data(), HASHES)
    first = await repo.upsert_threat(threat_data(merchant.id))
    assert first.status == "detected" and first.status_history[0].status == "detected"
    second = await repo.upsert_threat(threat_data(merchant.id, score=95.0))
    assert (
        second.id == first.id
        and second.composite_score == 95.0
        and second.first_seen_at == first.first_seen_at
    )
    assert (await repo.get_threat_by_target(merchant.id, "instagram", "TestShop_Official")).id == first.id
    await repo.upsert_threat(threat_data(merchant.id, handle="another_one", score=80))
    assert [t.composite_score for t in await repo.list_threats(merchant.id, None)] == [95.0, 80.0]

    filed = await repo.update_threat_status(first.id, "takedown_filed")
    assert filed.status == "takedown_filed"
    assert [t.id for t in await repo.list_threats(merchant.id, "takedown_filed")] == [first.id]
    assert [t.id for t in await repo.list_threats_by_status(["takedown_filed"])] == [first.id]
    resolved = await repo.update_threat_status(first.id, "resolved")
    assert resolved.resolved_at is not None
    stored = await repo.get_threat(first.id)
    assert [e.status for e in stored.status_history] == ["detected", "takedown_filed", "resolved"]
    assert stored.avatar_embedding == [0.1, 0.2]
    back = await repo.upsert_threat(threat_data(merchant.id, score=96))  # page is seen again
    assert back.status == "detected" and back.resolved_at is None
    with pytest.raises(NotFound):
        await repo.update_threat_status(uuid4(), "resolved")


async def test_scans(repo: Repository) -> None:
    merchant = await repo.create_merchant(merchant_data(), HASHES)
    threat = await repo.upsert_threat(threat_data(merchant.id))
    t0 = datetime(2026, 9, 27, 10, 0, tzinfo=UTC)
    for i in range(2):
        await repo.insert_scan(
            ScanCreate(
                input_value="x",
                input_kind="handle",
                verdict="impersonation",
                composite_score=91.5,
                merchant_id=merchant.id,
                threat_id=threat.id,
                result={"n": i},
                elapsed_ms=10 * (i + 1),
                created_at=t0 + timedelta(minutes=i),
            )
        )
    latest = await repo.latest_scan_for_threat(threat.id)
    assert latest.result == {"n": 1}
    assert (await repo.get_scan(latest.id)).elapsed_ms == 20
    assert await repo.get_scan(uuid4()) is None


async def test_reports_and_payment_lookup(repo: Repository) -> None:
    merchant = await repo.create_merchant(merchant_data(), HASHES)
    await repo.upsert_threat(threat_data(merchant.id))
    report_id = await repo.insert_report(ReportCreate(reported_phone="0798 999 111", target_handle="@Fake"))
    await repo.insert_report(ReportCreate(reported_phone="0798999111"), status="rejected")
    lookup = await repo.find_by_payment("+254798999111", None)
    assert (lookup.report_count, lookup.confirmed_reports, lookup.linked_threats) == (1, 0, 1)
    assert await repo.confirmed_reported_numbers() == frozenset()
    await repo.set_report_status(report_id, "confirmed")
    assert await repo.confirmed_reported_numbers() == frozenset({"+254798999111"})
    official = await repo.find_by_payment(None, "123456")
    assert official.merchant is not None and official.merchant.id == merchant.id
    assert (await repo.find_by_payment("0712000111", None)).merchant.id == merchant.id
    assert (await repo.find_by_payment(None, "654321")).linked_threats == 1
    assert (await repo.find_by_payment(None, None)).merchant is None
    with pytest.raises(NotFound):
        await repo.set_report_status(uuid4(), "confirmed")


async def test_alerts(repo: Repository) -> None:
    merchant = await repo.create_merchant(merchant_data(), HASHES)
    threat = await repo.upsert_threat(threat_data(merchant.id))
    t0 = datetime(2026, 9, 27, 10, 0, tzinfo=UTC)
    ids = []
    for i in range(3):
        alert = await repo.insert_alert(
            AlertCreate(
                merchant_id=merchant.id,
                threat_id=threat.id,
                kind="new_threat",
                title=f"a{i}",
                body="b",
                score=90,
                created_at=t0 + timedelta(seconds=i),
            )
        )
        ids.append(alert.id)
    assert (await repo.last_alert_for_threat(threat.id)).title == "a2"
    assert [a.title for a in await repo.list_alerts(merchant.id, None, False, 10)] == ["a2", "a1", "a0"]
    assert [a.title for a in await repo.list_alerts(merchant.id, t0, False, 10)] == ["a2", "a1"]
    assert len(await repo.list_alerts(merchant.id, None, False, 1)) == 1
    assert await repo.mark_alerts_read(merchant.id, [ids[0]]) == 2
    assert [a.title for a in await repo.list_alerts(merchant.id, None, True, 10)] == ["a2", "a1"]
    assert await repo.mark_alerts_read(merchant.id, []) == 2
    assert await repo.mark_alerts_read(merchant.id, None) == 0
    assert await repo.unread_count(merchant.id) == 0


async def test_remediation_logs_and_profiles(repo: Repository) -> None:
    merchant = await repo.create_merchant(merchant_data(), HASHES)
    threat = await repo.upsert_threat(threat_data(merchant.id))
    await repo.insert_remediation(
        RemediationCreate(
            threat_id=threat.id, playbook_type="consumer_warning", generated_content="x", generator="template"
        )
    )
    assert [r.playbook_type for r in await repo.list_remediations(threat.id)] == ["consumer_warning"]

    profile = TargetProfileRecord(
        platform="instagram",
        handle="some.page",
        display_name="Some Page",
        avatar_phash="c3d1a4f0e8b27c19",
        avatar_embedding=[1.0, 0.0],
        account_created_on=date(2026, 9, 1),
        fetched_via="seed",
        fetched_at=datetime(2026, 9, 27, tzinfo=UTC),
    )
    await repo.upsert_target_profile(profile)
    got = await repo.get_target_profile("instagram", "@Some.Page")
    assert (
        got is not None and got.avatar_embedding == [1.0, 0.0] and got.account_created_on == date(2026, 9, 1)
    )
    assert await repo.get_target_profile("tiktok", "some.page") is None


async def test_stats_and_ping(repo: Repository) -> None:
    merchant = await repo.create_merchant(merchant_data(), HASHES)
    threat = await repo.upsert_threat(threat_data(merchant.id))
    await repo.insert_scan(
        ScanCreate(
            input_value="x",
            input_kind="handle",
            verdict="impersonation",
            merchant_id=merchant.id,
            threat_id=threat.id,
            result={},
            elapsed_ms=40,
        )
    )
    stats = await repo.stats(None)
    assert (
        stats.pages_scanned,
        stats.threats_detected,
        stats.impersonations_blocked_7d,
        stats.merchants_protected,
        stats.median_detection_ms,
    ) == (1, 1, 1, 1, 40)
    mine = await repo.stats(merchant.id)
    assert (mine.active_threats, mine.resolved, mine.customers_warned_estimate) == (1, 0, 1)
    assert await repo.ping() in ("memory", "ok")


def test_compute_stats_empty() -> None:
    stats = compute_stats([], [], [], None, datetime.now(UTC))
    assert stats.median_detection_ms == 0 and stats.top_platforms == []
