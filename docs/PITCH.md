# Halisi: Finals Pitch Manual (v2)

**Project**: Halisi, check before you lipa. Scam and impersonation checks for Kenyan social commerce
**Team**: Chiromo Tech Club, University of Nairobi. Presenters: Collins Kimanzi (lead) and Ndegwa (frontend)
**Format**: 3-minute pitch + Q&A
**Version**: 2.0 (2026-11-05, TSK-052). Supersedes v1.0, which claimed features that were archived on 2026-10-22 (SMS, USSD, WhatsApp bot, Meta Rights automation, residential-proxy scraping) and quoted statistics we could not source.

> **Rule for this document (AGENTS.md golden rule 7): no invented facts.** Every number below is either
> produced by our own engine (and reproducible with the commands in section 5) or is explicitly marked
> `TO SOURCE`. Do not say a `TO SOURCE` figure on stage until a team member has opened the primary
> document and copied the exact figure, period and publisher.

---

## 1. The idea in two sentences

Anyone in Kenya can paste a link, handle, Till or phone number and get a plain answer **before** they send money.
Businesses that prove they own a brand get the same engine pointed at the people copying them.

| Layer | For | Works with zero registered merchants? | Cost |
| :-- | :-- | :-: | :-- |
| **1. Check before you lipa** | Any shopper | **Yes** (scam-pattern scoring, community payment reports) | Free |
| **2. Brand protection** | Verified merchants | n/a | Pricing not set. **Do not quote a figure.** |

Four verdicts. None of them ever means "safe":

| Stamp | Meaning |
| :-- | :-- |
| **HALISI** | Handle belongs to a verified or curated merchant |
| **FEKI** | Imitates a verified or curated merchant (logo, name, payment) |
| **ONYO** | High-risk signals (advance-payment demands, reported number). Not a claim that the seller is a scammer |
| **HAIJULIKANI** | Nothing found either way. Unknown, not safe |

## 2. Why it is a real engineering answer (all true today)

* **Five-dimension scorer** (visual, identity, payment, language, account) with confidence, renormalised when a signal is missing. Weights and thresholds are versioned in `AGENTS.md` section 7.2.
* **False-positive discipline is the headline, not an afterthought.** A personal number or a Pochi line is normal for Kenyan sellers, so payment alone never raises a page. An advance-payment demand is the gate; everything else only amplifies it. Honest shops, schools and travel agents are covered by regression tests.
* **Anyone can claim a brand, so claims are inert.** `claimed` merchants never produce a FEKI or a HALISI. A merchant becomes `verified` by placing a one-time code in their own bio. This stops a squatter from making Halisi endorse a scammer's Till.
* **Remediation is drafted, never auto-submitted.** NVIDIA NIM drafts platform, Safaricom and KE-CIRT reports in English and Swahili. A validator rejects any output containing a phone number, Till or handle that is not in the facts block, and falls back to a fixed template. A human reviews and sends. The evidence dossier carries a SHA-256 of the evidence bundle.
* **Private by construction.** Third-party numbers are masked on public surfaces (`0798 *** 111`); full numbers appear only to the affected merchant.
* **Degrades instead of dying.** Page unreadable? The user pastes the bio or logo (tier 3). Backend down? The frontend serves frozen fixtures.

### Honest limits (say these before a judge asks)

1. Halisi finds what people **check and report**, plus **probable look-alike handles it generates**. It does not crawl Instagram or TikTok.
2. Reading live social pages without a login is unreliable, especially from datacenter IPs. The manual fallback exists for this reason. Live fetching is not yet proven from the Brev instance.
3. Hash-only logo matching misses cropped logos. CLIP closes most of that gap but has not yet been run on the Brev GPU; until then cropped-logo clones lean on name and payment signals.
4. Verdicts are evidence-weighted heuristics, not proof. Swahili copy still needs a fluent-speaker review.
5. Demo merchants are **fictional** (Nairobi Sneaker Vault, Kilimani Glow, Pwani Threads). Nine curated real brands are seeded from public data only, with sources recorded; re-verify their handles before any public demo.

