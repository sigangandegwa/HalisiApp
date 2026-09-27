from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import os

class Settings(BaseSettings):
    app_env: str = "development"
    demo_mode: bool = False
    api_key: str = "change-me-long-random"
    cors_origins: str = "http://localhost:3000"
    public_check_rate_limit: str = "10/minute"

    supabase_url: str = ""
    supabase_service_role_key: str = ""

    enable_clip: bool = False
    engine_device: str = "auto"
    clip_model: str = "clip-ViT-B-32"
    threat_threshold: int = 70
    suspicious_threshold: int = 40

    llm_enabled: bool = True
    llm_base_url: str = "https://integrate.api.nvidia.com/v1"
    llm_api_key: str = ""
    llm_model: str = "meta/llama-3.1-8b-instruct"
    llm_timeout_seconds: int = 12

    telegram_bot_token: str = ""
    at_username: str = "sandbox"
    at_api_key: str = ""
    at_sender_id: str = ""

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding='utf-8',
        extra='ignore'
    )

    @property
    def parsed_cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

settings = Settings()
