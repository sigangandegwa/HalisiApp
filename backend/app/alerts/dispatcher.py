"""Alert dispatcher: writes merchant_alerts rows after upsert_threat.

Runs in FastAPI BackgroundTasks — pure DB work, no external calls.
Works identically with SupabaseRepository and MemoryRepository (DEMO_MODE).
"""
from datetime import UTC, datetime, timedelta

from app.core.config import settings
from app.core.repository import Repository
from app.schemas.alert import AlertCreate
from app.schemas.threat import ThreatRecord


async def dispatch_alert(
    repo: Repository,
    previous_threat: ThreatRecord | None,
    current_threat: ThreatRecord,
) -> None:
    """Dispatch an in-app alert row when a notable threat event occurs.

    Trigger conditions (§8.1):
    - Threat is newly created with composite ≥ THREAT_THRESHOLD → ``new_threat``
    - Existing threat's score rises ≥ 10 or crosses the threshold → ``score_increase``
    - Threat transitions to ``resolved`` → ``resolved``

    De-duplication: at most one alert per threat per ALERT_DEDUP_HOURS (default 6),
    unless the score rose (score_increase bypasses the window).
    """
    threat_threshold: float = float(settings.threat_threshold)
    dedup_hours: int = getattr(settings, "alert_dedup_hours", 6)

    kind: str | None = None
    title: str = ""

    if (
        current_threat.status == "resolved"
        and (previous_threat is None or previous_threat.status != "resolved")
    ):
        # Threat just became resolved.
        kind = "resolved"
        title = f"Threat resolved: @{current_threat.target_handle}"
    elif previous_threat is None:
        # Brand-new threat — fire if it clears the threshold.
        if current_threat.composite_score >= threat_threshold:
            kind = "new_threat"
            title = f"Impersonator detected: @{current_threat.target_handle}"
    else:
        # Existing threat: check for meaningful score movement.
        crossed = (
            previous_threat.composite_score < threat_threshold
            and current_threat.composite_score >= threat_threshold
        )
        rose = current_threat.composite_score >= previous_threat.composite_score + 10
        if crossed or rose:
            kind = "score_increase"
            title = (
                f"Score rose to {current_threat.composite_score}:"
                f" @{current_threat.target_handle}"
            )

    if not kind:
        return

    # De-duplication: skip if a recent alert for this threat exists,
    # UNLESS the score actually rose (score_increase always fires).
    if kind != "score_increase":
        last_alert = await repo.last_alert_for_threat(current_threat.id)
        if last_alert:
            now = datetime.now(UTC)
            # Normalise stored timestamp to aware if necessary.
            last_ts = last_alert.created_at
            if last_ts.tzinfo is None:
                last_ts = last_ts.replace(tzinfo=UTC)
            if now - last_ts < timedelta(hours=dedup_hours):
                return

    # Body: top reason's plain-text (no phone numbers — lock-screen safe).
    body = "A new threat has been detected."
    if current_threat.reasons:
        top_reason = current_threat.reasons[0]
        body = top_reason.get("text", body)

    alert = AlertCreate(
        merchant_id=current_threat.merchant_id,
        threat_id=current_threat.id,
        kind=kind,
        title=title,
        body=body,
        score=current_threat.composite_score,
    )
    await repo.insert_alert(alert)
