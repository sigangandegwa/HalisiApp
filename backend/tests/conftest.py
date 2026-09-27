"""Root test fixtures (BACKEND.md section 12).

Provides a ``client`` fixture backed by ``MemoryRepository`` seeded from
``backend/app/ingestion/fixtures/``.  All API tests share this fixture so no
test touches the network or Supabase.
"""

import os

import pytest
from fastapi.testclient import TestClient

# Force DEMO_MODE before any app module is imported so that the FastAPI
# lifespan picks up MemoryRepository and never tries to reach Supabase.
os.environ.setdefault("DEMO_MODE", "true")

from app.core.repository import MemoryRepository  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.main import app  # noqa: E402

# Patch settings at module level so even if Settings was already constructed
# it reflects demo_mode=True.
settings.demo_mode = True


@pytest.fixture()
def mem_repo() -> MemoryRepository:
    """A fresh MemoryRepository loaded from the committed fixtures JSON files."""
    return MemoryRepository()


@pytest.fixture()
def client(mem_repo: MemoryRepository) -> TestClient:
    """Synchronous TestClient with MemoryRepository injected into app.state.

    We set ``app.state.repo`` before the TestClient context manager starts so
    the lifespan sees it and does not create a SupabaseRepository.  After
    startup we overwrite it again with our fresh fixture-seeded instance in
    case the lifespan re-created it.
    """
    app.state.repo = mem_repo
    with TestClient(app, raise_server_exceptions=True) as c:
        # Overwrite again in case the lifespan recreated it.
        app.state.repo = mem_repo
        yield c
