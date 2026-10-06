# Halisi MVP Deployment Plan & Codebase Audit

## 1. MVP Deployment Instructions

To successfully deploy the Halisi MVP for the live demo, follow these prioritized steps:

### A. Database (Supabase)
1. **Provision:** Create a new project in your Supabase dashboard.
2. **Schema:** Run the full `database/schema.sql` (v2) in the Supabase SQL editor to create all required tables (`merchants`, `threats`, `merchant_alerts`, `scans`, `community_reports`) and apply the pgvector extension.
3. **Credentials:** Copy your `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` to the `.env` files in both the `backend/` and production environment.
4. **Seed:** Run the mock seeder locally pointing to production: `python -m app.ingestion.mock_seeder --target supabase --reset`.

### B. Detection Engine (NVIDIA Brev GPU)
1. **Provision:** Launch the `halisi-engine` instance on Brev (following `docs/BREV_ENGINE_SETUP.md`).
2. **Deploy Code:** `brev shell halisi-engine` and pull the latest code.
3. **Environment:** Ensure `.env` is populated with `DEMO_MODE=false` (to use Supabase) and your `NVIDIA_API_KEY` (for NIM remediation generation). 
4. **Service:** Restart the API service: `sudo systemctl restart halisi-api`.
5. **Network:** Expose the port on an `ngrok` static domain so the frontend can hit it.

### C. Frontend Application (Vercel)
1. **Configure:** In your Vercel project settings, define the required environment variables:
   - `HALISI_API_URL` (pointing to the ngrok static domain)
   - `DASHBOARD_PASSCODE` & `SESSION_SECRET` (for merchant authentication)
2. **Deploy:** Push the `main` branch to trigger a Vercel build. The build script `npm run build` will typecheck and compile the Next.js App Router.

---

## 2. Codebase Audit: Current State vs. Missing Pieces

An audit of the codebase confirms the backend structure is mostly complete, while significant portions of the Merchant UI are absent. **In-app alerts are correctly wired into the backend**, replacing Telegram/SMS.

### ✅ What is Completed (Ready)
*   **Backend Core & Endpoints:** FastAPI is fully implemented. The routes for `/check`, `/merchants`, `/reports`, and `/threats` are solid. The endpoints for in-app alerts (`/merchants/{id}/alerts` and `/alerts/read`) are correctly nested inside `merchants.py`.
*   **Alert Dispatcher:** `backend/app/alerts/dispatcher.py` handles de-duplication, score rises, and "resolved" states correctly using `merchant_alerts` logic. No SMS/Telegram traces remain.
*   **Engine & ML Components:** Hasher v2, Matcher v2, and the Composite Scorer are complete. The payment extractors and LLM playbooks (via NIM) are built.
*   **Public Frontend Pages:** The landing page (`app/(public)/page.tsx`), shareable check results, pay check (`/pay`), report page (`/report`), and verified certificate (`/v/[slug]`) exist. 
*   **Frontend Data & Style:** `src/lib/fixtures` are loaded, i18n Swahili translations are present, and the design tokens (`styleguide/page.tsx`) are implemented.

### 🚧 What is Missing (To Build for MVP)
*   **Merchant Dashboard (`app/dashboard`):** The entire merchant-facing UI is missing from the directory tree. This includes the KPI view, threat feed, and evidence board.
*   **In-App Alerts UI:** The backend alert endpoints exist, but the frontend UI (bell, drawer, toast, browser push notifications for the presenter's phone) needs to be built inside the dashboard layout.
*   **Onboarding Flow (`app/onboarding`):** Missing the wizard and logo fingerprinting grid for merchants.
*   **Simulator Stage (`app/simulator`):** The demo presentation stage (which acts as a projector view) is completely missing.
*   **Live Validations:** The codebase hasn't been verified with live open-graph fetching (Brev) or live NVIDIA NIM responses (currently mocked in tests).

**Verdict for Demo:** We are backend-ready but blocked on the Merchant Dashboard frontend. The next immediate coding step should be building `app/dashboard` and wiring it to the `/alerts` endpoints to prove the end-to-end flow.
