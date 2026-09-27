# Halisi Backend Guide (docs/BACKEND.md)

**Audience**: Geoffrey, Collins, and any AI coding agent working in `backend/` or `database/`.
**Status**: Authoritative spec for the backend MVP. If code disagrees with this file, fix the code or open a change to this file first. Never let them silently drift.
**Related**: [AGENTS.md](../AGENTS.md) (tasks and ownership), [data-flow.md](data-flow.md) (lifecycle), [BREV_ENGINE_SETUP.md](BREV_ENGINE_SETUP.md) (GPU deployment), [FRONTEND.md](FRONTEND.md) (consumer of the API contract).

---

## 0. Rules for AI agents working in the backend

1. Read AGENTS.md sections 1, 3 and 9, then this file, before writing code.
2. Pick one task card from section 13 and do only that task. Mark it `[/]` in AGENTS.md with your signature.
3. **The API contract in section 5 is frozen.** The frontend builds against it in parallel using fixtures. If you must change it, update section 5 and `frontend/src/lib/fixtures/` in the same commit, and log it in AGENTS.md section 6.
4. Every public function has type hints and a docstring. Every engine function is **pure**: no network, no DB. Pass data in, get scores out. I/O lives in `ingestion/`, `core/` and `api/`.
5. No test may touch the network. Use `respx` for httpx and generated PIL images for hashing.
6. Never invent numbers in user-facing text (phone numbers, tills, similarity %). They must come from computed evidence.
7. Run `ruff check . && pytest -q` from `backend/` before marking a task done.

---

## 1. Ownership (after Dennis's tasks were redistributed)

