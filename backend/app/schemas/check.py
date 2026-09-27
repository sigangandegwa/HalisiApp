from pydantic import Field
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from uuid import UUID
from .common import BaseSchema

class TargetFeatures(BaseSchema):
    platform: Optional[str] = None
    handle: Optional[str] = None
    display_name: Optional[str] = None
    url: Optional[str] = None
    avatar_url: Optional[str] = None
    follower_count: Optional[int] = None
    post_count: Optional[int] = None
    account_created_on: Optional[date] = None
    fetched_via: Optional[str] = None

class DimensionScore(BaseSchema):
    key: str
    label: str
    score: float
    weight: float
    available: bool
    evidence: str

class Reason(BaseSchema):
    code: str
    severity: str
    text: str
    text_sw: str

class MatcherHashes(BaseSchema):
    target_phash: Optional[str] = None
    reference_phash: Optional[str] = None
    hamming_distance: Optional[int] = None

class SafeAction(BaseSchema):
    text: str
    text_sw: str

class CheckResult(BaseSchema):
    scan_id: UUID
    verdict: str
    score: float
    confidence: float
    target: TargetFeatures
    matched_merchant: Optional[Dict[str, Any]] = None
    dimensions: List[DimensionScore] = Field(default_factory=list)
    reasons: List[Reason] = Field(default_factory=list)
    hashes: Optional[MatcherHashes] = None
    safe_action: Optional[SafeAction] = None
    threat_id: Optional[UUID] = None
    elapsed_ms: Optional[int] = None

class ScanCreate(BaseSchema):
    input_value: str
    input_kind: str
    platform: Optional[str] = None
    target_handle: Optional[str] = None
    source: str = "public_checker"
    verdict: str
    composite_score: Optional[float] = None
    merchant_id: Optional[UUID] = None
    threat_id: Optional[UUID] = None
    result: Dict[str, Any]
    elapsed_ms: Optional[int] = None

class ScanRecord(ScanCreate):
    id: UUID
    created_at: datetime
