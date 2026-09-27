"""Takedown tracker (TSK-029): a 404 / "page isn't available" resolves the threat and alerts. respx only."""

from uuid import uuid4

import httpx
import respx

from app.core.repository import MemoryRepository
from app.ingestion.takedown_tracker import page_is_gone, run_once
from app.schemas.threat import ThreatUpsert


async def resolve_public(host: str) -> list[str]:
    return ["157.240.1.174"]


def _threat(merchant_id, handle: str) -> ThreatUpsert:
    return ThreatUpsert(
        merchant_id=merchant_id,
        platform="instagram",
        target_handle=handle,
        target_url=f"https://instagram.com/{handle}",
        composite_score=92,
    )


@respx.mock
async def test_gone_pages_are_resolved() -> None:
    repo = MemoryRepository()
    merchant_id = uuid4()
    gone = await repo.upsert_threat(_threat(merchant_id, "gone_page"))
    unavailable = await repo.upsert_threat(_threat(merchant_id, "unavailable_page"))
    alive = await repo.upsert_threat(_threat(merchant_id, "alive_page"))
    untracked = await repo.upsert_threat(_threat(merchant_id, "untracked_page"))
    for t in (gone, unavailable, alive):
        await repo.update_threat_status(t.id, "takedown_filed")
    respx.get("https://instagram.com/gone_page").mock(return_value=httpx.Response(404))
    respx.get("https://instagram.com/unavailable_page").mock(
        return_value=httpx.Response(200, text="<h2>Sorry, this page isn't available.</h2>")
    )
    respx.get("https://instagram.com/alive_page").mock(
        return_value=httpx.Response(200, text="<html>profile</html>")
    )

    async with httpx.AsyncClient() as http:
        resolved = await run_once(repo, http, resolver=resolve_public)
    assert set(resolved) == {gone.id, unavailable.id}
    assert (await repo.get_threat(gone.id)).resolved_at is not None
    assert (await repo.get_threat(alive.id)).status == "takedown_filed"
    assert (await repo.get_threat(untracked.id)).status == "detected"
    assert {a.kind for a in repo.alerts.values()} == {"resolved"}


@respx.mock
async def test_blocked_or_failing_fetch_is_unknown() -> None:
    respx.get("https://instagram.com/x").mock(return_value=httpx.Response(429))
    respx.get("https://instagram.com/y").mock(side_effect=httpx.ConnectError("down"))
    async with httpx.AsyncClient() as http:
        assert await page_is_gone(http, "https://instagram.com/x", resolver=resolve_public) is None
        assert await page_is_gone(http, "https://instagram.com/y", resolver=resolve_public) is None
