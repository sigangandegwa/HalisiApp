# Halisi: Multi-Agent & Developer Synchronization Framework (AGENTS.md)

**Project**: Halisi, AI-powered brand impersonation detection for Kenyan businesses
**Organization**: Chiromo Tech Club, University of Nairobi
**Active team (3)**: Collins Kimanzi (Lead · Detection Engine · Design Direction), Geoffrey (API · Data · Ingestion · Alerts), Ndegwa (Frontend Application)
**Unavailable**: Dennis Kuria. His tasks were redistributed on 2026-09-27 (see section 2).
**Status**: Foundations. Engine v1 prototypes exist; API, frontend and deployment not started.
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
| **Geoffrey** | Backend API, Data, Ingestion, Alerts | Supabase schema, FastAPI core and endpoints, repository layer, security, URL parser, scraper, extractors, matcher, seeder, Telegram, SMS | `backend/app/{api,core,ingestion,alerts,schemas}/*`, `backend/app/engine/matcher.py`, `database/*` |
| **Ndegwa** | Frontend Application | Next.js app, all pages and components, data layer and proxy, demo mode, i18n | `frontend/*` |
| ~~Dennis Kuria~~ | *Unavailable* | Former: engine, alerts, DB, security | Redistributed: engine/scorer → Collins; DB, alerts, security, matcher → Geoffrey |

**Review pairs:** Collins reviews Ndegwa's motion and design; Geoffrey reviews Collins's engine PRs for API fit; Ndegwa reviews API changes for frontend impact.

---

## 3. Priority Task Matrix & Sprint Board

