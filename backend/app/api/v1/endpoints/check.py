"""``POST /check``, ``GET /check/{scan_id}``, ``GET /verify/payment`` (sections 5.2, 5.3)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query

from app.api.deps import CheckLimit, VerifyLimit, get_check_service, get_repo
from app.core.errors import NotFoundError
from app.core.repository import Repository
from app.schemas.check import CheckRequest, CheckResult
from app.schemas.common import ErrorResponse
from app.schemas.report import VerifyPaymentResult
from app.services.check import CheckService
from app.services.payments import verify_payment

router = APIRouter(tags=["public"])
ERRORS = {422: {"model": ErrorResponse}, 429: {"model": ErrorResponse}, 502: {"model": ErrorResponse}}


@router.post("/check", response_model=CheckResult, dependencies=[CheckLimit], responses=ERRORS)
async def check(
    body: CheckRequest,
    background: BackgroundTasks,
    service: Annotated[CheckService, Depends(get_check_service)],
) -> CheckResult:
    """Check a URL or handle. 502 ``TARGET_UNREACHABLE`` means: offer the manual fallback form."""
    outcome = await service.check(body)
    background.add_task(service.persist, outcome)
    return outcome.result


@router.get("/check/{scan_id}", response_model=CheckResult, responses={404: {"model": ErrorResponse}})
async def get_check(scan_id: UUID, repo: Annotated[Repository, Depends(get_repo)]) -> CheckResult:
    """Re-open a shared result."""
    scan = await repo.get_scan(scan_id)
    if scan is None:
        raise NotFoundError("Scan not found.")
    return CheckResult.model_validate(scan.result)


@router.get(
    "/verify/payment", response_model=VerifyPaymentResult, dependencies=[VerifyLimit], responses=ERRORS
)
async def verify(
    repo: Annotated[Repository, Depends(get_repo)],
    value: Annotated[str, Query(min_length=1, max_length=64)],
) -> VerifyPaymentResult:
    """Is this phone/till official, reported, or unknown ("not registered with Halisi")?"""
    return await verify_payment(repo, value)
