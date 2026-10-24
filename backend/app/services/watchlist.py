"""Typosquat watchlist: generate a merchant's likely look-alike handles and probe the ones that exist.

TSK-047, docs/PRODUCT_V2.md section 6. Probing goes through the normal ``check`` pipeline, so a hit is
scored, becomes a threat and raises the in-app alert exactly like a public check would.

Cost control: a variant whose profile Halisi already knows (seeded, or fetched before) is checked for
free. Variants that would need a live fetch share a small budget, so one click can't hammer a platform.
"""

import asyncio
from dataclasses import dataclass, field

from app.core.errors import HalisiError
from app.engine.variants import handle_variants
from app.schemas.check import CheckRequest
from app.schemas.merchant import (
    MerchantRecord,
    Watchlist,
    WatchlistFinding,
    WatchlistHandle,
    WatchlistScan,
)
from app.services.check import CheckService

LIVE_PROBE_BUDGET = 40
CONCURRENCY = 4
FLAG_VERDICTS = ("impersonation", "suspicious")
SCANNABLE_PLATFORMS = ("instagram", "tiktok", "facebook", "x")


def build_watchlist(merchant: MerchantRecord) -> Watchlist:
    """Likely look-alikes for every official handle of a merchant (no network)."""
    handles = [
        WatchlistHandle(
            platform=h.platform,
            handle=h.handle,
            variants=handle_variants(h.handle, merchant.business_name),
        )
        for h in merchant.official_handles
        if h.platform in SCANNABLE_PLATFORMS
    ]
    return Watchlist(merchant_id=merchant.id, handles=handles)


@dataclass
class _Tally:
    probed: int = 0
    resolved: int = 0
    unreachable: int = 0
    live_used: int = 0
    exhausted: bool = False
    findings: list[WatchlistFinding] = field(default_factory=list)


async def scan_watchlist(service: CheckService, merchant: MerchantRecord) -> WatchlistScan:
    """Probe every variant that resolves and report the ones that look like impersonation of ``merchant``."""
    watchlist = build_watchlist(merchant)
    tally = _Tally()
    live_allowed = not service.settings.demo_mode and service.settings.scraper_enabled
    gate = asyncio.Semaphore(CONCURRENCY)

    async def probe(platform: str, handle: str) -> None:
        known = await service.repo.get_target_profile(platform, handle)
        if known is None:
            if not live_allowed:
                return
            if tally.live_used >= LIVE_PROBE_BUDGET:
                tally.exhausted = True
                return
            tally.live_used += 1
        async with gate:
            tally.probed += 1
            try:
                outcome = await service.check(CheckRequest(handle=handle, platform=platform))  # type: ignore[arg-type]
            except HalisiError:
                tally.unreachable += 1
                return
        tally.resolved += 1
        result = outcome.result
        mine = result.matched_merchant is not None and result.matched_merchant.id == merchant.id
        if mine and result.verdict in FLAG_VERDICTS:
            await service.persist(outcome)
            tally.findings.append(
                WatchlistFinding(
                    platform=platform,
                    handle=handle,
                    verdict=result.verdict,
                    score=result.score,
                    scan_id=result.scan_id,
                    threat_id=result.threat_id,
                )
            )

    await asyncio.gather(*(probe(h.platform, v) for h in watchlist.handles for v in h.variants))
    tally.findings.sort(key=lambda f: -f.score)
    return WatchlistScan(
        merchant_id=merchant.id,
        variants_generated=sum(len(h.variants) for h in watchlist.handles),
        probed=tally.probed,
        resolved=tally.resolved,
        unreachable=tally.unreachable,
        budget_exhausted=tally.exhausted,
        findings=tally.findings,
    )
