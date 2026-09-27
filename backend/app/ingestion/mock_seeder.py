"""Mock seeder (TSK-007, docs/BACKEND.md section 7.3). The demo depends on it.

Fictional businesses only. Every score is computed by the real engine: each seeded page goes through
the same ``CheckService`` pipeline as ``POST /api/v1/check`` (tier-1 known profile -> hashes ->
extractors -> ``score_against_all``), so fixtures can never drift from what the API returns.

Seed set:
* 3 merchants: Nairobi Sneaker Vault (Till), Kilimani Glow (Paybill), Pwani Threads (Pochi).
* per merchant: a blatant clone (exact logo + JPEG + "OFFICIAL" caption, ``_official_ke`` handle,
  personal number, scam phrases, new account), a subtle clone (recoloured + cropped logo, homoglyph
  handle, Pochi request, no account data) and a look-alike legitimate competitor (own logo, similar
  name, own till) that must score ``no_match``.
* 5 community reports on the blatant clones' numbers, 2 confirmed.

IDs are uuid5 (deterministic) and every write is an upsert, so re-running is idempotent.

    python -m app.ingestion.mock_seeder --target memory            # seed in memory + export fixtures
    python -m app.ingestion.mock_seeder --target supabase [--reset] # needs SUPABASE_URL + key
"""

import argparse
import asyncio
import json
import shutil
import string
import sys
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
from PIL import Image

from app.core.config import BACKEND_DIR, Settings, get_settings
from app.core.repository import MemoryRepository, Repository, SupabaseRepository
from app.engine.embeddings import ClipEmbedder
from app.ingestion.fixtures import logos as L
from app.schemas.alert import AlertOut, AlertsResponse
from app.schemas.check import CheckRequest, CheckResult, TargetProfileRecord
from app.schemas.merchant import LogoFeatures, MerchantCreate, MerchantHandle, MerchantRecord
from app.schemas.report import ReportCreate, VerifyPaymentResult
from app.services.check import CheckService
from app.services.payments import verify_payment
from app.services.remediation import generate_playbooks
from app.services.serializers import public_merchant, threat_detail, threat_summary

SEED_NAMESPACE = uuid.UUID("1d7c6f7e-3f51-5b8e-a5f4-6a2d1c9b0e42")
SEED_NOW = datetime(2026, 9, 27, 9, 0, tzinfo=UTC)  # fixed clock for exported fixtures
ASSETS_DIR = BACKEND_DIR / "app" / "ingestion" / "fixtures" / "assets"
ASSET_URL_PREFIX = "/seed"
README_TEMPLATE = BACKEND_DIR / "app" / "ingestion" / "fixtures" / "seed_readme.md"
FRONTEND_EXPORT_DIR = BACKEND_DIR.parent / "frontend" / "src" / "lib" / "fixtures" / "seed"


def seed_id(kind: str, key: str) -> uuid.UUID:
    """Deterministic id for a seed row."""
    return uuid.uuid5(SEED_NAMESPACE, f"{kind}:{key}")


@dataclass(frozen=True)
class MerchantSeed:
    """One fictional merchant."""

    key: str
    logo: Callable[[], Image.Image]
    data: MerchantCreate
    created_days_ago: int = 30


@dataclass(frozen=True)
class TargetSeed:
    """One seeded page (clone or competitor)."""

    key: str
    merchant_key: str
    kind: str  # blatant | subtle | competitor
    handle: str
    display_name: str
    bio: str
    image: Callable[[], Image.Image]
    follower_count: int | None = None
    post_count: int | None = None
    account_age_days: int | None = None
    seen_days_ago: int = 1
    platform: str = "instagram"
    expect: str = "impersonation"


@dataclass(frozen=True)
class ReportSeed:
    """One community report."""

    key: str
    target_key: str
    phone: str
    status: str
    description: str
    days_ago: int


def _merchant(key: str, logo: Callable[[], Image.Image], **data: Any) -> MerchantSeed:
    return MerchantSeed(key=key, logo=logo, data=MerchantCreate(**data))


