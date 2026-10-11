"""Threat endpoints (sections 5.6, 5.7): detail, status updates, remediation playbooks. All key-protected."""

import json
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Response

from app.alerts.dispatcher import dispatch_resolved_alert
from app.api.deps import ApiKey, get_llm, get_repo, get_settings
from app.core.config import Settings
from app.core.errors import NotFoundError
from app.core.repository import Repository
from app.schemas.check import CheckResult
from app.schemas.common import ErrorResponse
from app.schemas.remediation import PlaybooksResponse
from app.schemas.threat import ThreatDetail, ThreatRecord, ThreatStatusUpdate
from app.services.dossier import (
    build_evidence_bundle,
    compute_evidence_hash,
    generate_dossier_pdf,
    render_dossier_html,
)
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


@router.get("/threats/{threat_id}/playbook", response_model=PlaybooksResponse, responses=NOT_FOUND)
@router.get("/threats/{threat_id}/playbooks", response_model=PlaybooksResponse, responses=NOT_FOUND)
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


async def _build_dossier_response(
    repo: Repository,
    threat: ThreatRecord,
    format: Literal["pdf", "html", "json"],
) -> Response:
    merchant = await repo.get_merchant(threat.merchant_id)
    if merchant is None:
        raise NotFoundError("Merchant not found.")
    scan = await repo.latest_scan_for_threat(threat.id)
    bundle = build_evidence_bundle(threat, merchant, scan)
    evidence_hash = compute_evidence_hash(bundle)

    if format == "json":
        data = {**bundle, "evidence_hash": evidence_hash}
        content = json.dumps(data, indent=2, ensure_ascii=False, default=str).encode("utf-8")
        media_type = "application/json"
        filename = f"halisi-dossier-{threat.id}.json"
    elif format == "html":
        html = render_dossier_html(threat, merchant, bundle, evidence_hash)
        content = html.encode("utf-8")
        media_type = "text/html; charset=utf-8"
        filename = f"halisi-dossier-{threat.id}.html"
    else:  # pdf
        html = render_dossier_html(threat, merchant, bundle, evidence_hash)
        content = generate_dossier_pdf(html)
        media_type = "application/pdf"
        filename = f"halisi-dossier-{threat.id}.pdf"

    headers = {
        "X-Evidence-Hash": evidence_hash,
        "Content-Disposition": f'inline; filename="{filename}"',
    }
    return Response(content=content, media_type=media_type, headers=headers)


@router.get("/threats/{threat_id}/dossier", responses=NOT_FOUND)
async def get_threat_dossier(
    threat_id: UUID,
    repo: Annotated[Repository, Depends(get_repo)],
    format: Literal["pdf", "html", "json"] = "pdf",
) -> Response:
    """Fetch an evidence dossier for legal and platform escalation, stamped with SHA-256."""
    threat = await _threat(repo, threat_id)
    return await _build_dossier_response(repo, threat, format)


@router.get("/merchants/{merchant_id}/threats/{threat_id}/dossier", responses=NOT_FOUND)
async def get_merchant_threat_dossier(
    merchant_id: UUID,
    threat_id: UUID,
    repo: Annotated[Repository, Depends(get_repo)],
    format: Literal["pdf", "html", "json"] = "pdf",
) -> Response:
    """Fetch an evidence dossier scoped to a merchant, stamped with SHA-256."""
    threat = await _threat(repo, threat_id)
    if threat.merchant_id != merchant_id:
        raise NotFoundError("Threat does not belong to this merchant.")
    return await _build_dossier_response(repo, threat, format)

