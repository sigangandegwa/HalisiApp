"""Merchant models: DB records (schema v2.2 ``merchants`` + ``merchant_handles``) and API shapes."""

from datetime import date, datetime
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.common import HANDLE_PATTERN, BaseSchema, MpesaType, Platform


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
    created_at: datetime
    updated_at: datetime
    official_handles: list[MerchantHandle] = Field(default_factory=list)


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
    """``POST /merchants`` response: the merchant plus its computed logo hashes."""

    logo_phash: str
    logo_dhash: str
    clip: bool = False
