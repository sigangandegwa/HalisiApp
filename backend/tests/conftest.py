"""Shared fixtures: DEMO_MODE settings, a seeded app + TestClient, API-key headers. No network anywhere."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app

API_KEY = "test-key-0123456789"
AUTH = {"X-Halisi-Key": API_KEY}


def make_settings(tmp_path: Path, **overrides: object) -> Settings:
    """Isolated DEMO_MODE settings (ignores any backend/.env)."""
    values: dict[str, object] = {
        "demo_mode": True,
        "api_key": API_KEY,
        "rate_limit_enabled": False,
        "media_dir": tmp_path / "media",
        "cors_origins": "http://localhost:3000",
        "llm_enabled": False,
        "enable_clip": False,
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)  # type: ignore[call-arg]


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return make_settings(tmp_path)


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    """Seeded DEMO_MODE app (MemoryRepository loaded through the real engine)."""
    with TestClient(create_app(settings)) as test_client:
        yield test_client


@pytest.fixture
def auth() -> dict[str, str]:
    return dict(AUTH)
