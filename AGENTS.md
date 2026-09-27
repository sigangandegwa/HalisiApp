# Halisi: Multi-Agent & Developer Synchronization Framework (AGENTS.md)

**Project**: Halisi \- AI-Powered Brand Impersonation Detection for Kenyan Businesses  
**Organization**: Chiromo Tech Club, University of Nairobi  
**Core Maintainers**: Collins Kimanzi (Lead/Architecture), Geoffrey (Ingestion/APIs), Ndegwa (Frontend/UI)  
**Status**: Pre-Development / Initial Setup  
**Version**: 0.1.0-alpha

---

## 1\. Purpose & Agent Operating Protocol

This file serves as the single source of truth (SSOT) for coordinating human developers (Collins, Geoffrey, Ndegwa) and autonomous/co-pilot AI coding agents (Gemini Spark, Claude Code, Cursor, Copilot).

### Golden Rules for AI Agents Working on This Repo:

1. **Read Before Modifying**: Before executing any code changes, read this file (`AGENTS.md`), `tech-stack.md`, and `data-flow.md`.  
2. **Atomic Updates**: Only work on one assigned task or file module at a time.  
3. **Register File Changes**: Whenever a file is created, modified, or deleted, update Section 6 (File Change & Mutation Log) with timestamp, author, and description.  
4. **Sync Task Status**: When beginning a task, move it from `[ ] (Pending)` to `[/] (In Progress)` with your agent/developer signature. Mark `[x] (Done)` only after verification.  
5. **Prompt Versioning**: Any update to system prompts or AI generation logic must be recorded in Section 7 (Prompt & Heuristic Registry).

---

## 2\. Team Ownership & Responsibilities Matrix

\+------------------+-----------------------------+----------------------------------------------+  
| Member           | Core Domain                 | Primary Files & Modules                      |  
\+------------------+-----------------------------+----------------------------------------------+  
| Collins Kimanzi  | UI/UX Engineer              | frontend/src/\*, UI Components, Design System |  
|                  |                             | Wireframes, Public Checker UI styling        |  
\+------------------+-----------------------------+----------------------------------------------+  
| Geoffrey         | Ingestion Pipelines, APIs   | backend/app/ingestion/\*, OpenGraph Scrapers, |  
|                  | & External Integrations     | Africa's Talking SMS, mock data generator    |  
\+------------------+-----------------------------+----------------------------------------------+  
| Ndegwa           | Frontend Application,       | frontend/src/\*, Public Link Checker UI,      |  
|                  | Design System & UX          | Merchant Dashboard, visual risk radar charts |  
\+------------------+-----------------------------+----------------------------------------------+  
| Dennis Kuria     | Tech Lead, AI Pipeline,     | backend/app/engine/\*, backend/app/alerts/\*,  |  
|                  | DB Admin, Full-Stack        | database schema, security, system consensus   |  
\+------------------+-----------------------------+----------------------------------------------+  
---

## 3\. Priority Task Matrix & Sprint Board

### Task Priority Hierarchy

- **P0 (Critical Blocker)**: Core foundation without which other modules fail. Must be finished first.  
- **P1 (High Priority)**: Core product feature necessary for MVP and hackathon judging.  
- **P2 (Medium Priority)**: Polish, telemetry, edge-case hardening, and auxiliary alert channels.

### Current Sprint Board

