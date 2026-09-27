"""``POST /simulator/clone`` (TSK-031, BACKEND.md section 5.10): build a synthetic clone, score it for real.

Nothing is fabricated: the clone's avatar is an actual edit of the merchant's logo pixels, its bio is
real text run through the real extractors, and the score comes from ``score_against_all``.
The result is persisted with ``source = 'simulator'``.
"""

import base64
import io
from datetime import datetime, timedelta
from pathlib import Path

from PIL import Image

from app.core.config import Settings
from app.core.errors import InvalidInput
from app.core.repository import utcnow
from app.engine.hasher import ImageFeatures
from app.ingestion.fixtures import logos as L
from app.schemas.check import CheckRequest
from app.schemas.merchant import MerchantRecord
from app.schemas.simulator import SimulatorTweaks
from app.services.check import Acquired, CheckOutcome, CheckService

SIMULATOR_PHONE_LOCAL = "0799 000 111"  # synthetic demo input, masked in public output
SEED_ASSETS_DIR = Path(__file__).resolve().parents[1] / "ingestion" / "fixtures" / "assets"
_EDITS = {"recolor": L.recolor, "crop": L.crop, "jpeg": L.jpeg}


def clone_handle(merchant: MerchantRecord, style: str) -> str:
    """Synthetic look-alike handle. Chosen so it doesn't collide with the seeded clones."""
    base = next(
        (h.handle for h in merchant.official_handles if h.platform == "instagram"),
        merchant.official_handles[0].handle if merchant.official_handles else merchant.slug.replace("-", ""),
    )
    if style == "suffix":
        return f"{base}_official"[:60]
    if style == "underscore":
        return "_".join(merchant.business_name.lower().split())[:60]
    for old, new in (("o", "0"), ("l", "1"), ("i", "1"), ("e", "3"), ("a", "4")):
        if old in base:
            return base.replace(old, new, 1)
    return base + "_"


def clone_bio(merchant: MerchantRecord, tweaks: SimulatorTweaks) -> str:
    """Synthetic bio text for the clone."""
    parts = [f"Welcome to {merchant.business_name}."]
    if tweaks.payment == "phone":
        parts.append(f"Order and pay on {SIMULATOR_PHONE_LOCAL}.")
    elif tweaks.payment == "pochi":
        parts.append(f"Pochi la biashara {SIMULATOR_PHONE_LOCAL}.")
    if tweaks.bio_tokens:
        parts.append("Lipa kwanza, pay before delivery. Offer ends today!")
    return " ".join(parts)


def load_logo(merchant: MerchantRecord, settings: Settings) -> Image.Image | None:
    """The merchant's stored logo pixels (seed assets or onboarded media), if available locally."""
    url = merchant.logo_url or ""
    name = url.rsplit("/", 1)[-1]
    if not name or "/" in name or "\\" in name or name.startswith("."):
        return None
    if url.startswith("/seed/"):
        path = SEED_ASSETS_DIR / name
    elif url.startswith("/media/"):
        path = Path(settings.media_dir) / name
    else:
        return None
    if not path.is_file():
        return None
    with Image.open(path) as img:
        return img.convert("RGB")


def _thumbnail_data_url(img: Image.Image, side: int = 160) -> str:
    buf = io.BytesIO()
    img.resize((side, side), Image.Resampling.LANCZOS).save(buf, "PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


async def simulate_clone(
    service: CheckService, merchant: MerchantRecord, tweaks: SimulatorTweaks, *, now: datetime | None = None
) -> CheckOutcome:
    """Build and score a synthetic clone of ``merchant``."""
    now = now or utcnow()
    logo = load_logo(merchant, service.settings)
    avatar: ImageFeatures | None
    avatar_url = None
    if logo is not None:
        edited = logo if tweaks.logo == "exact" else _EDITS[tweaks.logo](logo)
        avatar = await service.features_from_bytes(L.png_bytes(edited))
        avatar_url = _thumbnail_data_url(edited)
    elif tweaks.logo == "exact" and merchant.logo_phash and merchant.logo_dhash:
        avatar = ImageFeatures(merchant.logo_phash, merchant.logo_dhash, merchant.logo_embedding)
    else:
        raise InvalidInput(
            "This merchant's logo image isn't available on this server, so only logo='exact' works."
        )

    style = tweaks.handle_style
    page = Acquired(
        display_name=f"{merchant.business_name} Official" if style == "suffix" else merchant.business_name,
        bio=clone_bio(merchant, tweaks),
        avatar_url=avatar_url,
        avatar=avatar,
        follower_count=60,
        post_count=4,
        account_created_on=(now - timedelta(days=3)).date(),
        fetched_via="simulator",
    )
    handle = clone_handle(merchant, style)
    page.url = f"https://instagram.com/{handle}"
    return await service.check(
        CheckRequest(handle=handle, platform="instagram"), source="simulator", now=now, acquired=page
    )
