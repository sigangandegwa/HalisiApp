"""Shared Pydantic v2 base classes and enumerations (mirror database/schema.sql v2.2)."""

from typing import Literal

from pydantic import BaseModel, ConfigDict

Platform = Literal["instagram", "facebook", "tiktok", "x", "whatsapp", "website"]
Verdict = Literal["official", "impersonation", "suspicious", "no_match", "error"]
ThreatStatus = Literal["detected", "advisory_sent", "takedown_filed", "resolved", "false_positive"]
ThreatSource = Literal["public_checker", "scheduled", "community_report", "simulator", "seed"]
ScanSource = Literal["public_checker", "scheduled", "simulator", "seed"]
InputKind = Literal["url", "handle", "phone", "till"]
MpesaType = Literal["till", "paybill", "pochi", "none"]
AlertKind = Literal["new_threat", "score_increase", "resolved"]
ReportStatus = Literal["pending", "confirmed", "rejected"]
Language = Literal["en", "sw"]
PlaybookType = Literal["consumer_warning", "platform_takedown", "safaricom_report", "kecirt_report"]
FetchedVia = Literal["seed", "opengraph", "manual", "simulator", "none"]

PLATFORMS: tuple[str, ...] = ("instagram", "facebook", "tiktok", "x", "whatsapp", "website")
HANDLE_PATTERN = r"^[a-z0-9._]{1,60}$"


class BaseSchema(BaseModel):
    """Base for every schema: ORM-friendly, populated by field name."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ErrorDetail(BaseSchema):
    """``{"code": "...", "message": "..."}``."""

    code: str
    message: str


class ErrorResponse(BaseSchema):
    """Every error response: ``{"error": {"code", "message"}}`` (docs/BACKEND.md section 3)."""

    error: ErrorDetail
