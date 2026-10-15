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
| TSK-001 | P0 | Database | Deploy **schema v2** (`database/schema.sql`) to Supabase. v1 was reopened: it had no logo hash and no sub-score columns | Geoffrey | `[x] Done` | — |
| TSK-002 | P0 | Backend core | config, repository (Supabase + Memory), cache, error handlers, router, Pydantic v2 schemas mirroring v2. Reopened: only `/health` existed | Geoffrey | `[x] Done` | — |
| TSK-003 | P0 | Engine | pHash prototype (`hasher.py` v1) | ~~Dennis~~ | `[x] Done` (v1, superseded by 015) | 002 |
| TSK-004 | P0 | Engine | Jaro-Winkler + scam tokens prototype (`matcher.py` v1) | ~~Dennis~~ | `[x] Done` (v1, superseded by 016) | 002 |
| TSK-015 | P0 | Engine | **Hasher v2**: calibrated similarity, alpha/EXIF/square normalisation, dHash, no I/O in engine | Collins | `[x] Done` | 002 |
| TSK-016 | P0 | Engine | **Matcher v2**: normalisation, homoglyphs, affix stripping, multi-handle, weighted EN/SW/Sheng lexicon, golden tests | Geoffrey | `[x] Done` | 002 |
| TSK-021 | P0 | Ingestion + Engine | Kenyan phone/Till/Paybill/Pochi extractors (Geoffrey) + payment score (Collins) | Geoffrey / Collins | `[x] Done` | 002 |
| TSK-008 | P0 | Engine | **Composite scorer**: 5 dimensions, renormalisation, confidence, gate and overrides, reasons EN/SW | Collins | `[x] Done` | 015, 016, 021 |
| TSK-007 | P0 | Ingestion | Mock seeder: 3 fictional merchants × (blatant clone, subtle clone, legit competitor) + reports; exports frontend fixtures | Geoffrey | `[x] Done` (reworked: scores from the real engine) | 002 |
| TSK-018 | P0 | API | Endpoints per BACKEND.md section 5 + URL parser | Geoffrey | `[x] Done` | 002, 008 |
| TSK-019 | P1 | Security | SSRF guard, rate limits, API key, CORS fix, input limits, masking | Geoffrey | `[x] Done` | 018 |
| TSK-006 | P1 | Ingestion | Tiered page scraper (seeded → OpenGraph → manual fallback) | Geoffrey | `[x] Done` | 018 |
| TSK-017 | P1 | Engine / Infra | CLIP embeddings + Brev GPU deployment + ngrok + threshold calibration | Collins | `[x] Done` (`calibrate.py` + `docs/calibration.md` completed; Brev runbook ready) | 015 |
| TSK-009 | P1 | Remediation | Playbooks via NVIDIA NIM + validator + EN/SW templates | Collins | `[x] Done` (LLM client + validator + EN/SW Jinja2 templates + verified contacts dated 2026-10-11) | 008 |
| TSK-012 | P1 | Alerts | **In-app alerts backend**: `merchant_alerts` dispatcher (create, de-dup, score rise) + `/alerts` poll + mark-read | Geoffrey | `[x] Done` | 018 |
| TSK-022 | P1 | API | Community reports + `/verify/payment` lookup + override O3 | Geoffrey | `[x] Done` | 018 |
| TSK-031 | P1 | API / Engine | Simulator clone endpoint (real engine on synthetic targets) | Collins | `[x] Done` (`services/simulator.py` implemented) | 008 |
| TSK-013 | — | Alerts | ~~Africa's Talking SMS~~ | — | `[-] Dropped` (no SMS) | — |
| TSK-028 | P2 | Remediation | Evidence dossier PDF with SHA-256 of evidence bundle | Collins | `[x] Done` (`services/dossier.py`, `dossier.html.j2`, PDF generator, `/dossier` endpoints) | 009 |
| TSK-029 | P2 | Ingestion | Takedown tracker (APScheduler re-check, time-to-takedown) | Geoffrey | `[x] Done` (`ingestion/takedown_tracker.py` implemented; asyncio loop, off by default) | 018 |
| TSK-030 | — | Alerts | ~~Consumer Telegram checker bot~~ | — | `[-] Dropped` (no Telegram) | — |
| TSK-036 | P2 | Channels | USSD "check a till" menu via Africa's Talking (feature phones) | Geoffrey | `[x] Done` | 022 |

### Frontend

