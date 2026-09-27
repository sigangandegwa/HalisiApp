# Halisi: Developer Runbook and Hackathon Plan (DEVELOPMENT.md)

**Project**: Halisi, AI-powered brand impersonation detection for Kenyan businesses
**Team**: Collins (lead, engine, design), Geoffrey (API, data, ingestion, alerts), Ndegwa (frontend)
**Version**: 0.2 (2026-09-27)

> v0.1 of this file contained copy-pasted code (schema, hasher, scorer, remediation, Telegram) that had already drifted from the real files. For example, its hasher divided by 20 while `hasher.py` divides by 64, and its Telegram snippet used a parse mode that breaks on underscores in handles. **This file no longer contains implementation code.** The specs live in one place each:
>
> | Topic | Source of truth |
> | :-- | :-- |
> | Tasks, owners, status, change log, prompts | [AGENTS.md](../AGENTS.md) |
> | Backend architecture, API contract, engine maths, security | [BACKEND.md](BACKEND.md) |
> | Frontend design system, pages, motion, data layer | [FRONTEND.md](FRONTEND.md) |
> | GPU deployment, tunnel, demo-day failover | [BREV_ENGINE_SETUP.md](BREV_ENGINE_SETUP.md) |
> | Database | [database/schema.sql](../database/schema.sql) |
> | Stack choices | [tech-stack.md](tech-stack.md) · Flow: [data-flow.md](data-flow.md) |

---

## 1. Prerequisites

