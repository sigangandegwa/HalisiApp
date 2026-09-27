from pydantic import Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from .common import BaseSchema

class RemediationCreate(BaseSchema):
    threat_id: UUID
    playbook_type: str
    language: str = "en"
    generated_content: str
    generator: str
    prompt_id: Optional[str] = None
    model: Optional[str] = None
    dispatched_to: Optional[str] = None

class PlaybooksRequest(BaseSchema):
    generator: str = "llm"
    model: str = "meta/llama-3.1-8b-instruct"
    prompt_ids: List[str] = Field(default_factory=list)
    consumer_warning: Optional[Dict[str, Any]] = None
    platform_takedown: Optional[Dict[str, Any]] = None
    safaricom_report: Optional[Dict[str, Any]] = None
    kecirt_report: Optional[Dict[str, Any]] = None