MERCHANTS: tuple[MerchantSeed, ...] = (
    _merchant(
        "nsv",
        L.sneaker_logo,
        business_name="Nairobi Sneaker Vault",
        slug="nairobi-sneaker-vault",
        category="Sneakers",
        location="Nairobi CBD",
        established_on=date(2021, 3, 1),
        mpesa_type="till",
        mpesa_number="543210",
        mpesa_account_name="NAIROBI SNEAKER VAULT",
        phone_numbers=["+254712345678"],
        handles=[
            MerchantHandle(platform="instagram", handle="nairobisneakervault"),
            MerchantHandle(platform="tiktok", handle="nairobisneakervault"),
        ],
    ),
    _merchant(
        "kg",
        L.glow_logo,
        business_name="Kilimani Glow",
        slug="kilimani-glow",
        category="Beauty & skincare",
        location="Kilimani, Nairobi",
        established_on=date(2022, 6, 15),
        mpesa_type="paybill",
        mpesa_number="400200",
        mpesa_account_name="KILIMANI GLOW",
        phone_numbers=["+254722000333"],
        handles=[
            MerchantHandle(platform="instagram", handle="kilimaniglow"),
            MerchantHandle(platform="facebook", handle="kilimaniglow"),
        ],
    ),
    _merchant(
        "pt",
        L.threads_logo,
        business_name="Pwani Threads",
        slug="pwani-threads",
        category="Fashion",
        location="Mombasa",
        established_on=date(2020, 11, 2),
        mpesa_type="pochi",
        mpesa_number="+254700111222",
        mpesa_account_name="PWANI THREADS",
        phone_numbers=["+254700111222"],
        handles=[
            MerchantHandle(platform="instagram", handle="pwanithreads"),
            MerchantHandle(platform="tiktok", handle="pwanithreads"),
        ],
    ),
)


def _blatant(logo: Callable[[], Image.Image]) -> Callable[[], Image.Image]:
    return lambda: L.overlay_text(L.jpeg(logo()))


def _subtle(logo: Callable[[], Image.Image]) -> Callable[[], Image.Image]:
    return lambda: L.crop(L.recolor(logo()))


TARGETS: tuple[TargetSeed, ...] = (
    TargetSeed(
        "nsv_blatant",
        "nsv",
        "blatant",
        "nairobi_sneakervault_official_ke",
        "Nairobi Sneaker Vault Official",
        "Official page. Lipa kwanza, pay before delivery. Send money to 0798 999 111. Offer ends today!",
        _blatant(L.sneaker_logo),
        follower_count=212,
        post_count=9,
        account_age_days=8,
        seen_days_ago=2,
    ),
    TargetSeed(
        "nsv_subtle",
        "nsv",
        "subtle",
        "nairobisneakervau1t",
        "Nairobi Sneaker Vault",
        "New drops weekly. Pochi la biashara 0711 222 333. Delivery countrywide.",
        _subtle(L.sneaker_logo),
        seen_days_ago=1,
    ),
    TargetSeed(
        "nsv_competitor",
        "nsv",
        "competitor",
        "nairobisneakerhub",
        "Nairobi Sneaker Hub",
        "Nairobi sneaker plug since 2019. Visit our shop on Moi Avenue. Delivery countrywide. Till 889900",
        L.hub_logo,
        follower_count=5400,
        post_count=410,
        seen_days_ago=3,
        expect="no_match",
    ),
    TargetSeed(
        "kg_blatant",
        "kg",
        "blatant",
        "kilimaniglow_official_ke",
        "Kilimani Glow Official",
        "Glow sale! Lipa kabla ya delivery. Tuma pesa 0733 000 111. No refunds.",
        _blatant(L.glow_logo),
        follower_count=150,
        post_count=6,
        account_age_days=5,
        seen_days_ago=2,
    ),
    TargetSeed(
        "kg_subtle",
        "kg",
        "subtle",
        "kiiimaniglow",
        "Kilimani Glow",
        "Serums and skincare. Pochi la biashara 0745 600 700. Order now.",
        _subtle(L.glow_logo),
        seen_days_ago=1,
    ),
    TargetSeed(
        "kg_competitor",
        "kg",
        "competitor",
        "kilimanibeautybar",
        "Kilimani Beauty Bar",
        "Kilimani's neighbourhood beauty bar since 2018. Book via DM. Till 667788",
        L.beauty_logo,
        follower_count=8900,
        post_count=620,
        seen_days_ago=4,
        expect="no_match",
    ),
    TargetSeed(
        "pt_blatant",
        "pt",
        "blatant",
        "pwanithreads_official_ke",
        "Pwani Threads Official",
        "Mombasa fashion deals. Pay before delivery. Send money to 0799 111 222 only. Limited stock!",
        _blatant(L.threads_logo),
        follower_count=90,
        post_count=4,
        account_age_days=8,
        seen_days_ago=3,
    ),
    TargetSeed(
        "pt_subtle",
        "pt",
        "subtle",
        "pwanlthreads",
        "Pwani Threads",
        "Kitenge and linen. Tuma pesa kwa Pochi la biashara 0768 123 456.",
        _subtle(L.threads_logo),
        seen_days_ago=1,
    ),
    TargetSeed(
        "pt_competitor",
        "pt",
        "competitor",
        "pwanifashionhouse",
        "Pwani Fashion House",
        "Mombasa tailoring since 2015. Order now. Till 334455",
        L.coast_logo,
        follower_count=3100,
        post_count=280,
        seen_days_ago=5,
        expect="no_match",
    ),
)

