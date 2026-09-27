"""In-app merchant alerts (schema v2.1 ``merchant_alerts``, docs/BACKEND.md section 8)."""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.schemas.common import AlertKind, BaseSchema
from app.schemas.threat import ThreatSummary


class AlertCreate(BaseSchema):
    """A ``merchant_alerts`` row to insert."""

    id: UUID | None = None
    merchant_id: UUID
    threat_id: UUID
    kind: AlertKind
    title: str = Field(max_length=200)
    body: str = Field(max_length=500)
    score: float | None = None
    created_at: datetime | None = None


class AlertRecord(BaseSchema):
    """A stored alert."""

    id: UUID
    merchant_id: UUID
    threat_id: UUID
    kind: AlertKind
    title: str
    body: str
    score: float | None = None
    created_at: datetime
    read_at: datetime | None = None


class AlertOut(BaseSchema):
    """An alert with its threat summary embedded."""

    id: UUID
    threat_id: UUID
    kind: AlertKind
    title: str
    body: str
    score: float | None = None
    created_at: datetime
    read_at: datetime | None = None
    threat: ThreatSummary | None = None


class AlertsResponse(BaseSchema):
    """``GET /merchants/{id}/alerts``. Pass ``server_time`` back as ``since`` on the next poll."""

    alerts: list[AlertOut]
    unread_count: int
    server_time: datetime


class MarkReadRequest(BaseSchema):
    """``{"ids": [...]}`` or ``{"all": true}``."""

    ids: list[UUID] | None = Field(default=None, max_length=500)
    all: bool = False


class MarkReadResponse(BaseSchema):
    """Unread count after marking."""

    unread_count: int
