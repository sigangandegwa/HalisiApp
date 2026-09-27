# Halisi: Tech Stack Specification (tech-stack.md)

**Project**: Halisi, AI-powered brand impersonation detection for Kenyan businesses
**Team**: Chiromo Tech Club, University of Nairobi
**Target**: Hackathon MVP that can grow into a free-tier production bootstrap
**Version**: 0.2 (2026-09-27): revised after the architecture review. See AGENTS.md section 9 for what changed and why.

---

## 1. Architecture principles

* **Demo-proof first.** Every live dependency (scraping, GPU, LLM, Wi-Fi) has a fallback: seeded data, a CPU hash-only mode, deterministic templates, and offline fixtures. See BREV_ENGINE_SETUP.md section 12.
* **Evidence, not vibes.** Every score is explainable: sub-scores, evidence strings and plain-language reasons. Missing signals are reported as missing (confidence), never faked as 0.
* **Kenyan financial context first.** M-Pesa Till, Paybill and Pochi la Biashara mismatch detection, Swahili/Sheng scam language, and bilingual EN/SW output.
* **Fast where it matters.** Seeded/cached checks take < 1.2 s; live fetches take < 4 s.
* **Low cost.** Free tiers everywhere except the GPU (NVIDIA Brev, credit-based). The code also runs without a GPU.

---

## 2. Frontend (public checker + merchant control center)

Full spec: [FRONTEND.md](FRONTEND.md).

* **Framework**: Next.js (latest stable, App Router, ≥ 15), React 19, TypeScript strict
* **Styling**: Tailwind CSS v4 (CSS-first `@theme` tokens) + shadcn/ui, fully restyled
* **Motion**: Motion (`motion/react`) for UI; GSAP + ScrollTrigger for the scroll story (lazy-loaded); Lenis smooth scroll on desktop
* **Type**: Fraunces (variable display), Geist, Geist Mono via `next/font`
* **Data**: TanStack Query v5, zod runtime validation, `openapi-typescript` generated types
* **Charts**: custom SVG (5-axis radar, hash bit grids, evidence bars). No chart library needed.
* **Sharing**: `next/og` dynamic Open Graph images for verdicts and verified certificates
* **Hosting**: Vercel Hobby

---

## 3. Backend API + engine

Full spec: [BACKEND.md](BACKEND.md).

* **Framework**: FastAPI + Pydantic v2 + pydantic-settings
* **Runtime**: Python **3.12** (3.11–3.13 supported), managed with `uv`
* **HTTP**: HTTPX (one shared async client), tenacity retries
* **Background work**: FastAPI `BackgroundTasks` (alerts, persistence); APScheduler for the P2 takedown tracker. No Celery or Redis in the MVP.
* **Rate limiting**: slowapi
* **Hosting**: **NVIDIA Brev GPU instance** (API + engine in one service), exposed through an ngrok static domain. The laptop hot spare runs in CPU mode. See [BREV_ENGINE_SETUP.md](BREV_ENGINE_SETUP.md).

---

## 4. Detection engine (AI + similarity)

| Signal | Technique | Library | Runs on |
| :-- | :-- | :-- | :-- |
| Visual | pHash + dHash (64-bit), calibrated Hamming → similarity | `imagehash`, Pillow | CPU, < 5 ms |
| Visual (robust) | CLIP ViT-B-32 image embeddings (512-d), cosine similarity | `sentence-transformers`, PyTorch | **Brev GPU** (~15 ms) / CPU (~150 ms) / off |
| Identity | Normalised + homoglyph-folded Jaro-Winkler / ratio / token-set / containment | `rapidfuzz` | CPU |
| Payment | Kenyan phone / Till / Paybill / Pochi extraction vs the merchant registry | `re` | CPU |
| Language | Weighted EN/SW/Sheng scam-token lexicon | `re` | CPU |
| Account | Account age (when known), post/follower counts, first-seen recency | — | CPU |
| Remediation | Facts-grounded LLM drafting with output validation + template fallback | NVIDIA NIM (`meta/llama-3.1-8b-instruct`) via `openai` client | Hosted NIM (default) or self-hosted NIM on Brev |

Dropped from v0.1: the MiniLM bio embeddings (no clear gain over the lexicon for the MVP), ChromaDB (replaced by pgvector inside Supabase, one fewer system), and the Gemini API (replaced by NVIDIA NIM to align with the Brev GPU story; any OpenAI-compatible endpoint still works).

---

## 5. Data and storage

* **Relational + vectors**: Supabase Postgres with **pgvector** (`vector(512)` columns + the `match_merchant_logos` RPC). Schema: [database/schema.sql](../database/schema.sql).
* **Access**: the backend only uses the service-role key. RLS is enabled deny-by-default; the frontend never queries Supabase directly.
* **Media**: Supabase Storage for merchant logos and evidence snapshots.
* **Offline**: `MemoryRepository` seeded from fixtures (`DEMO_MODE=true`).

---

## 6. Ingestion

* **Tier 1**: seeded and previously seen targets (DB)
* **Tier 2**: HTTPX OpenGraph fetch (`og:title`, `og:description`, `og:image`), with login-wall detection. Instagram and Facebook often block unauthenticated or datacenter requests, so this tier is best-effort.
* **Tier 3**: manual fallback: the user pastes the bio and uploads the profile picture
* **Tier 4 (stretch)**: Playwright headless
* **Removed**: Safaricom Daraja "account name reconciliation". There's no public API for third parties to look up the registered name of an arbitrary till. Merchants self-declare the M-Pesa account name, and customers compare it with their confirmation SMS. A partner integration is future work.
* **Removed (for now)**: python-whois. Domain age only matters for website targets. Revisit if we add website scanning.

---

## 7. Alerts and remediation delivery

* **Telegram Bot API** (direct HTTPS via httpx, `parse_mode=HTML`): merchant alerts with photo + button; P2 consumer checker bot
* **Africa's Talking SMS** (sandbox delivers only to the AT simulator; live credits are needed for real phones)
* **Email drafts**: `mailto:` links with pre-filled subject/body (the human sends). Resend API is P2.
* **Evidence dossier**: Jinja2 → HTML → PDF (P2)
* **P2 stretch**: Africa's Talking USSD "check a till" menu for feature phones

---

## 8. Tooling

* Backend: `uv`, `ruff`, `pytest` + `pytest-asyncio` + `respx`
* Frontend: ESLint, `tsc --noEmit`, Lighthouse
* Repo: one GitHub monorepo (`backend/`, `frontend/`, `database/`, `docs/`), and every change is logged in AGENTS.md section 6
