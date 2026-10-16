"""API v1 router (mounted at ``/api/v1``). Contract: docs/BACKEND.md section 5."""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, check, merchants, reports, threats
from app.channels.telegram import router as telegram_router
from app.channels.ussd import router as ussd_router

router = APIRouter()
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(check.router)
router.include_router(merchants.router)
router.include_router(threats.router)
router.include_router(reports.router)
router.include_router(telegram_router, prefix="/channels/telegram", tags=["channels"])
router.include_router(ussd_router)

