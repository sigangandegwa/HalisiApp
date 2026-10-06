"""Application settings (pydantic-settings), read from the environment and ``backend/.env``.

See ``backend/.env.example`` for every variable. Telegram / Africa's Talking settings were dropped
on 2026-09-27: alerts are in-app only (docs/BACKEND.md section 8).
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
DEFAULT_API_KEY = "change-me-long-random"


class Settings(BaseSettings):
    """All runtime configuration. Field names map to upper-case env vars (``DEMO_MODE`` ...)."""

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    # --- app ---
    app_env: str = "development"
    demo_mode: bool = False
    api_key: str = DEFAULT_API_KEY
    cors_origins: str = "http://localhost:3000"
    public_check_rate_limit: str = "10/minute"
    verify_payment_rate_limit: str = "20/minute"
    report_rate_limit: str = "5/minute"
    rate_limit_enabled: bool = True
    trust_forwarded_for: bool = True   # true behind Render/cloud proxies to read X-Forwarded-For
    media_dir: Path = BACKEND_DIR / "media"  # onboarded merchant logos (served at /media)
    public_base_url: str = ""  # optional absolute prefix for asset URLs

    # --- supabase ---
    supabase_url: str = ""
    supabase_service_role_key: str = ""

    # --- engine ---
    enable_clip: bool = True
    engine_device: str = "cpu"  # auto | cuda | cpu
    clip_model: str = "clip-ViT-B-32"
    threat_threshold: float = 70.0
    suspicious_threshold: float = 40.0

    # --- ingestion ---
    scraper_enabled: bool = True  # tier-2 OpenGraph fetch (always off in DEMO_MODE)
    fetch_timeout_seconds: float = 5.0
    image_timeout_seconds: float = 8.0
    profile_cache_seconds: int = 600

    # --- LLM remediation (NVIDIA NIM, OpenAI-compatible) ---
    llm_enabled: bool = True
    llm_base_url: str = "https://integrate.api.nvidia.com/v1"
    llm_api_key: str = ""
    llm_model: str = "meta/llama-3.1-8b-instruct"
    llm_timeout_seconds: float = 12.0

    # --- in-app alerts ---
    alert_dedup_hours: float = 6.0

    # --- takedown tracker (TSK-029, P2) ---
    enable_takedown_tracker: bool = False
    takedown_check_hours: float = 12.0

    @property
    def cors_origins_list(self) -> list[str]:
        """``CORS_ORIGINS`` parsed as a comma-separated list. ``*`` is never allowed (credentials are on)."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip() and o.strip() != "*"]

    @property
    def parsed_cors_origins(self) -> list[str]:
        """Backwards-compatible alias of :attr:`cors_origins_list`."""
        return self.cors_origins_list

    @property
    def supabase_configured(self) -> bool:
        """Whether Supabase credentials are present."""
        return bool(self.supabase_url and self.supabase_service_role_key)

    @property
    def llm_available(self) -> bool:
        """Whether LLM calls may be made (never in DEMO_MODE, never without a key)."""
        return self.llm_enabled and bool(self.llm_api_key) and not self.demo_mode


@lru_cache
def get_settings() -> Settings:
    """Process-wide settings singleton (tests override it through ``app.dependency_overrides``)."""
    return Settings()


settings = get_settings()
