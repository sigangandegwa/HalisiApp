"""Halisi API app factory (docs/BACKEND.md sections 2-3, 10).

``uvicorn app.main:app`` starts with the settings from the environment. With ``DEMO_MODE=true`` the
app uses a MemoryRepository seeded through the real engine and makes no network calls at all.
"""

import asyncio
import contextlib
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from PIL import Image

from app.api.v1.router import router as api_v1_router
from app.core.config import DEFAULT_API_KEY, Settings, get_settings
from app.core.errors import install_error_handlers
from app.core.logging import setup_logging
from app.core.repository import MemoryRepository, Repository, SupabaseRepository, utcnow
from app.core.security import RateLimiter, Resolver, system_resolver
from app.engine.embeddings import ClipEmbedder
from app.engine.hasher import compute_hashes
from app.ingestion import mock_seeder
from app.ingestion.takedown_tracker import tracker_loop
from app.schemas.simulator import EngineHealth, HealthResponse
from app.services.check import CheckService
from app.services.remediation import LlmClient, NimClient

VERSION = "0.2.0"
MAX_BODY_BYTES = 8 * 1024 * 1024  # 5 MB image + base64 overhead + JSON
log = logging.getLogger("halisi")


def _llm_status(settings: Settings) -> str:
    if settings.demo_mode:
        return "templates (demo mode)"
    if not settings.llm_enabled:
        return "disabled"
    if not settings.llm_api_key:
        return "templates (no LLM_API_KEY)"
    return "nim-hosted" if "nvidia.com" in settings.llm_base_url else "nim-self-hosted"


def _hash_self_test() -> str:
    try:
        compute_hashes(Image.new("RGB", (32, 32), (255, 255, 255)))
        return "ok"
    except Exception:  # noqa: BLE001
        return "error"


def create_app(
    settings: Settings | None = None,
    *,
    repo: Repository | None = None,
    clip: ClipEmbedder | None = None,
    llm: LlmClient | None = None,
    resolver: Resolver = system_resolver,
    http_transport: httpx.AsyncBaseTransport | None = None,
    seed: bool | None = None,
) -> FastAPI:
    """Build the FastAPI app. Tests inject settings, a repository, a fake CLIP model, an LLM and transports.

    Args:
        seed: seed a MemoryRepository with the demo set (default: no repo injected and in-memory).
    """
    settings = settings or get_settings()
    setup_logging()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        http = httpx.AsyncClient(
            timeout=settings.fetch_timeout_seconds, follow_redirects=False, transport=http_transport
        )
        repository: Repository
        if repo is not None:
            repository = repo
        elif settings.demo_mode or not settings.supabase_configured:
            if not settings.demo_mode:
                log.warning("Supabase is not configured: using the in-memory demo repository")
            repository = MemoryRepository()
        else:
            repository = SupabaseRepository.from_settings(
                settings.supabase_url, settings.supabase_service_role_key
            )
        engine = clip or ClipEmbedder(settings.enable_clip, settings.clip_model, settings.engine_device)
        await asyncio.to_thread(engine.warm_up)

        service = CheckService(repository, settings, http, engine, resolver=resolver)
        app.state.settings = settings
        app.state.repo = repository
        app.state.clip = engine
        app.state.http = http
        app.state.check_service = service
        app.state.rate_limiter = RateLimiter()
        app.state.hash_status = _hash_self_test()
        app.state.llm = llm if llm is not None else (NimClient(settings) if settings.llm_available else None)
        if settings.api_key == DEFAULT_API_KEY and settings.app_env == "production":
            log.warning("API_KEY is still the example value: set a long random key")

        should_seed = (
            seed if seed is not None else (repo is None and isinstance(repository, MemoryRepository))
        )
        if should_seed:
            assets = await asyncio.to_thread(mock_seeder.write_assets)
            await mock_seeder.seed_repository(repository, service, now=utcnow(), assets=assets)

        tracker: asyncio.Task[None] | None = None
        if settings.enable_takedown_tracker and not settings.demo_mode:
            tracker = asyncio.create_task(tracker_loop(repository, http, settings.takedown_check_hours))
        try:
            yield
        finally:
            if tracker is not None:
                tracker.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await tracker
            await http.aclose()

    app = FastAPI(
        title="Halisi API",
        description="Brand-impersonation detection for Kenyan businesses",
        version=VERSION,
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
        allow_headers=["Content-Type", "X-Halisi-Key"],
    )

    @app.middleware("http")
    async def limit_body_size(request: Request, call_next):  # type: ignore[no-untyped-def]
        """Reject oversized bodies early (images are capped at 5 MB)."""
        length = request.headers.get("content-length")
        if length and length.isdigit() and int(length) > MAX_BODY_BYTES:
            return JSONResponse(
                status_code=413,
                content={"error": {"code": "PAYLOAD_TOO_LARGE", "message": "Request is too large."}},
            )
        response: Response = await call_next(request)
        return response

    install_error_handlers(app)

    @app.get("/health", response_model=HealthResponse, tags=["health"])
    async def health(request: Request) -> HealthResponse:
        """Liveness and engine status (section 5.1)."""
        state = request.app.state
        try:
            db = await state.repo.ping()
        except Exception as exc:  # noqa: BLE001
            log.warning("health: db ping failed: %r", exc)
            db = "error"
        hash_status = getattr(state, "hash_status", "error")
        ok = db != "error" and hash_status == "ok"
        return HealthResponse(
            status="ok" if ok else "degraded",
            version=VERSION,
            demo_mode=settings.demo_mode,
            engine=EngineHealth(clip=state.clip.status, hash=hash_status),
            llm=_llm_status(settings),
            db=db,
        )

    app.include_router(api_v1_router, prefix="/api/v1")
    mock_seeder.ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    app.mount("/seed", StaticFiles(directory=mock_seeder.ASSETS_DIR), name="seed-assets")
    settings.media_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/media", StaticFiles(directory=settings.media_dir), name="media")
    return app


app = create_app()
