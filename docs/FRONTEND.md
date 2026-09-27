# Halisi Frontend Guide (docs/FRONTEND.md)

**Audience**: Ndegwa (build owner), Collins (design direction and review), and any AI coding agent working in `frontend/`.
**Status**: Authoritative spec for the frontend MVP. Design decisions here are deliberate. Change them in this file first, then in code.
**Related**: [BACKEND.md section 5](BACKEND.md#5-api-contract-v1-frozen-the-frontend-depends-on-it) (API contract), [AGENTS.md](../AGENTS.md) (tasks), [data-flow.md](data-flow.md).

**Quality bar:** Awwwards-caliber craft (target self-score **8.5+/10** on the rubric in section 16) that still loads fast on a mid-range Android phone over Safaricom 4G. When the two conflict, the phone wins.

---

## 0. Rules for AI agents working in the frontend

1. Read AGENTS.md, this file, and BACKEND.md section 5 before writing code. Pick **one** task card (section 15) and mark it `[/]` in AGENTS.md.
2. **Build against fixtures first.** `src/lib/fixtures/*.json` match the frozen API contract exactly. The UI must work fully in demo mode before the backend exists.
3. Never hard-code colours, font sizes, easing curves or durations in components. Use the tokens in section 4.
4. Never use: Inter/Roboto/Arial/system-ui as display type, purple-blue gradients, `ease`/`linear` easing, emoji in the UI, unstyled shadcn defaults, stock illustrations, or fake statistics.
5. **Never tell a user a page is "safe".** Section 13 has the required wording.
6. Every animated component supports `prefers-reduced-motion`. Every interactive element has a designed focus state.
7. Before marking done: `npm run lint && npm run typecheck && npm run build` pass, and the page has been checked at 360 px and 1440 px widths.

---

## 1. Ownership

| Area | Owner |
| :-- | :-- |
| Design direction, tokens, signature-moment motion review, verified certificate design | **Collins** |
| All frontend implementation: pages, components, data layer, i18n, demo mode | **Ndegwa** |
| API contract questions | Geoffrey (BACKEND.md section 5) |

---

## 2. Creative concept

| | |
| :-- | :-- |
| **Brand essence** | *Truth.* "Halisi" means authentic. The product is a verdict. |
| **Visual tension** | **The original vs the forgery.** Warm banknote paper, security-print guilloche and ink stamps (the physical world's anti-counterfeit language) against misregistered, glitchy "feki" type. |
| **Signature moment** | **The Forensic Verdict** (section 8). You paste a link, the real logo and the suspect avatar slide together, their actual 64-bit perceptual hashes appear as 8×8 bit grids, the differing bits flash, five evidence bars fill, and a rubber-stamp verdict lands at display scale: **FEKI.** or **HALISI.** People will film this. |
| **Technical ambition** | Real forensic data *is* the animation. Nothing on screen is decorative fiction: the bit grid is the real pHash from the API, the bars are the real sub-scores, the character diff is the real handle difference. |

**Colour is evidence.** Green appears only when something is verified. Vermilion appears only when something is fake. Amber means caution. Everything else is ink on paper. Holding that rule is what makes the palette feel owned.

Two worlds:

- **Public (Paper):** landing, checker, result, verified merchant, report. Light, warm, editorial, trustworthy.
- **Merchant (Night Desk):** dashboard, threat detail, simulator. Dark, dense, instrument-like, the analyst's desk at 2 a.m.

---

## 3. Stack and setup

| Concern | Choice | Notes |
| :-- | :-- | :-- |
| Framework | **Next.js (latest stable, App Router, ≥ 15)** + React 19 + TypeScript `strict` | Docs previously said Next 14. Use whatever `create-next-app@latest` ships. |
| Styling | **Tailwind CSS v4** (CSS-first `@theme` in `globals.css`; there's no `tailwind.config.ts`) | |
| Primitives | **shadcn/ui**, fully restyled with our tokens | Never ship the default look. |
| Motion | **Motion** (`motion/react`) for UI/state transitions; **GSAP + ScrollTrigger** (`@gsap/react`) for the scroll story only | GSAP loads dynamically (section 12). |
| Smooth scroll | **Lenis**, desktop only (`pointer: fine`) | Native scroll on touch devices. |
| Data | **TanStack Query v5** + **zod** runtime validation + `openapi-typescript` generated types | |
| Fonts | `next/font/google`: **Fraunces** (variable: `opsz`, `wght`, `SOFT`), **Geist**, **Geist Mono** | |
| Icons | `lucide-react` at `strokeWidth={1.5}`, sized to cap height | Custom SVG for the seal, stamp and guilloche. |
| Other | `sonner` (toasts, restyled), `qrcode.react`, `diff` (`diffChars` for handle diffs), `next/og` (share images) | No Recharts: the radar is custom SVG (section 7.8). |
| Hosting | Vercel | |

```bash
# from repo root
npx create-next-app@latest frontend --ts --tailwind --eslint --app --src-dir --import-alias "@/*" --use-npm
cd frontend
npx shadcn@latest init
npx shadcn@latest add button input tabs dialog tooltip sheet skeleton toggle-group dropdown-menu sonner
npm i motion gsap @gsap/react lenis @tanstack/react-query zod qrcode.react diff clsx tailwind-merge lucide-react
npm i -D openapi-typescript @types/diff
# add "typecheck": "tsc --noEmit" and "types:api": "openapi-typescript $HALISI_API_URL/openapi.json -o src/lib/api-types.ts" to package.json scripts
```

`frontend/.env.local` (create `.env.local.example` with the same keys and empty values):

```text
HALISI_API_URL=https://<your-static-domain>.ngrok-free.app   # server-only; see BREV_ENGINE_SETUP.md
HALISI_API_KEY=                                               # server-only; same as backend API_KEY
DASHBOARD_PASSCODE=                                           # MVP merchant login
SESSION_SECRET=                                               # 32+ random chars, signs the session cookie
DEMO_FALLBACK=true                                            # serve fixtures if the API is unreachable
NEXT_PUBLIC_SITE_URL=http://localhost:3000
NEXT_PUBLIC_DEFAULT_LOCALE=en
```

### 3.1 Folder structure

```text
frontend/src/
├── app/
│   ├── layout.tsx                    # fonts, providers (Query, i18n, Lenis), ::selection, skip link
│   ├── page.tsx                      # landing + checker (Paper)
│   ├── check/[scanId]/page.tsx       # shareable result
│   ├── check/[scanId]/opengraph-image.tsx
│   ├── pay/page.tsx                  # "Check a till / phone before you pay"
│   ├── report/page.tsx               # community scam report
│   ├── v/[slug]/page.tsx             # public Halisi Verified certificate
│   ├── v/[slug]/opengraph-image.tsx
│   ├── (merchant)/                   # Night Desk theme, passcode-gated by middleware
│   │   ├── login/page.tsx
│   │   ├── dashboard/page.tsx
│   │   ├── dashboard/threats/[id]/page.tsx
│   │   ├── dashboard/onboarding/page.tsx
│   │   ├── dashboard/badge/page.tsx
│   │   └── simulator/page.tsx        # stage mode for judges (16:9)
│   ├── api/halisi/[...path]/route.ts # server proxy to FastAPI (section 9.1)
│   ├── api/session/route.ts          # passcode login -> signed httpOnly cookie
│   ├── not-found.tsx  error.tsx
│   └── globals.css                   # tokens (@theme), base styles
├── middleware.ts                     # protects (merchant) routes + merchant API paths
│   (public/sw.js at the project root: notificationclick handler only, section 6.10)
├── components/
│   ├── brand/      wordmark.tsx  seal.tsx  guilloche.tsx  microprint.tsx  stamp.tsx
│   ├── checker/    checker-input.tsx  example-chips.tsx  scan-sequence.tsx  hash-grid.tsx
│   │               evidence-bars.tsx  verdict-stamp.tsx  safe-action-card.tsx  manual-fallback.tsx
│   ├── story/      clone-anatomy.tsx  (GSAP pinned section)
│   ├── merchant/   kpi-tile.tsx  threat-row.tsx  handle-diff.tsx  score-radar.tsx  compare-slider.tsx
│   │               playbook-tabs.tsx  status-stepper.tsx  timeline.tsx  alert-bell.tsx  alert-drawer.tsx
│   ├── simulator/  clone-controls.tsx  fake-profile-card.tsx  phone-alert.tsx
│   └── ui/         (shadcn, restyled)
├── lib/
│   ├── api.ts            # typed client (calls /api/halisi/*), zod schemas
│   ├── api-types.ts      # generated, do not edit
│   ├── fixtures/         # copied from backend seeder: check-*.json, threats.json, merchant-*.json, stats.json
│   ├── hash.ts           # hexToBits(hex) -> 64 booleans, diffBits
│   ├── i18n/  en.ts  sw.ts  provider.tsx
│   ├── motion.ts         # easing + duration tokens exported for Motion/GSAP
│   ├── format.ts         # KES, dates (Africa/Nairobi), phone display 0712 345 678
│   └── utils.ts          # cn()
└── styles/  (optional partials)
```

---

## 4. Design tokens

Put these in `globals.css` under `@theme`. Components use only these names.

### 4.1 Colour

| Token | Value | Use |
| :-- | :-- | :-- |
| `--color-paper` | `#F2EEE3` | Public background (never `#fff`) |
| `--color-paper-2` | `#E8E2D2` | Cards and wells on paper |
| `--color-ink` | `#12130F` | Text and primary buttons (never `#000`) |
| `--color-ink-2` | `color-mix(in oklab, var(--color-ink) 64%, transparent)` | Secondary text |
| `--color-ink-3` | `color-mix(in oklab, var(--color-ink) 42%, transparent)` | Tertiary text and captions |
| `--color-rule` | `color-mix(in oklab, var(--color-ink) 12%, transparent)` | Hairlines |
| `--color-halisi` | `#1D5C43` | **Verified only**: banknote green |
| `--color-halisi-glow` | `#43C58A` | Verified accent on Night Desk |
| `--color-feki` | `#E4412A` | **Fake only**: stamp vermilion (large type, fills) |
| `--color-feki-ink` | `#B3301C` | Vermilion for small text on paper (AA contrast) |
| `--color-caution` | `#D99A1E` | Suspicious fills |
| `--color-caution-ink` | `#8A5A00` | Suspicious text on paper |
| `--color-night` | `#0D0F0C` | Night Desk background |
| `--color-night-2` | `#161913` | Night Desk panels |
| `--color-night-rule` | `color-mix(in oklab, var(--color-paper) 10%, transparent)` | Night Desk hairlines |

Also set `::selection { background: var(--color-ink); color: var(--color-paper); }` (inverted on Night Desk). Run contrast checks: body text ≥ 4.5:1, large display ≥ 3:1.

### 4.2 Typography

| Role | Font | Size (fluid) | Tracking / leading |
| :-- | :-- | :-- | :-- |
| Display XL (verdict stamp, hero) | Fraunces, `opsz 144`, `wght 600`, `SOFT 0` | `clamp(4.5rem, 14vw, 13rem)` | `-0.045em` / `0.88` |
| Display L (section titles) | Fraunces, `opsz 96`, `wght 500` | `clamp(2.75rem, 7vw, 6.5rem)` | `-0.035em` / `0.95` |
| Display italic accent | Fraunces italic, `SOFT 100` | inherit | the word *halisi* in headlines |
| Heading | Geist `600` | `clamp(1.25rem, 2vw, 1.75rem)` | `-0.01em` / `1.2` |
| Body | Geist `400` | `1.0625rem` (17 px), min 16 px | `0` / `1.6`, measure 45–75ch |
| Caption / label | Geist `500`, uppercase | `0.75rem` | `0.08em` / `1.3` |
| Data (handles, tills, hashes, scores) | Geist Mono `500`, `tabular-nums` | contextual | `0` |

Display-to-body ratio is about **12:1** on desktop. `text-wrap: balance` on headings and `pretty` on paragraphs. Use smart quotes and en dashes. Headline line breaks are set manually at the `sm` and `lg` breakpoints.

### 4.3 Space, radius, elevation

- Space scale (rem): `0.25 0.5 0.75 1 1.5 2 3 4 6 8 12 16`. Section padding: `clamp(4rem, 10vw, 10rem)` vertical.
- Grid: 12 columns, `gutter clamp(1rem, 2vw, 2rem)`, max width 1440 px, content offsets on the 8.33 % column grid.
- Radius: `2px` (paper cards: documents have sharp corners), `999px` (pills: input, chips, buttons). Nothing in between.
- Elevation: no drop shadows on paper. Depth comes from paper-2 wells, hairline rules and overlap. On Night Desk, use 1 px `night-rule` borders plus a subtle inner highlight.

### 4.4 Motion tokens (`lib/motion.ts` + CSS vars)

```ts
export const ease = {
  out:    [0.16, 1, 0.3, 1],     // expo out: default for entrances
  quart:  [0.25, 1, 0.5, 1],     // UI state changes
  inOut:  [0.87, 0, 0.13, 1],    // page and section transitions
  stamp:  [0.34, 1.56, 0.64, 1], // slight overshoot: verdict stamp only
} as const;
export const dur = { micro: 0.16, ui: 0.32, reveal: 0.8, story: 1.2 } as const;
export const stagger = { words: 0.06, lines: 0.09, cards: 0.07 } as const;
```

Only animate `transform`, `opacity`, `clip-path` and `filter` (the stamp only). Never animate layout properties.

### 4.5 Brand ornaments (`components/brand/`)

- **Guilloche**: generated SVG rosettes (hypotrochoid: `x=(R−r)cos t + d·cos((R−r)t/r)`), 0.5 px ink strokes at 7 % opacity, seeded per page. It draws in once on load (`stroke-dashoffset`, 1.6 s, `ease.out`) and never loops. Use it behind the hero, as the certificate border and as the seal ring. Mark it `aria-hidden`.
- **Microprint**: repeating `HALISI · AUTHENTIC · HALISI ·` at 6 px Geist Mono along section rules, like the microtext on a banknote. Decorative, `aria-hidden`.
- **Stamp**: the verdict word inside a double-rule rectangle, rotated −2.5°. An SVG `feTurbulence` + `feDisplacementMap` filter gives an ink-bleed edge. Colour comes from the verdict tokens.
- **Seal**: a circular guilloche ring with the merchant logo in the centre. Used on `/v/[slug]` and the badge.
- **Misregistration**: for "fake" type, two offset copies (vermilion and green at 40 %, ±2 px) behind the ink layer, like a badly printed counterfeit note. Used on the hero word and the FEKI stamp only.

---

## 5. Routes and information architecture

| Route | Theme | Purpose | Task |
| :-- | :-- | :-- | :-- |
| `/` | Paper | Landing: the checker *is* the hero | TSK-010 |
| `/check/[scanId]` | Paper | Shareable verdict + OG image | TSK-023 |
| `/pay` | Paper | Check a till/phone before paying | TSK-034 |
| `/report` | Paper | Report a scam page or number | TSK-034 |
| `/v/[slug]` | Paper | Halisi Verified certificate (QR target) | TSK-024 |
| `/login` | Night | Passcode login (MVP) | TSK-033 |
| `/dashboard` | Night | KPIs + live threat feed + alert bell/drawer (all merchant pages) | TSK-011, TSK-037 |
| `/dashboard/threats/[id]` | Night | Evidence board + playbooks | TSK-025 |
| `/dashboard/onboarding` | Night | Register merchant (3-step wizard) | TSK-026 |
| `/dashboard/badge` | Night | Download QR badge / story sticker | TSK-024 |
| `/simulator` | Night | Stage-mode live clone demo | TSK-027 |

Top nav (Paper): wordmark *Halisi* (Fraunces italic), `Check a page`, `Check a till`, `For businesses`, `Report`, EN/SW toggle, `Merchant login`. On mobile: wordmark + language toggle + menu sheet. The checker input sits above the fold on every breakpoint.

---

## 6. Page specifications

### 6.1 Landing `/` (TSK-010)

1. **Hero + checker (above the fold).** Asymmetric: the headline starts at column 1 and bleeds to column 11. The checker starts at column 2 and is offset below it.
   - Headline (Display XL on desktop, Display L on mobile): **"Before you pay, make sure it's *halisi*."** On load, the word *halisi* first renders misregistered as **ha1isi** (the counterfeit). After 900 ms its plates snap into registration and the `1` morphs to `l`. The typosquatting problem is demonstrated in one word. It replays on hover (desktop) and doesn't loop.
   - Sub (Body, ink-2, max 44ch): "Paste an Instagram, Facebook or TikTok link. Halisi checks it against verified Kenyan businesses in seconds."
   - **Checker input**: pill, 64 px tall, paper-2 fill, ink hairline. Tabs above it: `Link` | `Till / Phone` (the second navigates the same component to `/pay` mode). Submit button: ink pill, label `Check`. Paste is auto-detected (if the clipboard contains a supported URL, show a "Paste link" affordance). Enter submits.
   - **Example chips** (vital for judges): "Try a clone: @nairobi_sneakervault_official_ke", "Try the real one: @nairobisneakervault", "Try a competitor: @nairobisneakerhub". They fill the input and submit.
   - Background: guilloche rosette, top right, 7 % opacity, bleeding off-canvas.
2. **Result stage.** In place, below the input: the Forensic Verdict sequence (section 8). The URL updates to `/check/[scanId]` with `router.replace`. No reload, and the result is shareable.
3. **"Anatomy of a clone"**: pinned scroll story, desktop (GSAP ScrollTrigger, 5 beats = 5 dimensions). A generic social-profile card (not Instagram's UI or logo; trademark-neutral) assembles itself as you scroll: (1) the logo is copied (visual), (2) the handle mutates `nairobisneakervault → nairobi_sneakervault_official_ke` letter by letter (identity), (3) the bio types "Lipa kwanza. Pay before delivery." (language), (4) a phone number replaces the till (payment), (5) the "Joined 8 days ago" badge appears (account). At each beat, a Halisi annotation line draws to the element with the dimension name and weight. Mobile: no pin, five stacked cards with IntersectionObserver reveals.
4. **Proof band.** Live numbers from `/stats` (pages scanned, impersonations caught, businesses protected), in Geist Mono with a single count-up on first view. **No invented market statistics.** Any problem statistic in the copy must have a named, linked source (for example a Communications Authority of Kenya or Central Bank of Kenya report), or be cut.
5. **For businesses.** Left: "Get Halisi Verified. Give your customers one place to confirm it's really you." Right: a live-rendered certificate preview (section 6.4) tilting on pointer move (±4°, desktop only). CTA: `Protect my business` → `/login`.
6. **How protection works.** Three steps, laid out horizontally on desktop: *Detect* (a live alert in your Halisi dashboard within seconds) → *Warn* (AI-drafted customer warning in English and Swahili) → *Take down* (a report kit for Instagram, Safaricom and KE-CIRT/CC). Each step has a small, real UI crop, not an illustration.
7. **Footer.** Microprint rule, the tagline "Linda wateja wako. Linda jina lako." (*Protect your customers. Protect your name.*), Chiromo Tech Club credit, and a privacy note.

### 6.2 Shareable result `/check/[scanId]` (TSK-023)

- A server component fetches `GET /check/{scanId}`. It renders the **final state** of the verdict (no replayed choreography for returning visitors; offer "Replay scan").
- Actions: `Share warning on WhatsApp` (`https://wa.me/?text=` with EN/SW text and the result URL), `Copy link`, `Report this page`, `Check another`.
- `opengraph-image.tsx` (1200×630, `next/og`): paper background, the stamp word (FEKI / HALISI / TAHADHARI / HAIJULIKANI), target handle in mono, score, and the Halisi wordmark. This is what WhatsApp previews show, so the image does the viral work.

### 6.3 Check a till / phone `/pay` (TSK-034)

- One large mono input with Kenyan formatting as you type (`0712 345 678`, `Till 543 210`). It calls `/verify/payment`.
- `official` → green certificate strip showing the business name, M-Pesa account name, and a link to `/v/[slug]`.
- `reported` → vermilion strip: "Reported by N people as linked to scams. Do not send money." Show the masked number only.
- `unknown` → neutral: "This number isn't registered with Halisi. That doesn't mean it's safe. Confirm with the business through its official page." Plus a link to report.

### 6.4 Halisi Verified certificate `/v/[slug]` (TSK-024)

Designed like a title deed or banknote: guilloche border, seal with the merchant logo, business name in Display L, "Verified since" date, certificate serial (short merchant id in mono), official handles as buttons, and the **official payment method at the largest data size** (`Till 543 210 · NAIROBI SNEAKER VAULT`). A QR code points to this page. Footer: "If a page asks you to pay any other number, it is not us." Plus its own OG image.

`/dashboard/badge` lets the merchant download (a) a 1080×1920 **Instagram story sticker** PNG and (b) a square post badge with the QR. Render them with `next/og` for crisp PNGs.

### 6.5 Dashboard `/dashboard` (TSK-011), Night Desk

Bento grid (12 columns):

- Row 1: 4 KPI tiles: **Active threats** (vermilion numeral if > 0), **Pages scanned (7d)**, **Customers warned** (estimated, labelled as an estimate), **Median time to detect**. The numbers are Display L in Geist Mono, with a hairline sparkline where real data exists (no fake sparklines).
- Row 2 (8 cols): **Live threat feed**. Rows are sorted by score, with a 3 px severity rail on the left in the verdict colour, avatar, handle with character diff (`handle-diff.tsx`: characters that differ from the closest official handle are highlighted vermilion and underlined; added affixes like `_official_ke` in ink-3), score, top reason, age ("4 min ago"), and status pill. New threats slide in from the top (`ease.out`, 0.8 s) with a single vermilion pulse on the rail. `refetchInterval: 5000` during demos.
- Row 2 (4 cols): **Protection summary**: the merchant seal, official handles, and payment method. `Get your badge` links to `/dashboard/badge`.
- Empty state (a designed moment): guilloche rosette + "All quiet. Halisi is watching 3 official accounts." Not a sad illustration.

### 6.6 Threat detail `/dashboard/threats/[id]` (TSK-025), the Evidence Board

- **Header:** verdict stamp (medium size), handle diff, score, confidence ("Based on 5 of 5 signals"), status stepper (`Detected → Advisory sent → Takedown filed → Resolved`, plus a `Mark false positive` escape hatch).
- **Evidence (left, 7 cols):**
  - `compare-slider.tsx`: official logo vs suspect avatar with a draggable divider (keyboard: arrow keys move 5 %), and a `Difference` toggle (`mix-blend-mode: difference`, where identical regions go black, which is powerful on stage).
  - `hash-grid.tsx`: both 8×8 grids with the differing bits lit and the Hamming distance.
  - `score-radar.tsx`: 5-axis custom SVG radar, filled with `feki` at 18 % and a 1.5 px stroke; unavailable axes are drawn dashed and labelled "no data".
  - Evidence bars with the backend's evidence strings in mono.
  - Timeline: first seen, alert sent, playbook generated, status changes.
- **Playbooks (right, 5 cols):** tabs `Customers` | `Instagram / Facebook` | `Safaricom` | `KE-CIRT/CC`, an EN/SW toggle, the generated text in an editable textarea styled like a document, `Copy` (the icon morphs to a check, 160 ms), `Share to WhatsApp` / `Open report form` / `Open email draft` (`mailto:` with subject and body), and a provenance line: "Drafted by Llama 3.1 via NVIDIA NIM · review before sending" or "Standard template". `Generate` shows a skeleton that looks like the document being typeset.

### 6.7 Onboarding `/dashboard/onboarding` (TSK-026)

Three steps with a progress rule: **Business** (name, slug preview `halisi.app/v/…`, category, location, established date) → **Accounts & payments** (handles per platform with live normalisation; M-Pesa type `Till | Paybill | Pochi`, number, account name exactly as shown on the M-Pesa SMS; official phone numbers) → **Logo** (drop zone; once uploaded, show the computed pHash as an 8×8 grid: "This is your logo's fingerprint"). On submit: the certificate draws in with the guilloche and seal, then a CTA to the badge.

### 6.8 Simulator `/simulator` (TSK-027), stage mode

Built for a projector: 16:9, large type, high contrast, no scrolling.

- Left third: `clone-controls.tsx`. Pick a merchant; toggles for handle style (suffix / homoglyph / underscore), logo (exact / recolor / crop / jpeg), payment (phone / Pochi / none), and scam bio on/off. Big button: **Launch clone**.
- Centre: `fake-profile-card.tsx` assembles the clone (same motion language as the landing story).
- Right: the Forensic Verdict sequence runs on the real `/simulator/clone` result; then `phone-alert.tsx` slides in a phone-frame notification that mirrors the real in-app alert. The same alert fires as a browser notification on the presenter's phone, which has the dashboard open (section 6.10).
- Presenter keys: `1` `2` `3` load presets (blatant / subtle / competitor), `R` resets, `F` toggles fullscreen.

### 6.9 Error, 404, loading

- 404: large Display XL "**FEKI.**" stamp over "This page isn't halisi." Link home. It's an on-brand joke.
- Error boundary: "Something broke on our side. Your link wasn't checked." plus `Try again`.
- API unreachable with `DEMO_FALLBACK`: silently serve fixtures and show a small "Offline demo data" chip in the corner (be honest on stage).

### 6.10 In-app alerts (TSK-037), Night Desk

**No Telegram or SMS** (scope decision 2026-09-27). Alerts live inside Halisi, backed by `GET /merchants/{id}/alerts` (BACKEND.md section 8.2).

- **`useAlerts(merchantId)`**: TanStack Query polling every 5 s with the `since` cursor (the previous `server_time`). Mounted once in the `(merchant)` layout, so alerts arrive on every merchant page, including the simulator.
- **Bell** (`alert-bell.tsx`) in the Night Desk top bar: unread count in Geist Mono inside a vermilion pill. On a new alert it pulses once (scale 1 → 1.15 → 1, `ease.stamp`, 420 ms). No loops, no shaking.
- **Drawer** (`alert-drawer.tsx`, shadcn Sheet from the right): newest first, each row showing the severity rail, avatar, handle diff, score and time ago. Clicking a row opens the threat and marks it read. There's a `Mark all read` action. Empty state: "No alerts. Halisi is watching."
- **Toast** (sonner, restyled as a small document card with a vermilion rail): title + body + `Open` button, 8 s, one at a time (queue the rest). `aria-live="polite"`.
- **Tab title + favicon badge:** `(2) Halisi · Dashboard`, and the favicon swaps to a vermilion-dot variant while unread > 0.
- **Browser notifications (opt-in):**
  - Ask only after an explicit click on `Enable alerts on this device` (in the drawer and on `/dashboard`). Never prompt on page load.
  - Show them through the **service worker**: `navigator.serviceWorker.ready` → `registration.showNotification(title, { body, tag: threat_id, icon, data: { url } })`. `new Notification()` throws on Android Chrome, so the service worker is required.
  - `public/sw.js` does only one thing: handle `notificationclick` (focus or open `data.url`). No caching, no offline logic.
  - Notify only when `document.visibilityState !== "visible"`. When the tab is visible, the toast is enough.
  - iOS Safari only allows web notifications for sites added to the Home Screen (iOS 16.4+). For the demo, use an **Android** phone, or rely on the toast.
  - Background tabs throttle timers, so alerts can arrive up to about a minute late when the tab is hidden. Keep the dashboard visible on the presenter's phone.
- **Stage moment:** the presenter's phone is logged in to `/dashboard` with alerts enabled. When the simulator launches a clone on the projector, the phone buzzes with the real notification, and `phone-alert.tsx` on the projector mirrors the same alert.

---

## 7. Key component specs

| Component | Spec |
| :-- | :-- |
| `checker-input` | Controlled; validates with a URL/handle regex before submit; states: idle, focused (ink 2 px ring + paper-2 → paper transition), submitting (button becomes the scan bar), error (inline message, `feki-ink`, never a toast). |
| `scan-sequence` | Orchestrates section 8. Props: `result: CheckResult \| null`, `pending: boolean`. It can run a "pending" idle loop (scan line sweeping) until the result arrives, then plays the reveal. |
| `hash-grid` | Props: `hex: string`, `compareHex?: string`. 8×8 CSS grid of squares; bits from `lib/hash.ts`; differing cells use the verdict colour. Cells stagger in by diagonal (`(row+col)*12ms`). |
| `evidence-bars` | 5 rows: label, bar (scaleX from 0), mono score counting up, evidence caption. Unavailable → dashed empty bar + "No data". Weights are shown as small caps. |
| `verdict-stamp` | Props: `verdict`, `size: 'xl'\|'md'\|'sm'`. Word + English/Swahili subline. Section 8, step 5. |
| `safe-action-card` | Always rendered with a verdict. `official`: "This is the official page. Pay only via Till …". `impersonation`: "Don't send money. The real {business} is @{handle} · Till {n}", with a share button. `no_match` / `suspicious`: guidance + a link to `/pay`. |
| `manual-fallback` | Shown on a 502 `TARGET_UNREACHABLE`: "We couldn't open that page. Paste its bio and upload its profile picture and we'll check it." Sends the `manual` payload. |
| `handle-diff` | `diffChars(closestOfficial, target)` → added parts ink-3, substituted characters vermilion with a wavy underline. |
| `score-radar` | Custom SVG, 5 axes at 72° intervals; no library. The shape draws from the centre on mount (`ease.out`, 0.8 s). Accessible: `role="img"` + `aria-label` summarising the scores, with the table in `sr-only`. |
| `compare-slider` | Pointer + keyboard; `aria-valuenow`; images `object-fit: contain` on paper-2. |
| `playbook-tabs` | Radix Tabs restyled; copy uses `navigator.clipboard` with a textarea fallback. |

---

## 8. The signature moment: Forensic Verdict choreography

Runs when a `CheckResult` arrives. Total ≈ **2.4 s**, **skippable** (click or `Esc` jumps to the final state). The verdict text is announced to screen readers **immediately** via `aria-live="assertive"`. The animation never delays information for assistive tech.

| t (ms) | Beat | Motion |
| :-- | :-- | :-- |
| 0 | Input collapses into a 2 px scan bar | `scaleY` + opacity, `ease.quart`, 320 ms |
| 150 | Reference logo slides in from the left, suspect avatar from the right; they meet and overlap at 50 % opacity | `x`, `ease.out`, 800 ms |
| 700 | Scan line sweeps top to bottom across the overlap | `y`, `ease.inOut`, 600 ms |
| 900 | Two hash grids stagger in diagonally; differing bits flash the verdict colour twice; the Hamming readout counts `64 → 2` | 12 ms/cell stagger |
| 1300 | Evidence bars fill in weight order (visual, identity, payment, language, account); mono numbers count up | 90 ms stagger, 800 ms each |
| 1900 | **Stamp**: the verdict word lands: scale 1.12 → 1, rotate −6° → −2.5°, ink-bleed filter settles, a 1-frame 4 px "impact" offset of the page (disabled under reduced motion) | `ease.stamp`, 420 ms |
| 2200 | Safe-action card and share buttons rise in | `y 16 → 0`, `ease.out`, 600 ms |

Stamp words: **HALISI.** (official, green) · **FEKI.** (impersonation, vermilion, misregistered) · **TAHADHARI.** (suspicious, amber) · **HAIJULIKANI.** (no match, ink), each with an English subline: *Official page* / *Impersonator detected* / *Proceed with caution* / *Not a Halisi-verified page*.

Pending state: if the API takes longer than 600 ms, the scan bar shows honest step labels in mono ("Opening page…", "Comparing logo…", "Checking payment details…"). They're paced by time but worded so they're never false. After 8 s, show the manual fallback option.

Reduced motion: skip steps 0–1900 and render the final layout with a 160 ms opacity fade. No impact shake, no count-ups.

---

## 9. Data layer

### 9.1 Server proxy `app/api/halisi/[...path]/route.ts` (TSK-033)

- Forwards to `${HALISI_API_URL}/api/v1/<path>` with the method, JSON/multipart body and query. It adds `X-Halisi-Key`, `ngrok-skip-browser-warning: 1`, and `X-Forwarded-For` (client IP), and uses `AbortSignal.timeout(10_000)`.
- **Path allowlist.** Public: `check`, `check/*`, `verify/payment`, `merchants/<slug>` (GET), `reports` (POST), `stats` (GET). Merchant-only (requires a valid session cookie; enforced in both the route and `middleware.ts`): `merchants` (POST), `merchants/*/threats`, `merchants/*/alerts`, `merchants/*/alerts/read`, `threats/*`, `simulator/*`. Anything else returns 404. The proxy holds the API key, so without the allowlist anyone could use it as an open door.
- On a network error or 5xx, with `DEMO_FALLBACK=true`: return the matching fixture (by path and input) with the header `x-halisi-fixture: 1`. The UI shows the "Offline demo data" chip.
- Session: `/api/session` POST compares `DASHBOARD_PASSCODE` (constant-time) and sets an httpOnly, Secure, SameSite=Lax cookie signed with `SESSION_SECRET` (use `jose` for a JWT, 12 h expiry). Supabase Auth is P2.

### 9.2 Client

- `lib/api.ts` exposes `check(input)`, `getScan(id)`, `verifyPayment(value)`, `getMerchant(slug)`, `listThreats(merchantId, status?)`, `getThreat(id)`, `updateThreat(id, status)`, `generatePlaybooks(id, lang)`, `createReport(body)`, `getStats()`, `simulateClone(body)`. Every response is parsed with the zod schema matching BACKEND.md section 5.
- TanStack Query keys: `['scan', id]`, `['threats', merchantId, status]`, `['threat', id]`, `['stats']`, `['merchant', slug]`. Mutations invalidate the related keys. Don't use optimistic updates on verdicts.
- Server components fetch the public pages (`/check/[scanId]`, `/v/[slug]`) directly from the backend with `revalidate: 60`, going through the same helper that adds the key server-side.

---

## 10. Internationalisation (TSK-032)

- A small dictionary provider (no heavy i18n library): `lib/i18n/en.ts`, `sw.ts`, typed with `satisfies Record<keyof typeof en, string>`. The locale is kept in a cookie and toggled from the nav.
- Scope: all public pages and all verdict, reason and safe-action text (the backend provides `text_sw`), plus playbooks via `?lang=sw`. The dashboard can stay English for the MVP.
- Swahili copy must be reviewed by a fluent team member. Use natural Kenyan phrasing ("Usitume pesa", "Lipa tu kupitia Till …"), not machine-literal translations.

---

## 11. Accessibility (non-negotiable)

- WCAG 2.2 AA contrast. Colour is never the only signal: every verdict pairs its colour with a word and an icon shape (seal = official, broken seal = fake, triangle = caution, circle = unknown).
- Focus ring: `outline: 2px solid var(--color-ink); outline-offset: 3px` (paper-coloured on Night Desk). It's visible on every control and never removed.
- Skip link, landmark roles, one `h1` per page, and every form field has a label (placeholder text is not a label).
- Verdicts use `aria-live`. Charts carry text alternatives. The compare slider is keyboard operable.
- Tap targets ≥ 44 px. No hover-only information.
- `prefers-reduced-motion` honoured everywhere (section 8). Lenis is disabled under reduced motion.

---

## 12. Performance budget

| Metric | Budget (mid-range Android, "Fast 4G" throttle) |
| :-- | :-- |
| LCP (hero headline text) | < 2.0 s |
| CLS | < 0.02 |
| INP | < 200 ms |
| Landing JS (initial, gz) | < 180 KB |
| Lighthouse (mobile) | Performance ≥ 90, Accessibility ≥ 95 |

How:

- The hero has no images. The LCP element is the headline text (Fraunces subset `latin`, `display: swap`, preloaded).
- GSAP + ScrollTrigger load with `import()` when the story section is within 1 viewport (IntersectionObserver). Motion is already in the main bundle for the checker.
- Lenis loads only on `(pointer: fine)` and without reduced motion.
- Guilloche SVGs are generated once and memoised, paths ≤ 2k points, rendered as `<svg>`, not canvas.
- `next/image` with AVIF/WebP for avatars and logos, with explicit `width`/`height` or `aspect-ratio`.
- Test on a real mid-range Android (Tecno, Infinix, Samsung A-series: what customers actually use) as well as desktop Chrome.

---

## 13. Voice and required wording

Voice: calm, direct and protective, like a friend who works at the bank. Short sentences. No fear-mongering, no jargon on public pages ("logo match", not "perceptual hash", except as secondary mono evidence).

| Situation | Required wording | Never say |
| :-- | :-- | :-- |
| `official` | "This is the official page of {business}." | — |
| `impersonation` | "This page is impersonating {business}. Don't send money." | "This is 100% a scam" (we give a score, not a certainty) |
| `suspicious` | "Some signs don't add up. Confirm through {business}'s official page before paying." | "Probably fine" |
| `no_match` | "This page doesn't match any Halisi-verified business." | **"Safe"**, "Legit", "Verified" |
| Payment `unknown` | "This number isn't registered with Halisi." | "This number is safe" |

Third-party phone numbers on public pages are always masked (`0798 *** 111`). Full numbers appear only in the merchant dashboard.

---

## 14. QA checklist per page

- [ ] Works in demo mode with the backend off
- [ ] 360 px, 768 px and 1440 px layouts are intentional (not just stacked)
- [ ] Keyboard-only walkthrough possible; focus visible throughout
- [ ] Reduced motion: no motion beyond fades
- [ ] EN and SW strings present (public pages)
- [ ] Loading, empty and error states designed
- [ ] Lighthouse mobile within budget
- [ ] No emoji, no default shadcn look, no `ease`/`linear`, no `#000`/`#fff`

---

## 15. Frontend task cards (Definition of Done)

**TSK-005 Scaffold** · Ndegwa · P0. Section 3 setup, folder structure, fonts, providers, `globals.css` tokens stub. *Done:* `npm run build` passes; tokens render on a `/styleguide` dev page.

**TSK-020 Design system** · Collins (design) + Ndegwa (code) · P0 · 005. Full tokens (section 4), brand ornaments (guilloche, microprint, stamp, seal, misregistration), restyled shadcn button, input, tabs and toast, and the `/styleguide` page showing every token and state. *Done:* Collins signs off on the styleguide.

**TSK-033 Proxy, demo fallback, session** · Ndegwa · P0 · 005. Section 9.1, fixtures copied from the backend seeder, `middleware.ts`. *Done:* with the backend off, the whole checker flow works on fixtures; merchant paths 401 without the cookie.

**TSK-010 Landing + checker + Forensic Verdict** · Ndegwa (Collins reviews motion) · P1 · 020, 033. Sections 6.1, 7 and 8. *Done:* all 4 verdicts play correctly from the example chips; skip and reduced motion work; Lighthouse within budget.

**TSK-023 Shareable result + OG image** · Ndegwa · P1 · 010. Section 6.2. *Done:* pasting a result link in WhatsApp shows the stamp preview.

**TSK-034 Pay check + Report** · Ndegwa · P1 · 033. Section 6.3 + `/report`. *Done:* all 3 payment statuses render with the required wording; reports submit.

**TSK-024 Verified certificate + badge** · Collins (design) + Ndegwa · P1 · 020. Section 6.4. *Done:* the QR on the badge opens `/v/[slug]` on a phone; story sticker PNG downloads at 1080×1920.

**TSK-011 Dashboard** · Ndegwa · P1 · 033. Section 6.5. *Done:* a newly seeded threat appears within 5 s with the slide-in and pulse; empty state designed.

**TSK-037 In-app alerts** · Ndegwa · P1 · 011, backend TSK-012. Section 6.10. *Done:* on fixtures and on the live API, a new alert updates the bell, shows one toast, updates the tab title, and (with permission) shows a service-worker notification on Android Chrome that opens the threat when tapped; mark-read clears the badge; no permission prompt without a click.

**TSK-025 Threat detail + playbooks** · Ndegwa · P1 · 011. Section 6.6. *Done:* compare slider, hash grid, radar and playbook copy/share all work; status updates persist.

**TSK-026 Onboarding** · Ndegwa · P1 · 033. Section 6.7. *Done:* creates a merchant through the API and shows its fingerprint grid.

**TSK-027 Simulator stage** · Ndegwa · P1 · 010, backend TSK-031. Section 6.8. *Done:* presets 1–3 run end to end on a projector at 1920×1080, and the in-app alert arrives as a browser notification on a real Android phone.

**TSK-032 EN/SW i18n** · Ndegwa · P1 · 010. Section 10. *Done:* every public string toggles; a Swahili speaker has reviewed the copy.

---

## 16. Awwwards self-score (fill in before the demo)

| Category (weight) | Target | How we get there |
| :-- | :-- | :-- |
| Typography (25 %) | 9 | Fraunces display at 12:1, misregistered *halisi*, stamp verdicts |
| Composition (25 %) | 8 | Asymmetric hero, bleeding guilloche, bento Night Desk, certificate layout |
| Motion (20 %) | 9 | Forensic Verdict driven by real data; pinned clone anatomy |
| Colour and atmosphere (15 %) | 9 | "Colour is evidence": paper/ink + green/vermilion semantics; two worlds |
| Details and craft (15 %) | 8 | Handle diff, bit grids, microprint, designed empty/404 states, OG stamps |
| **Weighted total** | **≈ 8.7** | |

Cut ruthlessly if time runs out. Order of protection: (1) checker + Forensic Verdict, (2) threat detail + playbooks, (3) simulator, (4) certificate + badge, (5) scroll story. Three perfect things beat ten average ones.