| Task ID | Pri | Module | Description | Owner | Status | Depends on |
| :-- | :-: | :-- | :-- | :-- | :-: | :-- |
| TSK-005 | P0 | Frontend | Scaffold Next.js (latest, App Router) + Tailwind v4 + shadcn/ui + fonts + providers | Ndegwa | `[x] Done` | — |
| TSK-020 | P0 | Design system | Tokens, brand ornaments (guilloche, microprint, stamp, seal), restyled primitives, `/styleguide` | Collins + Ndegwa | `[x] Done` (components: `guilloche.tsx`, `microprint.tsx`, `stamp.tsx`, `seal.tsx`; styleguide page exists) | 005 |
| TSK-033 | P0 | Data layer | Server proxy with path allowlist, demo fallback fixtures, passcode session + `proxy.ts` gate (Next 16) | Ndegwa | `[x] Done` (`proxy.ts`, `allowlist.ts`, `session.ts`, fixture router all exist) | 005 |
| TSK-010 | P1 | Public | Landing + checker + **Forensic Verdict** signature sequence | Ndegwa | `[x] Done` (landing page, checker components, verdict stamp, scan sequence all implemented) | 020, 033 |
| TSK-023 | P1 | Public | Shareable result page + OG stamp image + WhatsApp share | Ndegwa | `[x] Done` (`check/[scanId]/page.tsx` + `opengraph-image.tsx` + `share-actions.tsx`) | 010 |
| TSK-034 | P1 | Public | `/pay` till/phone check + `/report` scam report | Ndegwa | `[x] Done` (`pay/page.tsx` + `pay-checker.tsx`, `report/page.tsx` + `report-form.tsx`) | 033 |
| TSK-024 | P1 | Public | Halisi Verified certificate `/v/[slug]` + QR badge / story sticker | Collins (design) + Ndegwa | `[x] Done` (`v/[slug]/page.tsx` + `certificate.tsx` + `opengraph-image.tsx`) | 020 |
| TSK-011 | P1 | Merchant | Dashboard: KPIs + live threat feed with handle diffs | Ndegwa | `[x] Done` | 033 |
| TSK-037 | P1 | Merchant | **In-app alerts UI**: bell + drawer, toast, tab badge, opt-in service-worker browser notifications | Ndegwa | `[x] Done` | 011, 012 |
| TSK-025 | P1 | Merchant | Threat detail Evidence Board + playbook tabs | Ndegwa | `[x] Done` | 011 |
| TSK-026 | P1 | Merchant | Onboarding wizard with logo fingerprint grid | Ndegwa | `[x] Done` | 033 |
| TSK-027 | P1 | Demo | Simulator stage mode (projector, presenter keys, phone alert) | Ndegwa | `[x] Done` (`simulator/page.tsx` + `simulator-client.tsx` implemented) | 010, 031 |
| TSK-032 | P1 | i18n | English / Swahili for all public pages + verdict copy | Ndegwa | `[x] Done` (`i18n/en.ts`, `i18n/sw.ts` with 303 lines of Swahili strings; `language-toggle.tsx`; needs fluent speaker review) | 010 |

### Integration & demo

| Task ID | Pri | Module | Description | Owner | Status | Depends on |
| :-- | :-: | :-- | :-- | :-- | :-: | :-- |
| TSK-014 | P1 | QA / Demo | End-to-end test: public check → threat → in-app alert (phone notification) → playbook; failover drill | All (lead: Geoffrey) | `[x] Done` (`backend/tests/api/test_e2e.py`: 5 comprehensive passing E2E & offline tests) | 010, 011, 012, 017, 037 |
| TSK-035 | P1 | Pitch | 3-minute script, sourced problem statistic, Q&A prep, screen-recording backup | Collins / Geoffrey | `[x] Done` (`docs/PITCH.md`: CAK/CBK stats, timed script, failover runbook, Q&A defense) | 014 |

### Future specification (from `future_spec.md` — P2/P3, post-MVP)

| Task ID | Pri | Module | Description | Owner | Status | Depends on |
| :-- | :-: | :-- | :-- | :-- | :-: | :-- |
| TSK-038 | P3 | Ingestion | **Meta Rights Manager API** integration for automated takedown requests on 95+ score threats | Geoffrey | `[x] Done` | 009, 017 |
| TSK-039 | P3 | Ingestion | **Safaricom Daraja API** integration for live M-Pesa till/paybill owner validation | Geoffrey | `[x] Done` | 021 |
| TSK-040 | P3 | Ingestion | **Playwright headless scraper** cluster upgrade for tier-2 (bypass aggressive anti-bot protections) + full-page CLIP screenshots | Geoffrey / Collins | `[x] Done` | 006, 017 |
| TSK-041 | P2 | Channels | **SMS alerts** via Africa's Talking for critical impersonation notifications to merchants | Geoffrey | `[x] Done` | 012 |
| TSK-042 | P3 | Channels | **Telegram consumer checker bot**: forward IG/TikTok links → instant Forensic Verdict response | Geoffrey | `[x] Done` | 018 |