REPORTS: tuple[ReportSeed, ...] = (
    ReportSeed(
        "r1",
        "nsv_blatant",
        "+254798999111",
        "confirmed",
        "Asked me to pay before delivery to this number.",
        3,
    ),
    ReportSeed(
        "r2", "nsv_blatant", "+254798999111", "pending", "Same page, same number, asked for a deposit.", 2
    ),
    ReportSeed(
        "r3", "kg_blatant", "+254733000111", "confirmed", "Fake Kilimani Glow page asked me to send money.", 3
    ),
    ReportSeed("r4", "kg_blatant", "+254733000111", "pending", "This number claims to be Kilimani Glow.", 2),
    ReportSeed("r5", "pt_blatant", "+254799111222", "pending", "Page pretending to be Pwani Threads.", 3),
)


def asset_name(key: str) -> str:
    """File name of a generated asset."""
    return f"{key}.png"


def asset_url(key: str) -> str:
    """Public URL of a generated asset (served by the backend at /seed, copy to frontend/public/seed)."""
    return f"{ASSET_URL_PREFIX}/{asset_name(key)}"


def render_assets() -> dict[str, bytes]:
    """PNG bytes for every merchant logo (``<key>_logo``) and target avatar (``<target key>``)."""
    out = {f"{m.key}_logo": L.png_bytes(m.logo()) for m in MERCHANTS}
    out.update({t.key: L.png_bytes(t.image()) for t in TARGETS})
    return out


def write_assets(directory: Path = ASSETS_DIR) -> dict[str, bytes]:
    """Write (or refresh) the generated PNGs; returns them."""
    assets = render_assets()
    directory.mkdir(parents=True, exist_ok=True)
    for key, data in assets.items():
        path = directory / asset_name(key)
        if not path.exists() or path.read_bytes() != data:
            path.write_bytes(data)
    return assets


@dataclass
class SeedResult:
    """What seeding produced (used by the fixture export and tests)."""

    merchants: dict[str, MerchantRecord]
    checks: dict[str, CheckResult]  # target key or "<merchant>_official" -> result
    now: datetime


async def seed_repository(
    repo: Repository,
    service: CheckService,
    *,
    now: datetime = SEED_NOW,
    assets: dict[str, bytes] | None = None,
) -> SeedResult:
    """Seed ``repo`` through the real check pipeline. Idempotent (uuid5 ids + upserts)."""
    assets = assets or render_assets()
    merchants: dict[str, MerchantRecord] = {}
    for m in MERCHANTS:
        features = await service.features_from_bytes(assets[f"{m.key}_logo"])
        merchants[m.key] = await repo.create_merchant(
            m.data,
            LogoFeatures(
                phash=features.phash,
                dhash=features.dhash,
                embedding=list(features.embedding) if features.embedding else None,
            ),
            logo_url=asset_url(f"{m.key}_logo"),
            merchant_id=seed_id("merchant", m.key),
            is_verified=True,
            created_at=now - timedelta(days=m.created_days_ago),
        )
    service.merchants.invalidate()

    targets = {t.key: t for t in TARGETS}
    for r in REPORTS:
        target = targets[r.target_key]
        await repo.insert_report(
            ReportCreate(
                target_handle=target.handle,
                platform=target.platform,
                reported_phone=r.phone,  # type: ignore[arg-type]
                description=r.description,
            ),
            report_id=seed_id("report", r.key),
            status=r.status,
            created_at=now - timedelta(days=r.days_ago),
        )

    for t in TARGETS:
        seen = now - timedelta(days=t.seen_days_ago)
        features = await service.features_from_bytes(assets[t.key])
        await repo.upsert_target_profile(
            TargetProfileRecord(
                platform=t.platform,
                handle=t.handle,
                url=f"https://instagram.com/{t.handle}",
                display_name=t.display_name,
                bio=t.bio,
                avatar_url=asset_url(t.key),
                avatar_phash=features.phash,
                avatar_dhash=features.dhash,
                avatar_embedding=list(features.embedding) if features.embedding else None,
                follower_count=t.follower_count,
                post_count=t.post_count,
                account_created_on=seen.date() - timedelta(days=t.account_age_days)
                if t.account_age_days
                else None,
                fetched_via="seed",
                fetched_at=seen,
            )
        )

    checks: dict[str, CheckResult] = {}
    for t in sorted(TARGETS, key=lambda x: -x.seen_days_ago):
        outcome = await service.check(
            CheckRequest(handle=t.handle, platform=t.platform),
            source="seed",  # type: ignore[arg-type]
            scan_id=seed_id("scan", t.key),
            now=now - timedelta(days=t.seen_days_ago),
        )
        await service.persist(outcome)
        checks[t.key] = outcome.result
    for m in MERCHANTS:
        handle = m.data.handles[0]
        outcome = await service.check(
            CheckRequest(handle=handle.handle, platform=handle.platform),
            source="seed",
            scan_id=seed_id("scan", f"{m.key}_official"),
            now=now - timedelta(hours=6),
        )
        await service.persist(outcome)
        checks[f"{m.key}_official"] = outcome.result

    for r in REPORTS:  # link reports to the threats they describe (now that the threats exist)
        target = targets[r.target_key]
        merchant = merchants[target.merchant_key]
        threat = await repo.get_threat_by_target(merchant.id, target.platform, target.handle)
        if threat is not None:
            await repo.insert_report(
                ReportCreate(
                    target_handle=target.handle,
                    platform=target.platform,
                    reported_phone=r.phone,  # type: ignore[arg-type]
                    description=r.description,
                ),
                report_id=seed_id("report", r.key),
                status=r.status,
                threat_id=threat.id,
                created_at=now - timedelta(days=r.days_ago),
            )
    return SeedResult(merchants=merchants, checks=checks, now=now)


