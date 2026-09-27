"""In-app alert dispatcher (TSK-012, docs/BACKEND.md section 8.1). No Telegram, no SMS.

Pure DB work, so it behaves identically on the MemoryRepository (DEMO_MODE) and Supabase.

Rules:
* threat created with composite >= threshold                       -> ``new_threat``
* existing threat's score rose by >= 10, or crossed the threshold   -> ``score_increase``
* threat moved to ``resolved``                                       -> ``resolved``
* de-duplication: at most one alert per threat per ``ALERT_DEDUP_HOURS`` unless the score rose
* ``false_positive`` threats never alert
* title/body never contain phone numbers (notifications can show on lock screens)
"""

import re
import uuid
from datetime import datetime, timedelta
from uuid import UUID

from app.core.repository import Repository, utcnow
from app.schemas.alert import AlertCreate, AlertRecord
from app.schemas.threat import ThreatRecord

SCORE_RISE = 10.0
_PHONE_LIKE = re.compile(r"\+?\d[\d\s*-]{6,}\d")


def _top_reason_text(threat: ThreatRecord) -> str:
    """Plain-language body: the top reason, with anything number-like removed."""
    text = str(threat.reasons[0].get("text", "")) if threat.reasons else ""
    text = _PHONE_LIKE.sub("a number", text).strip()
    return text or f"A page is imitating your business (score {threat.composite_score:.0f})."


def decide_kind(before: ThreatRecord | None, after: ThreatRecord, threshold: float) -> str | None:
    """Which alert (if any) a threat upsert should produce."""
    if after.status == "false_positive":
        return None
    if before is None:
        return "new_threat" if after.composite_score >= threshold else None
    if before.status == "false_positive":
        return None
    rose = after.composite_score - before.composite_score >= SCORE_RISE
    crossed = before.composite_score < threshold <= after.composite_score
    return "score_increase" if (rose or crossed) and after.composite_score >= threshold else None


async def dispatch_threat_alert(
    repo: Repository,
    before: ThreatRecord | None,
    after: ThreatRecord,
    *,
    threshold: float,
    dedup_hours: float,
    now: datetime | None = None,
) -> AlertRecord | None:
    """Write at most one ``merchant_alerts`` row for a threat upsert. Returns the alert or None."""
    kind = decide_kind(before, after, threshold)
    if kind is None:
        return None
    now = now or utcnow()
    last = await repo.last_alert_for_threat(after.id)
    if kind == "new_threat" and last is not None and now - last.created_at < timedelta(hours=dedup_hours):
        return None
    handle = f"@{after.target_handle}"
    title = (
        f"Impersonator detected: {handle}"
        if kind == "new_threat"
        else f"Score rose to {after.composite_score:.0f}: {handle}"
    )
    return await repo.insert_alert(
        AlertCreate(
            id=alert_id_for(after.id, kind, now),
            merchant_id=after.merchant_id,
            threat_id=after.id,
            kind=kind,  # type: ignore[arg-type]
            title=title[:200],
            body=_top_reason_text(after)[:500],
            score=after.composite_score,
            created_at=now,
        )
    )


async def dispatch_resolved_alert(
    repo: Repository, before: ThreatRecord, after: ThreatRecord, *, now: datetime | None = None
) -> AlertRecord | None:
    """``resolved`` alert when a threat moves into ``resolved``."""
    if before.status == "resolved" or after.status != "resolved":
        return None
    now = now or utcnow()
    return await repo.insert_alert(
        AlertCreate(
            id=alert_id_for(after.id, "resolved", now),
            merchant_id=after.merchant_id,
            threat_id=after.id,
            kind="resolved",
            title=f"Resolved: @{after.target_handle}"[:200],
            body="This page has been marked as resolved.",
            score=after.composite_score,
            created_at=now,
        )
    )


def alert_id_for(threat_id: UUID, kind: str, at: datetime) -> UUID:
    """Deterministic alert id (same threat + kind + time -> same row), so re-seeding is idempotent."""
    return uuid.uuid5(threat_id, f"{kind}:{at.isoformat()}")
