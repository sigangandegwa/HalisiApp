import os
from pathlib import Path

base = Path('.')

dirs = [
    'backend/app/api/v1/endpoints',
    'backend/app/core',
    'backend/app/engine',
    'backend/app/ingestion',
    'backend/app/alerts',
    'backend/app/schemas',
    'database'
]

for d in dirs:
    (base / d).mkdir(parents=True, exist_ok=True)
    if 'backend' in d:
        (base / d / '__init__.py').touch()

# Schema.sql (TSK-001)
with open(base / 'database/schema.sql', 'w') as f:
    f.write('''-- Halisi Supabase SQL Schema (TSK-001)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE merchants (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    mpesa_till VARCHAR(50) NOT NULL,
    official_social_handles TEXT[] NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE threats (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    target_url TEXT NOT NULL,
    suspected_scammer_handle VARCHAR(255),
    risk_score NUMERIC(5, 2) NOT NULL,
    similarity_hash TEXT,
    matched_merchant_id UUID REFERENCES merchants(id),
    status VARCHAR(50) DEFAULT 'open',
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE remediation_logs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    threat_id UUID REFERENCES threats(id) ON DELETE CASCADE,
    playbook_type VARCHAR(100) NOT NULL,
    generated_content TEXT NOT NULL,
    dispatched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
''')

# Schemas (TSK-002)
with open(base / 'backend/app/schemas/merchant.py', 'w') as f:
    f.write('''from pydantic import BaseModel
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
''')

with open(base / 'backend/app/schemas/threat.py', 'w') as f:
    f.write('''from pydantic import BaseModel
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
''')

# FastAPI main.py
with open(base / 'backend/app/main.py', 'w') as f:
    f.write('''from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Halisi API",
    description="AI-Powered Brand Impersonation Detection",
    version="0.1.0-alpha"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "operational", "service": "halisi_core"}
''')

print("Scaffolding complete.")