# --- fixture export (frontend offline mode) -----------------------------------------------------


def _dump(model: Any) -> Any:
    if isinstance(model, list):
        return [_dump(m) for m in model]
    return model.model_dump(mode="json") if hasattr(model, "model_dump") else model


def _write_json(directory: Path, name: str, payload: Any) -> None:
    (directory / name).write_text(
        json.dumps(_dump(payload), indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


async def export_fixtures(
    repo: Repository, seed: SeedResult, settings: Settings, directory: Path, assets: dict[str, bytes]
) -> list[str]:
    """Write every API-contract fixture + assets + README into ``directory``. Returns the file names."""
    if directory.exists():
        shutil.rmtree(directory)
    (directory / "assets").mkdir(parents=True)
    for key, data in assets.items():
        (directory / "assets" / asset_name(key)).write_bytes(data)

    threshold, suspicious = settings.threat_threshold, settings.suspicious_threshold
    files: list[str] = []
    index: list[dict[str, Any]] = []
    targets = {t.key: t for t in TARGETS}
    for key, result in seed.checks.items():
        name = f"check-{key}.json"
        _write_json(directory, name, result)
        files.append(name)
        target = targets.get(key)
        handle = target.handle if target else result.target.handle
        index.append(
            {
                "key": key,
                "file": name,
                "scan_id": str(result.scan_id),
                "handle": handle,
                "platform": result.target.platform,
                "url": result.target.url,
                "verdict": result.verdict,
                "score": result.score,
                "kind": target.kind if target else "official",
                "merchant_slug": result.matched_merchant.slug if result.matched_merchant else None,
            }
        )
    _write_json(directory, "checks.json", index)
    files.append("checks.json")

    for m in MERCHANTS:
        record = seed.merchants[m.key]
        slug = record.slug
        _write_json(directory, f"merchant-{slug}.json", public_merchant(record))
        threats = await repo.list_threats(record.id, None)
        _write_json(
            directory, f"threats-{slug}.json", [threat_summary(t, threshold, suspicious) for t in threats]
        )
        for t in threats:
            scan = await repo.latest_scan_for_threat(t.id)
            latest = CheckResult.model_validate(scan.result) if scan else None
            detail = threat_detail(
                t, latest, record, await repo.list_remediations(t.id), threshold, suspicious
            )
            _write_json(directory, f"threat-{t.id}.json", detail)
            files.append(f"threat-{t.id}.json")
            for lang in ("en", "sw"):
                playbooks = await generate_playbooks(MemoryRepository(), t, record, lang, None)  # type: ignore[arg-type]
                _write_json(directory, f"playbooks-{t.id}-{lang}.json", playbooks)
                files.append(f"playbooks-{t.id}-{lang}.json")
        alerts = await repo.list_alerts(record.id, None, False, 50)
        by_id = {t.id: t for t in threats}
        _write_json(
            directory,
            f"alerts-{slug}.json",
            AlertsResponse(
                alerts=[
                    AlertOut(
                        **a.model_dump(exclude={"merchant_id"}),
                        threat=threat_summary(by_id[a.threat_id], threshold, suspicious)
                        if a.threat_id in by_id
                        else None,
                    )
                    for a in alerts
                ],
                unread_count=await repo.unread_count(record.id),
                server_time=seed.now,
            ),
        )
        _write_json(directory, f"stats-{slug}.json", await repo.stats(record.id))
        files += [
            f"merchant-{slug}.json",
            f"threats-{slug}.json",
            f"alerts-{slug}.json",
            f"stats-{slug}.json",
        ]
    _write_json(directory, "stats.json", await repo.stats(None))
    files.append("stats.json")

    lookups: dict[str, VerifyPaymentResult] = {}
    values = [*(m.data.mpesa_number or "" for m in MERCHANTS), *(r.phone for r in REPORTS), "889900"]
    for value in dict.fromkeys(values):
        lookups[value] = await verify_payment(repo, value)
    _write_json(directory, "verify-payment.json", {k: v.model_dump(mode="json") for k, v in lookups.items()})
    files.append("verify-payment.json")
    (directory / "README.md").write_text(_readme(files), encoding="utf-8")
    return sorted(files)


def _readme(files: list[str]) -> str:
    """README for the exported fixture folder (template: fixtures/seed_readme.md)."""
    template = string.Template(README_TEMPLATE.read_text(encoding="utf-8"))
    return template.substitute(seed_now=SEED_NOW.isoformat(), count=len(files))


# --- CLI ----------------------------------------------------------------------------------------


async def _run(target: str, reset: bool, export: bool) -> int:
    settings = get_settings()
    assets = write_assets()
    clip = ClipEmbedder(settings.enable_clip, settings.clip_model, settings.engine_device)
    clip.load()
    async with httpx.AsyncClient() as http:
        if target == "supabase":
            if not settings.supabase_configured:
                print("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY not set: skipping Supabase seeding.")
                return 0
            repo: Repository = SupabaseRepository.from_settings(
                settings.supabase_url, settings.supabase_service_role_key
            )
            if reset:
                await _reset_supabase(repo)  # type: ignore[arg-type]
        else:
            repo = MemoryRepository()
        service = CheckService(repo, settings, http, clip)
        seed = await seed_repository(repo, service, now=SEED_NOW, assets=assets)
        for key, result in seed.checks.items():
            print(f"{key:18} {result.verdict:14} {result.score:6.2f}  confidence {result.confidence:.2f}")
        if export:
            files = await export_fixtures(repo, seed, settings, FRONTEND_EXPORT_DIR, assets)
            print(f"Exported {len(files)} fixture files to {FRONTEND_EXPORT_DIR}")
    return 0


async def _reset_supabase(repo: SupabaseRepository) -> None:
    """Delete only seed rows (by deterministic id / natural key)."""
    merchant_ids = [str(seed_id("merchant", m.key)) for m in MERCHANTS]
    await repo.delete_rows("merchant_alerts", "merchant_id", merchant_ids)
    await repo.delete_rows(
        "scans",
        "id",
        [str(seed_id("scan", t.key)) for t in TARGETS]
        + [str(seed_id("scan", f"{m.key}_official")) for m in MERCHANTS],
    )
    await repo.delete_rows("community_reports", "id", [str(seed_id("report", r.key)) for r in REPORTS])
    await repo.delete_rows("threats", "merchant_id", merchant_ids)
    await repo.delete_rows("merchants", "id", merchant_ids)  # cascades to merchant_handles
    await repo.delete_rows("target_profiles", "handle", [t.handle for t in TARGETS])


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Seed Halisi with the fictional demo set.")
    parser.add_argument("--target", choices=["supabase", "memory"], default="memory")
    parser.add_argument("--reset", action="store_true", help="delete existing seed rows first (supabase)")
    parser.add_argument("--no-export", action="store_true", help="don't write the frontend fixtures")
    parser.add_argument("--export", action="store_true", help="also export fixtures after seeding supabase")
    args = parser.parse_args(argv)
    export = (args.target == "memory" and not args.no_export) or args.export
    return asyncio.run(_run(args.target, args.reset, export))


if __name__ == "__main__":
    sys.exit(main())
