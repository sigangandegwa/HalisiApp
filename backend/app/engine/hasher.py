"""Perceptual hashing and calibrated visual similarity (TSK-015, spec: docs/BACKEND.md section 6.2).

Pure functions: no network, no DB. Callers normalise images first with
``app.engine.imaging.normalize`` so a logo and an avatar are hashed under the same conditions.
"""

import math
import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

import imagehash
from PIL import Image

from app.engine.constants import (
    CLIP_FULL_MATCH_COSINE,
    CLIP_NO_MATCH_COSINE,
    HASH_BITS,
    HASH_FULL_MATCH_BITS,
    HASH_NO_MATCH_BITS,
    HASH_SIZE,
)

_HEX_HASH = re.compile(rf"^[0-9a-f]{{{HASH_BITS // 4}}}$")

VisualSignal = Literal["phash", "dhash", "clip"]


@dataclass(frozen=True, slots=True)
class ImageHashes:
    """64-bit perceptual (pHash) and difference (dHash) hashes as 16-char lowercase hex."""

    phash: str
    dhash: str


@dataclass(frozen=True, slots=True)
class ImageFeatures:
    """Everything the engine compares for one image. ``embedding`` is None when CLIP is disabled."""

    phash: str
    dhash: str
    embedding: Sequence[float] | None = None


@dataclass(frozen=True, slots=True)
class VisualResult:
    """Outcome of comparing a target avatar with a merchant logo."""

    score: float                    # 0-100, max of the available signal similarities
    signal: VisualSignal            # which signal produced ``score``
    phash_distance: int             # 0-64
    dhash_distance: int             # 0-64
    clip_cosine: float | None       # None when either side has no embedding
    evidence: str                   # e.g. "pHash distance 2/64 · dHash distance 3/64 · CLIP similarity 0.97"


def compute_hashes(image: Image.Image) -> ImageHashes:
    """Compute pHash and dHash for an already normalised image."""
    return ImageHashes(
        phash=str(imagehash.phash(image, hash_size=HASH_SIZE)),
        dhash=str(imagehash.dhash(image, hash_size=HASH_SIZE)),
    )


def hamming(a_hex: str, b_hex: str) -> int:
    """Number of differing bits between two 64-bit hex hashes (0-64).

    Raises:
        ValueError: if either value is not a 16-char hex hash. v1 silently returned 0.0 on bad
            input, which hid bugs; the caller should decide how to treat a missing hash.
    """
    a, b = _check_hash(a_hex), _check_hash(b_hex)
    return (int(a, 16) ^ int(b, 16)).bit_count()


def hash_similarity(
    distance: int, *, full: int = HASH_FULL_MATCH_BITS, zero: int = HASH_NO_MATCH_BITS
) -> float:
    """Map a Hamming distance to a 0-100 similarity: 100 at ``<= full``, 0 at ``>= zero``, linear between."""
    if not 0 <= distance <= HASH_BITS:
        raise ValueError(f"Hamming distance must be between 0 and {HASH_BITS}, got {distance}.")
    return _ramp(float(zero - distance), float(zero - full))


def clip_similarity(
    cosine: float, *, full: float = CLIP_FULL_MATCH_COSINE, zero: float = CLIP_NO_MATCH_COSINE
) -> float:
    """Map a CLIP cosine similarity to 0-100: 100 at ``>= full``, 0 at ``<= zero``, linear between."""
    return _ramp(cosine - zero, full - zero)


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    """Cosine similarity of two equal-length vectors. Returns 0.0 if either vector is all zeros."""
    if len(a) != len(b):
        raise ValueError(f"Embedding lengths differ: {len(a)} vs {len(b)}.")
    dot = math.fsum(x * y for x, y in zip(a, b, strict=True))
    norm = math.sqrt(math.fsum(x * x for x in a)) * math.sqrt(math.fsum(y * y for y in b))
    return dot / norm if norm else 0.0


def visual_score(target: ImageFeatures, reference: ImageFeatures) -> VisualResult:
    """Compare a target avatar with a merchant logo.

    The score is the best of pHash, dHash and (when both sides have embeddings) CLIP similarity.
    Each catches different edits: hashes catch exact and re-compressed copies, CLIP catches
    recoloured, cropped or re-drawn logos. Ties keep the cheaper, more explainable signal
    (pHash, then dHash, then CLIP).
    """
    phash_distance = hamming(target.phash, reference.phash)
    dhash_distance = hamming(target.dhash, reference.dhash)
    candidates: list[tuple[float, VisualSignal]] = [
        (hash_similarity(phash_distance), "phash"),
        (hash_similarity(dhash_distance), "dhash"),
    ]
    evidence = [
        f"pHash distance {phash_distance}/{HASH_BITS}",
        f"dHash distance {dhash_distance}/{HASH_BITS}",
    ]

    clip_cos: float | None = None
    if target.embedding is not None and reference.embedding is not None:
        clip_cos = cosine(target.embedding, reference.embedding)
        candidates.append((clip_similarity(clip_cos), "clip"))
        evidence.append(f"CLIP similarity {clip_cos:.2f}")

    score, signal = max(candidates, key=lambda c: c[0])   # max() keeps the first of equal scores
    return VisualResult(
        score=score,
        signal=signal,
        phash_distance=phash_distance,
        dhash_distance=dhash_distance,
        clip_cosine=None if clip_cos is None else round(clip_cos, 4),
        evidence=" · ".join(evidence),
    )


def _check_hash(value: str) -> str:
    """Return ``value`` lowercased if it is a valid 64-bit hex hash, else raise ValueError."""
    normalized = value.strip().lower() if isinstance(value, str) else ""
    if not _HEX_HASH.match(normalized):
        raise ValueError(f"Not a {HASH_BITS}-bit hex hash: {value!r}.")
    return normalized


def _ramp(numerator: float, span: float) -> float:
    """Clamp ``numerator / span`` to [0, 1] and scale to a 0-100 score rounded to 2 dp."""
    return round(max(0.0, min(1.0, numerator / span)) * 100.0, 2)
