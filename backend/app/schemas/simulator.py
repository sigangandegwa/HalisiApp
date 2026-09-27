"""``POST /simulator/clone`` request (docs/BACKEND.md section 5.10) and ``/health`` response."""

from typing import Literal
from uuid import UUID

from app.schemas.common import BaseSchema


class SimulatorTweaks(BaseSchema):
    """How the synthetic clone is built."""

    handle_style: Literal["suffix", "homoglyph", "underscore"] = "suffix"
    logo: Literal["exact", "recolor", "crop", "jpeg"] = "exact"
    payment: Literal["phone", "pochi", "none"] = "phone"
    bio_tokens: bool = True


class SimulatorRequest(BaseSchema):
    """Which merchant to clone and how."""

    merchant_id: UUID
    tweaks: SimulatorTweaks = SimulatorTweaks()


class EngineHealth(BaseSchema):
    """Engine status: ``clip`` is cuda / cpu / disabled / error; ``hash`` is ok / error."""

    clip: str
    hash: str


class HealthResponse(BaseSchema):
    """``GET /health`` (section 5.1)."""

    status: Literal["ok", "degraded"]
    version: str
    demo_mode: bool
    engine: EngineHealth
    llm: str
    db: str
