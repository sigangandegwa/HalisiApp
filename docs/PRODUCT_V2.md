# Halisi Product v2: Two-Layer Restructure & "Case File" Redesign

**Date**: 2026-10-22 · **Owner**: Collins Kimanzi (lead) · **Supersedes**: `Restructure.md` (2026-10-17), the product framing in `docs/ANALYSIS.md` §3-4
**Status**: Authoritative for this sprint. Deadline window: 1-2 weeks. Judges: not yet identified.

---

## 1. Why this exists

`Restructure.md` narrowed Halisi to "protect registered merchants" and dropped the commonest scam:
a brand-new shop with no registered original, a personal number and pressure language. It also let
anyone claim a brand, so a scammer who claims it first would make Halisi endorse the scammer's Till.
This document fixes both and records the decisions taken on 2026-10-22.

## 2. Product: two layers

| Layer | For | Works with zero merchants? | Revenue |
| :-- | :-- | :-: | :-- |
| **1. Check before you lipa** | Any shopper: paste a link, handle, Till or phone | Yes | Free, forever |
| **2. Brand protection ("Content ID" for M-Pesa businesses)** | Verified merchants | n/a | SaaS (pricing to be sourced, do not state a figure we have not set) |

Layer 1 is the headline. Layer 2 is built on Layer 1's data: every check and report enriches the
payment-number reputation that merchants then act on.

## 3. Verdicts (no API enum change)

The API `Verdict` enum already has four useful values. Only the display names and the reachability change.

| API verdict | Stamp (EN/SW) | Meaning | Colour |
| :-- | :-- | :-- | :-- |
| `official` | **HALISI** | Handle/Till belongs to a **Verified** or **Curated** merchant | emerald |
| `impersonation` | **FEKI** | Imitates a Verified/Curated merchant (logo, name, payment) | signal red |
| `suspicious` | **ONYO** | High-risk scam signals. May or may not resemble a known brand | amber |
| `no_match` | **HAIJULIKANI** | No signals either way. Never means "safe" | slate |

Copy rules: never say "safe"; never call a named real business a scammer; ONYO says "high-risk signals", not "scam".

## 4. Engine: standalone (zero-merchant) scoring: TSK-043

New pure function `score_standalone(target, ctx)` in `backend/app/engine/scorer.py`, used by
`score_against_all` when the best merchant comparison is `no_match` (including when no merchants exist).

False-positive discipline: **a personal number in a bio is normal for Kenyan SMEs.** Payment alone must never raise a page.
Pressure language is the gate; other signals only amplify it.

| Signal | Rule |
| :-- | :-- |
| Language | `language_score(bio)` is the base. Below `STANDALONE_LANGUAGE_GATE` (25) the page stays `no_match` unless a reported number is present |
| Payment asymmetry | +15 only if language ≥ gate **and** a personal phone/Pochi (not a till/paybill) is requested |
| Account | +15 only if language ≥ gate **and** account signal ≥ 60 (new account or very few posts) |
| Community report | A number in a **confirmed** report → floor 85 (`COMMUNITY_REPORTED`), regardless of language |
| Cap | Without a confirmed report, a standalone score is capped at 84 so it can never reach FEKI (≥ 70 is `impersonation` only with a merchant) |
| Verdict | score ≥ 40 → `suspicious`; else `no_match`. Never `impersonation` without a verified merchant |

Reasons keep the existing codes (`SCAM_LANGUAGE`, `POCHI_REQUEST`, `NEW_ACCOUNT`, `LOW_ACTIVITY`, `COMMUNITY_REPORTED`); no brand name appears.
Confidence = 0.4 + 0.2 for each available signal group, max 0.9 (we cannot be sure without a reference).
Heuristic version: `STANDALONE` v1 (record in AGENTS.md §7.2).

## 5. Merchant trust tiers: TSK-044

`merchants.verification_status`: `curated` (Halisi-seeded from public sources) · `verified` (bio-code proven) · `claimed` (self-declared).

* Only `curated` and `verified` merchants enter `score_against_all` and the official short-circuit. `claimed` merchants are stored but inert, so a squatter cannot create a FEKI or a HALISI.
* `is_verified` stays and is derived: `status in (curated, verified)`.
* Onboarding creates `claimed` + a one-time `verification_code` (`halisi-XXXXXX`).
* `POST /merchants/{slug}/verification/check`: fetches the merchant's declared official handle(s) (same SSRF-guarded tiered acquisition as `/check`), looks for the code in the bio, and on success sets `verified`, `verified_at`.
* Certificate (`/v/[slug]`) and Strike Console strike actions require `verified`/`curated`.
* Error codes (additive): `VERIFICATION_CODE_NOT_FOUND`, `ALREADY_VERIFIED`.

## 6. Discovery: crowd-sourced

1. **Payment-number reputation** (exists: `/verify/payment`, `/reports`). Checks and reports are the sensors.
2. **Typosquat watchlist** (TSK-047): `GET /merchants/{id}/watchlist` returns generated look-alike handles per platform (homoglyph, separator, affix variants, from `matcher.py` tables). `POST` scans those that resolve through tiers 1-2 and ignores unreachable ones.
3. **Share-sheet entry** (frontend, TSK-051): PWA `share_target` so "Share → Halisi" from Instagram/TikTok opens the checker pre-filled.

Honest limit, stated in the pitch: Halisi finds what people check and report, plus probable variants; it does not crawl social platforms.

## 7. Strike Console: "Prepare strike", never "freeze"

Three actions, each generates a pack for a human to submit:

