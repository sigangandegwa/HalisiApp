-- =============================================================================
-- Halisi Supabase schema v2.1 (TSK-001)
-- v2.1 (2026-09-27): Telegram/SMS alert columns removed; merchant_alerts table added for in-app alerts.
-- Run in the Supabase SQL Editor on a fresh project. Safe to re-run (IF NOT EXISTS).
-- This file is the single source of truth for the data model.
-- backend/app/schemas/*.py (Pydantic) must mirror it. See docs/BACKEND.md section 4.
--
-- Access model: the FastAPI backend connects with the service-role key (bypasses RLS).
-- RLS is enabled with NO policies so the public anon key can read/write nothing.
-- The frontend never talks to Supabase directly in the MVP.
-- =============================================================================

create extension if not exists pgcrypto;   -- gen_random_uuid()
create extension if not exists vector;     -- pgvector: CLIP ViT-B-32 embeddings (512-d)

-- -----------------------------------------------------------------------------
-- merchants: verified ground truth for each protected business
-- -----------------------------------------------------------------------------
create table if not exists merchants (
    id                 uuid primary key default gen_random_uuid(),
    business_name      text not null,
    slug               text not null unique check (slug ~ '^[a-z0-9-]{3,60}$'),  -- public page: /v/<slug>
    aliases            text[] not null default '{}',
    category           text,
    location           text,
    established_on     date,
    logo_url           text,
    logo_phash         char(16),              -- 64-bit perceptual hash, hex
    logo_dhash         char(16),              -- 64-bit difference hash, hex
    logo_embedding     vector(512),           -- CLIP ViT-B-32, L2-normalised
    mpesa_type         text not null default 'till' check (mpesa_type in ('till', 'paybill', 'pochi', 'none')),
    mpesa_number       text,                  -- till / paybill / pochi phone
    mpesa_account_name text,                  -- name shown on the M-Pesa confirmation SMS
    phone_numbers      text[] not null default '{}',  -- official numbers, E.164 (+2547XXXXXXXX)
    is_verified        boolean not null default false,
    created_at         timestamptz not null default now(),
    updated_at         timestamptz not null default now()
);

-- -----------------------------------------------------------------------------
-- merchant_handles: every official account of a merchant (one row per platform handle)
-- -----------------------------------------------------------------------------
create table if not exists merchant_handles (
    id           uuid primary key default gen_random_uuid(),
    merchant_id  uuid not null references merchants(id) on delete cascade,
    platform     text not null check (platform in ('instagram', 'facebook', 'tiktok', 'x', 'whatsapp', 'website')),
    handle       text not null check (handle = lower(handle)),  -- normalised: lowercase, no '@'
    url          text,
    unique (platform, handle)
);

-- -----------------------------------------------------------------------------
-- threats: suspected impersonation pages linked to the merchant they imitate
-- Sub-scores are 0-100; NULL means the signal was unavailable (never store a fake 0).
-- -----------------------------------------------------------------------------
create table if not exists threats (
    id                  uuid primary key default gen_random_uuid(),
    merchant_id         uuid not null references merchants(id) on delete cascade,
    platform            text not null,
    target_handle       text not null,
    target_url          text not null,
    display_name        text,
    bio                 text,
    avatar_url          text,
    avatar_phash        char(16),
    avatar_embedding    vector(512),
    account_created_on  date,
    follower_count      integer,
    post_count          integer,
    extracted_phones    text[] not null default '{}',
    extracted_tills     text[] not null default '{}',

    visual_score        numeric(5,2),
    identity_score      numeric(5,2),
    payment_score       numeric(5,2),
    language_score      numeric(5,2),
    account_score       numeric(5,2),
    composite_score     numeric(5,2) not null check (composite_score between 0 and 100),
    confidence          numeric(3,2) not null default 1 check (confidence between 0 and 1),
    reasons             jsonb not null default '[]',   -- human-readable explanation list

    status              text not null default 'detected'
                        check (status in ('detected', 'advisory_sent', 'takedown_filed', 'resolved', 'false_positive')),
    source              text not null default 'public_checker'
                        check (source in ('public_checker', 'scheduled', 'community_report', 'simulator', 'seed')),
    first_seen_at       timestamptz not null default now(),
    last_checked_at     timestamptz not null default now(),
    resolved_at         timestamptz,
    unique (merchant_id, platform, target_handle)
);

-- -----------------------------------------------------------------------------
-- scans: every check performed (public checker, bot, scheduler). Powers stats + shareable results.
-- -----------------------------------------------------------------------------
create table if not exists scans (
    id               uuid primary key default gen_random_uuid(),
    input_value      text not null,           -- URL, handle, or phone/till the user submitted
    input_kind       text not null check (input_kind in ('url', 'handle', 'phone', 'till')),
    platform         text,
    target_handle    text,
    source           text not null default 'public_checker'
                     check (source in ('public_checker', 'scheduled', 'simulator', 'seed')),
    verdict          text not null check (verdict in ('official', 'impersonation', 'suspicious', 'no_match', 'error')),
    composite_score  numeric(5,2),
    merchant_id      uuid references merchants(id) on delete set null,
    threat_id        uuid references threats(id) on delete set null,
    result           jsonb not null,          -- full CheckResult payload (docs/BACKEND.md section 5)
    elapsed_ms       integer,
    created_at       timestamptz not null default now()
);

-- -----------------------------------------------------------------------------
-- remediation_logs: every generated playbook (LLM or template) and whether it was sent
-- -----------------------------------------------------------------------------
create table if not exists remediation_logs (
    id                 uuid primary key default gen_random_uuid(),
    threat_id          uuid not null references threats(id) on delete cascade,
    playbook_type      text not null check (playbook_type in ('consumer_warning', 'platform_takedown', 'safaricom_report', 'kecirt_report')),
    language           text not null default 'en' check (language in ('en', 'sw')),
    generated_content  text not null,
    generator          text not null check (generator in ('llm', 'template')),
    prompt_id          text,                  -- e.g. PROMPT_CONSUMER_DEFENSE_V2 (AGENTS.md section 7)
    model              text,                  -- e.g. meta/llama-3.1-8b-instruct
    dispatched_to      text,
    created_at         timestamptz not null default now(),
    dispatched_at      timestamptz
);

-- -----------------------------------------------------------------------------
-- community_reports: consumer-submitted scam reports (personal data: never expose publicly)
-- -----------------------------------------------------------------------------
create table if not exists community_reports (
    id                uuid primary key default gen_random_uuid(),
    target_url        text,
    target_handle     text,
    platform          text,
    reported_phone    text,                   -- E.164
    reported_till     text,
    description       text check (char_length(description) <= 1000),
    reporter_contact  text,                   -- optional, Data Protection Act 2019: minimise & protect
    status            text not null default 'pending' check (status in ('pending', 'confirmed', 'rejected')),
    threat_id         uuid references threats(id) on delete set null,
    created_at        timestamptz not null default now()
);

-- -----------------------------------------------------------------------------
-- merchant_alerts: in-app alerts shown in the dashboard bell, toasts and browser notifications
-- (no Telegram/SMS). One row per threat event; de-duplicated by the dispatcher.
-- -----------------------------------------------------------------------------
create table if not exists merchant_alerts (
    id           uuid primary key default gen_random_uuid(),
    merchant_id  uuid not null references merchants(id) on delete cascade,
    threat_id    uuid not null references threats(id) on delete cascade,
    kind         text not null check (kind in ('new_threat', 'score_increase', 'resolved')),
    title        text not null,                -- e.g. "Impersonator detected: @nairobi_sneakervault_official_ke"
    body         text not null,                -- top reason, plain language
    score        numeric(5,2),
    created_at   timestamptz not null default now(),
    read_at      timestamptz
);

-- -----------------------------------------------------------------------------
-- Indexes
-- -----------------------------------------------------------------------------
create index if not exists idx_handles_merchant      on merchant_handles (merchant_id);
create index if not exists idx_threats_merchant       on threats (merchant_id, status);
create index if not exists idx_threats_score          on threats (composite_score desc);
create index if not exists idx_threats_phones         on threats using gin (extracted_phones);
create index if not exists idx_merchants_phones       on merchants using gin (phone_numbers);
create index if not exists idx_merchants_mpesa        on merchants (mpesa_number);
create index if not exists idx_scans_created          on scans (created_at desc);
create index if not exists idx_reports_phone          on community_reports (reported_phone);
create index if not exists idx_reports_till           on community_reports (reported_till);
create index if not exists idx_alerts_merchant_time  on merchant_alerts (merchant_id, created_at desc);
create index if not exists idx_alerts_unread         on merchant_alerts (merchant_id) where read_at is null;

-- -----------------------------------------------------------------------------
-- updated_at trigger
-- -----------------------------------------------------------------------------
create or replace function set_updated_at() returns trigger
language plpgsql as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

drop trigger if exists trg_merchants_updated_at on merchants;
create trigger trg_merchants_updated_at
    before update on merchants
    for each row execute function set_updated_at();

-- -----------------------------------------------------------------------------
-- Vector search: nearest merchant logos to a target avatar embedding
-- Call from backend: supabase.rpc('match_merchant_logos', {...})
-- -----------------------------------------------------------------------------
create or replace function match_merchant_logos(query_embedding vector(512), match_count int default 5)
returns table (merchant_id uuid, similarity float)
language sql stable as $$
    select id, 1 - (logo_embedding <=> query_embedding) as similarity
    from merchants
    where logo_embedding is not null
    order by logo_embedding <=> query_embedding
    limit match_count;
$$;

-- -----------------------------------------------------------------------------
-- Row Level Security: deny-by-default for anon/authenticated roles
-- -----------------------------------------------------------------------------
alter table merchants          enable row level security;
alter table merchant_handles   enable row level security;
alter table threats            enable row level security;
alter table scans              enable row level security;
alter table remediation_logs   enable row level security;
alter table community_reports  enable row level security;
alter table merchant_alerts    enable row level security;
