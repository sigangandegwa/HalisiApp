from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from uuid import UUID

from app.core.security import limiter, verify_api_key
from app.schemas.check import CheckRequest, CheckResult
from app.schemas.merchant import MerchantRecord, MerchantCreate, PaymentLookup
from app.schemas.threat import ThreatSummary, ThreatDetail
from app.schemas.report import ReportCreate, ReportResponse, Stats
from app.schemas.remediation import PlaybooksRequest
from app.schemas.common import BaseSchema
from app.ingestion.url_parser import parse_input

router = APIRouter()

class HealthResponse(BaseSchema):
    status: str
    version: str
    demo_mode: bool
    engine: Dict[str, str]
    llm: str
    db: str

class SimulatorCloneRequest(BaseSchema):
    merchant_id: UUID
    tweaks: Dict[str, Any]

class ThreatStatusUpdate(BaseSchema):
    status: str

class ReadAlertsRequest(BaseSchema):
    ids: Optional[List[UUID]] = None
    all: Optional[bool] = None

class ReadAlertsResponse(BaseSchema):
    unread_count: int

class AlertsResponse(BaseSchema):
    alerts: List[Dict[str, Any]]
    unread_count: int
    server_time: str

@router.post("/check", response_model=CheckResult)
@limiter.limit("10/minute")
async def check_target(request: Request, payload: CheckRequest):
    """Check a URL or handle"""
    if payload.url:
        parsed = parse_input(payload.url)
    elif payload.handle:
        parsed = parse_input("@" + payload.handle)
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
            "fetched_via": "seed"
        }
    }

@router.get("/check/{scan_id}", response_model=CheckResult)
async def get_check(scan_id: UUID):
    """Re-open a shared result"""
    return {}

@router.get("/verify/payment", response_model=PaymentLookup)
@limiter.limit("20/minute")
async def verify_payment(request: Request, value: str):
    """Is this phone/till official or reported?"""
    return {"kind": "phone", "normalized": "+254712345678", "display": "0712 *** 678", "status": "unknown", "report_count": 0, "linked_threats": 0}

@router.get("/merchants/{slug}", response_model=MerchantRecord)
async def get_merchant(slug: str):
    """Public verified profile"""
    return {}

@router.post("/merchants", response_model=MerchantRecord)
async def onboard_merchant(api_key: str = Depends(verify_api_key)):
    """Onboard merchant (multipart: JSON + logo file)"""
    return {}

@router.get("/merchants/{id}/threats", response_model=List[ThreatSummary])
async def list_threats(id: UUID, status: Optional[str] = None, api_key: str = Depends(verify_api_key)):
    """Dashboard feed"""
    return []

@router.get("/merchants/{id}/alerts", response_model=AlertsResponse)
async def get_alerts(id: UUID, since: Optional[str] = None, unread: bool = True, api_key: str = Depends(verify_api_key)):
    """In-app alerts (polled every 5 s)"""
    return {"alerts": [], "unread_count": 0, "server_time": "2026-09-27T00:00:00Z"}

@router.post("/merchants/{id}/alerts/read", response_model=ReadAlertsResponse)
async def read_alerts(id: UUID, payload: ReadAlertsRequest, api_key: str = Depends(verify_api_key)):
    """Mark alerts read"""
    return {"unread_count": 0}

@router.get("/threats/{id}", response_model=ThreatDetail)
async def get_threat(id: UUID, api_key: str = Depends(verify_api_key)):
    """Threat detail"""
    return {}

@router.patch("/threats/{id}", response_model=ThreatDetail)
async def update_threat(id: UUID, payload: ThreatStatusUpdate, api_key: str = Depends(verify_api_key)):
    """Update status"""
    return {}

@router.post("/threats/{id}/playbooks", response_model=PlaybooksRequest)
async def generate_playbooks(id: UUID, lang: str = "en", api_key: str = Depends(verify_api_key)):
    """Generate remediation playbooks"""
    return {}

@router.post("/reports", response_model=ReportResponse)
@limiter.limit("5/minute")
async def create_report(request: Request, payload: ReportCreate):
    """Community scam report"""
    return {"id": "00000000-0000-0000-0000-000000000000", "status": "pending"}

@router.get("/stats", response_model=Stats)
async def get_stats(merchant_id: Optional[UUID] = None):
    """KPIs"""
    return {"pages_scanned": 0, "threats_detected": 0, "impersonations_blocked_7d": 0, "merchants_protected": 0, "median_detection_ms": 0, "top_platforms": []}

@router.post("/simulator/clone", response_model=CheckResult)
async def simulator_clone(payload: SimulatorCloneRequest, api_key: str = Depends(verify_api_key)):
    """Demo: build and score a synthetic clone"""
    return {}