## 3. Three-minute script

*Setup: dual screen. Ndegwa drives the live app, Collins the narration and the phone. The story is told as illustrative, not as a real case.*

**[0:00 – 0:30] The problem (Collins).**
"You see a pair of sneakers on Instagram. The shop looks right, the logo is right, the price is great. They say: *lipa kwanza* to this number. There is no checkout, no receipt, no way to ask anyone. This is how a large part of Kenya shops online, and the only safeguard today is your gut."
*Slide: one line only, "Check before you lipa." No statistic unless it has been moved out of `TO SOURCE` (section 6).*

**[0:30 – 1:20] Layer 1: the check (Ndegwa, live).**
1. Paste a handle that imitates a seeded merchant: `nairobi_sneakervault_official_ke`. The verdict takes over the screen: **FEKI**, **99/100**, confidence 1.0. Name what drove it: logo copy, look-alike handle, a number reported by customers, a Pochi request, "lipa kwanza", a days-old account.
2. Paste the real one, `nairobisneakervault`: **HALISI**.
3. Paste the honest competitor, `nairobisneakerhub`: **HAIJULIKANI**, and say why: "a similar name is not a crime. We need more than that."
"No registered business needed" beat: paste a page that only matches scam patterns (for example the bio `Tuma deposit ya 500 kwanza. Bei poa, leo tu!` on any new handle). **ONYO**, and the screen says *high-risk signals*, never *scam*.

**[1:20 – 2:15] Layer 2: the business side (Collins, then Ndegwa).**
"Njeri is a fictional merchant, but the flow is real." She proves she owns the brand with a code in her bio. The same check her customers ran creates a threat on her dashboard and an **in-app alert** (phone notification if the browser permission is granted). Open the Evidence Board: side-by-side logos, the hash difference, the payment mismatch. Press **Prepare**: platform report, Safaricom report, customer advisory, English and Swahili. "Prepare, not freeze. A person reviews and sends it. We do not pretend to have powers we do not have." Open the dossier and show the SHA-256.

**[2:15 – 2:45] Why we can be trusted (Collins).**
"Every claim is conservative by design: claimed brands are inert, honest sellers are protected by tests, the AI cannot invent a phone number, and every public number is masked." State the three honest limits from section 2 in one breath.

**[2:45 – 3:00] Close (Collins).**
"Layer 1 is free for every Kenyan shopper, and every check and report makes it stronger. Layer 2 is how brands pay to protect themselves. Check before you lipa. We are Halisi."

## 4. Failover (keep rehearsed)

```text
Tier 1  Live: Brev GPU + Supabase + hosted NIM
Tier 2  Laptop: FastAPI with DEMO_MODE=true (in-memory, seeded through the real engine, no network)
Tier 3  Frontend fixtures: frontend/src/lib/fixtures/seed/*.json served when the backend returns 502
```

* Tier 1 to 2: set `DEMO_MODE=true` in `backend/.env`, run `uvicorn app.main:app --port 8000`. Seeding takes a moment; **time it yourself in rehearsal** and write the number here: `____ s`.
* Tier 2 to 3: stop the backend; the Next.js proxy serves the frozen fixtures.
* Demo gotcha: seeded clones already have threats and alerts, so re-checking them creates no new alert. For the live "phone buzzes" moment use `/simulator` or a brand-new handle.

## 5. Reproduce every number in this document

| Claim | How to reproduce |
| :-- | :-- |
| FEKI 99, HALISI, HAIJULIKANI | `cd backend && python -m app.ingestion.mock_seeder --target memory` prints verdict, score, confidence per seed check |
| Honest shops stay unknown; advance-fee and deposit scams reach ONYO | `cd backend && pytest tests/engine/test_scorer.py -k "standalone or advance or honest"` |
| Third-party numbers are masked | `pytest tests/api/test_check.py tests/api/test_reports.py -k mask` |
| Whole suite | `cd backend && ruff check . && pytest -q` |

