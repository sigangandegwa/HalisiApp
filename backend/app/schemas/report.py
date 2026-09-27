"""Community reports, payment lookup and stats (docs/BACKEND.md sections 5.3, 5.8, 5.9)."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field, model_validator

from app.schemas.common import BaseSchema, Platform, ReportStatus
from app.schemas.merchant import MerchantRecord, PublicMerchant


class ReportCreate(BaseSchema):
    """``POST /reports`` body. At least one of url / handle / phone / till is required."""

    target_url: str | None = Field(default=None, max_length=2048)
    target_handle: str | None = Field(default=None, max_length=100)
    platform: Platform | None = None
    reported_phone: str | None = Field(default=None, max_length=30)
    reported_till: str | None = Field(default=None, max_length=20)
    description: str | None = Field(default=None, max_length=1000)
    reporter_contact: str | None = Field(default=None, max_length=200)

    @model_validator(mode="after")
    def _needs_a_target(self) -> "ReportCreate":
        if not any((self.target_url, self.target_handle, self.reported_phone, self.reported_till)):
            raise ValueError(
                "Provide at least one of target_url, target_handle, reported_phone, reported_till."
            )
        return self


class ReportRecord(BaseSchema):
    """A stored ``community_reports`` row. ``reporter_contact`` is never returned by any endpoint."""

    id: UUID
    target_url: str | None = None
    target_handle: str | None = None
    platform: str | None = None
    reported_phone: str | None = None
    reported_till: str | None = None
    description: str | None = None
    reporter_contact: str | None = None
    status: ReportStatus = "pending"
    threat_id: UUID | None = None
    created_at: datetime


class ReportCreated(BaseSchema):
    """``POST /reports`` response."""

    id: UUID
    status: ReportStatus = "pending"


class PaymentLookup(BaseSchema):
    """Repository answer for a phone/till: facts only (the API decides status and masking)."""

    merchant: MerchantRecord | None = None
    report_count: int = 0  # pending + confirmed (rejected reports are ignored)
    confirmed_reports: int = 0
    linked_threats: int = 0  # active impersonation threats whose page lists this number


class VerifyPaymentResult(BaseSchema):
    """``GET /verify/payment`` response. ``unknown`` means "not registered with Halisi", never "safe"."""

    kind: Literal["phone", "till"]
    normalized: str
    display: str
    status: Literal["official", "reported", "unknown"]
    merchant: PublicMerchant | None = None
    report_count: int
    linked_threats: int


class PlatformCount(BaseSchema):
    """``{platform, count}``."""

    platform: str
    count: int


class Stats(BaseSchema):
    """``GET /stats``. Merchant-only fields are None for the global view."""

    pages_scanned: int
    threats_detected: int
    impersonations_blocked_7d: int
    merchants_protected: int
    median_detection_ms: int
    top_platforms: list[PlatformCount] = Field(default_factory=list)
    active_threats: int | None = None
    resolved: int | None = None
    customers_warned_estimate: int | None = None  # count of checks that warned a user about this merchant
