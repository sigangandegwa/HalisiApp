"""Authentication endpoints for merchant dashboard session (contract: FRONTEND.md section 9.1)."""

import os
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.deps import get_repo, get_settings
from app.core.config import Settings
from app.core.errors import NotFoundError, UnauthorizedError
from app.core.repository import Repository
from app.schemas.auth import LoginRequest, LoginResponse, LogoutResponse

router = APIRouter(tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(
    payload: LoginRequest,
    repo: Annotated[Repository, Depends(get_repo)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> LoginResponse:
    expected = settings.dashboard_passcode or os.environ.get("DASHBOARD_PASSCODE") or "halisi-demo"
    if payload.passcode != expected:
        raise UnauthorizedError()

    if payload.identifier is None:
        raise NotFoundError("No registered business found matching that identifier.")

    clean = payload.identifier.strip()
    if not clean:
        raise NotFoundError("No registered business found matching that identifier.")

    handle_or_slug = clean.lower().lstrip("@")

    # 1. Try slug exact match
    merchant = await repo.get_merchant_by_slug(handle_or_slug)
    if not merchant:
        all_merchants = await repo.list_merchants()
        # 2. Search handles, case-insensitive business name, or slug
        merchant = next(
            (
                m
                for m in all_merchants
                if m.slug.lower() == handle_or_slug
                or m.business_name.strip().lower() == clean.lower()
                or any(h.handle.lower().lstrip("@") == handle_or_slug for h in m.official_handles)
            ),
            None,
        )

    if not merchant:
        raise NotFoundError("No registered business found matching that identifier.")

    return LoginResponse(
        ok=True,
        merchant_id=str(merchant.id),
        merchant_slug=merchant.slug,
        business_name=merchant.business_name,
    )


@router.post("/logout", response_model=LogoutResponse)
@router.delete("/logout", response_model=LogoutResponse)
async def logout() -> LogoutResponse:
    return LogoutResponse(ok=True, message="Logged out successfully")
