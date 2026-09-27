"""API v1 router — all endpoints for the Halisi API (BACKEND.md section 5).

The router wires the API contract to the repository and engine. Stub endpoints
return empty / fixture responses until the full engine integration is done.
"""

from datetime import datetime
from uuid import UUID

from dateutil.parser import isoparse
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from app.core.security import limiter, verify_api_key
from app.schemas.alert import AlertListResponse, AlertReadRequest, AlertReadResponse
from app.schemas.check import CheckRequest, CheckResult
from app.schemas.common import BaseSchema
from app.schemas.merchant import MerchantRecord, PaymentLookup
from app.schemas.remediation import PlaybooksRequest
from app.schemas.report import ReportCreate, ReportResponse, Stats
from app.schemas.threat import ThreatDetail, ThreatSummary

router = APIRouter()


class HealthResponse(BaseSchema):
    status: str
    version: str
    demo_mode: bool
    engine: dict[str, str]
    llm: str
    db: str


class SimulatorCloneRequest(BaseSchema):
    merchant_id: UUID
    tweaks: dict[str, object]


class ThreatStatusUpdate(BaseSchema):
    status: str


# ---------------------------------------------------------------------------
# Public endpoints
# ---------------------------------------------------------------------------


@router.post("/check", response_model=CheckResult)
@limiter.limit("10/minute")
async def check_target(request: Request, payload: CheckRequest):
    """Check a URL or handle for brand impersonation."""
    from app.ingestion.url_parser import parse_input  # lazy to avoid circular at module load

    if payload.url:
        parse_input(payload.url)
    elif payload.handle:
        parse_input("@" + payload.handle)
    elif payload.manual:
        pass
    else:
        raise HTTPException(status_code=422, detail="Missing url, handle, or manual input")

    return {
        "scan_id": "7b1c1d9e-2c1f-4b9a-9d0e-3f8a2c1e5b77",
        "verdict": "official",
        "score": 0.0,
        "confidence": 1.0,
        "target": {
            "platform": "instagram",
            "handle": "nairobi_sneakervault_official_ke",
            "fetched_via": "seed",
        },
    }


@router.get("/check/{scan_id}", response_model=CheckResult)
async def get_check(scan_id: UUID):
    """Re-open a shared result by scan ID."""
    return {}


@router.get("/verify/payment", response_model=PaymentLookup)
@limiter.limit("20/minute")
async def verify_payment(request: Request, value: str):
    """Verify whether a phone number or till is official, reported, or unknown.

    Response keys: kind, normalized, display, status, merchant, report_count, linked_threats.
    ``status`` is one of ``\"official\"`` | ``\"reported\"`` | ``\"unknown\"``.
    ``unknown`` means *not registered with Halisi*, **not** safe.
    """
    from app.engine.payment import canonical_phone, canonical_till

    phone = canonical_phone(value)
    till = canonical_till(value)
    if not phone and not till:
        raise HTTPException(status_code=422, detail="Invalid phone or till number")

    repo = request.app.state.repo
    return await repo.find_by_payment(phone=phone, till=till)


# ---------------------------------------------------------------------------
# Merchant endpoints
# ---------------------------------------------------------------------------


@router.get("/merchants/{slug}", response_model=MerchantRecord)
async def get_merchant(slug: str):
    """Public verified merchant profile (``/v/[slug]`` page)."""
    return {}


@router.post("/merchants", response_model=MerchantRecord)
async def onboard_merchant(api_key: str = Depends(verify_api_key)):
    """Onboard a merchant (multipart: JSON data + logo file)."""
    return {}


@router.get("/merchants/{id}/threats", response_model=list[ThreatSummary])
async def list_threats(
    id: UUID,
    status: str | None = None,
    api_key: str = Depends(verify_api_key),
):
    """Merchant threat feed sorted by composite score descending."""
    return []