| Task ID | Pri | Module | Description | Owner | Status | Depends on |
| :-- | :-: | :-- | :-- | :-- | :-: | :-- |
| TSK-001 | P0 | Database | Deploy **schema v2** (`database/schema.sql`) to Supabase. v1 was reopened: it had no logo hash and no sub-score columns | Geoffrey | `[ ] Pending` | — |
| TSK-002 | P0 | Backend core | config, repository (Supabase + Memory), cache, error handlers, router, Pydantic v2 schemas mirroring v2. Reopened: only `/health` existed | Geoffrey | `[x] Done` | 001 |
| TSK-003 | P0 | Engine | pHash prototype (`hasher.py` v1) | ~~Dennis~~ | `[x] Done` (v1, superseded by 015) | 002 |
| TSK-004 | P0 | Engine | Jaro-Winkler + scam tokens prototype (`matcher.py` v1) | ~~Dennis~~ | `[x] Done` (v1, superseded by 016) | 002 |
| TSK-015 | P0 | Engine | **Hasher v2**: calibrated similarity, alpha/EXIF/square normalisation, dHash, no I/O in engine | Collins | `[ ] Pending` | 002 |
| TSK-016 | P0 | Engine | **Matcher v2**: normalisation, homoglyphs, affix stripping, multi-handle, weighted EN/SW/Sheng lexicon, golden tests | Geoffrey | `[x] Done` | 002 |
| TSK-021 | P0 | Ingestion + Engine | Kenyan phone/Till/Paybill/Pochi extractors (Geoffrey) + payment score (Collins) | Geoffrey / Collins | `[ ] Pending` | 002 |
| TSK-008 | P0 | Engine | **Composite scorer**: 5 dimensions, renormalisation, confidence, gate and overrides, reasons EN/SW | Collins | `[ ] Pending` | 015, 016, 021 |
| TSK-007 | P0 | Ingestion | Mock seeder: 3 fictional merchants × (blatant clone, subtle clone, legit competitor) + reports; exports frontend fixtures | Geoffrey | `[ ] Pending` | 002 |
| TSK-018 | P0 | API | Endpoints per BACKEND.md section 5 + URL parser | Geoffrey | `[ ] Pending` | 002, 008 |
| TSK-019 | P1 | Security | SSRF guard, rate limits, API key, CORS fix, input limits, masking | Geoffrey | `[ ] Pending` | 018 |
| TSK-006 | P1 | Ingestion | Tiered page scraper (seeded → OpenGraph → manual fallback) | Geoffrey | `[ ] Pending` | 018 |
| TSK-017 | P1 | Engine / Infra | CLIP embeddings + Brev GPU deployment + ngrok + threshold calibration | Collins | `[ ] Pending` | 015 |
| TSK-009 | P1 | Remediation | Playbooks via NVIDIA NIM + validator + EN/SW templates | Collins | `[ ] Pending` | 008 |
| TSK-012 | P1 | Alerts | Telegram alerts (HTML mode, photo, button, de-dup) + chat linking | Geoffrey | `[ ] Pending` | 018 |
| TSK-022 | P1 | API | Community reports + `/verify/payment` lookup + override O3 | Geoffrey | `[ ] Pending` | 018 |
| TSK-031 | P1 | API / Engine | Simulator clone endpoint (real engine on synthetic targets) | Collins | `[ ] Pending` | 008 |
| TSK-013 | P2 | Alerts | Africa's Talking SMS (sandbox simulator) | Geoffrey | `[ ] Pending` | 018 |
| TSK-028 | P2 | Remediation | Evidence dossier PDF with SHA-256 of evidence bundle | Collins | `[ ] Pending` | 009 |
| TSK-029 | P2 | Ingestion | Takedown tracker (APScheduler re-check, time-to-takedown) | Geoffrey | `[ ] Pending` | 006 |
| TSK-030 | P2 | Alerts | Consumer Telegram checker bot (forward a link or number, get a verdict) | Geoffrey | `[ ] Pending` | 012, 022 |
| TSK-036 | P2 | Alerts | USSD "check a till" menu via Africa's Talking (feature phones) | Geoffrey | `[ ] Pending` | 022 |

### Frontend

| Task ID | Pri | Module | Description | Owner | Status | Depends on |
| :-- | :-: | :-- | :-- | :-- | :-: | :-- |
| TSK-005 | P0 | Frontend | Scaffold Next.js (latest, App Router) + Tailwind v4 + shadcn/ui + fonts + providers | Ndegwa | `[ ] Pending` | — |
| TSK-020 | P0 | Design system | Tokens, brand ornaments (guilloche, microprint, stamp, seal), restyled primitives, `/styleguide` | Collins + Ndegwa | `[ ] Pending` | 005 |
| TSK-033 | P0 | Data layer | Server proxy with path allowlist, demo fallback fixtures, passcode session + middleware | Ndegwa | `[ ] Pending` | 005 |
| TSK-010 | P1 | Public | Landing + checker + **Forensic Verdict** signature sequence | Ndegwa | `[ ] Pending` | 020, 033 |
| TSK-023 | P1 | Public | Shareable result page + OG stamp image + WhatsApp share | Ndegwa | `[ ] Pending` | 010 |
| TSK-034 | P1 | Public | `/pay` till/phone check + `/report` scam report | Ndegwa | `[ ] Pending` | 033 |
| TSK-024 | P1 | Public | Halisi Verified certificate `/v/[slug]` + QR badge / story sticker | Collins (design) + Ndegwa | `[ ] Pending` | 020 |
| TSK-011 | P1 | Merchant | Dashboard: KPIs + live threat feed with handle diffs | Ndegwa | `[ ] Pending` | 033 |
| TSK-025 | P1 | Merchant | Threat detail Evidence Board + playbook tabs | Ndegwa | `[ ] Pending` | 011 |
| TSK-026 | P1 | Merchant | Onboarding wizard with logo fingerprint grid | Ndegwa | `[ ] Pending` | 033 |
| TSK-027 | P1 | Demo | Simulator stage mode (projector, presenter keys, phone alert) | Ndegwa | `[ ] Pending` | 010, 031 |
| TSK-032 | P1 | i18n | English / Swahili for all public pages + verdict copy | Ndegwa | `[ ] Pending` | 010 |

