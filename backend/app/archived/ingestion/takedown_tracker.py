"""Takedown tracker (TSK-029, P2, docs/BACKEND.md section 9).

Re-fetches threats in ``advisory_sent`` / ``takedown_filed`` every ``TAKEDOWN_CHECK_HOURS``. A 404 or
a "page isn't available" response marks the threat ``resolved`` (``resolved_at`` set, a ``resolved``
alert written), which gives the dashboard its time-to-takedown.

Runs as a plain asyncio task in the API process (``ENABLE_TAKEDOWN_TRACKER=true``). The spec named
APScheduler; a single periodic coroutine does the same job without another dependency.
Never runs in DEMO_MODE (no network).
"""

import asyncio
import logging
from uuid import UUID

import httpx

from app.alerts.dispatcher import dispatch_resolved_alert
from app.core.repository import Repository
from app.core.security import Resolver, system_resolver
from app.ingestion.page_scraper import MAX_HTML_BYTES, FetchError, safe_get

log = logging.getLogger("halisi.takedown")
TRACKED_STATUSES = ("advisory_sent", "takedown_filed")
GONE_MARKERS = (
    "sorry, this page isn't available",
    "this page isn't available",
    "this content isn't available",
    "couldn't find this account",
    "this account doesn't exist",
    "page not found",
)


async def page_is_gone(
    http: httpx.AsyncClient, url: str, *, resolver: Resolver = system_resolver
) -> bool | None:
    """True if the page is gone, False if it is still up, None if we can't tell (blocked, network error)."""
    try:
        _, response, body = await safe_get(
            http, url, max_bytes=MAX_HTML_BYTES, timeout=8.0, resolver=resolver
        )
    except FetchError:
        return None
    if response.status_code in (404, 410):
        return True
    if response.status_code != 200:
        return None
    text = body[:200_000].decode("utf-8", errors="replace").lower()
    return any(marker in text for marker in GONE_MARKERS)


async def run_once(
    repo: Repository, http: httpx.AsyncClient, *, resolver: Resolver = system_resolver
) -> list[UUID]:
    """Check every tracked threat once; returns the ids that were resolved."""
    resolved: list[UUID] = []
    for threat in await repo.list_threats_by_status(TRACKED_STATUSES):
        gone = await page_is_gone(http, threat.target_url, resolver=resolver)
        if gone:
            after = await repo.update_threat_status(threat.id, "resolved")
            await dispatch_resolved_alert(repo, threat, after)
            resolved.append(threat.id)
    return resolved


async def tracker_loop(repo: Repository, http: httpx.AsyncClient, interval_hours: float) -> None:
    """Run :func:`run_once` forever (cancelled on shutdown)."""
    while True:
        try:
            done = await run_once(repo, http)
            if done:
                log.info("takedown tracker resolved %d threat(s)", len(done))
        except Exception as exc:  # noqa: BLE001 - keep the loop alive
            log.warning("takedown tracker run failed: %r", exc)
        await asyncio.sleep(interval_hours * 3600)