@router.get("/merchants/{id}/alerts", response_model=AlertListResponse)
async def get_alerts(
    id: UUID,
    request: Request,
    since: str | None = None,
    unread: bool = True,
    api_key: str = Depends(verify_api_key),
):
    """In-app alerts polled every 5 s. Use ``since`` (ISO-8601 server_time) as cursor."""
    repo = request.app.state.repo
    since_dt = isoparse(since) if since else None
    alerts = await repo.list_alerts(merchant_id=id, since=since_dt, unread_only=unread, limit=20)
    # Unread count is always the global unread, not just the current page.
    all_unread = await repo.list_alerts(merchant_id=id, since=None, unread_only=True, limit=1000)
    return AlertListResponse(
        alerts=alerts,
        unread_count=len(all_unread),
        server_time=datetime.utcnow(),
    )


@router.post("/merchants/{id}/alerts/read", response_model=AlertReadResponse)
async def read_alerts(
    id: UUID,
    payload: AlertReadRequest,
    request: Request,
    api_key: str = Depends(verify_api_key),
):
    """Mark alerts read. Send ``{\"all\": true}`` or ``{\"ids\": [\"…\"]}``."""
    repo = request.app.state.repo
    ids_to_mark = payload.ids if (not payload.all and payload.ids) else None
    await repo.mark_alerts_read(merchant_id=id, ids=ids_to_mark)
    all_unread = await repo.list_alerts(merchant_id=id, since=None, unread_only=True, limit=1000)
    return AlertReadResponse(unread_count=len(all_unread))


# ---------------------------------------------------------------------------
# Threat endpoints (key)
# ---------------------------------------------------------------------------


@router.get("/threats/{id}", response_model=ThreatDetail)
async def get_threat(id: UUID, api_key: str = Depends(verify_api_key)):
    """Full threat detail including unmasked phone numbers."""
    return {}


@router.patch("/threats/{id}", response_model=ThreatDetail)
async def update_threat(
    id: UUID,
    payload: ThreatStatusUpdate,
    api_key: str = Depends(verify_api_key),
):
    """Update threat status (e.g. ``takedown_filed``)."""
    return {}


@router.post("/threats/{id}/playbooks", response_model=PlaybooksRequest)
async def generate_playbooks(
    id: UUID,
    lang: str = "en",
    api_key: str = Depends(verify_api_key),
):
    """Generate EN/SW remediation playbooks via NVIDIA NIM (TSK-009)."""
    return {}


# ---------------------------------------------------------------------------
# Community reports (public, 5/min/IP)
# ---------------------------------------------------------------------------


@router.post("/reports", response_model=ReportResponse)
@limiter.limit("5/minute")
async def create_report(request: Request, payload: ReportCreate):
    """Submit a community scam report. At least one of url/handle/phone/till is required.

    Returns ``{id, status: \"pending\"}``.
    """
    if not (
        payload.target_url
        or payload.target_handle
        or payload.reported_phone
        or payload.reported_till
    ):
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": (
                        "At least one of target_url, target_handle, reported_phone,"
                        " or reported_till is required"
                    ),
                }
            },
        )

    repo = request.app.state.repo
    report_id = await repo.insert_report(payload)
    return {"id": report_id, "status": "pending"}


# ---------------------------------------------------------------------------
# Stats & simulator
# ---------------------------------------------------------------------------


@router.get("/stats", response_model=Stats)
async def get_stats(merchant_id: UUID | None = None):
    """Global KPIs (no key) or per-merchant KPIs (key required for own data)."""
    return {
        "pages_scanned": 0,
        "threats_detected": 0,
        "impersonations_blocked_7d": 0,
        "merchants_protected": 0,
        "median_detection_ms": 0,
        "top_platforms": [],
    }


@router.post("/simulator/clone", response_model=CheckResult)
async def simulator_clone(
    payload: SimulatorCloneRequest,
    api_key: str = Depends(verify_api_key),
):
    """Demo: build a synthetic clone and run the real engine on it (TSK-031)."""
    return {}
