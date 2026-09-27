"""``/check`` models (docs/BACKEND.md section 5.2), scans and cached target profiles."""

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import Field, model_validator

from app.schemas.common import BaseSchema, FetchedVia, InputKind, Platform, ScanSource, Verdict
from app.schemas.merchant import MatchedMerchant

MAX_AVATAR_BASE64 = 7_000_000  # ~5 MB decoded


class ManualInput(BaseSchema):
    """Manual fallback when the page can't be fetched: the user pastes the bio / uploads the avatar."""

    display_name: str | None = Field(default=None, max_length=120)
    bio: str | None = Field(default=None, max_length=2200)
    avatar_base64: str | None = Field(default=None, max_length=MAX_AVATAR_BASE64)


class CheckRequest(BaseSchema):
    """Exactly one of ``url`` / ``handle``. ``manual`` is the fallback after a 502."""

    url: str | None = Field(default=None, max_length=2048)
    handle: str | None = Field(default=None, max_length=2048)
    platform: Platform | None = None
    manual: ManualInput | None = None

    @model_validator(mode="after")
    def _exactly_one(self) -> "CheckRequest":
        if bool(self.url and self.url.strip()) == bool(self.handle and self.handle.strip()):
            raise ValueError("Provide exactly one of 'url' or 'handle'.")
        return self


class TargetInfo(BaseSchema):
    """What we know about the checked page."""

    platform: str | None = None
    handle: str | None = None
    display_name: str | None = None
    url: str | None = None
    avatar_url: str | None = None
    follower_count: int | None = None
    post_count: int | None = None
    account_created_on: date | None = None
    fetched_via: FetchedVia = "none"


class DimensionOut(BaseSchema):
    """One of the five sub-scores. Unavailable -> ``score 0, available false, evidence "No data"``."""

    key: Literal["visual", "identity", "payment", "language", "account"]
    label: str
    score: float
    weight: float
    available: bool
    evidence: str


class ReasonOut(BaseSchema):
    """Plain-language explanation (EN + SW)."""

    code: str
    severity: Literal["high", "medium"]
    text: str
    text_sw: str


class HashesOut(BaseSchema):
    """Hash comparison against the matched merchant's logo."""

    target_phash: str | None = None
    reference_phash: str | None = None
    hamming_distance: int | None = None


class SafeActionOut(BaseSchema):
    """ "Pay only via ..." line for the matched merchant."""

    text: str
    text_sw: str


class CheckResult(BaseSchema):
    """``POST /check`` response. Public: third-party phone numbers are masked."""

    scan_id: UUID
    verdict: Verdict
    score: float
    confidence: float
    target: TargetInfo
    matched_merchant: MatchedMerchant | None = None
    dimensions: list[DimensionOut] = Field(default_factory=list)
    reasons: list[ReasonOut] = Field(default_factory=list)
    hashes: HashesOut | None = None
    safe_action: SafeActionOut | None = None
    threat_id: UUID | None = None
    elapsed_ms: int


class ScanCreate(BaseSchema):
    """A ``scans`` row to insert. ``id`` may be supplied (seeder: deterministic uuid5)."""

    id: UUID | None = None
    input_value: str
    input_kind: InputKind
    platform: str | None = None
    target_handle: str | None = None
    source: ScanSource = "public_checker"
    verdict: Verdict
    composite_score: float | None = None
    merchant_id: UUID | None = None
    threat_id: UUID | None = None
    result: dict
    elapsed_ms: int | None = None
    created_at: datetime | None = None


class ScanRecord(ScanCreate):
    """A stored ``scans`` row."""

    id: UUID
    created_at: datetime


class TargetProfileRecord(BaseSchema):
    """``target_profiles`` row (schema v2.2): tier-1 known page metadata (seeded or OpenGraph-fetched).

    Manual submissions are never stored here, so one user cannot poison another user's result.
    """

    platform: str
    handle: str
    url: str | None = None
    display_name: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    avatar_phash: str | None = None
    avatar_dhash: str | None = None
    avatar_embedding: list[float] | None = None
    follower_count: int | None = None
    post_count: int | None = None
    account_created_on: date | None = None
    fetched_via: Literal["seed", "opengraph"] = "opengraph"
    fetched_at: datetime
