# Halisi: Multi-Agent & Developer Synchronization Framework (AGENTS.md)

**Project**: Halisi, AI-powered brand impersonation detection for Kenyan businesses
**Organization**: Chiromo Tech Club, University of Nairobi
**Active team (3)**: Collins Kimanzi (Lead · Detection Engine · Design Direction), Geoffrey (API · Data · Ingestion · Alerts), Ndegwa (Frontend Application)
**Unavailable**: Dennis Kuria. His tasks were redistributed on 2026-09-27 (see section 2).
**Status**: Foundations. Hasher v2, matcher v2, scorer and backend scaffolding merged; API endpoints, frontend and deployment not started.
**Version**: 0.2.0-alpha

---

## 1. Purpose & Agent Operating Protocol

This file is the single source of truth (SSOT) for coordinating human developers and AI coding agents (Claude Code, Cursor, Copilot, Gemini, Antigravity).

### Required reading, in order

1. `AGENTS.md` (this file): tasks, owners, known issues (section 9)
2. The guide for the area you're touching:
   - Backend / database / engine → [docs/BACKEND.md](docs/BACKEND.md)
   - Frontend → [docs/FRONTEND.md](docs/FRONTEND.md)
   - Deployment / GPU → [docs/BREV_ENGINE_SETUP.md](docs/BREV_ENGINE_SETUP.md)
3. Context: [docs/data-flow.md](docs/data-flow.md), [docs/tech-stack.md](docs/tech-stack.md), [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)

### Golden rules for AI agents

1. **Read before modifying.** Read the files above before changing anything.
2. **Atomic updates.** One task card per session. Don't "fix" unrelated files while you're there; note them in section 10 instead.
3. **Register file changes.** Every create, modify or delete gets a row in section 6.
4. **Sync task status.** Starting: `[ ] Pending` → `[/] In Progress (Agent/Human)`. Mark `[x] Done` only when the task card's *Definition of Done* in BACKEND.md section 13 or FRONTEND.md section 15 is met.
5. **Prompt & heuristic versioning.** Any change to LLM prompts, scoring weights, thresholds or token lists is recorded in section 7 with a new version.
6. **The API contract is frozen.** BACKEND.md section 5 changes only together with the fixtures in `backend/` and `frontend/`, in the same change.
7. **No invented facts.** No fabricated statistics in UI copy or the pitch, no invented numbers in generated remediation text, no real businesses labelled as scammers.
8. **Never commit secrets** (`.env`, keys, tokens) or build artefacts (`__pycache__`, `.next`, `.venv`).

---

## 2. Team Ownership & Responsibilities Matrix

| Member | Role | Owns | Primary paths |
| :-- | :-- | :-- | :-- |
| **Collins Kimanzi** | Lead, Detection Engine, AI Remediation, Design Direction | Imaging, hashing, CLIP, payment score, composite scorer, remediation/LLM, Brev deployment, design tokens and motion review, pitch | `backend/app/engine/*` (except `matcher.py`), `docs/BREV_ENGINE_SETUP.md`, `deploy/` |
| **Geoffrey** | Backend API, Data, Ingestion, Alerts | Supabase schema, FastAPI core and endpoints, repository layer, security, URL parser, scraper, extractors, matcher, seeder, in-app alert dispatcher + endpoints | `backend/app/{api,core,ingestion,alerts,schemas}/*`, `backend/app/engine/matcher.py`, `database/*` |
| **Ndegwa** | Frontend Application | Next.js app, all pages and components, data layer and proxy, demo mode, i18n | `frontend/*` |
| ~~Dennis Kuria~~ | *Unavailable* | Former: engine, alerts, DB, security | Redistributed: engine/scorer → Collins; DB, alerts, security, matcher → Geoffrey |

---

## 3. Priority Task Matrix & Sprint Board