**Priority:** **P0** = blocks others · **P1** = MVP / judged feature · **P2** = only after all P0/P1 are solid.
**Build order:** see [docs/DEVELOPMENT.md section 4](docs/DEVELOPMENT.md#4-build-order-critical-path).

### Backend & engine

| Task ID | Pri | Module | Description | Owner | Status | Depends on |
| :-- | :-: | :-- | :-- | :-- | :-: | :-- |
| TSK-001 | P0 | Database | Deploy **schema v2** (`database/schema.sql`) to Supabase. v1 was reopened: it had no logo hash and no sub-score columns | Geoffrey | `[ ] Pending` | — |
| TSK-002 | P0 | Backend core | config, repository (Supabase + Memory), cache, error handlers, router, Pydantic v2 schemas mirroring v2. Reopened: only `/health` existed | Geoffrey | `[/] In Progress` (v1 scaffold) | 001 |
| TSK-003 | P0 | Engine | pHash prototype (`hasher.py` v1) | ~~Dennis~~ | `[x] Done` (v1, superseded by 015) | 002 |
| TSK-004 | P0 | Engine | Jaro-Winkler + scam tokens prototype (`matcher.py` v1) | ~~Dennis~~ | `[x] Done` (v1, superseded by 016) | 002 |
| TSK-015 | P0 | Engine | **Hasher v2**: calibrated similarity, alpha/EXIF/square normalisation, dHash, no I/O in engine | Collins | `[ ] Pending` | 002 |
| TSK-016 | P0 | Engine | **Matcher v2**: normalisation, homoglyphs, affix stripping, multi-handle, weighted EN/SW/Sheng lexicon, golden tests | Geoffrey | `[ ] Pending` | 002 |
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
│   └── schema.sql                         [DONE v2, NOT DEPLOYED] TSK-001
├── backend/
│   ├── requirements.txt                   [DONE] core (UTF-8, curated)
│   ├── requirements-ml.txt                [DONE] torch + sentence-transformers (Brev)
│   ├── requirements-dev.txt               [DONE] pytest, respx, ruff
│   ├── .env.example                       [DONE]
│   ├── pyproject.toml                     [PLANNED] TSK-002
│   ├── app/
│   │   ├── main.py                        [V1: NEEDS REWRITE] CORS "*" + credentials; no lifespan/routers (TSK-002)
│   │   ├── core/ config.py database→repository.py cache.py security.py logging.py   [PLANNED] TSK-002/019
│   │   ├── api/v1/router.py + endpoints/  check merchants threats remediation reports stats simulator  [PLANNED] TSK-018/022/031
│   │   ├── engine/
│   │   │   ├── hasher.py                  [V1: NEEDS REWRITE] /64 normalisation, I/O inside engine (TSK-015)
│   │   │   ├── matcher.py                 [V1: NEEDS REWRITE] raw strings, no homoglyphs, prefix bias (TSK-016)
│   │   │   ├── imaging.py                 [PLANNED] TSK-015
│   │   │   ├── embeddings.py              [PLANNED] TSK-017
│   │   │   ├── payment.py                 [PLANNED] TSK-021
│   │   │   ├── scorer.py  constants.py    [PLANNED] TSK-008
│   │   │   ├── remediation.py + prompts/  [PLANNED] TSK-009
│   │   │   └── calibrate.py               [PLANNED] TSK-017
│   │   ├── ingestion/ url_parser.py page_scraper.py extractors.py mock_seeder.py fixtures/   [PLANNED] TSK-006/007/018/021
│   │   ├── alerts/ telegram_bot.py africas_talking.py dispatcher.py                        [PLANNED] TSK-012/013
│   │   └── schemas/ merchant.py threat.py [V1: NEEDS REWRITE] Pydantic v1 Config, mirror schema v1 (TSK-002)
│   │                check.py remediation.py report.py common.py                           [PLANNED] TSK-002
│   └── tests/                             [PLANNED] see BACKEND.md section 12
├── frontend/                              [PLANNED] TSK-005, full tree in FRONTEND.md section 3.1
├── deploy/                                [PLANNED] update.sh, systemd units (TSK-017)
├── test_hash.py, test_matcher.py          [V1: DELETE after porting] print scripts, always exit 0 (TSK-015/016)
└── skills-lock.json                       [DONE] agent design skills lock
```

---

## 5. Milestone Checklists

### Milestone 1: Environment & foundation

- [ ] Collins: Create GitHub repo `chiromo-tech-club/halisi`, add Geoffrey and Ndegwa, protect `main`.
- [ ] Geoffrey: Create the Supabase project, run schema v2, share credentials via the password manager (TSK-001).
- [ ] Geoffrey: Backend boots in `DEMO_MODE` with no network (TSK-002).
- [ ] Ndegwa: Next.js scaffold + proxy + fixtures working with the backend off (TSK-005, TSK-033).
- [ ] Collins: Brev account + credits, `halisi-engine` instance, ngrok static domain (TSK-017 part 1).

### Milestone 2: Detection brain

- [ ] Collins: Hasher v2 + imaging with tests (TSK-015).
- [ ] Geoffrey: Matcher v2 golden table passing (TSK-016); extractors (TSK-021).
- [ ] Collins: Scorer with required tests (TSK-008).
- [ ] Geoffrey: Seeder with 3 merchants × 3 targets (TSK-007); `/check` live (TSK-018).

### Milestone 3: Remediation & alerts

- [ ] Collins: NIM playbooks + validator + EN/SW templates (TSK-009); prompts registered in section 7.
- [ ] Geoffrey: Telegram alert with photo + button arrives on a phone (TSK-012).
- [ ] Geoffrey: Reports + payment lookup (TSK-022).

### Milestone 4: Frontend control center & public verification

- [ ] Ndegwa: Landing + Forensic Verdict (TSK-010), share page (TSK-023), pay/report (TSK-034).
- [ ] Ndegwa: Dashboard (TSK-011), threat detail (TSK-025), onboarding (TSK-026).
- [ ] Ndegwa + Collins: Certificate + badge (TSK-024), simulator stage (TSK-027), Swahili (TSK-032).

### Milestone 5: Rehearsal & live-demo hardening

- [ ] All: End-to-end run from public check to Telegram alert (TSK-014).
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
| 1 | High | `hasher.compare_hashes` normalises over 64 bits, so unrelated images score ~50 % visual similarity and push innocent pages toward "suspicious" | Open → TSK-015 (calibrated curve in BACKEND.md section 6.2) |
| 2 | High | `schema.sql` v1 couldn't store the logo hash or sub-scores; three different schemas existed (schema.sql, DEVELOPMENT.md, Pydantic) | Fixed: schema v2 written. Deploy → TSK-001; Pydantic → TSK-002 |
| 3 | High | The plan relied on data we can't get: account creation date (25 % weight) isn't in public IG/FB metadata; unauthenticated Instagram scraping is routinely blocked, especially from datacenter IPs like Brev's | Fixed in spec: "account" dimension re-weighted to 10 % with renormalisation + confidence; tiered acquisition with a manual fallback (BACKEND.md section 7.2) |
| 4 | High | No answer to "is this the real page?": an exact official handle scored 100 % "typosquatting" | Fixed in spec: O1 official short-circuit, `official` verdict |
| 5 | High | Matcher: no separator or homoglyph normalisation, and Jaro-Winkler prefix bias flags every `nairobi_*` handle | Open → TSK-016 (golden tests) |
| 6 | Medium | `main.py` CORS `allow_origins=["*"]` + `allow_credentials=True`: invalid, and Starlette reflects any origin | Open → TSK-002/019 |
| 7 | Medium | User-supplied URLs fetched server-side with no SSRF guard or size limits (the avatar URL comes from attacker-controlled OG tags) | Open → TSK-019 |
| 8 | Medium | `requirements.txt` was UTF-16 (PowerShell `pip freeze`), in the wrong folder, Windows-specific and missing supabase/settings/test deps | Fixed: curated UTF-8 `backend/requirements{,-ml,-dev}.txt` |
| 9 | Medium | `.gitignore` had `/_pycache_` (typo), so Python 3.14 `.pyc` files were committed | Fixed |
| 10 | Medium | Tests were print scripts that always exit 0; `test_hash.py` needs the internet | Open → TSK-015/016 (pytest + generated images) |
| 11 | Medium | Threshold inconsistent (75 vs 80); README overclaimed "Automated Safaricom & Meta takedowns" and "checks Safaricom records" | Fixed: single threshold 70; README reworded; human-in-the-loop stated |
| 12 | Medium | Telegram snippet used legacy Markdown, which fails on `_` in handles | Fixed in spec: HTML parse mode + escaping (BACKEND.md section 8.1) |
| 13 | Medium | Ownership contradictions: Collins listed as UI/UX but assigned backend; milestones said Dennis while the board said Collins; docs referenced a `docs/` folder that didn't exist | Fixed: section 2 rewritten; docs moved to `docs/` |
| 14 | Low | Pydantic v1 `class Config` in v2 code; `id: str` instead of UUID | Open → TSK-002 |
| 15 | Low | `build_monorepo.py` would overwrite real files if re-run | Fixed: deleted (it's in git history) |
| 16 | Low | Unsourced pitch statistic ("over 70% of social commerce…") | Open → TSK-035: source it or cut it |
| 17 | Info | Legal/ethical: third-party phone numbers are personal data (Data Protection Act 2019); "safe" verdicts create liability | Fixed in spec: masking, "never say safe" wording rules |
| 18 | Info | Contact channels (Safaricom fraud, KE-CIRT/CC) and the Meta portal claims weren't verified | Open → TSK-009: verify and date in `constants.py` |

---

## 10. Blockers & Notes

- *(none yet. Add `[!]` items here as `TSK-xxx: reason (owner, date)`)*
- Brev GPU credits: confirm the amount with the organisers before sizing the instance (BREV_ENGINE_SETUP.md section 3).
