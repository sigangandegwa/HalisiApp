from pydantic import Field
from typing import List, Optional
from datetime import date, datetime
from uuid import UUID
from .common import BaseSchema

class MerchantHandle(BaseSchema):
    platform: str
    handle: str
    url: Optional[str] = None

class MerchantPayment(BaseSchema):
    type: str
    number: Optional[str] = None
    account_name: Optional[str] = None

class MerchantFeatures(BaseSchema):
    id: UUID
    business_name: str
    slug: str
    aliases: List[str] = Field(default_factory=list)
    category: Optional[str] = None
    location: Optional[str] = None
    established_on: Optional[date] = None
    logo_url: Optional[str] = None
    logo_phash: Optional[str] = None
    logo_dhash: Optional[str] = None
    logo_embedding: Optional[List[float]] = None
    mpesa_type: str = "till"
    mpesa_number: Optional[str] = None
    mpesa_account_name: Optional[str] = None
    phone_numbers: List[str] = Field(default_factory=list)
    telegram_chat_id: Optional[str] = None
    alert_phone: Optional[str] = None
    is_verified: bool = False
    created_at: datetime
    updated_at: datetime

class MerchantRecord(MerchantFeatures):
    official_handles: List[MerchantHandle] = Field(default_factory=list)

class MerchantCreate(BaseSchema):
    business_name: str
    slug: str
    aliases: List[str] = Field(default_factory=list)
    category: Optional[str] = None
    location: Optional[str] = None
    established_on: Optional[date] = None
    mpesa_type: str = "till"
    mpesa_number: Optional[str] = None
    mpesa_account_name: Optional[str] = None
    phone_numbers: List[str] = Field(default_factory=list)
    handles: List[MerchantHandle] = Field(default_factory=list)
    telegram_chat_id: Optional[str] = None
    alert_phone: Optional[str] = None

class LogoFeatures(BaseSchema):
    phash: str
    dhash: str
    embedding: Optional[List[float]] = None

class PaymentLookup(BaseSchema):
    kind: str
    normalized: str
    display: str
    status: str
    merchant: Optional[MerchantRecord] = None
    report_count: int
    linked_threats: int
