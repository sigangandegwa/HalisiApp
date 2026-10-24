"""API v1 router (mounted at ``/api/v1``). Contract: docs/BACKEND.md section 5.

Telegram and USSD channels are archived (docs/PRODUCT_V2.md section 9) and no longer routed.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, check, merchants, reports, threats

router = APIRouter()
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(check.router)
router.include_router(merchants.router)
router.include_router(threats.router)
router.include_router(reports.router)
