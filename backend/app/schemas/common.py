from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID
from typing import Optional, List, Dict, Any

class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class PaginatedResponse(BaseSchema):
    items: List[Any]
    total: int
    page: int
    size: int