### Integration & demo

| Task ID | Pri | Module | Description | Owner | Status | Depends on |
| :-- | :-: | :-- | :-- | :-- | :-: | :-- |
| TSK-014 | P1 | QA / Demo | End-to-end test: public check → threat → Telegram → playbook; failover drill | All (lead: Geoffrey) | `[ ] Pending` | 010, 011, 012, 017 |
| TSK-035 | P1 | Pitch | 3-minute script, sourced problem statistic, Q&A prep, screen-recording backup | Collins | `[ ] Pending` | 014 |

*Legend: `[ ] Pending` | `[/] In Progress` | `[x] Done` | `[!] Blocked`*

---

## 4\. Codebase Architecture & File Status Map

halisi/  
├── backend/  
│   ├── app/  
│   │   ├── api/  
│   │   │   ├── v1/  
│   │   │   │   ├── endpoints/  
│   │   │   │   │   ├── check.py            \[PLANNED\] \- Public link check route (GET/POST)  
│   │   │   │   │   ├── merchants.py        \[PLANNED\] \- Onboarding & brand management  
│   │   │   │   │   ├── threats.py          \[PLANNED\] \- Threat feeds, filters & audits  
│   │   │   │   │   └── remediation.py      \[PLANNED\] \- Trigger & export AI playbooks  
│   │   │   │   └── router.py               \[PLANNED\] \- API v1 aggregator  
│   │   ├── core/  
│   │   │   ├── config.py                   \[PLANNED\] \- App settings & ENV parser  
│   │   │   ├── database.py                 \[PLANNED\] \- Supabase Postgres client  
│   │   │   └── security.py                 \[PLANNED\] \- API key & rate limiter  
│   │   ├── engine/  
│   │   │   ├── hasher.py                   \[PLANNED\] \- pHash/dHash visual matching  
│   │   │   ├── embeddings.py               \[PLANNED\] \- CLIP ViT-B-32 vectorizer  
│   │   │   ├── matcher.py                  \[PLANNED\] \- RapidFuzz string & token logic  
│   │   │   ├── scorer.py                   \[PLANNED\] \- 5-dimension risk math (0-100)  
│   │   │   └── remediation.py              \[PLANNED\] \- AI prompt playbooks generator  
│   │   ├── ingestion/  
│   │   │   ├── page\_scraper.py             \[PLANNED\] \- Public OpenGraph metadata parser  
│   │   │   └── mock\_seeder.py              \[PLANNED\] \- Demo dataset for presentation  
│   │   ├── alerts/  
│   │   │   ├── telegram\_bot.py             \[PLANNED\] \- Telegram push bot dispatcher  
│   │   │   └── africas\_talking.py          \[PLANNED\] \- Kenyan SMS gateway client  
│   │   ├── schemas/  
│   │   │   ├── merchant.py                 \[PLANNED\] \- Pydantic models for onboarding  
│   │   │   ├── threat.py                   \[PLANNED\] \- Threat & forensic payload models  
│   │   │   └── remediation.py              \[PLANNED\] \- Playbook schema models  
│   │   └── main.py                         \[PLANNED\] \- FastAPI startup & CORS middleware  
│   ├── tests/                              \[PLANNED\] \- Pytest unit & integration tests  
│   ├── requirements.txt                    \[PLANNED\] \- Locked backend dependencies  
│   └── .env.example                        \[PLANNED\] \- Sample environment variables  
│  
├── frontend/  
│   ├── src/  
│   │   ├── app/  
│   │   │   ├── page.tsx                    \[PLANNED\] \- Landing page \+ Public Link Checker  
│   │   │   ├── dashboard/  
│   │   │   │   ├── page.tsx                \[PLANNED\] \- Active threat monitor & stats  
│   │   │   │   ├── threats/\[id\]/page.tsx   \[PLANNED\] \- Threat forensic breakdown  
│   │   │   │   └── register/page.tsx       \[PLANNED\] \- Merchant onboarding wizard  
│   │   │   └── layout.tsx                  \[PLANNED\] \- Root navigation & theme provider  
│   │   ├── components/  
│   │   │   ├── threat-badge.tsx            \[PLANNED\] \- Dynamic risk pill (Low/Med/High)  
│   │   │   ├── score-radar.tsx             \[PLANNED\] \- 5-axis Recharts radar chart  
│   │   │   ├── playbook-card.tsx           \[PLANNED\] \- Action cards for AI playbooks  
│   │   │   ├── live-simulator.tsx          \[PLANNED\] \- Demo sandbox for judges  
│   │   │   └── ui/                         \[PLANNED\] \- Button, Card, Input, Modal (shadcn)  
│   │   └── lib/  
│   │       ├── api.ts                      \[PLANNED\] \- Typed API client  
│   │       └── utils.ts                    \[PLANNED\] \- Formatters (dates, currency, hashes)  
│   ├── package.json                        \[PLANNED\] \- Frontend dependencies  
│   ├── tailwind.config.ts                  \[PLANNED\] \- Theme, colors, typography  
│   └── .env.local.example                  \[PLANNED\] \- Public API URL config  
│  
├── docs/  
│   ├── tech-stack.md                       \[SYNCHRONIZED\] \- Tech stack specification  
│   ├── data-flow.md                        \[SYNCHRONIZED\] \- Data flow & architecture  
│   └── DEVELOPMENT.md                      \[SYNCHRONIZED\] \- Step-by-step dev runbook  
└── AGENTS.md                               \[ACTIVE\] \- Coordination & task tracking  
---

