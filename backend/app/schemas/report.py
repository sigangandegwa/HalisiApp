from pydantic import Field
from typing import Optional
from datetime import datetime
from uuid import UUID
from .common import BaseSchema

class ReportCreate(BaseSchema):
    target_url: Optional[str] = None
    target_handle: Optional[str] = None
    platform: Optional[str] = None
    reported_phone: Optional[str] = None
    reported_till: Optional[str] = None
    description: Optional[str] = Field(None, max_length=1000)
    reporter_contact: Optional[str] = None

class ReportResponse(BaseSchema):
    id: UUID
    status: str = "pending"

class Stats(BaseSchema):
    pages_scanned: int
    threats_detected: int
    impersonations_blocked_7d: int
    merchants_protected: int
    median_detection_ms: int
    top_platforms: list[dict]
    active_threats: Optional[int] = None
    resolved: Optional[int] = None
    customers_warned_estimate: Optional[int] = None
