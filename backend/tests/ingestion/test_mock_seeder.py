"""Mock seeder (TSK-007): real-engine scores, determinism, idempotency, both targets, fixture export."""

import json
from pathlib import Path

import httpx
import pytest

from app.core.repository import MemoryRepository, SupabaseRepository
from app.engine.embeddings import ClipEmbedder
from app.engine.hasher import hamming
from app.ingestion import mock_seeder as seeder
from app.schemas.check import CheckResult
from app.services.check import CheckService
from tests.conftest import make_settings
from tests.fakes import FakeSupabase


async def _seed(repo, tmp_path: Path):
    settings = make_settings(tmp_path)
    async with httpx.AsyncClient() as http:
        service = CheckService(repo, settings, http, ClipEmbedder(False))
        return await seeder.seed_repository(repo, service), service


async def test_verdicts_come_from_the_real_engine(tmp_path: Path) -> None:
    seed, _ = await _seed(MemoryRepository(), tmp_path)
    for target in seeder.TARGETS:
        result = seed.checks[target.key]
        assert result.verdict == target.expect, (target.key, result.score)
        if target.kind == "blatant":
            assert result.score >= 90 and result.confidence == 1.0
        elif target.kind == "subtle":
            assert result.score >= 70
        else:
            assert result.score < 40 and result.matched_merchant is None
    for m in seeder.MERCHANTS:
        assert seed.checks[f"{m.key}_official"].verdict == "official"


async def test_merchant_payment_types_and_numbers(tmp_path: Path) -> None:
    seed, _ = await _seed(MemoryRepository(), tmp_path)
    types = {
        k: (m.mpesa_type, bool(m.phone_numbers), bool(m.mpesa_account_name))
        for k, m in seed.merchants.items()
        if k in {"nsv", "kg", "pt"}
    }
    assert types == {"nsv": ("till", True, True), "kg": ("paybill", True, True), "pt": ("pochi", True, True)}
    assert all(len(seed.merchants[m.key].official_handles) == 2 for m in seeder.MERCHANTS)


async def test_curated_brands_are_public_data_only(tmp_path: Path) -> None:
    """Curated real brands: marked curated, official on their own handle, and no invented payment numbers."""
    seed, _ = await _seed(MemoryRepository(), tmp_path)
    curated = {c.key: seed.merchants[c.key] for c in seeder.CURATED}
    assert len(curated) == 9
    assert all(m.verification_status == "curated" and m.is_verified for m in curated.values())
    assert all(m.phone_numbers == [] for m in curated.values())          # never a personal number
    published = {k: m.mpesa_number for k, m in curated.items() if m.mpesa_number}
    assert published == {"kplc": "888880", "kcb": "522522", "equity": "247247", "dstv": "444900"}
    assert all(m.mpesa_type == "paybill" for k, m in curated.items() if k in published)
    assert all(m.mpesa_type == "none" for k, m in curated.items() if k not in published)
    for c in seeder.CURATED:
        assert seed.checks[f"{c.key}_official"].verdict == "official"
    raw = json.loads(seeder.CURATED_FILE.read_text(encoding="utf-8"))
    assert raw["collected_on"] == "2026-10-22"
    assert all(b["sources"] and b["confidence"] in {"high", "medium"} for b in raw["brands"])


def test_logos_are_distinct_and_clones_are_edited_copies() -> None:
    from app.engine.hasher import compute_hashes
    from app.engine.imaging import normalize

    h = {
        k: compute_hashes(normalize(f()))
        for k, f in {**seeder.L.MERCHANT_LOGOS, **seeder.L.COMPETITOR_LOGOS}.items()
    }
    keys = list(h)
    for i, a in enumerate(keys):
        for b in keys[i + 1 :]:
            assert hamming(h[a].phash, h[b].phash) >= 24, (a, b)  # unrelated logos -> visual 0
    for t in seeder.TARGETS:
        if t.kind == "blatant":
            logo = {"nsv": "sneaker", "kg": "glow", "pt": "threads"}[t.merchant_key]
            avatar = compute_hashes(normalize(t.image()))
            assert hamming(avatar.phash, h[logo].phash) <= 8  # an edited copy, not a new image