## 5\. Active & Pending Sprint Checklists

### Milestone 1: Environment & Foundation

- [ ] Collins: Create GitHub repository `chiromo-tech-club/halisi`.  
- [ ] Collins: Configure Supabase project, execute `schema.sql`, add service keys to `.env`.  
- [ ] Geoffrey: Test Playwright OpenGraph scraper fallback with 2 sample links.  
- [ ] Ndegwa: Initialize Next.js 14 project, configure Tailwind CSS, install `shadcn/ui` base components.

### Milestone 2: Core Engine & Ingestion (The Detection Brain)

- [x] Dennis: Implement `backend/app/engine/hasher.py` and write unit test with 2 sample logos.  
- [x] Dennis: Implement `backend/app/engine/matcher.py` with Jaro-Winkler and token weighting.  
- [ ] Dennis: Combine sub-scores in `backend/app/engine/scorer.py` and output normalized 0-100 score.  
- [ ] Geoffrey: Build `backend/app/ingestion/mock_seeder.py` with 3 authentic Kenyan stores and 2 realistic clone targets.  
- [ ] Geoffrey: Build basic HTTPX OpenGraph metadata scraper in `page_scraper.py`.

### Milestone 3: AI Remediation & Alert Channels

- [ ] Collins: Author and test the 3 prompt templates in `remediation.py` (Consumer, Meta Takedown, Safaricom Fraud).  
- [ ] Collins: Deploy Telegram Bot and test message dispatch via `telegram_bot.py`.  
- [ ] Geoffrey: Configure Africa's Talking Sandbox SMS client and dispatch test message.

### Milestone 4: Frontend Control Center & Public Verification

- [ ] Ndegwa: Build Public Link Checker on `/` with loading states and risk breakdown cards.  
- [ ] Ndegwa: Build Merchant Dashboard `/dashboard` showing incoming alerts and active protection count.  
- [ ] Ndegwa: Build Threat Detail page `/dashboard/threats/[id]` with one-click copy buttons for AI remediation copy.  
- [ ] Ndegwa: Build Live Clone Simulator component for presentation stage.

### Milestone 5: Rehearsal & Live Demo Hardening

