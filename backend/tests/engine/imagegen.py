"""Deterministic synthetic logos and clone-style edits for engine tests (no network, no files).

The generators live in ``app.ingestion.fixtures.logos`` so the seeder and the tests use identical pixels.
"""

from app.ingestion.fixtures.logos import (
    SIZE,
    crop,
    downscale,
    glow_logo,
    invert,
    jpeg,
    overlay_text,
    png_bytes,
    recolor,
    sneaker_logo,
    threads_logo,
)

ALL_LOGOS = {"sneaker": sneaker_logo, "glow": glow_logo, "threads": threads_logo}

__all__ = [
    "ALL_LOGOS",
    "SIZE",
    "crop",
    "downscale",
    "glow_logo",
    "invert",
    "jpeg",
    "overlay_text",
    "png_bytes",
    "recolor",
    "sneaker_logo",
    "threads_logo",
]
