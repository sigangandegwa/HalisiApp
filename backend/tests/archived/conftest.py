"""Fixtures for archived features: their routers are mounted on a test app only, never on the live one."""

from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.archived.channels.telegram import router as telegram_router
from app.archived.channels.ussd import router as ussd_router
from app.core.config import Settings
from app.main import create_app


def mount_archived_routers(app: FastAPI) -> FastAPI:
    """Mount the archived USSD and Telegram routers at their old paths (/api/v1/channels/...)."""
    app.include_router(ussd_router, prefix="/api/v1")
    app.include_router(telegram_router, prefix="/api/v1/channels/telegram")
    return app


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    """Seeded DEMO_MODE app with the archived routers mounted."""
    with TestClient(mount_archived_routers(create_app(settings))) as test_client:
        yield test_client
