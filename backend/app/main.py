from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import httpx
from app.core.config import settings
from app.core.repository import MemoryRepository, SupabaseRepository
from app.api.v1.router import router as api_v1_router
from app.core.logging import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup HTTP client
    app.state.http_client = httpx.AsyncClient(timeout=8.0, follow_redirects=True)
    
    # Initialize repository
    if settings.demo_mode:
        app.state.repo = MemoryRepository()
        logger.info("Starting in DEMO_MODE with MemoryRepository")
    else:
        app.state.repo = SupabaseRepository()
        
    # Warm up CLIP if enabled
    if settings.enable_clip:
        logger.info(f"Warming up CLIP model on {settings.engine_device}")
        # TODO: Add actual CLIP warm-up code here

    yield
    
    await app.state.http_client.aclose()

app = FastAPI(
    title="Halisi API",
    description="AI-Powered Brand Impersonation Detection",
    version="0.2.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.parsed_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DomainException(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code

@app.exception_handler(DomainException)
async def domain_exception_handler(request: Request, exc: DomainException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred"}}
    )

@app.get("/health")
def health_check():
    return {
        "status": "ok", 
        "version": "0.2.0", 
        "demo_mode": settings.demo_mode,
        "engine": { 
            "clip": "cuda" if settings.enable_clip else "disabled", 
            "hash": "ok" 
        }, 
        "llm": "nim-hosted" if settings.llm_enabled else "disabled", 
        "db": "ok"
    }

app.include_router(api_v1_router, prefix="/api/v1")