Do not state a latency, throughput or hallucination-rate figure on stage. Anything not in this table is unmeasured.

## 6. Statistics worksheet (`TO SOURCE`)

v1 of this document quoted figures attributed to the CAK, the CBK and the KBA (for example "68% of social commerce fraud", "82% of micro-merchants", "+34.2% impersonation", "KES 4,500 to 15,000 average loss", "90% of buyers use WhatsApp"). **None of them could be traced to a primary publication and they have been removed.** Do not restore them.

Real, citable material exists, but it must be read from the primary document by a team member. Starting points (found by web search on 2026-11-05; **the figures were not verified by us and the primary hosts could not be opened from the build sandbox**):

| Need | Where to look | Caution |
| :-- | :-- | :-- |
| Scale of cyber threats in Kenya | Communications Authority of Kenya, quarterly *Cyber Security Report* PDFs on `ca.go.ke` (National KE-CIRT/CC) | Press coverage of different quarters disagrees by large amounts. Quote one named quarter and the publisher's own wording. This is **general cyber threat events**, not social-commerce fraud |
| Fraud in the banking sector | Central Bank of Kenya, *Financial Sector Stability Report 2024* | Covers **banks**, not Instagram/TikTok shops or M-Pesa merchants. Do not present it as social-commerce fraud |
| Losses to cybercrime | Press coverage dated 2026-04-29 citing a quarterly report | Secondary source. Find and cite the underlying report |

Acceptable fallback if nothing is sourced in time: **no statistic at all.** The opening scenario and the live demo carry the pitch. A judge who finds one fabricated number discounts everything else.

## 7. Judge Q&A (answers grounded in the code)

**How do you read pages when Instagram blocks scrapers?**
Three tiers: seeded/known profile, public OpenGraph metadata, and a manual fallback where the user pastes the bio or logo. We have not proven live fetching from datacenter IPs, which is exactly why tier 3 exists. We do not use residential proxies or headless-browser clusters; that code is archived.

**How do you avoid flagging an honest seller?**
Payment details alone never raise a page, because personal numbers and Pochi are normal for small Kenyan sellers. Pressure language (an advance-payment demand) is the gate. Similar names alone are capped below the suspicious line, and the honest competitor in our demo is the proof. These cases are regression tests.

**Defamation and the Data Protection Act?**
Verdict wording never says "safe" and never calls a named business a scammer; ONYO says "high-risk signals". Third-party numbers are masked publicly. We have not had this reviewed by counsel; the dossier cites statutes as context for the merchant, not as a legal finding.

**Can the AI hallucinate a number into a takedown?**
Output is validated against the facts block: any phone number, Till or handle not present in the facts rejects the output and a fixed template is used instead. We say "validated", not "zero hallucinations".

**Can anyone claim a brand?**
They can claim it, but a claim does nothing: claimed brands are excluded from scoring. Ownership is proven by a code in the brand's own bio.

**Does Halisi take down accounts or freeze Tills?**
No. It prepares the evidence and the report; a person submits it to the platform, to Safaricom's fraud channel, or to KE-CIRT. Contact channels were verified on 2026-10-11 and are dated in `constants.py`.

**Feature phones?**
Not today. A USSD channel was prototyped and archived (`backend/app/archived/`). It is on the roadmap, not in the product.

**What is the business model?**
Free consumer layer; paid brand-protection layer. We have not set a price and will not quote one.

## 8. Slide checklist

* [ ] No statistic on any slide unless it moved out of section 6 with a primary source and period.
* [ ] No mention of SMS, USSD, Telegram, WhatsApp bot, Meta Rights API or Daraja as features.
* [ ] "Prepare", never "freeze" or "automatic takedown".
* [ ] Demo merchants labelled fictional on screen.
* [ ] Failover rehearsed three times; seeding time written into section 4.