| Area | Owner | Paths |
| :-- | :-- | :-- |
| Detection engine: imaging, hashing, CLIP, payment score, composite scorer | **Collins** | `backend/app/engine/{imaging,hasher,embeddings,payment,scorer,constants}.py` |
| Text engine: identity matcher + scam-language tokens | **Geoffrey** | `backend/app/engine/matcher.py` |
| AI remediation (LLM + templates, prompts) | **Collins** | `backend/app/engine/remediation.py`, `backend/app/engine/prompts/` |
| Brev GPU deployment | **Collins** | `docs/BREV_ENGINE_SETUP.md`, `deploy/` |
| API, config, DB, repository layer, security | **Geoffrey** | `backend/app/api/*`, `backend/app/core/*`, `database/*` |
| Ingestion (URL parsing, OG scraper, extractors, seeder) | **Geoffrey** | `backend/app/ingestion/*` |
| Alerts (Telegram, Africa's Talking) | **Geoffrey** | `backend/app/alerts/*` |

---

## 2. Architecture

```text
 Browser ──► Next.js (Vercel) ──server-side proxy──►  Halisi API (FastAPI)  ──► Supabase Postgres + pgvector
             /api/halisi/*       adds X-Halisi-Key     runs on NVIDIA Brev GPU        (service-role key)
                                                        │
                                                        ├── engine/   pure scoring (pHash, dHash, CLIP, RapidFuzz)
                                                        ├── ingestion/ URL parse, OG fetch, extractors, seeder
                                                        ├── alerts/    Telegram, Africa's Talking
                                                        └── LLM ──► NVIDIA NIM (hosted build.nvidia.com, or self-hosted on Brev)
```

**Deployment decision (hackathon):** one FastAPI service holds both the API and the engine and runs on a Brev GPU instance, exposed with a stable ngrok domain. The same code runs on any laptop with `ENABLE_CLIP=false` (hash-only) as a hot spare. Splitting the engine into a separate microservice adds a network hop and a second deploy for no demo benefit, so don't do it for the MVP.

### 2.1 `/api/v1/check` request lifecycle and latency budget

| Step | Module | Budget (p50) |
| :-- | :-- | :-- |
| Parse input (URL / handle / phone / till) | `ingestion/url_parser.py` | 1 ms |
| Result cache lookup (10 min TTL, key = platform+handle) | `core/cache.py` | < 5 ms |
| Official-handle short-circuit (exact match in `merchant_handles`) | `engine/scorer.py` | < 5 ms |
| Fetch profile metadata (seed DB → OG fetch → manual input) | `ingestion/page_scraper.py` | 0 ms seeded / 0.8–2.5 s live |
| Fetch avatar, compute pHash + dHash | `engine/hasher.py` | 300 ms fetch + 5 ms |
| CLIP embedding (GPU / CPU) | `engine/embeddings.py` | 15 ms / 150 ms |
| Score against all merchants (in-memory, N < 100) | `engine/scorer.py` | < 10 ms |
| Persist scan + threat, dispatch alerts | FastAPI `BackgroundTasks` | off the request path |

Targets: **< 1.2 s** for seeded/cached targets (the demo path), **< 4 s** for live fetches. Return `elapsed_ms` in every response.

---

## 3. Project layout and conventions

```text
backend/
├── app/
│   ├── main.py                    # app factory, lifespan (http client, CLIP warm-up, merchant cache), routers, error handlers
│   ├── core/
│   │   ├── config.py              # Settings(BaseSettings) reading .env (see backend/.env.example)
│   │   ├── repository.py          # Repository protocol + SupabaseRepository + MemoryRepository (DEMO_MODE / tests)
│   │   ├── cache.py               # tiny TTL cache for check results
│   │   ├── security.py            # API-key dependency, rate limiter, SSRF guard (is_public_url)
│   │   └── logging.py
│   ├── api/v1/
│   │   ├── router.py
│   │   └── endpoints/  check.py  merchants.py  threats.py  remediation.py  reports.py  stats.py  simulator.py
│   ├── engine/
│   │   ├── imaging.py             # load/normalise images (alpha, EXIF, square pad, size limits)
│   │   ├── hasher.py              # pHash/dHash + calibrated similarity
│   │   ├── embeddings.py          # CLIP ViT-B-32 (optional, lazy)
│   │   ├── matcher.py             # identity (handle/name) + language (scam tokens)
│   │   ├── payment.py             # payment-signal scoring from extracted phones/tills
│   │   ├── scorer.py              # 5-dimension composite, overrides, verdict, reasons
│   │   ├── remediation.py         # playbook generation (LLM + template fallback + validation)
│   │   └── prompts/               # versioned prompt files, IDs registered in AGENTS.md section 7
│   ├── ingestion/
│   │   ├── url_parser.py          # URL/handle/phone/till → Target
│   │   ├── page_scraper.py        # tiered metadata fetch
│   │   ├── extractors.py          # Kenyan phone/till/paybill regexes, OG description parser
│   │   ├── mock_seeder.py         # seeds Supabase or MemoryRepository
│   │   └── fixtures/              # seed JSON + generated logo assets
│   ├── alerts/  telegram_bot.py  africas_talking.py  dispatcher.py
│   └── schemas/ merchant.py  threat.py  check.py  remediation.py  report.py  common.py
├── tests/  (mirrors app/: tests/engine/test_hasher.py, ...)
├── requirements.txt  requirements-ml.txt  requirements-dev.txt
├── pyproject.toml                 # ruff + pytest config (asyncio_mode = "auto")
└── .env.example
```

Conventions:

- **Python 3.12** (3.11–3.13 OK). Use `uv` (`uv venv --python 3.12`), not a system Python. The committed `.pyc` files came from 3.14, which some ML wheels don't support yet.
- Pydantic v2 style only: `model_config = ConfigDict(from_attributes=True)`, **not** `class Config:` (v1, deprecated). Use `uuid.UUID` for ids, `datetime` with timezone.
- One shared `httpx.AsyncClient` created in the FastAPI `lifespan`, stored on `app.state`. Never create a client per request.
- CPU-bound work (CLIP, hashing big images) goes through `await asyncio.to_thread(...)` so it doesn't block the event loop.
- Errors: raise domain exceptions (`TargetUnreachable`, `UnsupportedPlatform`, `InvalidImage`) and map them to JSON in `main.py`: `{"error": {"code": "...", "message": "..."}}`. Never leak stack traces.
- Logging: structured, one line per check with `scan_id`, verdict, score and `elapsed_ms`. Never log secrets or full phone numbers.
- `config.py` must parse `CORS_ORIGINS` as a comma-separated list. `main.py` currently has `allow_origins=["*"]` with `allow_credentials=True`. That's invalid under the CORS spec, and Starlette handles it by reflecting any origin. Replace it with `settings.cors_origins`.

---

## 4. Data model

**Source of truth: [database/schema.sql](../database/schema.sql) (v2).** Tables: `merchants`, `merchant_handles`, `threats`, `scans`, `remediation_logs`, `community_reports`, plus the RPC `match_merchant_logos`.

Why v2 replaced v1: v1 had no `logo_phash` (there was nothing to compare against), a single `risk_score` (the 5-dimension breakdown couldn't be stored), one till string, and no scans/reports tables. Its Pydantic models (`schemas/merchant.py`, `schemas/threat.py`) must be rewritten to mirror v2 (TSK-002).

Rules:

- Handles are stored normalised: lowercase, no `@`, no trailing slash.
- Phone numbers are stored in E.164 format (`+254712345678`).
- A `NULL` sub-score means "signal unavailable". Never store `0` for unknown.
- The frontend never queries Supabase directly. All access goes through the API.

`Repository` protocol (in `core/repository.py`). Both implementations must pass the same tests:

```python
class Repository(Protocol):
    async def list_merchants(self) -> list[MerchantRecord]: ...
    async def get_merchant(self, merchant_id: UUID) -> MerchantRecord | None: ...
    async def get_merchant_by_slug(self, slug: str) -> MerchantRecord | None: ...
    async def find_official_handle(self, platform: str, handle: str) -> MerchantRecord | None: ...
    async def find_by_payment(self, phone: str | None, till: str | None) -> PaymentLookup: ...
    async def create_merchant(self, data: MerchantCreate, hashes: LogoFeatures) -> MerchantRecord: ...
    async def upsert_threat(self, threat: ThreatUpsert) -> ThreatRecord: ...
    async def list_threats(self, merchant_id: UUID, status: str | None) -> list[ThreatRecord]: ...
    async def get_threat(self, threat_id: UUID) -> ThreatRecord | None: ...
    async def update_threat_status(self, threat_id: UUID, status: str) -> ThreatRecord: ...
    async def insert_scan(self, scan: ScanCreate) -> UUID: ...
    async def get_scan(self, scan_id: UUID) -> ScanRecord | None: ...
    async def insert_remediation(self, log: RemediationCreate) -> None: ...
    async def insert_report(self, report: ReportCreate) -> UUID: ...
    async def stats(self, merchant_id: UUID | None) -> Stats: ...
```

The supabase-py client is synchronous. Wrap its calls in `asyncio.to_thread` inside `SupabaseRepository`.

---

## 5. API contract v1 (FROZEN: the frontend depends on it)

Base path `/api/v1`. JSON everywhere. Write endpoints require the header `X-Halisi-Key: <API_KEY>`. The Next.js server proxy adds it, so browsers never see it. Public endpoints are rate-limited per IP.

| Method | Path | Auth | Purpose |
| :-- | :-- | :-- | :-- |
| GET | `/health` | none | Liveness and engine status |
| POST | `/api/v1/check` | public, 10/min/IP | Check a URL or handle |
| GET | `/api/v1/check/{scan_id}` | public | Re-open a shared result |
| GET | `/api/v1/verify/payment?value=` | public, 20/min/IP | Is this phone/till official or reported? |
| GET | `/api/v1/merchants/{slug}` | public | Public verified profile (`/v/[slug]` page) |
| POST | `/api/v1/merchants` | key | Onboard merchant (multipart: JSON + logo file) |
| GET | `/api/v1/merchants/{id}/threats?status=` | key | Dashboard feed |
| GET | `/api/v1/threats/{id}` | key | Threat detail |
| PATCH | `/api/v1/threats/{id}` | key | Update status `{ "status": "takedown_filed" }` |
| POST | `/api/v1/threats/{id}/playbooks?lang=en\|sw` | key | Generate remediation playbooks |
| POST | `/api/v1/reports` | public, 5/min/IP | Community scam report |
| GET | `/api/v1/stats?merchant_id=` | public (global) / key (merchant) | KPIs |
| POST | `/api/v1/simulator/clone` | key | Demo: build and score a synthetic clone |

### 5.1 `GET /health`

```json
{ "status": "ok", "version": "0.2.0", "demo_mode": false,
  "engine": { "clip": "cuda", "hash": "ok" }, "llm": "nim-hosted", "db": "ok" }
```

### 5.2 `POST /api/v1/check`

Request (exactly one of `url` / `handle`; `manual` is the fallback when the page can't be fetched):

```json
{
  "url": "https://instagram.com/nairobi_sneakervault_official_ke",
  "handle": null,
  "platform": null,
  "manual": { "display_name": null, "bio": null, "avatar_base64": null }
}
```

Response `CheckResult`:

```json
{
  "scan_id": "7b1c1d9e-2c1f-4b9a-9d0e-3f8a2c1e5b77",
  "verdict": "impersonation",
  "score": 94.25,
  "confidence": 1.0,
  "target": {
    "platform": "instagram",
    "handle": "nairobi_sneakervault_official_ke",
    "display_name": "Nairobi Sneaker Vault Official",
    "url": "https://instagram.com/nairobi_sneakervault_official_ke",
    "avatar_url": "https://.../clone_nsv.png",
    "follower_count": 212,
    "post_count": 9,
    "account_created_on": "2026-09-19",
    "fetched_via": "seed"
  },
  "matched_merchant": {
    "id": "0b4b...",
    "business_name": "Nairobi Sneaker Vault",
    "slug": "nairobi-sneaker-vault",
    "logo_url": "https://.../real_nsv.png",
    "official_handles": [{ "platform": "instagram", "handle": "nairobisneakervault", "url": "https://instagram.com/nairobisneakervault" }],
    "payment": { "type": "till", "number": "543210", "account_name": "NAIROBI SNEAKER VAULT" }
  },
  "dimensions": [
    { "key": "visual",   "label": "Logo match",        "score": 97.5, "weight": 0.30, "available": true,  "evidence": "pHash distance 2/64 · CLIP similarity 0.97" },
    { "key": "identity", "label": "Name & handle",     "score": 92.0, "weight": 0.25, "available": true,  "evidence": "'nairobi_sneakervault_official_ke' contains 'nairobisneakervault' + suffix '_official_ke'" },
    { "key": "payment",  "label": "Payment details",   "score": 100,  "weight": 0.25, "available": true,  "evidence": "Asks for payment to 0798 *** 111 (not registered to this business)" },
    { "key": "language", "label": "Scam language",     "score": 80.0, "weight": 0.10, "available": true,  "evidence": "'pay before delivery', 'lipa kwanza'" },
    { "key": "account",  "label": "Account signals",   "score": 90.0, "weight": 0.10, "available": true,  "evidence": "Account is 8 days old · 9 posts" }
  ],
  "reasons": [
    { "code": "LOGO_COPY",        "severity": "high", "text": "Uses a logo 97% identical to Nairobi Sneaker Vault's.", "text_sw": "Inatumia nembo inayofanana 97% na ya Nairobi Sneaker Vault." },
    { "code": "PAYMENT_MISMATCH", "severity": "high", "text": "Asks you to pay a phone number that is not registered to this business.", "text_sw": "Inakuomba ulipe namba ambayo haijasajiliwa na biashara hii." }
  ],
  "hashes": { "target_phash": "c3d1a4f0e8b27c19", "reference_phash": "c3d1a4f0e8b27c1b", "hamming_distance": 2 },
  "safe_action": { "text": "Pay only via Buy Goods Till 543210 (NAIROBI SNEAKER VAULT) through @nairobisneakervault.", "text_sw": "Lipa tu kupitia Till 543210 (NAIROBI SNEAKER VAULT) kupitia @nairobisneakervault." },
  "threat_id": "1f0e...",
  "elapsed_ms": 412
}
```

Verdicts: `official` (exact official handle), `impersonation` (score ≥ 70), `suspicious` (40–69, or ≥ 70 with confidence < 0.5), `no_match` (< 40, **never phrased as "safe"**), `error`.

For `official`: `score` = 0, `dimensions` = [], and `matched_merchant` is set. For `no_match`: `matched_merchant` = null. Include `reasons` for any scam-language hits anyway (an unrelated page can still be a scam).

Public responses **mask** third-party phone numbers (`0798 *** 111`). Full numbers appear only in key-authenticated threat endpoints (merchant dashboard). This limits harm if we ever produce a false positive (Data Protection Act 2019, defamation risk).

Errors: `422` invalid input, `404` scan not found, `429` rate limited, `502` `{"error":{"code":"TARGET_UNREACHABLE"}}`. On 502 the frontend offers the manual fallback form.

### 5.3 `GET /api/v1/verify/payment?value=0798999111`

```json
{ "kind": "phone", "normalized": "+254798999111", "display": "0798 *** 111",
  "status": "reported",                 // "official" | "reported" | "unknown"
  "merchant": null,                     // set when status = "official" (public profile subset)
  "report_count": 3, "linked_threats": 1 }
```

`unknown` must be phrased as "not registered with Halisi", **not** as "safe".

### 5.4 `GET /api/v1/merchants/{slug}` (public)

`{ business_name, slug, logo_url, category, location, established_on, is_verified, official_handles[], payment{type,number,account_name}, verified_since }`

### 5.5 `POST /api/v1/merchants` (key, multipart)

Fields: `data` (JSON: business_name, slug, aliases[], category, location, established_on, mpesa_type, mpesa_number, mpesa_account_name, phone_numbers[], handles[{platform, handle}], telegram_chat_id?, alert_phone?) and `logo` (PNG/JPEG/WebP ≤ 5 MB). The server computes pHash, dHash and CLIP, and returns the merchant plus `logo_phash`.

### 5.6 Threat endpoints (key)

`GET /merchants/{id}/threats` returns `ThreatSummary[]`: `{ id, platform, target_handle, target_url, avatar_url, composite_score, verdict, status, first_seen_at, top_reason }`, sorted by score desc.

`GET /threats/{id}` returns `ThreatDetail`: every `CheckResult` field (unmasked) plus `status`, `status_history[]`, `extracted_phones[]`, `extracted_tills[]`, `playbooks_generated[]`.

### 5.7 `POST /threats/{id}/playbooks?lang=en`

```json
{
  "generator": "llm",                       // or "template" (fallback)
  "model": "meta/llama-3.1-8b-instruct",
  "prompt_ids": ["PROMPT_CONSUMER_DEFENSE_V2", "PROMPT_PLATFORM_TAKEDOWN_V2", "PROMPT_SAFARICOM_REPORT_V2"],
  "consumer_warning": { "title": "Scam alert", "body": "…", "whatsapp_share_url": "https://wa.me/?text=…" },
  "platform_takedown": { "platform": "instagram", "report_url": "https://help.instagram.com/…", "body": "…" },
  "safaricom_report":  { "channel": "email", "to": "<verified address>", "subject": "…", "body": "…" },
  "kecirt_report":     { "to": "<verified address>", "subject": "…", "body": "…" }
}
```

### 5.8 `POST /api/v1/reports`

`{ target_url?, target_handle?, platform?, reported_phone?, reported_till?, description?, reporter_contact? }` → `{ id, status: "pending" }`. At least one of url/handle/phone/till is required.

### 5.9 `GET /api/v1/stats`

`{ pages_scanned, threats_detected, impersonations_blocked_7d, merchants_protected, median_detection_ms, top_platforms: [{platform, count}] }`. With a merchant key it also returns `{ active_threats, resolved, customers_warned_estimate }`.

### 5.10 `POST /api/v1/simulator/clone` (demo)

`{ merchant_id, tweaks: { handle_style: "suffix"|"homoglyph"|"underscore", logo: "exact"|"recolor"|"crop"|"jpeg", payment: "phone"|"pochi"|"none", bio_tokens: true } }` returns a `CheckResult`. It builds a synthetic target in memory and runs the real engine on it. Nothing is fabricated, and the result is persisted with `source = 'simulator'`.

**Type generation:** the frontend runs `npx openapi-typescript <API>/openapi.json -o src/lib/api-types.ts`. Give every endpoint a `response_model` so the OpenAPI output is exact.

---

## 6. Detection engine specification (Collins; matcher: Geoffrey)

The engine answers two separate questions:

1. **Who is this page imitating?** Resemblance: `visual` and `identity`.
2. **How dangerous is it?** Malice: `payment`, `language` and `account`.

A page that resembles nobody is `no_match`, however scammy its bio is. A page that resembles a merchant but shows no malice signals is at most `suspicious`. That separation is what stops Halisi from flagging every Nairobi shop that says "delivery countrywide".

### 6.1 Image loading (`engine/imaging.py`)

```python
Image.MAX_IMAGE_PIXELS = 25_000_000          # decompression-bomb guard

def normalize_image(data: bytes, size: int = 256) -> Image.Image:
    """Decode bytes -> EXIF-corrected RGB square on white. Raises InvalidImage."""
    # 1. Image.open + .verify() then reopen (verify invalidates the file)
    # 2. ImageOps.exif_transpose
    # 3. If mode has alpha (RGBA/LA/P with transparency): alpha-composite onto WHITE.
    #    Transparent PNG logos otherwise hash against a black background and never match their avatar.
    # 4. Pad to square with white (letterbox, keep aspect) - IG avatars are square, logos often aren't
    # 5. Resize to size x size with LANCZOS, convert("RGB")
```

Fetching (in `ingestion/`, not engine): shared client, `timeout=8s`, `follow_redirects=True` with max 3, streaming with a **5 MB cap**, `content-type` must start with `image/`, and the URL must pass `core.security.is_public_url` (SSRF guard, section 11).

### 6.2 Hasher v2 (`engine/hasher.py`), TSK-015

Bug in v1: `similarity = 100 - distance/64*100`. Two **unrelated** images have an expected pHash Hamming distance of about 32 (each bit is roughly a coin flip), so v1 gives unrelated logos about **50% visual similarity**. Fed into the composite, that pushes innocent pages toward "suspicious". The v1 function also downloads inside the engine (I/O in pure code) and ignores transparency.

v2 API:

```python
def compute_hashes(img: Image.Image) -> ImageHashes:        # phash + dhash, hash_size=8 -> 16 hex chars each
def hamming(a_hex: str, b_hex: str) -> int                    # 0..64
def hash_similarity(distance: int, *, full: int = 4, zero: int = 24) -> float:
    """100 if distance <= full, 0 if distance >= zero, linear between."""
def visual_score(target: ImageFeatures, ref: ImageFeatures) -> VisualResult:
    """max(phash_sim, dhash_sim, clip_sim); evidence string names the winning signal."""
```

CLIP mapping (starting values, **calibrate on the seed set in TSK-017**): cosine ≥ 0.93 → 100, ≤ 0.80 → 0, linear between. Record the final thresholds in `engine/constants.py` together with the calibration table (distance distributions for same, edited and unrelated pairs).

### 6.3 Embeddings (`engine/embeddings.py`), TSK-017

- `sentence-transformers` `SentenceTransformer("clip-ViT-B-32")`, loaded once in `lifespan` **only if** `ENABLE_CLIP=true`. Device: `cuda` if available and `ENGINE_DEVICE != cpu`.
- `embed_image(img) -> list[float] | None` with `normalize_embeddings=True` (512-d). Call it via `asyncio.to_thread`.
- Warm up with one dummy image at startup. The first CUDA call is slow, and it must not land on a judge.
- When disabled, return `None`, and the visual score falls back to hashes. The code path must work with or without the model.

### 6.4 Identity matcher v2 (`engine/matcher.py`), TSK-016 (Geoffrey)

v1 problems: it compares raw strings, so `.`, `_` and `-` count as characters. It has no homoglyph folding (`l/1/i`, `0/o`, `rn/m`), no removal of scam affixes (`official`, `ke`, `kenya`, `shop`), no display-name comparison, and it takes only one authentic handle while merchants have several. Jaro-Winkler also has a **prefix bias**: every `nairobi_*` handle gets a large boost against `nairobisneakervault`. Using JW alone is a false-positive machine in Kenya, where handles commonly start with a city name.

```python
AFFIXES = {"official", "real", "original", "genuine", "the", "ke", "kenya", "254", "nairobi_official",
           "shop", "store", "online", "deals", "offers", "hq", "team", "care", "support"}
HOMOGLYPHS = [("rn", "m"), ("vv", "w"), ("0", "o"), ("1", "l"), ("i", "l"), ("|", "l"), ("3", "e"), ("5", "s"), ("@", "a")]

def normalize_handle(h: str) -> str:           # lowercase, strip @, NFKC, remove . _ - and spaces
def fold_homoglyphs(s: str) -> str:            # apply HOMOGLYPHS in order
def strip_affixes(tokens: list[str]) -> list[str]
def identity_score(target_handle, target_name, merchant) -> IdentityResult:
    """Max over every official handle + business_name + aliases of:
       a) 0.5*JaroWinkler + 0.5*fuzz.ratio   on fold(normalize(x))
       b) fuzz.token_set_ratio               on affix-stripped tokens
       c) containment: 95 if fold(ref) in fold(target) and len(ref) >= 6
       Evidence names which comparison won and which affixes/homoglyphs were found."""
```

Golden tests (must pass; add more, never delete):

| Official | Target | Expect |
| :-- | :-- | :-- |
| `nairobisneakervault` | `nairobi_sneakervault_official_ke` | ≥ 90 |
| `nairobisneakervault` | `nairobisneakervau1t` | ≥ 90 |
| `nairobisneakervault` | `nairobi.sneaker.vault` | ≥ 95 |
| `kilimaniglow` | `kiIimaniglow_ke` (capital i) | ≥ 90 |
| `nairobisneakervault` | `nairobi_bakery` | < 50 |
| `nairobisneakervault` | `nairobisneakerhub` (real competitor) | < 70 |
| `pwanithreads` | `mombasa_fashion_house` | < 30 |

### 6.5 Payment signal (`engine/payment.py` + `ingestion/extractors.py`), TSK-021 / TSK-016

Extractors (Geoffrey, `ingestion/extractors.py`). Run them on bio, captions and link-in-bio text:

```python
KE_PHONE = re.compile(r"(?<!\d)(?:\+?254[\s-]?|0)([17](?:[\s-]?\d){8})(?!\d)")    # -> "+254" + 9 digits
TILL     = re.compile(r"(?:till|buy\s*goods|\bb\.?g\.?\b)\s*(?:no\.?|number|#|:)?\s*(\d{5,7})(?!\d)", re.I)
PAYBILL  = re.compile(r"pay\s*bill\s*(?:no\.?|number|#|:)?\s*(\d{5,7})(?!\d)", re.I)
WA_LINK  = re.compile(r"wa\.me/(\d{10,13})")
POCHI    = re.compile(r"pochi\s*la\s*biashara|send\s*money\s*to|tuma\s*pesa", re.I)
```

Scoring (Collins, `engine/payment.py`):

| Situation | payment score |
| :-- | :-- |
| No phone/till found | `None` (unavailable) |
| Only numbers/tills registered to the resembled merchant | 0 |
| Unregistered phone/till found, and resemblance ≥ 60 | **100** |
| Unregistered phone/till found, resemblance < 60 | 60 |
| Pochi / "send money" phrasing next to an unregistered number | 100 |
| Number appears in a `confirmed` community report | 100 (and see override O3) |

### 6.6 Language signal (`engine/matcher.py`)

Weighted tokens, English + Swahili + Sheng. **Low-weight tokens are ones legitimate Kenyan shops use too.** Score = `min(100, sum(weights of matched tokens))`, or `None` if there's no text at all.

| Weight | Tokens |
| :-- | :-- |
| 40 | `pay before delivery`, `lipa kwanza`, `lipa kabla`, `pochi la biashara`, `send money to`, `tuma pesa`, `deposit required`, `pay via m-pesa before` |
| 25 | `payment with order`, `no refunds`, `non-refundable`, `offer ends today`, `leo tu`, `whatsapp only`, `dm for price`, `limited stock` |
| 10 | `strictly delivery`, `no physical shop`, `inbox to order`, `delivery countrywide`, `order now` |

v1's flat `matches * 33.33` also caps at 99.99 instead of 100. Use explicit weights.

### 6.7 Account signal

`account_created_on` is usually **not available** from public Instagram/Facebook metadata (it only appears in the app's "About this account"). Don't design around it. Use:

- account age when known: < 30 days → 90, < 90 → 60, < 365 → 30, else 10
- `post_count < 12` → 60; `follower_count < 300` while resemblance ≥ 80 → 70
- Halisi `first_seen_at` less than 7 days ago for a page resembling a merchant established over a year ago → 50

Score = max of the available sub-signals, or `None` if none are available.

### 6.8 Composite scorer (`engine/scorer.py`), TSK-008

```python
WEIGHTS = {"visual": 0.30, "identity": 0.25, "payment": 0.25, "language": 0.10, "account": 0.10}

def score_target(target: TargetFeatures, merchant: MerchantFeatures, ctx: ScoringContext) -> ScoreResult:
    # O1 official short-circuit: exact normalised handle on same platform in merchant_handles
    #    -> verdict "official", score 0 (checked BEFORE scoring, in the API layer, across all merchants)
    dims = {k: fn(...) for k, fn in DIMENSIONS}               # each: float 0-100 or None
    available = {k: v for k, v in dims.items() if v is not None}
    wsum = sum(WEIGHTS[k] for k in available)
    composite = sum(WEIGHTS[k] * v for k, v in available.items()) / wsum    # renormalise over available
    confidence = round(wsum, 2)                                              # share of evidence we had
    resemblance = max(dims["visual"] or 0, dims["identity"] or 0)

    if resemblance < 50:  composite = min(composite, 39)                     # G1 resemblance gate
    if resemblance >= 80 and dims["payment"] == 100: composite = max(composite, 90)   # O2 payment hijack
    if ctx.confirmed_report_hit: composite = max(composite, 85)             # O3 community-confirmed
    verdict = tier(composite)                                                # >=70 impersonation, >=40 suspicious, else no_match
    if verdict == "impersonation" and confidence < 0.5: verdict = "suspicious"   # O4 thin evidence
    return ScoreResult(composite=round(composite, 2), confidence=confidence, verdict=verdict,
                       dimensions=..., reasons=build_reasons(dims, merchant, target))
```

In the API layer, score the target against **every** merchant and keep the highest composite. `ScoreResult` must be JSON-serialisable and identical to the `CheckResult` subset in section 5.2.

Weights and thresholds live in `engine/constants.py` and are overridable via env (`THREAT_THRESHOLD`, `SUSPICIOUS_THRESHOLD`). Any change is logged in AGENTS.md section 7 (heuristics registry).

Reasons: each dimension ≥ 60 emits a `Reason(code, severity, text, text_sw)`. Codes: `LOGO_COPY`, `HANDLE_LOOKALIKE`, `PAYMENT_MISMATCH`, `POCHI_REQUEST`, `SCAM_LANGUAGE`, `NEW_ACCOUNT`, `LOW_ACTIVITY`, `COMMUNITY_REPORTED`. Keep the text short, concrete, and free of jargon for consumers.

Required scorer tests: the seeded blatant clone ≥ 90 → `impersonation`; the subtle clone ≥ 70; the competitor with a similar name < 40 → `no_match`; the official handle → `official`; logo-only evidence (all other signals `None`) gives confidence 0.30 and at most `suspicious`.

### 6.9 AI remediation (`engine/remediation.py`), TSK-009

- **Facts first.** Build a `RemediationFacts` object from the DB: merchant name, official handles, till and account name, target handle/URL, masked-free phone numbers, actual hash distance, actual scores, first_seen_at. The LLM gets only these facts.
- **LLM:** NVIDIA NIM through the OpenAI-compatible client (`openai.AsyncOpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY)`). Default `meta/llama-3.1-8b-instruct`. Use `meta/llama-3.3-70b-instruct` if the Swahili quality isn't good enough. `temperature=0.3`, JSON output, `timeout=LLM_TIMEOUT_SECONDS`.
- **Validation (anti-hallucination):** parse into Pydantic. Then extract every phone number, till and `@handle` from the output and assert each one appears in the facts. On any failure (timeout, bad JSON, invented number), fall back to the **deterministic template**, set `generator="template"`, and log why.
- **Templates** live in `engine/prompts/templates/*.j2` (EN + SW) and always work offline. They are the demo safety net.
- **Human in the loop:** Halisi drafts; the merchant sends. Never auto-email Safaricom or KE-CIRT/CC.
- **Accuracy of channels:** the Instagram impersonation report form and the Facebook IP report form are public. Meta's *Brand Rights Protection* portal needs enrolment, so don't claim we file there. Before the demo, verify the current Safaricom fraud-reporting channels (commonly cited: forwarding scam SMS to **333**, and a fraud email address) and the National **KE-CIRT/CC** (Communications Authority) incident contact. Store them in `engine/constants.py` with a `VERIFIED_ON` date.
- Log every generation to `remediation_logs` with `prompt_id` and `model`.
- Prompt files: `engine/prompts/consumer_defense_v2.md`, `platform_takedown_v2.md`, `safaricom_report_v2.md`, `kecirt_report_v1.md`. The registry is AGENTS.md section 7.

---

## 7. Ingestion (Geoffrey)

### 7.1 URL parser (`ingestion/url_parser.py`), part of TSK-018

Accept: `instagram.com/<h>`, `www.instagram.com/<h>/?igsh=…`, `facebook.com/<h>`, `facebook.com/profile.php?id=<n>`, `m.facebook.com/…`, `fb.com/…`, `tiktok.com/@<h>`, `x.com/<h>`, `twitter.com/<h>`, `wa.me/<phone>` (→ payment check), raw `@handle` (platform defaults to instagram), and raw phone/till numbers (→ `/verify/payment`). Strip query strings and tracking params. Reject anything else with `422 UNSUPPORTED_PLATFORM`. Max input length 2048.

### 7.2 Page scraper (`ingestion/page_scraper.py`), TSK-006

Instagram and Facebook actively block unauthenticated and datacenter scraping (login walls, 429s). Brev's IPs are datacenter IPs. So design **tiers**, and never let the demo depend on tier 2:

1. **Known targets**: seeded/previously seen threats in the DB (instant, demo path).
2. **OpenGraph fetch** with httpx: mobile User-Agent, 5 s timeout, parse `og:title`, `og:description`, `og:image`. The Instagram description often reads `"1,234 Followers, 56 Following, 78 Posts - See Instagram photos and videos from Name (@handle)"`. Parse counts and name with a tolerant regex. Treat any login-wall response as a failure.
3. **Manual fallback**: the frontend lets the user paste the bio and upload the profile picture (`manual` in the request). This is a real product feature, not a hack. It works for any platform, including WhatsApp catalogues.
4. *(Stretch)* Playwright headless with a persistent context, only if tiers 1–3 are solid.

Return `TargetProfile(platform, handle, display_name, bio, avatar_url | avatar_bytes, follower_count, post_count, account_created_on, fetched_via)`. Cache it for 10 minutes.

### 7.3 Mock seeder (`ingestion/mock_seeder.py`), TSK-007: P0, the demo depends on it

Use **fictional** businesses only. Search each name first to make sure it isn't a real Kenyan business. Never label a real third-party account as a scammer in the demo.

- 3 merchants: *Nairobi Sneaker Vault* (sneakers, Till), *Kilimani Glow* (beauty, Paybill), *Pwani Threads* (Mombasa fashion, Pochi). Each has a generated logo (PIL/SVG, committed under `fixtures/assets/`), 2 handles, official numbers, and an `established_on` date.
- Per merchant, 3 targets: **blatant clone** (exact logo, `_official_ke` suffix, personal number, scam tokens, 8 days old), **subtle clone** (recoloured and cropped logo, homoglyph handle, Pochi request, no age data), and a **look-alike legitimate competitor** (different logo, similar name, own till). The competitor must score `no_match`. It's the false-positive proof for judges.
- Generate logo variants programmatically (`recolor`, `crop 85%`, `jpeg q=35`, `add "OFFICIAL" text`, `downscale 64px`). They double as the hash/CLIP calibration set (TSK-017).
- 5 community reports, 2 of them `confirmed`, pointing at the blatant clones' phone numbers.
- Commands: `python -m app.ingestion.mock_seeder --target supabase|memory --reset`. It must be idempotent.
- The same fixtures JSON is copied to `frontend/src/lib/fixtures/` for offline frontend mode.

---

## 8. Alerts (Geoffrey)

### 8.1 Telegram (`alerts/telegram_bot.py`), TSK-012

- Call the Bot API directly with the shared httpx client. No extra library is needed.
- Use **`parse_mode: "HTML"` with `html.escape()`**. The old snippet in DEVELOPMENT.md used legacy `Markdown`. Handles like `nairobi_sneakervault_official_ke` contain underscores, which Telegram reads as italics markers, and the API rejects the message with *"can't parse entities"*.
- Message: verdict, score, target handle, top 2 reasons, and an inline keyboard button "Open in Halisi" (dashboard threat URL). If `avatar_url` is available, use `sendPhoto` with the caption.
- Linking a merchant: deep link `https://t.me/<bot>?start=<merchant_slug>`. A `/start` handler (webhook or `getUpdates` polling script) stores `chat_id` on the merchant.
- Trigger: `dispatcher.py` runs in `BackgroundTasks` when a threat is created or crosses the threshold. De-duplicate: one alert per threat per 6 hours.

### 8.2 Africa's Talking SMS (`alerts/africas_talking.py`), TSK-013

- The **sandbox does not deliver to real phones**. Messages appear in the AT web simulator (simulator.africastalking.com). For the demo, show the simulator on screen, or use live credits.
- The SDK is synchronous. Call it via `asyncio.to_thread`. Keep messages at 160 characters or fewer.

### 8.3 (P2) Consumer checker bot, TSK-030

The same Telegram bot answers consumers: forward a link or type a till/phone number, and the bot calls `/check` or `/verify/payment` internally and replies with the verdict and safe action (EN/SW).

---

## 9. Remediation tracking loop (P2, TSK-029)

An APScheduler job in the API process (not Celery or Redis for the MVP) re-fetches `status in ('advisory_sent','takedown_filed')` threats every 12 hours. HTTP 404 or a "page isn't available" response sets `resolved` and `resolved_at`. The dashboard shows time-to-takedown.

---

## 10. Demo mode

`DEMO_MODE=true` means: `MemoryRepository` loaded from fixtures, the scraper serves tier 1 only, LLM calls are skipped (templates), and alerts are logged instead of sent unless `TELEGRAM_BOT_TOKEN` is set. The whole backend then runs with **no internet**. Test it with Wi-Fi off before demo day.

---

## 11. Security checklist (must be green before the demo)

- [ ] **SSRF guard** `is_public_url(url)`: `https` only, resolve DNS, reject private, loopback, link-local, multicast and reserved IPs (`ipaddress` module), re-check after each redirect, max 3 redirects. Apply it to every server-side fetch (profile pages *and* avatar URLs taken from OG tags, which the attacker controls).
- [ ] Image limits: 5 MB, 25 MP, content-type check, Pillow `verify()`.
- [ ] Rate limits (slowapi): `/check` 10/min/IP, `/verify/payment` 20/min/IP, `/reports` 5/min/IP. Behind ngrok, read the client IP from `X-Forwarded-For` (first hop) only when the request comes through the tunnel.
- [ ] `X-Halisi-Key` required on all write/merchant endpoints; compare with `secrets.compare_digest`.
- [ ] CORS: explicit origins from env. No `*` with credentials.
- [ ] Secrets only in `.env`. The service-role key never leaves the backend. `.env` is gitignored.
- [ ] Public responses mask third-party phone numbers. Reporter contact info is never returned by any endpoint.
- [ ] Validation: Pydantic models with `max_length` on every string; handle regex `^[a-z0-9._]{1,60}$`.
- [ ] Error handler returns generic messages; details are only logged.
- [ ] Prompt injection: scraped bios go into the LLM **only as quoted data** inside the facts block, and the output validator (section 6.9) blocks any number that isn't in the facts.

---

## 12. Testing

```text
backend/tests/
├── conftest.py                  # MemoryRepository fixture seeded from fixtures, TestClient, respx router
├── engine/test_imaging.py       # alpha->white, EXIF, square pad, bomb guard
├── engine/test_hasher.py        # identical=100, recolor/crop >= 80, unrelated <= 10 (generated images)
├── engine/test_matcher.py       # golden identity table (section 6.4) + language weights
├── engine/test_payment.py       # extractor regexes: 0712 345 678, +254-712-345678, 0112345678, "Till No. 543210"
├── engine/test_scorer.py        # section 6.8 required cases, renormalisation, overrides
├── engine/test_remediation.py   # validator rejects invented number; template fallback on timeout
├── api/test_check.py            # official / impersonation / no_match / 422 / 502 -> manual
└── api/test_security.py         # SSRF (127.0.0.1, 169.254.169.254, [::1], redirect-to-private), rate limit, API key
```

The root-level `test_hash.py` and `test_matcher.py` are print scripts. They always exit 0, even on failure, and `test_hash.py` needs the internet. Port their cases into `backend/tests/` with real `assert`s, then delete them (TSK-015/016).

`pyproject.toml`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
[tool.ruff]
line-length = 110
target-version = "py312"
```

---

## 13. Backend task cards (Definition of Done)

Each card: owner · priority · depends on. **Done** means the code is merged, tests pass, and AGENTS.md is updated.

**TSK-001 Deploy schema v2**: Geoffrey · P0. Run `database/schema.sql` in Supabase, and add the URL and service key to `backend/.env`. *Done:* all 6 tables and the RPC exist; `select match_merchant_logos(array_fill(0, array[512])::vector, 1)` runs.

**TSK-002 Core scaffolding**: Geoffrey · P0 · 001. `config.py`, `repository.py` (both implementations), `cache.py`, `logging.py`, `main.py` lifespan and error handlers, `api/v1/router.py`, Pydantic v2 schemas for every model in section 5, and `pyproject.toml`. *Done:* `uvicorn app.main:app` starts with `DEMO_MODE=true` and no network; `/health` matches section 5.1; `/docs` lists every route (stubs return fixtures).

**TSK-015 Hasher v2 + imaging**: Collins · P0 · 002. Implements sections 6.1–6.2 and moves the download into ingestion. *Done:* `test_imaging.py` and `test_hasher.py` pass; unrelated generated images score ≤ 10.

**TSK-016 Matcher v2**: Geoffrey · P0 · 002. Implements sections 6.4 and 6.6. *Done:* the golden table passes; root test scripts are deleted.

**TSK-021 Extractors + payment score**: Geoffrey (extractors), Collins (score) · P0. Implements section 6.5. *Done:* `test_payment.py` passes, with at least 12 real-world Kenyan formats.

**TSK-008 Scorer**: Collins · P0 · 015, 016, 021. Implements section 6.8. *Done:* the required scorer tests pass; `ScoreResult` serialises to the section 5.2 shape.

**TSK-007 Mock seeder**: Geoffrey · P0 · 002. Implements section 7.3. *Done:* `--target memory` and `--target supabase` both work and are idempotent; fixtures are exported to the frontend.

**TSK-018 API endpoints**: Geoffrey · P0 · 002, 008. Section 5 routes plus the URL parser (section 7.1). *Done:* `api/test_check.py` passes; the OpenAPI schema generates clean TS types.

**TSK-019 Security hardening**: Geoffrey · P1 · 018. Section 11. *Done:* `api/test_security.py` passes; every checklist item is ticked.

**TSK-006 Page scraper**: Geoffrey · P1 · 018. Tiers 1–3 (section 7.2). *Done:* 2 live public pages fetched (record whether IG blocks from Brev's IP); login walls are detected; the manual fallback works end to end.

**TSK-017 CLIP + Brev deployment**: Collins · P1 · 015. Section 6.3 plus BREV_ENGINE_SETUP.md. *Done:* `/health` shows `clip: cuda` on Brev; the calibration table is committed; thresholds are updated in constants.

**TSK-009 Remediation**: Collins · P1 · 008. Section 6.9. *Done:* LLM and template paths both produce EN and SW output; the validator test passes; prompts are registered in AGENTS.md section 7.

**TSK-012 Telegram alerts**: Geoffrey · P1 · 018. Section 8.1. *Done:* a seeded clone triggers a real Telegram message with a photo and button, and no duplicate within 6 hours.

**TSK-022 Reports + payment lookup**: Geoffrey · P1 · 018. `/reports` and `/verify/payment`. *Done:* a confirmed report flips a number to `reported`, and O3 applies in `/check`.

**TSK-031 Simulator endpoint**: Collins · P1 · 008. Section 5.10. *Done:* each tweak combination returns a real engine score within 1.5 s.

**TSK-013 Africa's Talking SMS**: Geoffrey · P2. **TSK-029 Takedown tracker**: Geoffrey · P2. **TSK-030 Consumer Telegram bot**: Geoffrey · P2. **TSK-028 Evidence dossier PDF** (Jinja2 → HTML → PDF, including side-by-side images, hashes, timestamps and a SHA-256 of the evidence bundle): Collins · P2.

---

## 14. Known pitfalls

- `requirements.txt` was saved as **UTF-16** by PowerShell `pip freeze >`. Linux tooling and GitHub treat that as binary. It has been replaced by curated UTF-8 files in `backend/`. On Windows use `uv pip freeze | Out-File -Encoding utf8`, or better, edit by hand.
- `test_*.py` in the repo root import `backend.app...`. The backend's import root is `backend/` (`app.*`). Run everything from `backend/`.
- The IG `og:image` is a signed CDN URL that expires. Hash it at fetch time and store the hash, not just the URL.
- CLIP gives every pair of flat-colour logos a fairly high cosine similarity. Always calibrate on your own seed set before trusting the thresholds.
- Don't call Supabase from inside engine functions. It makes them untestable and slow.
