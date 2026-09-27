"""Community reports, stats and the simulator (sections 5.8-5.10)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Request

from app.api.deps import ApiKey, ReportLimit, get_check_service, get_repo
from app.core.errors import NotFoundError, Unauthorized
from app.core.repository import Repository
from app.core.security import has_valid_api_key
from app.schemas.check import CheckResult
from app.schemas.common import ErrorResponse
from app.schemas.report import ReportCreate, ReportCreated, Stats
from app.schemas.simulator import SimulatorRequest
from app.services.check import CheckService
from app.services.simulator import simulate_clone

router = APIRouter()


@router.post(
    "/reports",
    response_model=ReportCreated,
    status_code=201,
    dependencies=[ReportLimit],
    tags=["public"],
    responses={422: {"model": ErrorResponse}, 429: {"model": ErrorResponse}},
)
async def create_report(body: ReportCreate, repo: Annotated[Repository, Depends(get_repo)]) -> ReportCreated:
    """Community scam report. Stored as ``pending``; only ``confirmed`` reports affect scores (O3)."""
    report_id = await repo.insert_report(body)
    return ReportCreated(id=report_id, status="pending")


@router.get("/stats", response_model=Stats, tags=["public"], responses={401: {"model": ErrorResponse}})
async def stats(
    request: Request, repo: Annotated[Repository, Depends(get_repo)], merchant_id: UUID | None = None
) -> Stats:
    """Global KPIs (public); per-merchant KPIs need the API key."""
    if merchant_id is not None:
        if not has_valid_api_key(request):
            raise Unauthorized()
        if await repo.get_merchant(merchant_id) is None:
            raise NotFoundError("Merchant not found.")
    return await repo.stats(merchant_id)


@router.post(
    "/simulator/clone",
    response_model=CheckResult,
    dependencies=[ApiKey],
    tags=["demo"],
    responses={404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
async def simulator_clone(
    body: SimulatorRequest,
    background: BackgroundTasks,
    repo: Annotated[Repository, Depends(get_repo)],
    service: Annotated[CheckService, Depends(get_check_service)],
) -> CheckResult:
    """Build a synthetic clone of a merchant and score it with the real engine (persisted as 'simulator')."""
    merchant = await repo.get_merchant(body.merchant_id)
    if merchant is None:
        raise NotFoundError("Merchant not found.")
    outcome = await simulate_clone(service, merchant, body.tweaks)
    background.add_task(service.persist, outcome)
    return outcome.result
