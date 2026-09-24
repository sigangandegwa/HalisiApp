-- Halisi Supabase SQL Schema (TSK-001)
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
