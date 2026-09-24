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

| Task ID | Priority | Module | Description | Owner | Status | Dependencies |
| :---- | :---: | :---- | :---- | :---- | :---: | :---- |
| **TSK-001** | **P0** | Database | Deploy Supabase SQL schema (`merchants`, `threats`, `remediation_logs`) | Collins | `[x] Done` | None |
| **TSK-002** | **P0** | Backend Core | Initialize FastAPI monorepo scaffolding with Pydantic v2 schemas | Collins | `[x] Done` | TSK-001 |
| **TSK-003** | **P0** | AI Engine | Implement perceptual hash calculation (`hasher.py`) with `imagehash` | Dennis | `[x] Done` | TSK-002 |
| **TSK-004** | **P0** | AI Engine | Implement `rapidfuzz` Jaro-Winkler string similarity & Kenyan scam tokens | Dennis | `[ ] Pending` | TSK-002 |
| **TSK-005** | **P0** | Frontend | Scaffold Next.js 14 App Router with Tailwind CSS and shadcn/ui | Ndegwa | `[ ] Pending` | None |
| **TSK-006** | **P1** | Ingestion | Build Playwright OpenGraph public scraper (`page_scraper.py`) | Geoffrey | `[ ] Pending` | TSK-002 |
| **TSK-007** | **P1** | Ingestion | Create realistic mock dataset generator (`mock_seeder.py`) for demo | Geoffrey | `[ ] Pending` | TSK-002 |
| **TSK-008** | **P1** | AI Engine | Build composite scoring algorithm (`scorer.py`) with 5 weighted dimensions | Collins | `[ ] Pending` | TSK-003, TSK-004 |
| **TSK-009** | **P1** | Remediation | Implement AI remediation playbooks (Consumer, Platform, Safaricom) | Collins | `[ ] Pending` | TSK-008 |
| **TSK-010** | **P1** | Frontend | Implement Public Link Checker landing page with instant risk badge | Ndegwa | `[ ] Pending` | TSK-005, TSK-008 |
| **TSK-011** | **P1** | Frontend | Build Merchant Dashboard with active threat feed & forensic radar | Ndegwa | `[ ] Pending` | TSK-005, TSK-009 |
| **TSK-012** | **P1** | Alerts | Implement Telegram Bot alert dispatcher (`telegram_bot.py`) | Collins / Geoffrey | `[ ] Pending` | TSK-008 |
| **TSK-013** | **P2** | Alerts | Integrate Africa's Talking SMS sandbox gateway (`africas_talking.py`) | Geoffrey | `[ ] Pending` | TSK-008 |
| **TSK-014** | **P2** | QA / Demo | End-to-end integration test with live clone simulator for judges | All | `[ ] Pending` | TSK-010, TSK-011 |


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
- [ ] Dennis: Implement `backend/app/engine/matcher.py` with Jaro-Winkler and token weighting.  
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

---

## 7\. Prompt & Heuristic Registry

### Prompt 1: Social Media Warning Copy (`PROMPT_CONSUMER_DEFENSE_V1`)

- **Location**: `backend/app/engine/remediation.py`  
- **Purpose**: Generates high-urgency, clear consumer warnings for Instagram Stories and WhatsApp statuses.  
- **Key Constraints**: Must mention the scam handle, warn against sending deposits, state the authentic M-Pesa Buy Goods Till, and avoid ambiguous language.

### Prompt 2: Meta Brand Rights Takedown Notice (`PROMPT_META_TAKEDOWN_V1`)

- **Location**: `backend/app/engine/remediation.py`  
- **Purpose**: Generates a formal copyright/impersonation claim for Meta's enforcement portal.  
- **Key Constraints**: Must cite side-by-side logo similarity, account creation age disparity, and evidence of financial fraud.

### Prompt 3: Safaricom Fraud Escalation Report (`PROMPT_SAFARICOM_ESCALATION_V1`)

- **Location**: `backend/app/engine/remediation.py`  
- **Purpose**: Generates a formal inquiry to `fraud@safaricom.co.ke` and the 333 SMS desk.  
- **Key Constraints**: Highlights illicit collection of mobile money, recipient phone number/till, and links to the impersonated brand.

---

## 8\. Agent-to-Agent Hand-off Protocol

When an AI agent finishes a coding session:

1. Ensure all new functions have docstrings and type annotations.  
2. Update the corresponding Task ID in Section 3 from `[/] In Progress` to `[x] Done`.  
3. Add a row to Section 6 (File Change & Mutation Log).  
4. If a blocker was encountered, mark `[!] Blocked` in Section 3 with a brief explanation under the table.