**Priority:** **P0** = blocks others · **P1** = MVP / judged feature · **P2** = only after all P0/P1 are solid.
**Build order:** see [docs/DEVELOPMENT.md section 4](docs/DEVELOPMENT.md#4-build-order-critical-path).

### Backend & engine

| Task ID | Pri | Module | Description | Owner | Status | Depends on |
| :-- | :-: | :-- | :-- | :-- | :-: | :-- |
| TSK-001 | P0 | Database | Deploy **schema v2** (`database/schema.sql`) to Supabase. v1 was reopened: it had no logo hash and no sub-score columns | Geoffrey | `[ ] Pending` | — |
| TSK-002 | P0 | Backend core | config, repository (Supabase + Memory), cache, error handlers, router, Pydantic v2 schemas mirroring v2. Reopened: only `/health` existed | Geoffrey | `[x] Done` (follow-ups in section 10) | `[x] Done` (follow-ups closed 2026-09-27) |
| TSK-003 | P0 | Engine | pHash prototype (`hasher.py` v1) | ~~Dennis~~ | `[x] Done` (v1, superseded by 015) | 002 |
| TSK-004 | P0 | Engine | Jaro-Winkler + scam tokens prototype (`matcher.py` v1) | ~~Dennis~~ | `[x] Done` (v1, superseded by 016) | 002 |
| TSK-015 | P0 | Engine | **Hasher v2**: calibrated similarity, alpha/EXIF/square normalisation, dHash, no I/O in engine | Collins | `[x] Done` | 002 |
| TSK-016 | P0 | Engine | **Matcher v2**: normalisation, homoglyphs, affix stripping, multi-handle, weighted EN/SW/Sheng lexicon, golden tests | Geoffrey | `[x] Done` (follow-ups in section 10) | `[x] Done` (v2.1: spec golden table restored) |
| TSK-021 | P0 | Ingestion + Engine | Kenyan phone/Till/Paybill/Pochi extractors (Geoffrey) + payment score (Collins) | Geoffrey / Collins | `[/] In Progress` (payment score done; extractors merged; `PaymentEvidence` adapter pending) | `[x] Done` |
| TSK-008 | P0 | Engine | **Composite scorer**: 5 dimensions, renormalisation, confidence, gate and overrides, reasons EN/SW | Collins | `[x] Done` | 015, 016, 021 |
| TSK-007 | P0 | Ingestion | Mock seeder: 3 fictional merchants × (blatant clone, subtle clone, legit competitor) + reports; exports frontend fixtures | Geoffrey | `[/] In Progress` (reopened: v1 hard-coded its scores; rework via the real engine) | `[x] Done` (reworked: scores from the real engine) |
| TSK-018 | P0 | API | Endpoints per BACKEND.md section 5 + URL parser | Geoffrey | `[x] Done` | `[x] Done` |
| TSK-019 | P1 | Security | SSRF guard, rate limits, API key, CORS fix, input limits, masking | Geoffrey | `[x] Done` | `[x] Done` (DNS-rebinding pinning is a follow-up) |
| TSK-006 | P1 | Ingestion | Tiered page scraper (seeded → OpenGraph → manual fallback) | Geoffrey | `[x] Done` | `[/] In Progress` (code + respx tests done; live fetch from Brev untested) |
| TSK-017 | P1 | Engine / Infra | CLIP embeddings + Brev GPU deployment + ngrok + threshold calibration | Collins | `[ ] Pending` | `[/] In Progress` (`embeddings.py` done with a fake model; Brev deploy + calibration pending) |
| TSK-009 | P1 | Remediation | Playbooks via NVIDIA NIM + validator + EN/SW templates | Collins | `[ ] Pending` | `[/] In Progress` (LLM + validator + EN/SW templates done; real NIM run and verified contacts pending) |
| TSK-012 | P1 | Alerts | **In-app alerts backend**: `merchant_alerts` dispatcher (create, de-dup, score rise) + `/alerts` poll + mark-read (was Telegram) | Geoffrey | `[x] Done` | `[x] Done` |
| TSK-022 | P1 | API | Community reports + `/verify/payment` lookup + override O3 | Geoffrey | `[x] Done` | `[x] Done` (no report-moderation endpoint yet) |
| TSK-031 | P1 | API / Engine | Simulator clone endpoint (real engine on synthetic targets) | Collins | `[ ] Pending` | `[x] Done` |
| TSK-013 | — | Alerts | ~~Africa's Talking SMS~~ | — | `[-] Dropped` (no SMS) | — |
| TSK-028 | P2 | Remediation | Evidence dossier PDF with SHA-256 of evidence bundle | Collins | `[ ] Pending` | 009 |
| TSK-029 | P2 | Ingestion | Takedown tracker (APScheduler re-check, time-to-takedown) | Geoffrey | `[ ] Pending` | `[x] Done` (asyncio loop, off by default) |
| TSK-030 | — | Alerts | ~~Consumer Telegram checker bot~~ | — | `[-] Dropped` (no Telegram) | — |
| TSK-036 | P2 | Channels | USSD "check a till" menu via Africa's Talking (feature phones). Stretch only; needs an AT account | Geoffrey | `[ ] Pending` | 022 |

### Frontend

| Task ID | Pri | Module | Description | Owner | Status | Depends on |
| :-- | :-: | :-- | :-- | :-- | :-: | :-- |
| TSK-005 | P0 | Frontend | Scaffold Next.js (latest, App Router) + Tailwind v4 + shadcn/ui + fonts + providers | Ndegwa | `[x] Done` | — |
| TSK-020 | P0 | Design system | Tokens, brand ornaments (guilloche, microprint, stamp, seal), restyled primitives, `/styleguide` | Collins + Ndegwa | `[/] In Progress` (reopened: files were committed empty in `a3cbb70`) | 005 |
| TSK-033 | P0 | Data layer | Server proxy with path allowlist, demo fallback fixtures, passcode session + `proxy.ts` gate (Next 16) | Ndegwa | `[/] In Progress` (reopened: files were committed empty in `a3cbb70`) | 005 |
| TSK-010 | P1 | Public | Landing + checker + **Forensic Verdict** signature sequence | Ndegwa | `[ ] Pending` | 020, 033 |
| TSK-023 | P1 | Public | Shareable result page + OG stamp image + WhatsApp share | Ndegwa | `[ ] Pending` | 010 |
| TSK-034 | P1 | Public | `/pay` till/phone check + `/report` scam report | Ndegwa | `[ ] Pending` | 033 |
| TSK-024 | P1 | Public | Halisi Verified certificate `/v/[slug]` + QR badge / story sticker | Collins (design) + Ndegwa | `[ ] Pending` | 020 |
| TSK-011 | P1 | Merchant | Dashboard: KPIs + live threat feed with handle diffs | Ndegwa | `[x] Done` | 033 |
| TSK-037 | P1 | Merchant | **In-app alerts UI**: bell + drawer, toast, tab badge, opt-in service-worker browser notifications | Ndegwa | `[x] Done` | 011, 012 |
| TSK-025 | P1 | Merchant | Threat detail Evidence Board + playbook tabs | Ndegwa | `[x] Done` | 011 |
| TSK-026 | P1 | Merchant | Onboarding wizard with logo fingerprint grid | Ndegwa | `[x] Done` | 033 |
| TSK-027 | P1 | Demo | Simulator stage mode (projector, presenter keys, phone alert) | Ndegwa | `[ ] Pending` | 010, 031 |
| TSK-032 | P1 | i18n | English / Swahili for all public pages + verdict copy | Ndegwa | `[ ] Pending` | 010 |

### Integration & demo

| Task ID | Pri | Module | Description | Owner | Status | Depends on |
| :-- | :-: | :-- | :-- | :-- | :-: | :-- |
| TSK-014 | P1 | QA / Demo | End-to-end test: public check → threat → in-app alert (phone notification) → playbook; failover drill | All (lead: Geoffrey) | `[ ] Pending` | 010, 011, 012, 017, 037 |
| TSK-035 | P1 | Pitch | 3-minute script, sourced problem statistic, Q&A prep, screen-recording backup | Collins | `[ ] Pending` | 014 |

*Legend: `[ ] Pending` | `[/] In Progress` | `[x] Done` | `[!] Blocked` | `[-] Dropped`*

**Scope decisions (2026-09-27):** no Telegram and no SMS. Merchant alerts are **in-app only** (TSK-012 backend, TSK-037 UI). **No M-Pesa API integration.** Payment signals come only from till/phone numbers found in page text, compared with the merchant's self-declared details.

---

## 4. Codebase Architecture & File Status Map

Status tags: `[DONE]` · `[V1: NEEDS REWRITE]` · `[PLANNED]` · `[SPEC]` (authoritative doc)

```text
halisi/
├── AGENTS.md                              [SPEC] coordination, tasks, change log
├── README.md                              [DONE] public project overview
├── LICENSE.md                             [DONE] MIT
├── docs/
│   ├── BACKEND.md                         [SPEC] backend + engine + API contract
│   ├── FRONTEND.md                        [SPEC] design system + pages + data layer
│   ├── BREV_ENGINE_SETUP.md               [SPEC] NVIDIA Brev GPU deployment + demo-day runbook
│   ├── DEVELOPMENT.md                     [SPEC] runbook, build order, demo script
│   ├── data-flow.md                       [SPEC] lifecycle + remediation
│   ├── tech-stack.md                      [SPEC] stack choices
│   └── calibration.md                     [PLANNED] TSK-017 threshold calibration table
├── database/
│   └── schema.sql                         [DONE v2.2, NOT DEPLOYED] TSK-001 (v2.1 merchant_alerts; v2.2 target_profiles, avatar_dhash, status_history + upgrade block)
├── backend/
│   ├── requirements.txt                   [DONE] core (UTF-8, curated)
│   ├── requirements-ml.txt                [DONE] torch + sentence-transformers (Brev)
│   ├── requirements-dev.txt               [DONE] pytest, respx, ruff
│   ├── .env.example                       [DONE]
│   ├── pyproject.toml                     [DONE] pytest + ruff config
│   ├── app/
│   │   ├── main.py                        [DONE] lifespan, explicit CORS, error handlers (TSK-002)
│   │   ├── core/ config.py repository.py cache.py logging.py errors.py security.py   [DONE] Memory + Supabase repos, SSRF guard, API key, rate limits
│   │   ├── api/ deps.py v1/router.py v1/endpoints/{check,merchants,threats,reports}.py   [DONE] all section 5 routes (TSK-018/012/022/031)
│   │   ├── services/ check.py payments.py remediation.py serializers.py simulator.py   [DONE] orchestration between API, repo and engine
│   │   ├── engine/
│   │   │   ├── hasher.py                  [DONE v2] pHash/dHash, calibrated similarity, CLIP combine (TSK-015)
│   │   │   ├── matcher.py                 [DONE v2] identity + language scoring (TSK-016)
│   │   │   ├── imaging.py                 [DONE] decode limits, EXIF, alpha→white, square pad (TSK-015)
│   │   │   ├── constants.py               [DONE] image, visual, payment, scorer and account heuristics (TSK-015/008)
│   │   │   ├── embeddings.py              [DONE code] lazy optional CLIP; GPU run pending (TSK-017)
│   │   │   ├── payment.py                 [DONE] payment score, phone/till canonicalisation, masking (TSK-021 half)
│   │   │   ├── scorer.py                  [DONE] composite scorer, O1-O4/G1, reasons EN/SW, safe action (TSK-008)
│   │   │   ├── remediation.py + prompts/  [DONE] NIM client, validator, EN/SW Jinja2 templates (TSK-009)
│   │   │   └── calibrate.py               [PLANNED] TSK-017
│   │   ├── ingestion/ url_parser.py page_scraper.py extractors.py mock_seeder.py fixtures/   [PLANNED] TSK-006/007/018/021
│   │   ├── alerts/ dispatcher.py                                                            [DONE] TSK-012 (in-app only)
│   │   └── schemas/ merchant.py threat.py check.py remediation.py report.py common.py   [DONE] Pydantic v2 (TSK-002)
│   └── tests/engine/                      [DONE] hasher, imaging, matcher, payment, scorer tests · api/ [PLANNED]
├── frontend/                              [PLANNED] TSK-005, full tree in FRONTEND.md section 3.1
├── deploy/                                [PLANNED] update.sh, systemd units (TSK-017)
└── skills-lock.json                       [DONE] agent design skills lock
```

---

## 5. Milestone Checklists

### Milestone 1: Environment & foundation

- [ ] Collins: Create GitHub repo `chiromo-tech-club/halisi`, add Geoffrey and Ndegwa, protect `main`.
- [ ] Geoffrey: Create the Supabase project, run schema v2, share credentials via the password manager (TSK-001).
- [x] Geoffrey: Backend boots in `DEMO_MODE` with no network (TSK-002).
- [x] Ndegwa: Next.js scaffold + proxy + fixtures working with the backend off (TSK-005, TSK-033).
- [ ] Collins: Brev account + credits, `halisi-engine` instance, ngrok static domain (TSK-017 part 1).

### Milestone 2: Detection brain

- [x] Collins: Hasher v2 + imaging with tests (TSK-015).
- [x] Geoffrey: Matcher v2 golden table passing (TSK-016).
- [x] Geoffrey: Kenyan phone/till extractors (TSK-021).
- [x] Collins: Scorer with required tests (TSK-008).
- [x] Geoffrey: Seeder with 3 merchants × 3 targets (TSK-007); `/check` live (TSK-018).

### Milestone 3: Remediation & alerts

- [ ] Collins: NIM playbooks + validator + EN/SW templates (TSK-009); prompts registered in section 7.
- [x] Geoffrey: In-app alert rows created and de-duplicated; `/alerts` poll works (TSK-012).
- [x] Geoffrey: Reports + payment lookup (TSK-022).

### Milestone 4: Frontend control center & public verification

- [ ] Ndegwa: Landing + Forensic Verdict (TSK-010), share page (TSK-023), pay/report (TSK-034).
- [ ] Ndegwa: Dashboard (TSK-011), in-app alerts with phone notification (TSK-037), threat detail (TSK-025), onboarding (TSK-026).
- [ ] Ndegwa + Collins: Certificate + badge (TSK-024), simulator stage (TSK-027), Swahili (TSK-032).

### Milestone 5: Rehearsal & live-demo hardening

- [ ] All: End-to-end run from public check to in-app alert on the presenter's phone (TSK-014).
- [ ] All: Failover drill Brev → laptop → offline (BREV_ENGINE_SETUP.md section 12).
- [ ] Collins: Pitch rehearsed 3× under 3:00 with a sourced statistic (TSK-035).

---

## 6. File Change & Mutation Log

*All developers and agents MUST append every file creation, modification or deletion here.*

| Date & Time (EAT) | Author / Agent | Action | File Path | Summary of Change |
| :-- | :-- | :-- | :-- | :-- |
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
| 2026-09-27 16:30 | Claude Code / Collins | CREATE / UPDATE / DELETE | `backend/app/engine/{imaging,constants,hasher}.py`, `backend/tests/engine/*`, `backend/pyproject.toml`; deleted `test_hash.py` | TSK-015 hasher v2: image limits, EXIF, alpha→white, square pad; pHash+dHash with calibrated 4→24-bit curve; CLIP combine; 58 offline tests + 3 strict xfails documenting that hashes miss crops |
| 2026-09-27 17:10 | Claude Code / Collins | UPDATE | `database/schema.sql` (v2.1), `backend/.env.example`, `backend/requirements.txt`, `AGENTS.md`, `README.md`, `docs/{BACKEND,FRONTEND,data-flow,tech-stack,DEVELOPMENT,BREV_ENGINE_SETUP}.md` | Scope change: no Telegram, no SMS, no M-Pesa API. Alerts are in-app only: `merchant_alerts` table + `/alerts` poll + mark-read (TSK-012 repurposed), bell/drawer/toast/service-worker notifications (new TSK-037). TSK-013 and TSK-030 dropped; `africastalking` removed |
| 2026-09-27 14:52 | Antigravity / Ndegwa | CREATE / UPDATE | `frontend/*`, `AGENTS.md` | TSK-005 frontend scaffold: Next.js + Tailwind v4 + shadcn/ui + design tokens + fonts. `npm run typecheck` passing. |
| 2026-09-27 14:58 | Gemini 3.1 Pro (High) / Geoffrey | CREATE | `backend/app/ingestion/extractors.py`, `backend/tests/engine/test_payment.py` | Implemented TSK-021 payment extractors (phones, tills, paybills, pochi). Added 12 passing tests |
| 2026-09-27 15:19 | Gemini 3.1 Pro (High) / Geoffrey | CREATE | `backend/app/ingestion/mock_seeder.py`, `backend/app/ingestion/fixtures/*` | Implemented TSK-007 mock seeder. Programmatically generated PIL logos and variants for 3 fictional merchants, dumped 3 merchants, 9 threats, and 5 reports to JSON and copied them to frontend fixtures |
| 2026-09-27 15:23 | Antigravity / Ndegwa | CREATE / UPDATE | `frontend/src/*`, `AGENTS.md` | TSK-020 & TSK-033 completed: Brand ornaments (Guilloche, Microprint, Stamp, Seal) and Styleguide page built. API layer configured with Next.js proxy, auth middleware, and demo JSON fixtures. |
| 2026-09-27 21:00 | Claude Code / Collins | UPDATE / MOVE | `AGENTS.md`, `backend/app/tests/engine/test_payment.py` → split into `backend/tests/ingestion/test_extractors.py` | Review of PRs #3–#4 and `a3cbb70`/`c42f224`: resolved committed conflict markers in `test_payment.py`; removed a third duplicated sprint board; reopened TSK-007 (hard-coded scores), TSK-020 and TSK-033 (10 files committed as 0 bytes). Backend suite back to 123 passed |
| 2026-09-27 22:10 | Claude Code (backend agent) / Collins | CREATE / UPDATE / DELETE | `backend/**`, `database/schema.sql` (v2.2), `docs/BACKEND.md`, `frontend/src/lib/fixtures/seed/**`, `.gitignore` | Seeder rebuilt on the real engine (deterministic); extractor `PaymentEvidence` adapter; matcher v2.1 (spec golden table passes); real Memory/Supabase repositories; all section 5 endpoints; in-app alerts; reports + payment lookup + O3; SSRF/API-key/rate-limit security; tiered scraper; simulator; NIM remediation + EN/SW templates; CLIP module; takedown tracker. 355 tests pass, ruff clean; lead verified with a live DEMO_MODE server |
| 2026-09-27 16:15 | Antigravity / Agent | CREATE / UPDATE | `backend/app/alerts/dispatcher.py`, `backend/app/schemas/alert.py`, `backend/app/api/v1/router.py`, `backend/app/core/repository.py`, `backend/tests/api/test_alerts.py` | Implemented TSK-012 (In-app alerts backend): added `Alert` schemas and repository methods, implemented `dispatch_alert` BackgroundTask, created alert endpoints `/merchants/{id}/alerts` and `/alerts/read`, and added test suite `test_alerts.py` |
| 2026-09-27 16:27 | Antigravity / Agent | UPDATE | `backend/app/alerts/dispatcher.py`, `backend/app/schemas/alert.py`, `AGENTS.md` | TSK-012 finalisation: fixed all ruff lint errors (import order, unused imports, `Optional`→`X\|None`, `timezone.UTC` alias, line-length); tightened de-dup logic (score_increase bypasses window per spec, resolved/new_threat still obey it; timezone-aware comparison). All 4 `test_alerts.py` tests pass, ruff clean. Marked TSK-012 `[x] Done` in both task matrices. |
| 2026-09-27 16:26 | Antigravity / Agent | UPDATE | `backend/app/ingestion/page_scraper.py`, `backend/tests/ingestion/test_page_scraper.py` | TSK-006: Fixed incomplete edit — added missing `from datetime import date` import (F821), sorted imports (I001), converted `Optional[X]` to `X \| None` (UP045), split long User-Agent string (E501), added `raise … from err` (B904). Used `getattr` for optional ThreatRecord fields. Fixed incorrect PNG magic-bytes assertion in tests. `ruff check` clean; 4/4 tests pass. |
| 2026-09-27 16:30 | Antigravity / Agent | CREATE | `backend/tests/conftest.py` | TSK-022: Root pytest conftest with `mem_repo` + `client` fixtures. Sets `DEMO_MODE=true` env var before app import and patches `settings.demo_mode` so `lifespan` always picks `MemoryRepository`. No network required. |
| 2026-09-27 16:30 | Antigravity / Agent | CREATE | `backend/tests/api/__init__.py` | TSK-022: Empty package init so pytest can discover `conftest.py` from the root `tests/` directory. |
| 2026-09-27 16:30 | Antigravity / Agent | UPDATE | `backend/app/api/v1/router.py` | TSK-022: Rewrote router clean — removed unused `MerchantCreate` import, replaced `Dict`/`List`/`Optional` with built-ins, fixed all E501 long lines, changed `/reports` validation error from `HTTPException` (returns `{detail}`) to `JSONResponse(422, {error:{code,message}})` matching the global DomainException shape; moved `parse_input` import inside endpoint to avoid circular load. `ruff check` clean. |
| 2026-09-27 16:30 | Antigravity / Agent | UPDATE | `AGENTS.md` | TSK-022: Marked `[x] Done` in both task matrices and the Milestone 3 checklist; appended mutation log rows. Override O3 already wired in `scorer.py` (lines 269-271). |

---


## 7. Prompt & Heuristic Registry

### 7.1 LLM prompts (location: `backend/app/engine/prompts/`)

All prompts receive only a **facts block** built from the DB. Scraped text appears only as quoted data. Output is JSON, validated so that every phone number, till and handle in the output must appear in the facts. On failure the deterministic template is used. Model default: `meta/llama-3.1-8b-instruct` via NVIDIA NIM.

| ID | Status | Purpose | Key constraints |
| :-- | :-- | :-- | :-- |
| `PROMPT_CONSUMER_DEFENSE_V1` | Retired | Story/WhatsApp warning | — |
| `PROMPT_CONSUMER_DEFENSE_V2` | Implemented (TSK-009; real NIM run pending) | Customer warning, **EN + SW** | Name the fake handle, the real handle and the real Till/Paybill; "don't send money to {number}"; ≤ 700 chars; calm, no ALL-CAPS paragraphs; natural Kenyan Swahili |
| `PROMPT_META_TAKEDOWN_V1` | Retired | Meta Brand Rights claim | Replaced: the Brand Rights Protection portal needs enrolment |
| `PROMPT_PLATFORM_TAKEDOWN_V2` | Implemented (TSK-009; real NIM run pending) | Text for the public Instagram/Facebook/TikTok impersonation report forms | Cite the **actual** hash distance and scores, first-seen date and official handle; no invented percentages (v1 hard-coded "96%") |
| `PROMPT_SAFARICOM_ESCALATION_V1` | Retired | Safaricom fraud email | — |
| `PROMPT_SAFARICOM_REPORT_V2` | Implemented (TSK-009; real NIM run pending) | Report of the receiving number/till used to defraud customers | Receiving number/till, impersonated merchant + official till, victim path; channel addresses from `constants.py` (verified and dated) |
| `PROMPT_KECIRT_REPORT_V1` | Implemented (TSK-009; real NIM run pending) | Incident report to National KE-CIRT/CC | Computer Misuse and Cybercrimes Act 2018 framing; factual; contact verified before the demo |

### 7.2 Scoring heuristics (location: `backend/app/engine/constants.py`)

| ID | Version | Value | Notes |
| :-- | :-- | :-- | :-- |
| `WEIGHTS` | v2 | visual .30 · identity .25 · payment .25 · language .10 · account .10 | v1 (docs only): visual .25, lexical .20, temporal .25, payment .20, engagement .10. Temporal was cut because account age is rarely observable |
| `THRESHOLDS` | v2 | impersonation ≥ 70 · suspicious ≥ 40 | v1 was inconsistent (75 in data-flow, 80 in README) |
| `HASH_SIMILARITY` | v2 (checked on generated set) | 100 at ≤ 4 bits, 0 at ≥ 24 | v1: `100 − d/64·100` scored unrelated images ~50 %. Generated set: edits 0–8 bits, unrelated 30–40, crops 10–28 (missed). Re-check on real seed logos in TSK-017 |
| `CLIP_SIMILARITY` | v1 (uncalibrated) | 100 at cosine ≥ 0.93, 0 at ≤ 0.80 | Calibrate in TSK-017 |
| `OVERRIDES` | v2 | G1 resemblance < 50 → cap 39 · O2 (visual ≥ 80 or identity ≥ 90) + payment 100 from a personal/Pochi/reported number → floor 90 · O3 confirmed report and resemblance ≥ 50 → floor 85 · O4 confidence < 0.5 → max suspicious | v1 O2 used resemblance ≥ 80, which floored the similar-named competitor (identity 88) at 90. v1 O3 had no resemblance condition. BACKEND.md section 6.8 |
| `PAYMENT` | v2 | unregistered phone 100 (close) / 60 · unregistered till/paybill 50 (close) / 25 · Pochi or reported 100 · official only 0 | v1: any unregistered number 100. Tills need a registered business, so they're weaker evidence |
| `LOGO_CONTRADICTS` | v1 | visual ≤ 20 → name-only "close resemblance" needs identity ≥ 90 | Stops `nairobi_bakery` + own number reading as suspicious (was 45) |
| `ACCOUNT` | v2 | age < 30 d 90 · < 90 d 60 · < 365 d 30 · else 10; < 12 posts 60; < 300 followers (visual ≥ 80) 70; known-but-normal 10 | v1 first-seen < 7 d signal removed (always true on a first check) |
| `SCAM_TOKENS` | v2.1 | Weighted 40/25/10 EN + SW + Sheng, **word-boundary** matching; text with no phrases = 0.0 | v2 matched substrings ("leo tu" fired inside "Leo tunauza") and returned None for clean text |
| `MATCHER` | v2.1 | Jaro-Winkler weight 0.5 → 0.3; "distinctive remainder" rule: after stripping the shared prefix/suffix, a remainder differing by > 2 edits pulls the score toward the remainder's similarity (weight 0.65); plain truncation gets edit similarity without the prefix bonus | Fixes the prefix bias: `nairobi_bakery` 77.7 → 47.6, `nairobisneakerhub` 88.4 → 43.2; must-hit cases still 100. Spec golden table restored |

---

## 8. Agent-to-Agent Hand-off Protocol

When an AI agent finishes a coding session:

1. All new functions have docstrings and type annotations; `ruff check . && pytest -q` (backend) or `npm run lint && npm run typecheck && npm run build` (frontend) pass.
2. Update the task in section 3 (`[/]` → `[x]` only if its Definition of Done is met).
3. Add a row to section 6.
4. If blocked, mark `[!] Blocked` in section 3 and add a line to section 10.
5. Leave a 3-line summary in the PR description: what changed, how it was verified, what's next.

---

## 9. Architecture Review: 2026-09-27 (Claude Code)

Findings from the full-repo review, and what was done about each. **Open** items are owned by the task shown.

| # | Severity | Finding | Resolution |
| :-- | :-- | :-- | :-- |
| 1 | High | `hasher.compare_hashes` normalises over 64 bits, so unrelated images score ~50 % visual similarity and push innocent pages toward "suspicious" | Fixed (TSK-015): calibrated curve, unrelated logos now score 0 |
| 2 | High | `schema.sql` v1 couldn't store the logo hash or sub-scores; three different schemas existed (schema.sql, DEVELOPMENT.md, Pydantic) | Fixed: schema v2 written. Deploy → TSK-001; Pydantic → TSK-002 |
| 3 | High | The plan relied on data we can't get: account creation date (25 % weight) isn't in public IG/FB metadata; unauthenticated Instagram scraping is routinely blocked, especially from datacenter IPs like Brev's | Fixed in spec: "account" dimension re-weighted to 10 % with renormalisation + confidence; tiered acquisition with a manual fallback (BACKEND.md section 7.2) |
| 4 | High | No answer to "is this the real page?": an exact official handle scored 100 % "typosquatting" | Fixed in spec: O1 official short-circuit, `official` verdict |
| 5 | High | Matcher: no separator or homoglyph normalisation, and Jaro-Winkler prefix bias flags every `nairobi_*` handle | Fixed (TSK-016): normalisation, homoglyph folding, affix stripping, containment. Golden thresholds need tightening (section 10) |
| 6 | Medium | `main.py` CORS `allow_origins=["*"]` + `allow_credentials=True`: invalid, and Starlette reflects any origin | Fixed (TSK-002): explicit origins from `CORS_ORIGINS` |
| 7 | Medium | User-supplied URLs fetched server-side with no SSRF guard or size limits (the avatar URL comes from attacker-controlled OG tags) | Open → TSK-019 |
| 8 | Medium | `requirements.txt` was UTF-16 (PowerShell `pip freeze`), in the wrong folder, Windows-specific and missing supabase/settings/test deps | Fixed: curated UTF-8 `backend/requirements{,-ml,-dev}.txt` |
| 9 | Medium | `.gitignore` had `/_pycache_` (typo), so Python 3.14 `.pyc` files were committed | Fixed |
| 10 | Medium | Tests were print scripts that always exit 0; `test_hash.py` needs the internet | Hasher part fixed (TSK-015: pytest, generated images, `test_hash.py` deleted); matcher part fixed (TSK-016, root `test_matcher.py` deleted) |
| 11 | Medium | Threshold inconsistent (75 vs 80); README overclaimed "Automated Safaricom & Meta takedowns" and "checks Safaricom records" | Fixed: single threshold 70; README reworded; human-in-the-loop stated |
| 12 | Medium | Telegram snippet used legacy Markdown, which fails on `_` in handles | Moot: Telegram dropped 2026-09-27; alerts are in-app |
| 13 | Medium | Ownership contradictions: Collins listed as UI/UX but assigned backend; milestones said Dennis while the board said Collins; docs referenced a `docs/` folder that didn't exist | Fixed: section 2 rewritten; docs moved to `docs/` |
| 14 | Low | Pydantic v1 `class Config` in v2 code; `id: str` instead of UUID | Fixed (TSK-002) |
| 15 | Low | `build_monorepo.py` would overwrite real files if re-run | Fixed: deleted (it's in git history) |
| 16 | Low | Unsourced pitch statistic ("over 70% of social commerce…") | Open → TSK-035: source it or cut it |
| 17 | Info | Legal/ethical: third-party phone numbers are personal data (Data Protection Act 2019); "safe" verdicts create liability | Fixed in spec: masking, "never say safe" wording rules |
| 18 | Info | Contact channels (Safaricom fraud, KE-CIRT/CC) and the Meta portal claims weren't verified | Open → TSK-009: verify and date in `constants.py` |

---

## 10. Blockers & Notes

- *(no blockers. Add `[!]` items here as `TSK-xxx: reason (owner, date)`)*
- Brev GPU credits: confirm the amount with the organisers before sizing the instance (BREV_ENGINE_SETUP.md section 3).
- Hash-only visual scoring misses cropped logos. Until CLIP runs on Brev (TSK-017), cropped-logo clones rely on identity + payment signals (the subtle seeded clones still score 90).
- **Not yet exercised against real services:** Supabase (TSK-001; the repo is tested against a fake client), NVIDIA NIM (TSK-009, LLM mocked in tests), live Instagram/OpenGraph fetch from Brev (TSK-006).
- **Contacts:** `VERIFIED_ON = None` for the Safaricom and KE-CIRT/CC channels. The addresses are placeholders, and the platform report links point at help-centre home pages. Verify and date them before the demo (TSK-009); the frontend must show a "confirm contact before sending" note while `contacts_verified` is false.
- **Demo gotchas:** seeded clones already have threats and alerts, so re-checking them creates no new alert. For the live "phone buzzes" moment use `/simulator` or a new handle. DEMO_MODE's in-memory store reseeds on restart.
- **Security follow-ups:** pin the resolved IP for fetches (a short-TTL DNS-rebinding race is possible); add a report-moderation endpoint (TSK-022).
- **Contract:** section 5.11 of BACKEND.md lists additive changes (merchant `id` on the public profile, 201s, ThreatDetail timestamps, playbook `language` / `contacts_verified` / `generator`, error codes, relative asset URLs). Frontend must copy `src/lib/fixtures/seed/assets/` to `public/seed/` for fixture mode.
- Swahili strings (reasons, safe action, templates) need a fluent speaker's review (TSK-032).
- Branch hygiene: rebase on `main` before opening a PR. Old bases re-added `.pyc` files, duplicated the board and committed conflict markers. Check `git diff --stat` for 0-byte files before committing (commit `a3cbb70` saved 10 frontend files empty).
| 2026-09-27 18:00 | Antigravity / Agent | CREATE / UPDATE | rontend/src/app/dashboard/*, rontend/src/app/onboarding/*, rontend/src/components/merchant/* | Implemented Merchant Dashboard layout, pages, and components including live threats feed, Evidence Board, Onboarding wizard and In-app alerts.
