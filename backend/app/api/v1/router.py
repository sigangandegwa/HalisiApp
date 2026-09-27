"""API v1 router (mounted at ``/api/v1``). Contract: docs/BACKEND.md section 5."""

from fastapi import APIRouter

from app.api.v1.endpoints import check, merchants, reports, threats

router = APIRouter()
router.include_router(check.router)
router.include_router(merchants.router)
router.include_router(threats.router)
router.include_router(reports.router)
