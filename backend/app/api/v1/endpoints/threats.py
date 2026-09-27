"""Threat endpoints (sections 5.6, 5.7): detail, status updates, remediation playbooks. All key-protected."""

from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends

from app.alerts.dispatcher import dispatch_resolved_alert
from app.api.deps import ApiKey, get_llm, get_repo, get_settings
from app.core.config import Settings
from app.core.errors import NotFoundError
from app.core.repository import Repository
from app.schemas.check import CheckResult
from app.schemas.common import ErrorResponse
from app.schemas.remediation import PlaybooksResponse
from app.schemas.threat import ThreatDetail, ThreatRecord, ThreatStatusUpdate
from app.services.remediation import LlmClient, generate_playbooks
from app.services.serializers import threat_detail

router = APIRouter(tags=["threats"], dependencies=[ApiKey])
NOT_FOUND = {404: {"model": ErrorResponse}}


async def _threat(repo: Repository, threat_id: UUID) -> ThreatRecord:
    threat = await repo.get_threat(threat_id)
    if threat is None:
        raise NotFoundError("Threat not found.")
    return threat


async def _detail(repo: Repository, threat: ThreatRecord, settings: Settings) -> ThreatDetail:
    scan = await repo.latest_scan_for_threat(threat.id)
    latest = CheckResult.model_validate(scan.result) if scan else None
    merchant = await repo.get_merchant(threat.merchant_id)
    return threat_detail(
        threat,
        latest,
        merchant,
        await repo.list_remediations(threat.id),
        settings.threat_threshold,
        settings.suspicious_threshold,
    )


@router.get("/threats/{threat_id}", response_model=ThreatDetail, responses=NOT_FOUND)
async def get_threat(
    threat_id: UUID,
    repo: Annotated[Repository, Depends(get_repo)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ThreatDetail:
    """Evidence board: the latest check result (unmasked numbers) plus workflow state."""
    return await _detail(repo, await _threat(repo, threat_id), settings)


@router.patch("/threats/{threat_id}", response_model=ThreatDetail, responses=NOT_FOUND)
async def update_threat(
    threat_id: UUID,
    body: ThreatStatusUpdate,
    repo: Annotated[Repository, Depends(get_repo)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ThreatDetail:
    """Move a threat through its workflow; ``resolved`` writes a ``resolved`` in-app alert."""
    before = await _threat(repo, threat_id)
    after = await repo.update_threat_status(threat_id, body.status)
    await dispatch_resolved_alert(repo, before, after)
    return await _detail(repo, after, settings)


@router.post("/threats/{threat_id}/playbooks", response_model=PlaybooksResponse, responses=NOT_FOUND)
async def playbooks(
    threat_id: UUID,
    repo: Annotated[Repository, Depends(get_repo)],
    llm: Annotated[LlmClient | None, Depends(get_llm)],
    lang: Literal["en", "sw"] = "en",
) -> PlaybooksResponse:
    """Draft the four remediation playbooks (LLM when available, validated; templates otherwise)."""
    threat = await _threat(repo, threat_id)
    merchant = await repo.get_merchant(threat.merchant_id)
    if merchant is None:
        raise NotFoundError("Merchant not found.")
    return await generate_playbooks(repo, threat, merchant, lang, llm)
