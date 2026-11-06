# Halisi: Finals Pitch Manual (v2)

**Project**: Halisi, check before you lipa. Scam and impersonation checks for Kenyan social commerce
**Team**: Chiromo Tech Club, University of Nairobi. Presenters: Collins Kimanzi (lead) and Ndegwa (frontend)
**Format**: 3-minute pitch + Q&A
**Version**: 2.1 (2026-11-06: Brev and ngrok dropped, full Q&A added). Earlier: 2.0 (2026-11-05, TSK-052). Supersedes v1.0, which claimed features that were archived on 2026-10-22 (SMS, USSD, WhatsApp bot, Meta Rights automation, residential-proxy scraping) and quoted statistics we could not source.

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
| **2. Brand protection** | Verified merchants | n/a | Planned tiers: Free, Pro, All Access (section 7, Q6). **No price is set; do not quote a figure. Billing and tier gating are not built.** |

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
* **Remediation is drafted, never auto-submitted.** NVIDIA NIM drafts platform, Safaricom and KE-CIRT reports in English; Swahili uses reviewed templates until a fluent speaker signs off on the model's Swahili. A validator rejects any output containing a phone number, Till or handle that is not in the facts block, and falls back to a fixed template. A human reviews and sends. The evidence dossier carries a SHA-256 of the evidence bundle.
* **Private by construction.** Third-party numbers are masked on public surfaces (`0798 *** 111`); full numbers appear only to the affected merchant.
* **Degrades instead of dying.** Page unreadable? The user pastes the bio or logo (tier 3). Backend down? The frontend serves frozen fixtures.

### Honest limits (say these before a judge asks)