- [ ] All: Run end-to-end integration test from public check to Telegram alert.  
- [ ] All: Rehearse 3-minute hackathon pitch script with judges' rubric in mind.  
- [ ] All: Verify fallback offline mock mode in case venue Wi-Fi throttles live API calls.

---

## 6\. File Change & Mutation Log

*All developers and agents MUST append any file modification or creation here.*

| Date & Time (EAT) | Author / Agent | Action | File Path | Summary of Change |
| :---- | :---- | :---- | :---- | :---- |
| 2026-09-23 00:50 | Gemini Spark / Collins | CREATE | `tech-stack.md` | Initial technical stack specification |
| 2026-09-23 00:50 | Gemini Spark / Collins | CREATE | `data-flow.md` | Complete data flow and AI remediation lifecycle |
| 2026-09-23 00:50 | Gemini Spark / Collins | CREATE | `DEVELOPMENT.md` | Step-by-step developer setup and implementation guide |
| 2026-09-23 00:51 | Gemini Spark / Collins | CREATE | `AGENTS.md` | Monorepo sync, task boards, codebase map & guidelines |
| 2026-09-24 03:02 | Antigravity / Agent | UPDATE | `AGENTS.md` | Add Dennis to Team Ownership & Responsibilities Matrix |
| 2026-09-24 03:06 | Antigravity / Agent | UPDATE | `All .md files` | Purged Meta Ad API & automated Safaricom escalations to ensure hackathon feasibility |
| 2026-09-24 03:15 | Antigravity / Agent | CREATE | `backend/app/*`, `database/schema.sql` | Scaffolded FastAPI monorepo, schemas, and Supabase SQL. Assigned UI to Collins/Dennis |
| 2026-09-24 03:38 | Antigravity / Agent | CREATE | `README.md`, `LICENSE.md` | Created animated project README and open-source MIT license |
| 2026-09-25 00:20 | Antigravity / Agent | CREATE | `backend/app/engine/hasher.py`, `test_hash.py` | Implemented TSK-003 perceptual hashing and unit tests. Fixed team roles for Dennis and Collins |
| 2026-09-25 00:26 | Antigravity / Agent | CREATE | `backend/app/engine/matcher.py`, `test_matcher.py` | Implemented TSK-004 Jaro-Winkler string similarity and Kenyan scam token logic |
| 2026-09-26 21:00 | Claude Code / Collins | UPDATE | `.gitignore`, `skills-lock.json` | Installed `elite-product-studio` and `top-design` agent skills for UI/UX and design review work |
| 2026-09-27 13:45 | Claude Code / Collins | MOVE | `tech-stack.md`, `data-flow.md`, `DEVELOPMENT.md` → `docs/` | Matched the documented repo layout |
| 2026-09-27 13:45 | Claude Code / Collins | UPDATE | `docs/tech-stack.md`, `docs/data-flow.md`, `docs/DEVELOPMENT.md` | v0.2: Brev + NIM, pgvector over ChromaDB, 5-dimension resemblance/malice model, single 70 threshold, removed stale duplicated code, new build order and demo script |
| 2026-09-27 13:45 | Claude Code / Collins | CREATE | `docs/BACKEND.md`, `docs/FRONTEND.md`, `docs/BREV_ENGINE_SETUP.md` | Detailed agent guides: frozen API contract, engine specs, security, design system, Brev deployment, failover |
| 2026-09-27 13:45 | Claude Code / Collins | UPDATE | `database/schema.sql` | Schema v2: merchant_handles, sub-scores, confidence, pgvector, scans, community_reports, RLS, RPC |
| 2026-09-27 13:45 | Claude Code / Collins | CREATE / DELETE | `backend/requirements*.txt`, `backend/.env.example`; deleted root `requirements.txt` | Replaced the UTF-16 `pip freeze` with curated UTF-8 core/ml/dev files; env template |
| 2026-09-27 13:45 | Claude Code / Collins | UPDATE / DELETE | `.gitignore`; untracked `__pycache__/*.pyc`; deleted `build_monorepo.py` | Fixed the `/_pycache_` typo (pyc files were committed); removed the one-shot scaffold that would overwrite files if re-run |
| 2026-09-27 13:45 | Claude Code / Collins | UPDATE | `AGENTS.md`, `README.md` | 3-person team, redistributed Dennis's tasks, new sprint board, real file-status map, review findings |
| 2026-09-27 13:47 | Gemini 3.1 Pro (High) / Geoffrey | CREATE / UPDATE | `backend/app/core/*`, `backend/app/schemas/*`, `backend/app/api/v1/router.py`, `backend/pyproject.toml` | Scaffolded backend core and v2 schemas, completed TSK-002 |
| 2026-09-27 14:38 | Gemini 3.1 Pro (High) / Geoffrey | UPDATE | `backend/app/engine/matcher.py`, `backend/tests/engine/test_matcher.py` | Implemented TSK-016 Matcher v2 with normalisation, homoglyphs, and language scoring. Added and passed golden tests |

