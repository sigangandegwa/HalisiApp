from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class MerchantBase(BaseModel):
    name: str
    mpesa_till: str
    official_social_handles: List[str]

class MerchantCreate(MerchantBase):
    pass

class Merchant(MerchantBase):
    id: str
    created_at: datetime
    class Config:
        from_attributes = True
