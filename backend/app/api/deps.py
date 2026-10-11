"""FastAPI dependencies: app-scoped settings, repository and services (set up in ``main.lifespan``)."""

from fastapi import Depends, Request

from app.core.config import Settings
from app.core.repository import Repository
from app.core.security import rate_limit, require_api_key
from app.ingestion.daraja import DarajaClient
from app.ingestion.meta_rights import MetaRightsManagerClient
from app.services.check import CheckService
from app.services.remediation import LlmClient


def get_settings(request: Request) -> Settings:
    """The app's settings."""
    return request.app.state.settings


def get_repo(request: Request) -> Repository:
    """The app's repository."""
    return request.app.state.repo


def get_check_service(request: Request) -> CheckService:
    """The app's check pipeline."""
    return request.app.state.check_service


def get_daraja_client(request: Request) -> DarajaClient:
    """The app's Daraja client."""
    client = getattr(request.app.state, "daraja", None)
    if client is not None:
        return client
    return DarajaClient(request.app.state.settings, http=getattr(request.app.state, "http", None))


def get_meta_rights_client(request: Request) -> MetaRightsManagerClient:
    """The app's Meta Rights Manager client."""
    client = getattr(request.app.state, "meta_rights", None)
    if client is not None:
        return client
    return MetaRightsManagerClient(
        request.app.state.settings,
        http_client=getattr(request.app.state, "http", None),
    )


def get_llm(request: Request) -> LlmClient | None:
    """The LLM client, or None (DEMO_MODE, disabled, or no key): templates only."""
    return request.app.state.llm


ApiKey = Depends(require_api_key)
CheckLimit = Depends(rate_limit("public_check_rate_limit", "check"))
VerifyLimit = Depends(rate_limit("verify_payment_rate_limit", "verify_payment"))
ReportLimit = Depends(rate_limit("report_rate_limit", "reports"))