async def test_ids_are_deterministic_and_seeding_is_idempotent(tmp_path: Path) -> None:
    repo = MemoryRepository()
    first, service = await _seed(repo, tmp_path)
    counts = (
        len(repo.merchants),
        len(repo.threats),
        len(repo.scans),
        len(repo.reports),
        len(repo.alerts),
        len(repo.profiles),
    )
    assert counts == (12, 6, 21, 5, 6, 9)       # 3 fictional + 9 curated merchants
    again = await seeder.seed_repository(repo, service)
    assert (
        len(repo.merchants),
        len(repo.threats),
        len(repo.scans),
        len(repo.reports),
        len(repo.alerts),
        len(repo.profiles),
    ) == counts
    assert {k: r.scan_id for k, r in first.checks.items()} == {k: r.scan_id for k, r in again.checks.items()}
    assert first.merchants["nsv"].id == seeder.seed_id("merchant", "nsv")
    confirmed = [r for r in repo.reports.values() if r.status == "confirmed"]
    assert len(confirmed) == 2 and all(r.threat_id for r in repo.reports.values())


async def test_supabase_target_is_idempotent_too(tmp_path: Path) -> None:
    fake = FakeSupabase()
    repo = SupabaseRepository(fake)
    await _seed(repo, tmp_path)
    sizes = {name: len(rows) for name, rows in fake.tables.items()}
    await _seed(repo, tmp_path)
    assert {name: len(rows) for name, rows in fake.tables.items()} == sizes
    assert sizes["merchants"] == 12 and sizes["merchant_handles"] == 37 and sizes["threats"] == 6
    assert sizes["community_reports"] == 5 and sizes["merchant_alerts"] == 6 and sizes["target_profiles"] == 9


def test_supabase_cli_skips_cleanly_without_credentials(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    monkeypatch.setattr(
        seeder, "get_settings", lambda: make_settings(tmp_path, supabase_url="", supabase_service_role_key="")
    )
    assert seeder.main(["--target", "supabase"]) == 0
    assert "skipping" in capsys.readouterr().out


async def test_export_writes_contract_shaped_fixtures(tmp_path: Path) -> None:
    repo = MemoryRepository()
    seed, service = await _seed(repo, tmp_path)
    out = tmp_path / "seed"
    files = await seeder.export_fixtures(
        repo, seed, make_settings(tmp_path), out, seeder.render_assets(), service
    )
    assert (out / "README.md").exists() and (out / "assets" / "nsv_logo.png").exists()
    index = json.loads((out / "checks.json").read_text(encoding="utf-8"))
    assert len(index) == 21
    for entry in index:
        result = CheckResult.model_validate_json((out / entry["file"]).read_text(encoding="utf-8"))
        assert result.verdict == entry["verdict"]
    blatant = (out / "check-nsv_blatant.json").read_text(encoding="utf-8")
    assert "798999111" not in blatant and "0798 *** 111" in blatant  # public fixture is masked
    threats = json.loads((out / "threats-nairobi-sneaker-vault.json").read_text(encoding="utf-8"))
    assert [t["target_handle"] for t in threats] == [
        "nairobi_sneakervault_official_ke",
        "nairobisneakervau1t",
    ]
    detail = json.loads((out / f"threat-{threats[0]['id']}.json").read_text(encoding="utf-8"))
    assert detail["extracted_phones"] == ["+254798999111"]  # merchant fixture is unmasked
    alerts = json.loads((out / "alerts-nairobi-sneaker-vault.json").read_text(encoding="utf-8"))
    assert alerts["unread_count"] == 2 and alerts["alerts"][0]["threat"]["id"]
    verify = json.loads((out / "verify-payment.json").read_text(encoding="utf-8"))
    assert verify["543210"]["status"] == "official" and verify["+254798999111"]["status"] == "reported"
    assert verify["889900"]["status"] == "unknown"
    assert json.loads((out / "stats.json").read_text(encoding="utf-8"))["threats_detected"] == 6
    assert any(f.startswith("playbooks-") for f in files)

    # offline watchlist: generated look-alikes + the recorded scan, linked to seeded scans
    watch = json.loads((out / "watchlist-nairobi-sneaker-vault.json").read_text(encoding="utf-8"))
    instagram = next(h for h in watch["handles"] if h["platform"] == "instagram")
    assert "nairobisneakervau1t" in instagram["variants"]
    scan = json.loads((out / "watchlist-scan-nairobi-sneaker-vault.json").read_text(encoding="utf-8"))
    found = {f["handle"] for f in scan["findings"]}
    assert found == {"nairobi_sneakervault_official_ke", "nairobisneakervau1t"}
    seeded_scan_ids = {entry["scan_id"] for entry in index}
    assert all(f["scan_id"] in seeded_scan_ids for f in scan["findings"])
    assert json.loads((out / "watchlist-scan-kenya-power.json").read_text(encoding="utf-8"))["findings"] == []