1. Halisi finds what people **check and report**, plus **probable look-alike handles it generates**. It does not crawl Instagram or TikTok.
2. Reading live social pages without a login is unreliable, especially from datacenter IPs. The manual fallback exists for this reason. Live fetching worked for public profiles in testing (a real Safaricom page was read in 2.8 s on 2026-11-06) but is not guaranteed from every network.
3. Hash-only logo matching misses cropped logos. CLIP could close most of that gap but is **switched off** (no GPU in the deployment), so cropped-logo clones lean on name and payment signals.
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
Tier 1  Live: hosted backend (HALISI_API_URL) + Supabase + hosted NIM
Tier 2  Laptop: FastAPI with DEMO_MODE=true (in-memory, seeded through the real engine, no network)
Tier 3  Frontend fixtures: frontend/src/lib/fixtures/seed/*.json served when the backend returns 502
```

* Tier 1 to 2: set `DEMO_MODE=true` in `backend/.env`, run `uvicorn app.main:app --port 8000`. Seeding takes a moment; **time it yourself in rehearsal** and write the number here: `____ s`.
* Tier 2 to 3: stop the backend; the Next.js proxy serves the frozen fixtures.
* Live-mode gotcha (found 2026-11-06): seeded clone handles such as `nairobi_sneaker_vault_` do **not** resolve against the real database (the seed lookup exists only in `DEMO_MODE`), and the nine curated real brands exist only in the fixtures unless they are seeded into Supabase. For a live FEKI use `/simulator` or paste manual details.
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

Legend: **[ready]** safe to say as written. **[you fill]** only the presenter can supply it. **[TO SOURCE]** needs a primary document first. **[Kimanzi]** / **[Ndegwa]** owner of the answer. Wording that is not in the code is marked, so nobody says it by accident.

### A. Story and product

**Q1. Where does the name come from? [ready]**
*Halisi* is Swahili for "authentic" or "genuine". The product answers one question: is this the real one?

**Q2. What inspired Halisi? [Ndegwa, you fill]**
Ndegwa tried selling sneakers online and ran into the problem from the seller's side. *Tell it in your own words, in two or three sentences, and only what actually happened.* The demo merchant, Nairobi Sneaker Vault, is fictional and is labelled that way on screen.

**Q3. Which technologies did you use? [ready]**

| Layer | Stack |
| :-- | :-- |
| Frontend | Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS v4, shadcn/ui, Motion and GSAP animation, Lenis smooth scroll, TanStack Query, zod |
| Backend | Python, FastAPI, Pydantic v2, slowapi rate limiting |
| Detection engine | ImageHash (pHash and dHash), RapidFuzz (Jaro-Winkler) with homoglyph folding, a five-signal composite scorer. CLIP image embeddings exist in code but are off |
| Data | Supabase (Postgres) |
| AI | NVIDIA NIM, `nvidia/nemotron-3.5-lightning-30b-a3b`, drafts reports only. Output is validated against a facts block, with fixed templates as fallback |
| Evidence | Jinja2 templates and a PDF dossier carrying a SHA-256 of the evidence bundle |

**Q4. What problem does Halisi solve? [ready, one correction]**
Clone-and-collect scams: a fake shop on Instagram, TikTok or Facebook copies a real brand's name and logo and asks for payment to a personal number or Till. Buyers lose money; the real seller loses the sale and the trust. *Say Instagram, TikTok and Facebook. Do not say Telegram: the Telegram bot was archived and is not in the product.*

**Q5. How do you know this really hurts Kenyans? [TO SOURCE]**
The case-study document (`Brand_Impersonation_Case_Studies.docx`) is **not in this repository**, so nobody can check what it says. Add it to `docs/` and copy the exact cases, dates and publishers into section 6 before quoting any of them. Until then, lead with the live demo, and say "we have spoken to sellers who lost sales to copycats" **only if that is true**. A fabricated or unattributable figure costs more than having none.

**Q6. How will Halisi sustain itself? [ready, with limits]**
B2B, in tiers. The tier split is the team's plan; **no price is set and billing and tier gating are not built**.

| Tier | Intended content | In the product today |
| :-- | :-- | :-- |
| **Free** | Brand checker, payment checker, community reporting, user-input verification | All built |
| **Pro** | Merchant dashboard, clone alerts, Halisi Verified certificate | Built, not gated or billed |
| **All Access** | AI remediation drafts, tamper-evident evidence dossier | Built, not gated or billed |

The typosquat watchlist is built but has no tier yet. Decide where it sits. Shoppers always check for free, which keeps the community data flowing that the paid layer relies on.

**Q7. How will you scale? [Kimanzi, draft from the code]**
The backend is stateless, so more copies can run behind one URL. State lives in Supabase. The LLM is hosted NIM, so adding capacity needs no GPU on our side. Scoring is deterministic and fast (a live check measured about 0.6 to 2.8 s including a real page fetch). Growth path: more curated brands from public data, merchant self-service verification, then paid tiers and feature-phone channels (USSD was prototyped and archived). *Expanding beyond Kenya needs local scam-language lexicons and payment rails; say so rather than promising it.*

**Q8. What stops you scaling right now? [Kimanzi, draft from what we measured]**
1. Reading social pages without a login is unreliable, so coverage depends on public metadata and user-pasted details.
2. No platform partnership or API access, so Halisi cannot take anything down itself; a person submits each report.
3. Cropped-logo detection is weaker while CLIP is off.
4. Swahili model output is not reliable yet; Swahili relies on reviewed templates and still needs a fluent reviewer.
5. No legal review yet of verdict wording and the Data Protection Act position.
6. Tier gating and billing are not built, and no merchant has paid.

**Q9. Who are the competitors, and why do they not serve this market? [Kimanzi, VERIFY before stage]**
Brand-protection vendors such as Red Points, BrandVerity and Brandshield sell takedown and monitoring to brand owners. To our knowledge they do not offer a shopper-facing "is this page real?" check, M-Pesa-aware signals, or Swahili and Sheng scam language, and they are not Kenyan-owned. *Open each vendor's current product page and confirm this before you say it. Do not say their solutions "have not worked": we have no evidence of that.*

**Q10. What are your unique value propositions? [ready, one correction]**
1. Hyper-local language: Swahili, English and Sheng scam phrases, and Swahili output.
2. Kenyan-built, for Kenyan payment habits (Till, Paybill, Pochi la Biashara, personal numbers).
3. M-Pesa-aware checking: Halisi compares the number on a page with the brand's declared Till or phone and with numbers customers have reported. **It does not query M-Pesa or Safaricom.** The Daraja integration was archived, so never say "we validate M-Pesa accounts" or "we check Safaricom records".
4. A shopper-facing check anyone can use without registering.

**Q11. What impact will Halisi have? [TO SOURCE, do not quote numbers]**
The draft answers said "reduce digital fraud by about 40%" and "prevent over KSh 800M of losses". **Neither figure is measured or sourced, and Halisi has no deployment from which to measure them. Do not say them.** Honest framing: every check gives a shopper a decision before they pay; every report strengthens the number reputation other shoppers see; verified brands get evidence ready to send. If a judge asks for numbers: "We have not measured impact yet. What we can show is how each check behaves, and the test suite that guards against flagging honest sellers."

**Q12. How is user data protected? [Kimanzi, from the code]**
- Third-party phone numbers are masked on public surfaces (`0798 *** 111`); full numbers reach only the affected merchant.
- The database denies access by default (row-level security on every table), and the browser never holds the database key. The Next.js server proxy holds the API key and forwards only an allowlist of paths.
- Merchant routes need a signed session and only reach that merchant's own records.
- Rate limits on the public endpoints, a guard that stops the server being used to fetch internal addresses, and limits on input size.
- Community reports store the reporter's contact only if they give it, and the schema notes the Data Protection Act 2019 aim of minimising it.
- Curated brands: only hashes of logos are stored, not copies.
- Honest limit: no formal Data Protection Act review or registration has been done.

**Q13. How do you make sure the merchants you onboard are genuine? [Ndegwa, from the code]**
Signing up creates a *claimed* brand, which is inert: it can never cause a FEKI or a HALISI. To become *verified*, the merchant puts a one-time code (`halisi-xxxxxx`) in the bio of an account they claim, and Halisi reads the bio and looks for it. A scammer cannot edit someone else's bio, so squatting a brand name gains nothing. Halisi also seeds well-known brands itself from public sources (`curated`). *Internal note: the live Supabase needs schema v2.3 before this works end to end.*

**Q14. How does Halisi detect a clone? [Kimanzi, ready]**
Five signals, each scored 0-100 and weighted: visual (30%, logo hashes), identity (25%, name and handle similarity, including homoglyph and separator tricks), payment (25%, the number asked for versus the brand's declared one and reported numbers), language (10%, pressure and advance-payment phrases in English, Swahili and Sheng) and account (10%, age and activity). Missing signals are dropped and the rest renormalised, and the confidence figure falls. A score of 70 or more against a known brand reads FEKI; 40 or more reads ONYO. **The "AI" is mostly deterministic heuristics and perceptual hashing; the language model only drafts reports.** Say that plainly if asked where the AI is.

**Q15. How do you handle false positives? [Kimanzi, ready]**
A personal number or a Pochi line is normal for small Kenyan sellers, so payment alone never raises a page; an advance-payment demand is the gate. A similar name alone is capped below the warning line, and a logo that clearly differs vetoes a name-only match. A school's registration fee and a travel agent's visa fee do not trigger the fee rule. These cases are regression tests. Merchants can mark a case "not an imitation". ONYO says "high-risk signals", never "scam", and no verdict ever says "safe".

**Q16. Who benefits most? [ready]**
Two groups, in this order: shoppers, who get a free check before they pay, and Kenyan brands and small businesses, who get alerts and evidence ready to send. The brands are the paying side.

**Q17. What are the features? [ready, honest labels]**

| Feature | What it really is |
| :-- | :-- |
| Brand checker | Paste a link or handle, get a verdict |
| Forensic verdict experience | The full-screen HALISI, FEKI, ONYO or HAIJULIKANI reveal with the evidence behind it |
| Payment checker | Look up a phone number or Till against merchants' declared details and community reports (not against M-Pesa) |
| Community reporting | Anyone can report a number or account |
| User-input verification | If a page cannot be read, the user pastes the bio or logo |
| Merchant dashboard and alerts | The case board with in-app alerts (not SMS, and not push unless the browser permission is granted) |
| AI remediation | Drafted platform, Safaricom and KE-CIRT reports plus a customer advisory; a person reviews and sends |
| Tamper-evident evidence dossier | PDF with a SHA-256 of the evidence bundle, so later edits are detectable |
| Halisi Verified certificate and badge | Public page with a QR code, shown only for verified or curated brands |
| Typosquat watchlist | Look-alike handles generated for a merchant, with an optional scan of the ones that exist |

### B. Other questions to expect

**How do you read pages when Instagram blocks scrapers? [ready]**
Three tiers: a known profile, public OpenGraph metadata, and a manual fallback where the user pastes the bio or logo. We do not use residential proxies or headless-browser clusters; that code is archived.

**Can the AI hallucinate a number into a takedown? [ready]**
Output is validated against the facts block: any phone number, Till, handle or percentage not in the facts rejects the output and a fixed template is used. We say "validated", not "zero hallucinations". The validator checks facts, not language quality, which is why Swahili stays on templates.

**What happened when you tested the model for real? [ready, a good story]**
On 2026-11-06 a live check found that the original model had been retired by NVIDIA (HTTP 410), so every draft had silently fallen back to templates. We switched models, found the new one needed its thinking pass turned off to return anything, and found its Swahili was not fit to send. English drafts now come from the model; Swahili stays on templates. It shows the fallback worked, and why we test against the real service.

**Can anyone claim a brand? [ready]**
They can claim it, but a claim does nothing until the bio code is found on an account they control.

**Does Halisi take down accounts or freeze Tills? [ready]**
No. It prepares the evidence and the report; a person submits it to the platform, to Safaricom's fraud channel or to KE-CIRT. Contact channels were verified on 2026-10-11 and are dated in `constants.py`.

**What about defamation and the Data Protection Act? [ready, with a gap]**
Verdict wording never says "safe" and never calls a named business a scammer. Third-party numbers are masked publicly. We have not had this reviewed by counsel.

**How accurate is it? [ready]**
We have not measured precision or recall on real-world data and will not quote a percentage. What we have are regression tests for the cases that matter most (honest sellers staying clear, blatant clones flagged) and a calibration of the logo-hash curve.

**Does it work on feature phones or offline? [ready]**
Not on feature phones: the USSD channel was prototyped and archived. The web app works in a phone browser, and if the backend is unreachable the frontend serves frozen demo data, clearly marked as offline.

**Why not just use the platforms' own report buttons? [ready]**
Platforms act on reports, but they give a shopper no way to check a page before paying and a small seller no way to see copycats. Halisi sits before the payment and gives the seller ready-to-send evidence for the platform's own process.

**What does it cost to run? [you fill]**
Hosted NIM, Supabase and a small backend host. State the actual current monthly cost rather than an estimate.

**Who is on the team and who built what? [you fill]**
Collins Kimanzi (lead, detection engine, remediation, design direction), Geoffrey (API, data, ingestion, alerts), Ndegwa (frontend). Dennis Kuria's tasks were redistributed when he became unavailable.

**How will you get your first paying merchants? [you fill, no plan on record]**
There is no go-to-market plan in the repo. Agree an honest answer as a team (for example, a pilot with a few Kenyan online sellers) and do not claim signed customers unless they exist.

## 8. Slide checklist

* [ ] No statistic on any slide unless it moved out of section 6 with a primary source and period.
* [ ] No mention of SMS, USSD, Telegram, WhatsApp bot, Meta Rights API or Daraja as features.
* [ ] "Prepare", never "freeze" or "automatic takedown".
* [ ] Demo merchants labelled fictional on screen.
* [ ] Failover rehearsed three times; seeding time written into section 4.

* [ ] Impact slide carries no percentage and no KSh figure unless it was sourced in section 6.
* [ ] "Validates M-Pesa" or "checks Safaricom records" appears nowhere; say "compares with the brand's declared details and community reports".
* [ ] The pricing slide shows tier names only, with no price.

## 9. Showcase: where and how we demo

**Fill these in before the event** (nobody has recorded them in the repo): event name `<fill>`, date and time slot `<fill>`, venue or link `<fill>`, projector or screen type `<fill>`.

**What the audience sees**
1. The public site on a phone and a laptop: `<frontend URL>` (Netlify or Vercel, configured in that host's environment).
2. The merchant console on the presenter's phone, for the live alert: `<frontend URL>/dashboard`.
3. The backend behind it: `<backend URL>`, reached only through the frontend's server proxy. Open `<backend URL>/health` before going on stage; it must say `"db": "ok"` and `"demo_mode": false`.

**Environment checklist (no tunnel; everything is an environment variable)**
- Frontend host: `HALISI_API_URL` (backend URL), `HALISI_API_KEY`, `SESSION_SECRET`, `DASHBOARD_PASSCODE`, `DEMO_FALLBACK=true`, `NEXT_PUBLIC_SITE_URL`.
- Backend host: `DEMO_MODE=false`, `API_KEY`, `CORS_ORIGINS` (the frontend domain), Supabase keys, `LLM_API_KEY`, `LLM_MODEL`.
- Supabase: schema v2.3 applied, and only the merchants you intend to demo present (remove or demote test registrations).
- Confirm on the morning of the event that English playbooks come back with `generator` set to `llm`.

**Run order on stage** follows section 3, with these live-mode substitutions: use `/simulator` or pasted manual details for the FEKI moment (see section 4), and a brand-new handle for the phone alert.

**If something fails:** section 4 (Tier 2 laptop in `DEMO_MODE`, Tier 3 frozen fixtures). Rehearse it three times and write the seeding time into section 4.