1. **Platform report**: NIM-written text + link to the platform's impersonation form + SHA-256 dossier.
2. **Safaricom fraud report**: `mailto:` to the verified contact in `constants.py` with the dossier; says "request review", never "freeze".
3. **Customer advisory**: WhatsApp-status copy (EN/SW) naming the real handle and Till.

Buttons are labelled "Prepare" and, after generation, "Copy" / "Open". Status "Submitted" is only set by the merchant ticking it themselves.

## 8. Seed data policy: TSK-046

* Keep the three fictional merchants and their clone stories (they power the FEKI demo).
* Add ~10-12 **curated real brands**: public handle + publicly published Paybill/Till only, each with a `source_url` recorded in the seed file. Anything unconfirmed is `null`; never invent a number.
* We store **hashes only**, not copies, of logos fetched from a brand's own site.
* No fictional clone ever uses a real brand's real handle. Clones of real brands exist only as simulator inputs with obviously synthetic handles.
* UI counters (checks run, numbers reported) come from the database or are removed. No invented "KSh protected" / "clones neutralised" figures.

## 9. Dormant code: TSK-045

Unroute and move to `backend/app/archived/`: `channels/telegram.py`, `channels/ussd.py`, `ingestion/meta_rights.py`, `ingestion/daraja.py`, `alerts/sms.py`, `ingestion/takedown_tracker.py`, `ingestion/playwright_scraper.py`. Their tests stay in `backend/tests/archived/` and run; anything coupled to the live path is rewired to skip them. The payment lookup keeps working without Daraja.
Remove `frontend/src/app/dashboard/onboarding/page.tsx`. Mark them `Archived` in AGENTS.md.

## 10. Design system v3: "Case File" (TSK-048)

**Idea**: the product is a live case file. Paste → the console boots and scans → the **verdict takes over the whole viewport** in its colour, then settles into the case-file detail. One idea per screen; neutral chrome; colour is reserved for verdicts.

References: Rockstar VI (cinematic full-bleed, one big thing per screen), KPR Verse (diegetic terminal/boot, numbered files), Apple (terse declarative copy, restraint). A fourth reference, huyphan.com, could not be loaded; pending screenshots.

| Token | Value | Use |
| :-- | :-- | :-- |
| `--ink` | `#07070A` | canvas (both public and merchant) |
| `--ink-2` / `--ink-3` | `#0E0E13` / `#16161D` | raised surfaces |
| `--bone` | `#F1EEE6` | primary text |
| `--bone-dim` | `#9A978F` | secondary text |
| `--line` | `rgba(241,238,230,.10)` | hairlines |
| `--halisi` | `#1FBF84` | HALISI only |
| `--feki` | `#FF3B30` | FEKI only |
| `--onyo` | `#FFB020` | ONYO only |
| `--haijulikani` | `#8A93A6` | HAIJULIKANI only |

Type: **Big Shoulders Display** (800/900) for monumental words, **Geist** for UI/body, **Geist Mono** for case data. Verdict word ≈ 38vw, tracking -0.02em. Headlines short and declarative, ending in a full stop ("Check before you lipa.").
Motion: Lenis smooth scroll; GSAP timelines for the boot sequence, verdict takeover, and scroll choreography; `motion` for small UI springs. WebGL is allowed (lazy-loaded) for the hero field and ink/flood effects, with a CSS fallback.
Rules: `prefers-reduced-motion` and a low-power flag degrade to static composition; never block on a "screen unsupported" gate; Swahili is a first-class voice (stamps, microcopy); Kenyan nods are subtle (pattern accents, Swahili microcopy).

Surfaces, in build order: (1) tokens + primitives + shell, (2) landing + checker + verdict takeover, (3) result/share page + OG image, (4) merchant console + case-file threat detail, (5) onboarding + verification + certificate, (6) pay/report, login, simulator, styleguide.

## 11. Task cards

| ID | Pri | Description | Owner of record |
| :-- | :-: | :-- | :-- |
| TSK-043 | P0 | Standalone scoring + ONYO reachable without a merchant | Collins |
| TSK-044 | P0 | Merchant verification tiers + bio-code check; claimed merchants inert | Geoffrey |
| TSK-045 | P0 | Unroute + archive dormant channels/integrations | Geoffrey |
| TSK-046 | P1 | Curated real-brand seed (public data, sources recorded) | Geoffrey |
| TSK-047 | P1 | Typosquat watchlist endpoints | Geoffrey |
| TSK-048 | P0 | Design system v3 tokens, primitives, shell, motion kit | Collins + Ndegwa |
| TSK-049 | P0 | Landing + checker + verdict takeover + result/share | Ndegwa |
| TSK-050 | P1 | Merchant Strike Console + case-file threat detail | Ndegwa |
| TSK-051 | P1 | Onboarding + verification UI, certificate, PWA share target | Ndegwa |
| TSK-052 | P1 | Pitch v2: remove unsourced statistics, rewrite around two layers | Collins |

Definition of Done: backend `ruff check . && pytest -q` clean; frontend `npm run lint && npm run typecheck && npm run build` clean; fixtures in `frontend/src/lib/fixtures/` regenerated whenever a contract field changes (golden rule 6).

## 12. Open items

* Source (or cut) the "68% of social commerce fraud" figure. It was in `Restructure.md` with no source.
* Fourth design reference (huyphan.com) unreachable; need a screenshot.
* Pricing figure (`KES 2,500/month` in `Restructure.md`) is unvalidated; do not present it as fact.
* Swahili copy still needs a fluent reviewer.
