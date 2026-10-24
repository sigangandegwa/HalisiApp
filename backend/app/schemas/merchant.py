"""Merchant models: DB records (schema v2.2 ``merchants`` + ``merchant_handles``) and API shapes."""

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from app.schemas.common import HANDLE_PATTERN, BaseSchema, MpesaType, Platform, Verdict, VerificationStatus


class MerchantHandle(BaseSchema):
    """One official account. ``handle`` is normalised: lowercase, no '@', no trailing slash."""

    platform: Platform
    handle: str = Field(pattern=HANDLE_PATTERN, max_length=60)
    url: str | None = Field(default=None, max_length=2048)

    @field_validator("handle", mode="before")
    @classmethod
    def _normalise(cls, value: str) -> str:
        return value.strip().lower().lstrip("@").rstrip("/") if isinstance(value, str) else value


class MerchantPayment(BaseSchema):
    """The merchant's official M-Pesa channel (public by design)."""

    type: MpesaType
    number: str | None = None
    account_name: str | None = None


class LogoFeatures(BaseSchema):
    """Hashes (and optional CLIP embedding) of a merchant logo."""

    phash: str = Field(min_length=16, max_length=16)
    dhash: str = Field(min_length=16, max_length=16)
    embedding: list[float] | None = None


class MerchantCreate(BaseSchema):
    """``POST /merchants`` ``data`` JSON (docs/BACKEND.md section 5.5)."""

    business_name: str = Field(min_length=2, max_length=120)
    slug: str = Field(pattern=r"^[a-z0-9-]{3,60}$")
    aliases: list[str] = Field(default_factory=list, max_length=10)
    category: str | None = Field(default=None, max_length=60)
    location: str | None = Field(default=None, max_length=120)
    established_on: date | None = None
    mpesa_type: MpesaType = "till"
    mpesa_number: str | None = Field(default=None, max_length=20)
    mpesa_account_name: str | None = Field(default=None, max_length=80)
    phone_numbers: list[str] = Field(default_factory=list, max_length=10)
    handles: list[MerchantHandle] = Field(default_factory=list, max_length=10)

    @field_validator("aliases")
    @classmethod
    def _alias_lengths(cls, value: list[str]) -> list[str]:
        if any(len(a) > 120 for a in value):
            raise ValueError("alias too long")
        return value


class MerchantRecord(BaseSchema):
    """A ``merchants`` row with its ``merchant_handles``."""

    id: UUID
    business_name: str
    slug: str
    aliases: list[str] = Field(default_factory=list)
    category: str | None = None
    location: str | None = None
    established_on: date | None = None
    logo_url: str | None = None
    logo_phash: str | None = None
    logo_dhash: str | None = None
    logo_embedding: list[float] | None = None
    mpesa_type: MpesaType = "till"
    mpesa_number: str | None = None
    mpesa_account_name: str | None = None
    phone_numbers: list[str] = Field(default_factory=list)
    is_verified: bool = False
    verification_status: VerificationStatus = "claimed"
    verification_code: str | None = None
    verified_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    official_handles: list[MerchantHandle] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _derive_status(cls, data: Any) -> Any:
        """Rows written before schema v2.3 have only ``is_verified``: those are Halisi-seeded (curated)."""
        if isinstance(data, dict) and not data.get("verification_status"):
            data = {**data, "verification_status": "curated" if data.get("is_verified") else "claimed"}
        return data

    @model_validator(mode="after")
    def _sync_is_verified(self) -> "MerchantRecord":
        """``is_verified`` is derived: true exactly for curated and verified merchants."""
        self.is_verified = self.verification_status in ("curated", "verified")
        return self


class PublicMerchant(BaseSchema):
    """``GET /merchants/{slug}`` (section 5.4): public verified profile for ``/v/[slug]``."""

    id: UUID
    business_name: str
    slug: str
    logo_url: str | None = None
    category: str | None = None
    location: str | None = None
    established_on: date | None = None
    is_verified: bool
    verification_status: VerificationStatus = "claimed"
    official_handles: list[MerchantHandle]
    payment: MerchantPayment
    verified_since: datetime | None = None


class MatchedMerchant(BaseSchema):
    """``CheckResult.matched_merchant`` (section 5.2)."""

    id: UUID
    business_name: str
    slug: str
    logo_url: str | None = None
    official_handles: list[MerchantHandle]
    payment: MerchantPayment


class MerchantCreated(PublicMerchant):
    """``POST /merchants`` response: the merchant, its logo hashes and the bio code that proves ownership."""

    logo_phash: str
    logo_dhash: str
    clip: bool = False
    verification_code: str | None = None


class WatchlistHandle(BaseSchema):
    """One official handle and the look-alikes Halisi would watch for (generated, not confirmed to exist)."""

    platform: Platform
    handle: str
    variants: list[str]


class Watchlist(BaseSchema):
    """``GET /merchants/{id}/watchlist``."""

    merchant_id: UUID
    handles: list[WatchlistHandle]


class WatchlistFinding(BaseSchema):
    """A look-alike that exists and scored as impersonation or suspicious for this merchant."""

    platform: str
    handle: str
    verdict: Verdict
    score: float
    scan_id: UUID
    threat_id: UUID | None = None


class WatchlistScan(BaseSchema):
    """``POST /merchants/{id}/watchlist/scan``. ``unreachable``: could not be read, which is not "safe"."""

    merchant_id: UUID
    variants_generated: int
    probed: int
    resolved: int
    unreachable: int
    budget_exhausted: bool = False
    findings: list[WatchlistFinding] = Field(default_factory=list)


class VerificationState(BaseSchema):
    """``GET /merchants/{id}/verification`` and the result of ``POST .../verification/check``."""

    status: VerificationStatus
    is_verified: bool
    verification_code: str | None = None      # only while ``claimed``
    handles_to_check: list[MerchantHandle] = Field(default_factory=list)
    checked: list[str] = Field(default_factory=list)   # "platform:handle" fetched on this attempt
    found_on: str | None = None                        # "platform:handle" where the code was found
    verified_at: datetime | None = None
    instructions: str | None = None
