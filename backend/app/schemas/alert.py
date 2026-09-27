"""Pydantic schemas for in-app merchant alerts (merchant_alerts table, schema v2.1)."""
from datetime import datetime
from uuid import UUID

from .common import BaseSchema
from .threat import ThreatSummary


class AlertCreate(BaseSchema):
    """Data required to insert a new alert row."""

    merchant_id: UUID
    threat_id: UUID
    kind: str  # "new_threat" | "score_increase" | "resolved"
    title: str
    body: str
    score: float


class AlertRecord(AlertCreate):
    """Hydrated alert row returned from the repository."""

    id: UUID
    created_at: datetime
    read_at: datetime | None = None
    threat: ThreatSummary | None = None


class AlertListResponse(BaseSchema):
    """Response envelope for GET /merchants/{id}/alerts."""

    alerts: list[AlertRecord]
    unread_count: int
    server_time: datetime


class AlertReadRequest(BaseSchema):
    """Body for POST /merchants/{id}/alerts/read."""

    ids: list[UUID] | None = None
    all: bool | None = False


class AlertReadResponse(BaseSchema):
    """Response for mark-read — echoes remaining unread count."""

    unread_count: int
