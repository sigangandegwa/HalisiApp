from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ThreatBase(BaseModel):
    target_url: str
    suspected_scammer_handle: Optional[str] = None
    risk_score: float
    similarity_hash: Optional[str] = None
    matched_merchant_id: Optional[str] = None

class ThreatCreate(ThreatBase):
    pass

class Threat(ThreatBase):
    id: str
    status: str = "open"
    detected_at: datetime
    class Config:
        from_attributes = True
