from pydantic import Field
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from uuid import UUID
from .common import BaseSchema

class ThreatUpsert(BaseSchema):
    merchant_id: UUID
    platform: str
    target_handle: str
    target_url: str
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    avatar_phash: Optional[str] = None
    avatar_embedding: Optional[List[float]] = None
    account_created_on: Optional[date] = None
    follower_count: Optional[int] = None
    post_count: Optional[int] = None
    extracted_phones: List[str] = Field(default_factory=list)
    extracted_tills: List[str] = Field(default_factory=list)
    
    visual_score: Optional[float] = None
    identity_score: Optional[float] = None
    payment_score: Optional[float] = None
    language_score: Optional[float] = None
    account_score: Optional[float] = None
    composite_score: float
    confidence: float = 1.0
    reasons: List[Dict[str, Any]] = Field(default_factory=list)
    status: str = "detected"
    source: str = "public_checker"

class ThreatRecord(ThreatUpsert):
    id: UUID
    first_seen_at: datetime
    last_checked_at: datetime
    resolved_at: Optional[datetime] = None

class ThreatSummary(BaseSchema):
    id: UUID
    platform: str
    target_handle: str
    target_url: str
    avatar_url: Optional[str] = None
    composite_score: float
    verdict: str
    status: str
    first_seen_at: datetime
    top_reason: Optional[Dict[str, Any]] = None

class ThreatDetail(ThreatRecord):
    verdict: str
    status_history: List[Dict[str, Any]] = Field(default_factory=list)
    playbooks_generated: List[Dict[str, Any]] = Field(default_factory=list)