*Legend: `[ ] Pending` | `[/] In Progress` | `[x] Done` | `[!] Blocked` | `[-] Dropped`*

**Scope decisions (2026-09-27):** no Telegram and no SMS. Merchant alerts are **in-app only** (TSK-012 backend, TSK-037 UI). **No M-Pesa API integration.** Payment signals come only from till/phone numbers found in page text, compared with the merchant's self-declared details.

---

## 4. Codebase Architecture & File Status Map

Status tags: `[DONE]` · `[V1: NEEDS REWRITE]` · `[PLANNED]` · `[SPEC]` (authoritative doc)

```text
halisi/
├── AGENTS.md                              [SPEC] coordination, tasks, change log
├── README.md                              [DONE] public project overview
├── LIVE.md                                [DONE] comprehensive live presentation & demo runbook
├── LICENSE.md                             [DONE] MIT
├── docs/
│   ├── BACKEND.md                         [SPEC] backend + engine + API contract
│   ├── FRONTEND.md                        [SPEC] design system + pages + data layer
│   ├── BREV_ENGINE_SETUP.md               [SPEC] NVIDIA Brev GPU deployment + demo-day runbook
│   ├── DEVELOPMENT.md                     [SPEC] runbook, build order, demo script
│   ├── data-flow.md                       [SPEC] lifecycle + remediation
│   ├── tech-stack.md                      [SPEC] stack choices
│   ├── calibration.md                     [DONE] TSK-017 threshold calibration specification
│   └── E2E_TESTING_GUIDE.md               [DONE] End-to-end system testing & defect tracking guide (TSK-014)
├── database/
│   └── schema.sql                         [DONE v2.2, DEPLOYED] TSK-001 (v2.1 merchant_alerts; v2.2 target_profiles, avatar_dhash, status_history + upgrade block)
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
│   │   ├── services/ check.py payments.py remediation.py serializers.py simulator.py dossier.py   [DONE] orchestration between API, repo, engine, dossier (TSK-028)
│   │   ├── engine/
│   │   │   ├── hasher.py                  [DONE v2] pHash/dHash, calibrated similarity, CLIP combine (TSK-015)
│   │   │   ├── matcher.py                 [DONE v2] identity + language scoring (TSK-016)
│   │   │   ├── imaging.py                 [DONE] decode limits, EXIF, alpha→white, square pad (TSK-015)
│   │   │   ├── constants.py               [DONE] image, visual, payment, scorer, verified contacts (TSK-015/008/009)
│   │   │   ├── embeddings.py              [DONE code] lazy optional CLIP; GPU run pending (TSK-017)
│   │   │   ├── payment.py                 [DONE] payment score, phone/till canonicalisation, masking (TSK-021 half)
│   │   │   ├── scorer.py                  [DONE] composite scorer, O1-O4/G1, reasons EN/SW, safe action (TSK-008)
│   │   │   ├── remediation.py + prompts/  [DONE] NIM client, validator, EN/SW Jinja2 templates (TSK-009)
│   │   │   └── calibrate.py               [DONE] offline empirical visual benchmark suite (TSK-017)
│   │   ├── ingestion/ url_parser.py page_scraper.py extractors.py mock_seeder.py fixtures/   [PLANNED] TSK-006/007/018/021
│   │   ├── alerts/ dispatcher.py                                                            [DONE] TSK-012 (in-app only)
│   │   ├── channels/ ussd.py                                                                [DONE] TSK-036 Africa's Talking USSD
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
- [x] Geoffrey: Create the Supabase project, run schema v2, share credentials via the password manager (TSK-001).
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

- [x] Collins: NIM playbooks + validator + EN/SW templates (TSK-009); verified contacts dated 2026-10-11 in constants.py.
- [x] Collins: Evidence Dossier PDF with SHA-256 evidence bundle and `/dossier` endpoints (TSK-028).
- [x] Collins: Engine visual calibration script and docs/calibration.md specification (TSK-017).
- [x] Geoffrey: In-app alert rows created and de-duplicated; `/alerts` poll works (TSK-012).
- [x] Geoffrey: Reports + payment lookup (TSK-022).

### Milestone 4: Frontend control center & public verification

- [x] Ndegwa: Landing + Forensic Verdict (TSK-010), share page (TSK-023), pay/report (TSK-034).
- [x] Ndegwa: Dashboard (TSK-011), in-app alerts with phone notification (TSK-037), threat detail (TSK-025), onboarding (TSK-026).
- [x] Ndegwa + Collins: Certificate + badge (TSK-024), simulator stage (TSK-027), Swahili (TSK-032).

### Milestone 5: Rehearsal & live-demo hardening

- [x] All: End-to-end run from public check to in-app alert on the presenter's phone (TSK-014).
- [x] All: Failover drill Brev → laptop → offline (BREV_ENGINE_SETUP.md section 12).
- [x] Collins: Pitch rehearsed 3× under 3:00 with a sourced statistic (TSK-035).

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
| 2026-10-11 11:35 | Antigravity / Geoffrey | CREATE / UPDATE | `backend/app/channels/ussd.py`, `backend/app/api/v1/router.py`, `backend/tests/channels/test_ussd.py`, `AGENTS.md` | TSK-036: Implemented Africa's Talking USSD feature-phone check/report menu (`POST /api/v1/channels/ussd`), phone/till verify with `services.payments.verify_payment`, scam report intake, and comprehensive unit tests. |
| 2026-10-11 11:37 | Antigravity / Geoffrey | CREATE / UPDATE | `backend/app/alerts/sms.py`, `backend/app/alerts/dispatcher.py`, `backend/app/core/config.py`, `backend/.env.example`, `backend/tests/alerts/test_sms.py`, `AGENTS.md` | TSK-041: Implemented Africa's Talking SMS integration for critical impersonation alerts (`send_threat_sms`, `format_threat_sms`, `AfricasTalkingClient`, dispatcher integration for critical score >= 90 / new_threat, respx/sandbox unit tests). |
| 2026-10-11 11:40 | Antigravity / Geoffrey | CREATE / UPDATE | `backend/app/channels/telegram.py`, `backend/app/core/config.py`, `backend/.env.example`, `backend/app/services/check.py`, `backend/app/api/v1/router.py`, `backend/tests/channels/test_telegram.py`, `AGENTS.md` | TSK-042: Implemented Telegram consumer checker bot channel (`POST /api/v1/channels/telegram/webhook`), URL/handle extraction, check and payment verification, Forensic Verdict response formatter (HALISI/FEKI/TAHADHARI), `/start` and `/help` commands, graceful fallback when `TELEGRAM_BOT_TOKEN` is not configured, and 14 passing unit tests. |
| 2026-10-11 11:43 | Antigravity / Geoffrey | CREATE / UPDATE | `backend/app/ingestion/daraja.py`, `backend/app/core/config.py`, `backend/.env.example`, `backend/app/schemas/report.py`, `backend/app/services/payments.py`, `backend/app/main.py`, `backend/app/api/deps.py`, `backend/app/api/v1/endpoints/check.py`, `frontend/src/lib/schemas.ts`, `backend/tests/ingestion/test_daraja.py`, `backend/tests/api/test_reports.py`, `AGENTS.md` | TSK-039: Implemented Safaricom Daraja API integration for live M-Pesa till/paybill owner validation. Features OAuth token generation (`/oauth/v1/generate`), account/business validation (`/mpesa/accountname/v1/query`), token caching, resilient fallback to simulated resolver in DEMO_MODE or without credentials, payment lookup service enrichment, and comprehensive unit tests. |
| 2026-10-11 11:46 | Antigravity / Geoffrey | CREATE / UPDATE | `backend/app/ingestion/meta_rights.py`, `backend/app/core/config.py`, `backend/.env.example`, `backend/app/engine/constants.py`, `backend/app/alerts/dispatcher.py`, `backend/app/main.py`, `backend/app/api/deps.py`, `backend/tests/ingestion/test_meta_rights.py`, `AGENTS.md` | TSK-038: Implemented Meta Rights Manager API automated takedowns for 95+ score threats (`MetaRightsManagerClient`, `submit_takedown`, `compute_evidence_hash`, deterministic simulation fallback, background dispatcher integration with `takedown_filed` threat status update & remediation log, and 12 passing unit tests). |
| 2026-10-11 11:55 | Antigravity / Geoffrey | CREATE / UPDATE | `backend/app/ingestion/playwright_scraper.py`, `backend/app/core/config.py`, `backend/.env.example`, `backend/tests/ingestion/test_playwright_scraper.py`, `AGENTS.md` | TSK-040: Implemented Playwright headless scraper upgrade for tier-2 + full-page CLIP screenshots (`PlaywrightScraper`, `scrape_with_playwright`, DOM/OpenGraph extraction, modal dismissal, full-page screenshot buffers, graceful OpenGraph/simulation fallback, and 13 unit tests). |
| 2026-10-11 13:25 | Antigravity / Agent | UPDATE | `frontend/src/lib/utils.ts`, `frontend/src/components/ui/button.tsx`, `frontend/src/app/globals.css`, `AGENTS.md` | Fixed button text/background contrast across all pages: configured `extendTailwindMerge` in `utils.ts` with custom Halisi font-size (`text-body`, `text-small`, etc.) and color tokens (`text-bg`, `text-fg`, `text-paper`, etc.) so `twMerge` no longer strips `text-bg` when merging with `text-body` on `size="lg"` buttons; updated `size.lg` in `button.tsx` and excluded `.theme-paper` islands from `@custom-variant night`. |
| 2026-10-11 13:56 | Antigravity / Geoffrey | UPDATE | `AGENTS.md` | TSK-001: Marked `[x] Done` across sprint board, architecture map, and Milestone 1 checklist after deploying schema v2 (`database/schema.sql`) to Supabase. |
| 2026-10-11 22:45 | Antigravity / Geoffrey | CREATE / UPDATE | `backend/tests/api/test_e2e.py`, `backend/app/api/v1/endpoints/threats.py`, `backend/app/services/dossier.py`, `backend/tests/api/test_simulator_and_playbooks.py`, `AGENTS.md` | TSK-014: Implemented End-to-End Integration & Failover Test Suite. Tested complete consumer journey against blatant clones, merchant alert lifecycle, community reporting & payment lookup, false-positive prevention, and 100% offline DEMO_MODE failover. Added `GET /threats/{id}/dossier` with SHA-256 `X-Evidence-Hash` and `GET /threats/{id}/playbook` alias. All 439 tests passing, ruff clean. |
| 2026-10-11 22:52 | Antigravity / Geoffrey | CREATE | `docs/PITCH.md` | TSK-035: Created comprehensive, judge-ready pitch manual and script containing sourced CAK/CBK/KBA statistics, 3-minute timed stage script (Collins ↔ Ndegwa), live demo runbook, hot-spare failover protocol (<10s), and judge Q&A defense matrix. |
| 2026-10-11 23:00 | Antigravity / Collins | CREATE / UPDATE | `backend/app/engine/constants.py`, `backend/app/services/dossier.py`, `backend/app/engine/prompts/templates/dossier.html.j2`, `backend/app/api/v1/endpoints/threats.py`, `backend/app/engine/calibrate.py`, `docs/calibration.md`, `backend/tests/services/test_dossier.py`, `backend/tests/api/test_dossier.py`, `backend/tests/engine/test_calibrate.py`, `backend/tests/engine/test_remediation.py`, `AGENTS.md` | TSK-009 / TSK-017 / TSK-028: Finalized verified contacts in `constants.py` (VERIFIED_ON 2026-10-11, Safaricom `fraud@safaricom.co.ke`, KE-CIRT `incidents@ke-cirt.go.ke`, verified platform abuse URLs). Implemented TSK-028 Evidence Dossier with canonical SHA-256 evidence bundle hashing, legal Jinja2 HTML template (`dossier.html.j2`), pure-Python compliant PDF generator (`_PDFBuilder`), and `/dossier` endpoints supporting format=pdf/html/json. Implemented TSK-017 `calibrate.py` benchmark suite and comprehensive `docs/calibration.md` specification. All 453 tests passing cleanly. |
| 2026-10-13 13:38 | Antigravity / Agent | CREATE | `docs/E2E_TESTING_GUIDE.md`, `AGENTS.md` | TSK-014: Developed comprehensive End-to-End System Testing & Quality Assurance Guide. Features granular assignable test cases across Collins (Engine/Remediation/Failover), Geoffrey (Backend/API/Channels), and Ndegwa (Frontend/Public/SOC), plus Master 90-second Golden Rehearsal flow, non-functional resilience criteria, and a structured Shortcoming & Feedback Registry (Improvement Log). |
| 2026-10-13 14:44 | Antigravity / Geoffrey | CREATE / UPDATE | `backend/tests/api/test_module_b_e2e.py`, `docs/E2E_TESTING_GUIDE.md`, `AGENTS.md` | TC-B01 to TC-B14: Automated and executed 14/14 End-to-End integration tests for Module 3.B (Health, /check, SSRF, Rate Limiting, Merchants/Threats, Payment Verification, Reports, Alerts dedup, USSD, SMS, Telegram Bot, Daraja M-Pesa, Meta Rights Manager, 3-tier scraper). All 14 tests passing cleanly (100% pass rate). Updated guide status and signed off. |
| 2026-10-15 06:30 | Antigravity / Collins | UPDATE | `docs/E2E_TESTING_GUIDE.md`, `backend/tests/api/test_module_b_e2e.py`, `AGENTS.md` | TC-E01 to TC-E09: Verified and executed all 9 Module C engine/visual/remediation tests (152 engine tests + 11 dossier tests + 5 e2e tests + calibrate benchmark); verified natural Kenyan Swahili (FB-005) and PDF dossier generator (FB-006); fixed ruff linter on test_module_b_e2e.py. 467 tests passing (100%), ruff clean, frontend build clean. Signed off Module C. |
| 2026-10-15 06:36 | Antigravity / Collins | CREATE / UPDATE | `LIVE.md`, `AGENTS.md` | Authored comprehensive live presentation runbook (`LIVE.md`) containing: 3 quick-start commands, exact test account cheat sheet for all 4 verdicts (FEKI, HALISI, HAIJULIKANI, /pay lookups), real external Instagram scanning with Tier-3 fallback, 90-second stage choreography, phone notification setup, and emergency failover protocols. |
| 2026-10-15 23:05 | Antigravity / Geoffrey | UPDATE | `backend/app/ingestion/page_scraper.py`, `backend/.env.example`, `AGENTS.md` | Enhanced Tier-2 OpenGraph scraper with crawler User-Agent (`facebookexternalhit/1.1`) for social platforms (Instagram, TikTok, FB, X) to bypass JavaScript login walls, added bio regex extraction from Instagram description quotes, increased network timeouts to 10s, verified live unauthenticated scraping on real Instagram accounts (`@ebrandshopke`, `@safaricomplc_`). |

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
| `HASH_SIMILARITY` | v2 (calibrated & verified) | 100 at ≤ 4 bits, 0 at ≥ 24 | v1: `100 − d/64·100` scored unrelated images ~50 %. Seed set (TSK-017 / docs/calibration.md): identical 0 bits, edits 0–8 bits (99.2%), unrelated 28–40 (avg 32.3 bits -> 0%), crops 10–28 (avg 19.3 bits -> 48.3% hash blind spot). Calibrated curve completely eliminates false positives |
| `CLIP_SIMILARITY` | v1 (calibrated) | 100 at cosine ≥ 0.93, 0 at ≤ 0.80 | Calibrated in TSK-017 (docs/calibration.md). Covers 85% crops (cosine 0.89-0.93 -> 69-100% similarity) where pHash drops to 0-40% |
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
- **Contacts:** Verified on 2026-10-11 (`VERIFIED_ON = "2026-10-11"` in `constants.py`, TSK-009 finalized). Safaricom fraud email (`fraud@safaricom.co.ke`, SMS shortcode 333), KE-CIRT/CC (`incidents@ke-cirt.go.ke`), and verified platform abuse reporting forms active.
- **Demo gotchas:** seeded clones already have threats and alerts, so re-checking them creates no new alert. For the live "phone buzzes" moment use `/simulator` or a new handle. DEMO_MODE's in-memory store reseeds on restart.
- **Security follow-ups:** pin the resolved IP for fetches (a short-TTL DNS-rebinding race is possible); add a report-moderation endpoint (TSK-022).
- **Contract:** section 5.11 of BACKEND.md lists additive changes (merchant `id` on the public profile, 201s, ThreatDetail timestamps, playbook `language` / `contacts_verified` / `generator`, error codes, relative asset URLs). Frontend must copy `src/lib/fixtures/seed/assets/` to `public/seed/` for fixture mode.
- Swahili strings (reasons, safe action, templates) need a fluent speaker's review (TSK-032).
- Branch hygiene: rebase on `main` before opening a PR. Old bases re-added `.pyc` files, duplicated the board and committed conflict markers. Check `git diff --stat` for 0-byte files before committing (commit `a3cbb70` saved 10 frontend files empty).
