"""Remediation playbooks (docs/BACKEND.md sections 5.7 and 6.9) and ``remediation_logs`` rows."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from app.schemas.common import BaseSchema, Language, PlaybookType

Generator = Literal["llm", "template"]


class RemediationCreate(BaseSchema):
    """A ``remediation_logs`` row to insert."""

    threat_id: UUID
    playbook_type: PlaybookType
    language: Language = "en"
    generated_content: str
    generator: Generator
    prompt_id: str | None = None
    model: str | None = None
    dispatched_to: str | None = None


class RemediationRecord(RemediationCreate):
    """A stored ``remediation_logs`` row."""

    id: UUID
    created_at: datetime
    dispatched_at: datetime | None = None


class ConsumerWarning(BaseSchema):
    """Story / WhatsApp warning for customers."""

    title: str
    body: str
    whatsapp_share_url: str
    generator: Generator = "template"


class PlatformTakedown(BaseSchema):
    """Text for the platform's public impersonation report form."""

    platform: str
    report_url: str
    body: str
    generator: Generator = "template"


class SafaricomReport(BaseSchema):
    """Report of the receiving number/till. ``to`` is a placeholder until verified (constants.VERIFIED_ON)."""

    channel: str
    to: str
    subject: str
    body: str
    generator: Generator = "template"


class KecirtReport(BaseSchema):
    """Incident report to National KE-CIRT/CC. ``to`` is a placeholder until verified."""

    to: str
    subject: str
    body: str
    generator: Generator = "template"


class PlaybooksResponse(BaseSchema):
    """``POST /threats/{id}/playbooks``. ``generator`` is "llm" only when all four came from the LLM."""

    generator: Generator
    model: str | None
    language: Language
    prompt_ids: list[str]
    consumer_warning: ConsumerWarning
    platform_takedown: PlatformTakedown
    safaricom_report: SafaricomReport
    kecirt_report: KecirtReport
    contacts_verified: bool = False  # False while constants.VERIFIED_ON is None: merchant must confirm
