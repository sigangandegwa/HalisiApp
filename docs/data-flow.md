# Halisi: End-to-End Data Flow and AI Remediation Lifecycle (data-flow.md)

**Project**: Halisi, AI-powered brand impersonation detection for Kenyan businesses
**Team**: Chiromo Tech Club, University of Nairobi
**Version**: 0.2 (2026-09-27). Scoring maths and API shapes are authoritative in [BACKEND.md](BACKEND.md). This file explains the *flow*.

---

## 1. System overview

```text
                         [ AUTHENTIC MERCHANT ]
                                   │ (1) Onboarding: name, handles, logo, M-Pesa Till/Paybill/Pochi,
                                   │     M-Pesa account name, official phone numbers
                                   ▼
                  ┌──────────────────────────────────┐
                  │  Merchant ingestion              │
                  │  - pHash + dHash of logo         │
                  │  - CLIP embedding (Brev GPU)     │
                  │  - Store in Postgres + pgvector  │
                  │  - Issue Halisi Verified page+QR │
                  └────────────────┬─────────────────┘
          ┌────────────────────────┼─────────────────────────────┐
          ▼                        ▼                             ▼
 (2a) Public Link Checker   (2b) Pay check: till/phone    (2c) Community report / scheduled
 customer pastes URL        "is this number official?"     re-check / simulator
          │                        │                             │
          ▼                        ▼                             │
 ┌──────────────────────┐   registry + reports lookup           │
 │ Target acquisition   │   → official / reported / unknown     │
 │ T1 seeded/known      │◄──────────────────────────────────────┘
 │ T2 OpenGraph fetch   │
 │ T3 manual bio+avatar │
 └──────────┬───────────┘
            ▼
 ┌──────────────────────────────────────────────┐
 │ O1 Official short-circuit                    │── exact official handle ──► verdict OFFICIAL
 └──────────┬───────────────────────────────────┘
            ▼
 ┌──────────────────────────────────────────────┐
 │ Feature extraction                           │
 │ avatar hashes + CLIP · handle/name · phones, │
 │ tills, Pochi phrases · scam tokens · counts  │
 └──────────┬───────────────────────────────────┘
            ▼
 ┌──────────────────────────────────────────────┐
 │ 5-dimension scoring vs EVERY merchant        │
 │ RESEMBLANCE: Visual 30% · Identity 25%       │
 │ MALICE:      Payment 25% · Language 10% ·    │
 │              Account 10%                     │
 │ renormalise over available signals → conf.   │
 │ G1 gate · O2 payment hijack · O3 reported    │
 └──────────┬───────────────────────────────────┘
            ▼
   ≥ 70 IMPERSONATION  │  40–69 SUSPICIOUS  │  < 40 NO MATCH (never "safe")
            │
            ▼
 threat upsert → Telegram/SMS alert → merchant dashboard → AI remediation playbooks (human sends)
```

---

## 2. Lifecycle stages

### Stage 1: Ground-truth onboarding

1. The merchant registers business details, **every** official handle (`merchant_handles`), the M-Pesa method (Till / Paybill / Pochi), the exact **M-Pesa account name** customers see on the confirmation SMS, and official phone numbers.
2. The logo is normalised (EXIF fix, transparency flattened onto white, padded to square), then hashed (pHash, dHash) and embedded (CLIP ViT-B-32, 512-d) into `merchants.logo_embedding`.
3. Halisi issues a **Halisi Verified** certificate page (`/v/<slug>`) and a QR story sticker. The merchant posts it, so customers have one trusted place to confirm the real page and till.

### Stage 2: Target discovery

- **2a Public Link Checker**: the customer pastes an Instagram, Facebook, TikTok or X link, or an `@handle`.
- **2b Pay check**: the customer types a till or phone number (or a `wa.me/` link is detected). The API answers from the merchant registry and community reports: `official` / `reported` / `unknown`.
- **2c Other channels**: community scam reports, the simulator (demo), and (P2) scheduled re-checks and the Telegram consumer bot.

Target acquisition is tiered because Instagram and Facebook often block unauthenticated or datacenter requests:

| Tier | Source | Reliability |
| :-- | :-- | :-- |
| T1 | Seeded or previously seen targets | Instant, the demo path |
| T2 | OpenGraph fetch (`og:title`, `og:description` with follower/post counts, `og:image`) | Best-effort, may hit login walls |
| T3 | Manual: user pastes bio + uploads the profile picture | Always works, any platform |

### Stage 3: Scoring

Two questions are answered separately:

1. **Resemblance (who is it imitating?)**: Visual (logo vs avatar: pHash/dHash/CLIP, calibrated) and Identity (normalised, homoglyph-folded handle/name similarity against every official handle and alias).
2. **Malice (how dangerous?)**: Payment (an unregistered phone/till/Pochi request while resembling a merchant), Language (weighted EN/SW/Sheng scam lexicon), and Account (age when known, low activity, first-seen recency).

Rules (details and constants in BACKEND.md section 6.8):

- **Renormalisation**: unavailable signals are excluded, and the weights of the rest are rescaled. `confidence` = share of total weight that was available.
- **G1 resemblance gate**: if resemblance < 50, the page is not imitating this merchant (score capped at 39).
- **O2 payment hijack**: resemblance ≥ 80 **and** an unregistered payment number → score floor 90.
- **O3 community-confirmed**: the number appears in a confirmed report → floor 85.
- **O4 thin evidence**: an impersonation-level score with confidence < 0.5 is downgraded to *suspicious*.

Verdicts: `official` · `impersonation` (≥ 70) · `suspicious` (40–69) · `no_match` (< 40). A single threshold (70) is used everywhere. v0.1 used 75 in this doc and 80 in the README.

### Stage 4: Alerting

When a threat is created, or crosses 70, a background task:

1. upserts `threats` (unique per merchant + platform + handle),
2. sends a Telegram alert (photo, score, top reasons, "Open in Halisi" button), de-duplicated per 6 h,
3. optionally sends an SMS via Africa's Talking,
4. makes the threat appear in the dashboard live feed (polling, 5 s).

---

## 3. AI remediation engine

Halisi **drafts**; the merchant **decides and sends**. Nothing is auto-filed with Meta, Safaricom or the authorities. That's safer legally, and it's honest in the pitch.

| Playbook | Audience | Deliverable | Delivery |
| :-- | :-- | :-- | :-- |
| 1. Consumer defense | Customers and followers | Story/status warning in **English + Swahili**: the fake handle, the real handle, the real Till, "don't send money to …" | Copy, Share to WhatsApp |
| 2. Platform takedown | Instagram / Facebook / TikTok | Impersonation report text with evidence: side-by-side logos, real hash distance, first-seen dates | Opens the platform's public impersonation/IP report form |
| 3. Financial escalation | Safaricom fraud channels | Report naming the receiving number/till, the victims' path (fake page), and the real merchant's till | `mailto:` draft / SMS guidance (channels verified before the demo) |
| 4. Cyber incident | National KE-CIRT/CC | Incident summary under the Computer Misuse and Cybercrimes Act, 2018 | `mailto:` draft (contact verified before the demo) |

Generation pipeline:

1. Build **facts** from the DB only (names, handles, numbers, real scores, dates).
2. Call NVIDIA NIM (`meta/llama-3.1-8b-instruct`) with a versioned prompt (AGENTS.md section 7). Scraped text is passed only as quoted data.
3. **Validate**: parse as JSON; every number or handle in the output must exist in the facts.
4. On any failure (timeout, invalid output, or LLM disabled), use the **deterministic template** (EN/SW).
5. Log to `remediation_logs` (`generator`, `prompt_id`, `model`).

### Tracking loop (P2)

The threat status moves `detected → advisory_sent → takedown_filed → resolved` (or `false_positive`). A 12-hour scheduler re-fetches filed targets; a 404 or "page unavailable" response means `resolved`, and time-to-takedown is recorded. The v0.1 "second-tier legal notice" and "community mass-report" ideas are parked. Coordinated mass-reporting can itself violate platform rules.

---

## 4. Privacy and ethics

- Phone numbers of alleged scammers are personal data under Kenya's **Data Protection Act, 2019**. Store the minimum, mask them on public pages, and show full numbers only to the affected merchant.
- Never tell a consumer a page is "safe". We can only say it doesn't match a verified business.
- The demo uses fictional businesses only. Never label real third-party accounts as scammers without confirmation.