- **Python 3.12** via [uv](https://docs.astral.sh/uv/) (`uv` downloads the right Python for you)
- **Node.js 20 or 22 LTS** + npm
- Git, and on Windows: **WSL** for the Brev CLI
- Accounts: Supabase, NVIDIA (build.nvidia.com API key + Brev), ngrok (static domain), Telegram (@BotFather), Africa's Talking sandbox, Vercel. Details are in BREV_ENGINE_SETUP.md section 2.

---

## 2. Local setup

### 2.1 Backend (runs fully offline in demo mode)

```bash
cd backend
uv venv --python 3.12
# macOS/Linux: source .venv/bin/activate      Windows PowerShell: .venv\Scripts\Activate.ps1
uv pip install -r requirements.txt -r requirements-dev.txt
# optional, heavy (~2 GB): uv pip install -r requirements-ml.txt   (CLIP; usually only on Brev)
cp .env.example .env            # set DEMO_MODE=true to start without Supabase
uvicorn app.main:app --reload --port 8080
# http://localhost:8080/health   http://localhost:8080/docs
ruff check . && pytest -q
```

Windows note: never regenerate requirements with `pip freeze > requirements.txt` in PowerShell. It writes UTF-16, which is what broke the old root `requirements.txt`. Edit the curated files by hand.

### 2.2 Database

1. Create the Supabase project and run [database/schema.sql](../database/schema.sql) in the SQL editor.
2. Put `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` in `backend/.env` and set `DEMO_MODE=false`.
3. Seed it: `python -m app.ingestion.mock_seeder --target supabase --reset`.

### 2.3 Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local     # HALISI_API_URL=http://localhost:8080, DEMO_FALLBACK=true
npm run dev                           # http://localhost:3000
npm run types:api                     # regenerate API types whenever the backend contract changes
```

### 2.4 GPU engine on Brev

See [BREV_ENGINE_SETUP.md](BREV_ENGINE_SETUP.md). Short version: `brev shell halisi-engine` → pull → `sudo systemctl restart halisi-api` → check `/health`.

---

## 3. Git workflow

- `main` is always demo-able. Work on short branches named `tsk-018-check-endpoint` and merge through a PR reviewed by one other person (or at least a self-review with the diff open).
- Commit messages start with the task ID: `TSK-018: add /check endpoint with URL parser`.
- Every PR updates AGENTS.md: task status (section 3) and the change log (section 6).
- The API contract (BACKEND.md section 5) changes only in a PR that updates the fixtures in both `backend/` and `frontend/`.

---

## 4. Build order (critical path)

```text
Phase 0: Foundations (parallel)
  Geoffrey: TSK-001 schema v2 → TSK-002 scaffolding (DEMO_MODE works) → TSK-007 seeder
  Collins:  TSK-015 hasher v2 · TSK-020 design tokens (with Ndegwa) · Brev instance up (TSK-017 part 1)
  Ndegwa:   TSK-005 scaffold → TSK-033 proxy + fixtures (frontend works with backend off)

Phase 1: Detection brain
  Geoffrey: TSK-016 matcher v2 · TSK-021 extractors → TSK-018 API endpoints
  Collins:  TSK-008 scorer (needs 015/016/021) → TSK-031 simulator endpoint
  Ndegwa:   TSK-010 landing + checker + Forensic Verdict (on fixtures)

Phase 2: Product loop
  Geoffrey: TSK-012 Telegram · TSK-022 reports + pay lookup · TSK-019 security · TSK-006 scraper
  Collins:  TSK-009 remediation (NIM + templates) · TSK-017 CLIP on GPU + calibration
  Ndegwa:   TSK-011 dashboard → TSK-025 threat detail · TSK-023 share page · TSK-034 pay/report

Phase 3: Wow + polish
  Ndegwa:   TSK-027 simulator stage · TSK-024 certificate/badge (Collins designs) · TSK-032 SW copy · TSK-026 onboarding
  Collins:  TSK-035 pitch + script · design QA pass (FRONTEND.md section 16)
  Geoffrey: TSK-014 end-to-end test · failover drill (BREV_ENGINE_SETUP.md section 12)

Phase 4 (only if everything above is solid): P2 cards: TSK-013, 028, 029, 030, 036
```

**Integration checkpoints** (the whole team, 15 minutes each):

1. End of phase 0: the frontend renders a fixture `CheckResult`, and the backend `/health` works in demo mode.
2. End of phase 1: a real `/check` against the seeded blatant clone returns ≥ 90 through the Next.js proxy.
3. End of phase 2: seeded clone → Telegram alert on a phone → dashboard → playbook copied.
4. End of phase 3: full rehearsal on the projector with the failover drill.

---

## 5. Demo script (3 minutes)

Rules: fictional merchants only. Every number on screen comes from the live engine. Don't cite any statistic we can't source. Replace the placeholder below with a sourced figure (for example a Communications Authority of Kenya or Central Bank of Kenya report) or leave it out.

**0:00–0:40 The problem (Collins)**
"Njeri runs *Nairobi Sneaker Vault* on Instagram. Last week a customer sent KES 6,500 to a page with Njeri's logo, her photos, and the handle `nairobi_sneakervault_official_ke`. The page was 8 days old. The money went to a personal number. Njeri lost a sale *and* her name. [Sourced fraud statistic here.] Today there's no quick way for that customer to check before paying."

**0:40–1:50 Live: the customer's side (Ndegwa drives)**

1. On the phone-sized browser: paste the clone link → the **Forensic Verdict** plays: logos overlap, hash bits flash, bars fill, **FEKI.** stamps down. Read the reasons aloud: "97% logo match, handle look-alike, asks for payment to an unregistered number."
2. Paste the real handle → **HALISI.**, with the official Till and the account name.
3. Paste the similar-named *competitor* → **HAIJULIKANI.** "We don't flag honest businesses that just have similar names." This is the false-positive proof judges look for.
4. `/pay`: type the clone's number → "Reported by 3 people." Then show the WhatsApp share preview with the stamp.

**1:50–2:40 Live: the merchant's side (Collins drives)**

1. `/simulator`: preset 2 (subtle clone: homoglyph handle, recoloured logo, Pochi request) → Launch → scores live → **the Telegram alert buzzes on the presenter's phone** (hold it up).
2. Open the threat → drag the compare slider, toggle Difference → open Playbooks → the Swahili customer warning, drafted by **Llama 3.1 on NVIDIA NIM** and grounded in the evidence → Copy → Share to WhatsApp. Then show the Instagram report kit and the Safaricom draft.

**2:40–3:00 Close (Collins)**
"Halisi gives customers a verdict before they pay, and gives businesses a response kit in the first minute. The engine runs on NVIDIA GPUs through Brev. Next: a WhatsApp checker, a USSD menu for feature phones, and partnerships with banks and telcos."

Backups: the 60-second screen recording, and the offline mode (BREV_ENGINE_SETUP.md section 12).

---

## 6. Judge Q&A prep

| Likely question | Answer |
| :-- | :-- |
| How do you get Instagram data if it blocks scrapers? | Tiered acquisition: known targets, best-effort OpenGraph, and a manual fallback where the user uploads the picture and pastes the bio. We don't depend on scraping, and a platform partnership or official API access is the production path. |
| False positives? | Resemblance and malice are scored separately; a page must look like a merchant *and* show danger signals. Missing data lowers confidence instead of raising the score. We never say "safe". Show the competitor demo. |
| Why is the AI trustworthy? | The LLM only rewrites facts we computed. A validator rejects any output containing a number or handle that isn't in the evidence, and we fall back to templates. A human sends everything. |
| Business model? | Free for consumers. Merchants pay for monitoring and verified badges (freemium). B2B2C: banks, telcos and marketplaces embed the check. |
| Why the GPU? | CLIP embeddings catch recoloured, cropped and re-compressed logos that hashes miss, at about 15 ms on GPU. That lets us scan many candidate pages per merchant continuously. The LLM runs on NVIDIA NIM. |
| Privacy? | Data Protection Act 2019: minimal storage, masked numbers in public, reporter details never exposed. |

---

## 7. Hackathon checklist

- [ ] GitHub repo created; all 3 members have push access; branch protection on `main`
- [ ] Supabase schema v2 deployed and seeded
- [ ] Brev instance up; `/health` shows `clip: cuda`; ngrok static domain live
- [ ] Vercel deployed with `HALISI_API_URL`, `HALISI_API_KEY`, `DASHBOARD_PASSCODE`, `SESSION_SECRET`
- [ ] Telegram bot linked to the demo merchant; the alert arrives on the presenter's phone
- [ ] All 4 verdicts demo correctly from the example chips
- [ ] Failover drill done (Brev → laptop → offline)
- [ ] Swahili copy reviewed by a fluent speaker
- [ ] Safaricom and KE-CIRT/CC contact channels verified and dated in `engine/constants.py`
- [ ] Screen recording backup saved on 2 devices
- [ ] Pitch rehearsed 3× under 3:00
