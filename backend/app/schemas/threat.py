"""Threat models: ``threats`` rows and the dashboard shapes (docs/BACKEND.md section 5.6)."""

from datetime import date, datetime
from uuid import UUID

from pydantic import Field

from app.schemas.check import CheckResult, ReasonOut
from app.schemas.common import BaseSchema, Language, PlaybookType, ThreatSource, ThreatStatus, Verdict


class StatusEvent(BaseSchema):
    """One entry of ``threats.status_history``."""

    status: ThreatStatus
    at: datetime


class ThreatUpsert(BaseSchema):
    """Insert-or-update payload, unique on (merchant_id, platform, target_handle)."""

    id: UUID | None = None
    merchant_id: UUID
    platform: str
    target_handle: str
    target_url: str
    display_name: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    avatar_phash: str | None = None
    avatar_dhash: str | None = None
    avatar_embedding: list[float] | None = None
    account_created_on: date | None = None
    follower_count: int | None = None
    post_count: int | None = None
    extracted_phones: list[str] = Field(default_factory=list)
    extracted_tills: list[str] = Field(default_factory=list)
    visual_score: float | None = None
    identity_score: float | None = None
    payment_score: float | None = None
    language_score: float | None = None
    account_score: float | None = None
    composite_score: float = Field(ge=0, le=100)
    confidence: float = Field(default=1.0, ge=0, le=1)
    reasons: list[dict] = Field(default_factory=list)
    source: ThreatSource = "public_checker"
    seen_at: datetime | None = None  # defaults to now; the seeder passes a fixed time


class ThreatRecord(BaseSchema):
    """A stored ``threats`` row."""

    id: UUID
    merchant_id: UUID
    platform: str
    target_handle: str
    target_url: str
    display_name: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    avatar_phash: str | None = None
    avatar_dhash: str | None = None
    avatar_embedding: list[float] | None = None
    account_created_on: date | None = None
    follower_count: int | None = None
    post_count: int | None = None
    extracted_phones: list[str] = Field(default_factory=list)
    extracted_tills: list[str] = Field(default_factory=list)
    visual_score: float | None = None
    identity_score: float | None = None
    payment_score: float | None = None
    language_score: float | None = None
    account_score: float | None = None
    composite_score: float
    confidence: float = 1.0
    reasons: list[dict] = Field(default_factory=list)
    status: ThreatStatus = "detected"
    source: ThreatSource = "public_checker"
    status_history: list[StatusEvent] = Field(default_factory=list)
    first_seen_at: datetime
    last_checked_at: datetime
    resolved_at: datetime | None = None


class ThreatSummary(BaseSchema):
    """Dashboard feed row, sorted by score desc."""

    id: UUID
    platform: str
    target_handle: str
    target_url: str
    avatar_url: str | None = None
    composite_score: float
    verdict: Verdict
    status: ThreatStatus
    first_seen_at: datetime
    top_reason: ReasonOut | None = None


class PlaybookLogEntry(BaseSchema):
    """One generated playbook (from ``remediation_logs``)."""

    playbook_type: PlaybookType
    language: Language
    generator: str
    prompt_id: str | None = None
    model: str | None = None
    created_at: datetime


class ThreatDetail(CheckResult):
    """Every ``CheckResult`` field (unmasked for the merchant) plus the threat's workflow state.

    ``scan_id`` / ``elapsed_ms`` come from the latest scan of this page (None if it has none).
    """

    scan_id: UUID | None = None  # type: ignore[assignment]
    elapsed_ms: int | None = None  # type: ignore[assignment]
    status: ThreatStatus
    status_history: list[StatusEvent] = Field(default_factory=list)
    extracted_phones: list[str] = Field(default_factory=list)
    extracted_tills: list[str] = Field(default_factory=list)
    playbooks_generated: list[PlaybookLogEntry] = Field(default_factory=list)
    first_seen_at: datetime
    last_checked_at: datetime
    resolved_at: datetime | None = None


class ThreatStatusUpdate(BaseSchema):
    """``PATCH /threats/{id}`` body."""

    status: ThreatStatus
