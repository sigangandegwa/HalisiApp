"""Merchant endpoints (sections 5.4-5.6, 8.2): public profile, onboarding, threat feed, in-app alerts."""

import asyncio
import json
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from pydantic import ValidationError

from app.api.deps import ApiKey, get_check_service, get_repo, get_settings
from app.core.config import Settings
from app.core.errors import ConflictError, InvalidImage, InvalidInput, NotFoundError
from app.core.repository import Conflict, Repository, utcnow
from app.engine import imaging
from app.engine.constants import MAX_IMAGE_BYTES
from app.ingestion.fixtures.logos import png_bytes
from app.schemas.alert import AlertOut, AlertsResponse, MarkReadRequest, MarkReadResponse
from app.schemas.common import ErrorResponse, ThreatStatus
from app.schemas.merchant import LogoFeatures, MerchantCreate, MerchantCreated, PublicMerchant
from app.schemas.threat import ThreatSummary
from app.services.check import CheckService
from app.services.serializers import public_merchant, threat_summary

router = APIRouter(tags=["merchants"])
ALLOWED_LOGO_TYPES = {"image/png", "image/jpeg", "image/webp"}


async def _merchant_or_404(repo: Repository, merchant_id: UUID) -> None:
    if await repo.get_merchant(merchant_id) is None:
        raise NotFoundError("Merchant not found.")


@router.get("/merchants/{slug}", response_model=PublicMerchant, responses={404: {"model": ErrorResponse}})
async def get_public_merchant(slug: str, repo: Annotated[Repository, Depends(get_repo)]) -> PublicMerchant:
    """Public verified profile (``/v/[slug]``)."""
    merchant = await repo.get_merchant_by_slug(slug.lower()[:60])
    if merchant is None:
        raise NotFoundError("Merchant not found.")
    return public_merchant(merchant)


@router.post(
    "/merchants",
    response_model=MerchantCreated,
    status_code=201,
    dependencies=[ApiKey],
    responses={409: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
async def onboard_merchant(
    data: Annotated[str, Form(max_length=20_000, description="MerchantCreate JSON")],
    logo: Annotated[UploadFile, File(description="PNG/JPEG/WebP <= 5 MB")],
    repo: Annotated[Repository, Depends(get_repo)],
    service: Annotated[CheckService, Depends(get_check_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> MerchantCreated:
    """Onboard a merchant: the server computes the logo pHash, dHash and (if enabled) CLIP embedding."""
    try:
        payload = MerchantCreate.model_validate(json.loads(data))
    except (json.JSONDecodeError, ValidationError) as exc:
        raise InvalidInput(f"Invalid merchant data: {str(exc)[:200]}") from exc
    if logo.content_type not in ALLOWED_LOGO_TYPES:
        raise InvalidImage("The logo must be a PNG, JPEG or WebP image.")
    raw = await logo.read(MAX_IMAGE_BYTES + 1)
    if len(raw) > MAX_IMAGE_BYTES:
        raise InvalidImage("The logo is larger than 5 MB.")
    features = await service.features_from_bytes(raw)

    try:
        normalised = await asyncio.to_thread(imaging.normalize_image, raw)
    except imaging.InvalidImage as exc:
        raise InvalidImage(str(exc)) from exc
    media = settings.media_dir
    media.mkdir(parents=True, exist_ok=True)
    filename = f"{payload.slug}-{features.phash}.png"
    await asyncio.to_thread((media / filename).write_bytes, png_bytes(normalised))

    try:
        record = await repo.create_merchant(
            payload,
            LogoFeatures(
                phash=features.phash,
                dhash=features.dhash,
                embedding=list(features.embedding) if features.embedding else None,
            ),
            logo_url=f"/media/{filename}",
        )
    except Conflict as exc:
        raise ConflictError(exc.message, code=exc.code) from exc
    service.merchants.invalidate()
    return MerchantCreated(
        **public_merchant(record).model_dump(),
        logo_phash=features.phash,
        logo_dhash=features.dhash,
        clip=features.embedding is not None,
    )


@router.get(
    "/merchants/{merchant_id}/threats",
    response_model=list[ThreatSummary],
    dependencies=[ApiKey],
    responses={404: {"model": ErrorResponse}},
)
async def list_threats(
    merchant_id: UUID,
    repo: Annotated[Repository, Depends(get_repo)],
    settings: Annotated[Settings, Depends(get_settings)],
    status: ThreatStatus | None = None,
) -> list[ThreatSummary]:
    """Dashboard feed, highest score first."""
    await _merchant_or_404(repo, merchant_id)
    threats = await repo.list_threats(merchant_id, status)
    return [threat_summary(t, settings.threat_threshold, settings.suspicious_threshold) for t in threats]


@router.get(
    "/merchants/{merchant_id}/alerts",
    response_model=AlertsResponse,
    dependencies=[ApiKey],
    responses={404: {"model": ErrorResponse}},
)
async def list_alerts(
    merchant_id: UUID,
    repo: Annotated[Repository, Depends(get_repo)],
    settings: Annotated[Settings, Depends(get_settings)],
    since: datetime | None = None,
    unread: bool = False,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> AlertsResponse:
    """In-app alerts, newest first. Poll every 5 s passing the previous ``server_time`` as ``since``."""
    await _merchant_or_404(repo, merchant_id)
    server_time = utcnow()
    alerts = await repo.list_alerts(merchant_id, since, unread, limit)
    out: list[AlertOut] = []
    for alert in alerts:
        threat = await repo.get_threat(alert.threat_id)
        summary = (
            threat_summary(threat, settings.threat_threshold, settings.suspicious_threshold)
            if threat
            else None
        )
        out.append(AlertOut(**alert.model_dump(exclude={"merchant_id"}), threat=summary))
    return AlertsResponse(
        alerts=out, unread_count=await repo.unread_count(merchant_id), server_time=server_time
    )


@router.post(
    "/merchants/{merchant_id}/alerts/read",
    response_model=MarkReadResponse,
    dependencies=[ApiKey],
    responses={404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
async def mark_alerts_read(
    merchant_id: UUID, body: MarkReadRequest, repo: Annotated[Repository, Depends(get_repo)]
) -> MarkReadResponse:
    """``{"ids": [...]}`` or ``{"all": true}``."""
    await _merchant_or_404(repo, merchant_id)
    if not body.all and body.ids is None:
        raise InvalidInput("Send either 'ids' or 'all: true'.")
    unread = await repo.mark_alerts_read(merchant_id, None if body.all else body.ids)
    return MarkReadResponse(unread_count=unread)