---

## 7. Prompt & Heuristic Registry

### 7.1 LLM prompts (location: `backend/app/engine/prompts/`)

All prompts receive only a **facts block** built from the DB. Scraped text appears only as quoted data. Output is JSON, validated so that every phone number, till and handle in the output must appear in the facts. On failure the deterministic template is used. Model default: `meta/llama-3.1-8b-instruct` via NVIDIA NIM.

| ID | Status | Purpose | Key constraints |
| :-- | :-- | :-- | :-- |
| `PROMPT_CONSUMER_DEFENSE_V1` | Retired | Story/WhatsApp warning | — |
| `PROMPT_CONSUMER_DEFENSE_V2` | Planned (TSK-009) | Customer warning, **EN + SW** | Name the fake handle, the real handle and the real Till/Paybill; "don't send money to {number}"; ≤ 700 chars; calm, no ALL-CAPS paragraphs; natural Kenyan Swahili |
| `PROMPT_META_TAKEDOWN_V1` | Retired | Meta Brand Rights claim | Replaced: the Brand Rights Protection portal needs enrolment |
| `PROMPT_PLATFORM_TAKEDOWN_V2` | Planned (TSK-009) | Text for the public Instagram/Facebook/TikTok impersonation report forms | Cite the **actual** hash distance and scores, first-seen date and official handle; no invented percentages (v1 hard-coded "96%") |
| `PROMPT_SAFARICOM_ESCALATION_V1` | Retired | Safaricom fraud email | — |
| `PROMPT_SAFARICOM_REPORT_V2` | Planned (TSK-009) | Report of the receiving number/till used to defraud customers | Receiving number/till, impersonated merchant + official till, victim path; channel addresses from `constants.py` (verified and dated) |
| `PROMPT_KECIRT_REPORT_V1` | Planned (TSK-009) | Incident report to National KE-CIRT/CC | Computer Misuse and Cybercrimes Act 2018 framing; factual; contact verified before the demo |

### 7.2 Scoring heuristics (location: `backend/app/engine/constants.py`)

| ID | Version | Value | Notes |
| :-- | :-- | :-- | :-- |
| `WEIGHTS` | v2 | visual .30 · identity .25 · payment .25 · language .10 · account .10 | v1 (docs only): visual .25, lexical .20, temporal .25, payment .20, engagement .10. Temporal was cut because account age is rarely observable |
| `THRESHOLDS` | v2 | impersonation ≥ 70 · suspicious ≥ 40 | v1 was inconsistent (75 in data-flow, 80 in README) |
| `HASH_SIMILARITY` | v2 (uncalibrated) | 100 at ≤ 4 bits, 0 at ≥ 24 | v1: `100 − d/64·100` scored unrelated images ~50 %. Calibrate in TSK-017 |
| `CLIP_SIMILARITY` | v1 (uncalibrated) | 100 at cosine ≥ 0.93, 0 at ≤ 0.80 | Calibrate in TSK-017 |
| `OVERRIDES` | v1 | G1 resemblance < 50 → cap 39 · O2 resemblance ≥ 80 + payment 100 → floor 90 · O3 confirmed report → floor 85 · O4 confidence < 0.5 → max suspicious | BACKEND.md section 6.8 |
| `SCAM_TOKENS` | v2 | Weighted 40/25/10 EN + SW + Sheng | v1: 10 English tokens, flat 33.33 each |

---

## 8\. Agent-to-Agent Hand-off Protocol

When an AI agent finishes a coding session:

1. Ensure all new functions have docstrings and type annotations.  
2. Update the corresponding Task ID in Section 3 from `[/] In Progress` to `[x] Done`.  
3. Add a row to Section 6 (File Change & Mutation Log).  
4. If a blocker was encountered, mark `[!] Blocked` in Section 3 with a brief explanation under the table.