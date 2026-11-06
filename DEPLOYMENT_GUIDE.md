# Comprehensive Halisi Deployment Guide

This guide provides end-to-end instructions for deploying the Halisi MVP, including setting up the Supabase database, deploying the backend on any host with a public HTTPS URL (LLM drafting runs on hosted NVIDIA NIM, so no GPU is needed), and launching the frontend on Netlify or Vercel.

---

## Phase 1: Database Setup (Supabase)

1. **Create Project**: Go to [Supabase](https://supabase.com/) and create a new project.
2. **Apply Schema**: Navigate to the SQL Editor in your Supabase dashboard. Copy the contents of `database/schema.sql` (v2) and execute it. This will create all necessary tables (`merchants`, `threats`, `merchant_alerts`, `scans`, `community_reports`), configure RLS, and enable the `pgvector` extension.
3. **Get Credentials**: Go to **Project Settings > API** and copy your `Project URL` (SUPABASE_URL) and `service_role secret` (SUPABASE_SERVICE_ROLE_KEY).
4. **Seed the Database**: From your local machine, run the mock seeder against the live database:
   ```bash
   cd backend
   cp .env.example .env
   # Add your SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY to .env
   python -m app.ingestion.mock_seeder --target supabase --reset
   ```

---

## Phase 2: Backend Setup (any host, configured through environment variables)

**Decision (2026-11-06):** NVIDIA Brev and the ngrok tunnel are no longer part of the plan. The backend needs no GPU: remediation drafting calls **hosted NVIDIA NIM** over HTTPS, and CLIP stays off (`ENABLE_CLIP=false`; logo matching uses pHash/dHash). The frontend reaches the backend through one environment variable, `HALISI_API_URL`, instead of a tunnel.

1. **Pick a host** that can run a Python 3.12 web process (or the `backend/Dockerfile`) and gives it a public **HTTPS** URL. Any such host works; nothing in the code depends on one.
2. **Install and start** (shown for a plain Linux host; with Docker, build `backend/Dockerfile` instead):
   ```bash
   git clone https://github.com/sigangandegwa/HalisiApp.git && cd HalisiApp/backend
   python3.12 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   uvicorn app.main:app --host 0.0.0.0 --port 8080
   ```
   Keep it running under the host's process manager (systemd, the platform's own supervisor, or similar).
3. **Set environment variables** on the host (never commit them):
   - `APP_ENV=production`, `DEMO_MODE=false`
   - `API_KEY=<a_secure_random_string>` (the same value goes into the frontend as `HALISI_API_KEY`)
   - `CORS_ORIGINS=https://<your-frontend-domain>`
   - `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`
   - `ENABLE_CLIP=false`, `ENGINE_DEVICE=cpu`
   - `LLM_ENABLED=true`, `LLM_API_KEY=<your_nvidia_build_key>`, `LLM_MODEL=nvidia/nemotron-3.5-lightning-30b-a3b`, `LLM_DISABLE_THINKING=true`, `LLM_SWAHILI=false`
   - Check the model before demo day with a real call: NVIDIA retired all `meta/llama-*` models on 2026-08-26 and still lists them in `/models`.
4. **Apply the full schema** to Supabase, including the **v2.3 upgrade block** at the end of `database/schema.sql`. Without it, registering a business fails.
5. **Point the frontend at it:** set `HALISI_API_URL=https://<your-backend-host>` in the frontend's environment (Phase 3).

---

## Phase 3: Frontend Setup (Netlify or Vercel)

### Option A: Netlify (Recommended)
1. **Import Repository**: In [Netlify Dashboard](https://app.netlify.com/), click **Add new site > Import an existing project**, and select the `HalisiApp` GitHub repository.
2. **Build Settings**: Automatically detected from `netlify.toml`:
   - **Base directory**: `frontend`
   - **Build command**: `npm run build`
   - **Publish directory**: `.next`
   - **Plugin**: `@netlify/plugin-nextjs` (installed automatically)
3. **Configure Environment Variables**:
   In **Site configuration > Environment variables**, add:
   - `NEXT_PUBLIC_SITE_URL`: Your live Netlify domain (e.g. `https://halisi.netlify.app`)
   - `HALISI_API_URL`: the backend's public HTTPS URL (or omit for self-contained offline demo fixtures)
   - `HALISI_API_KEY`: API key matching your backend
   - `DASHBOARD_PASSCODE`: `halisi-demo` (or your custom admin passcode)
   - `SESSION_SECRET`: 32+ character random secret string
   - `SHOW_DEMO_PASSCODE`: `true` (displays passcode hint on `/login` for judges)
   - `DEMO_FALLBACK`: `true` (guarantees 100% uptime with pre-seeded demo fixtures if the backend is unreachable)
4. **Deploy Site**: Click **Deploy site**. The build runs cleanly with local fonts and zero external network bottlenecks.

### Option B: Vercel
1. **Create Vercel Project**: Import your GitHub repository into a new Vercel project (set Root Directory to `frontend`).
2. **Configure Environment Variables**: Add the same variables as above (`HALISI_API_URL`, `HALISI_API_KEY`, `DASHBOARD_PASSCODE`, `SESSION_SECRET`, `DEMO_FALLBACK`).
3. **Deploy**: Trigger a deployment. Vercel runs `npm run build`, outputting the compiled Next.js App Router application.

---

## Phase 4: Verification & Demo Day Checks

- **Health Check**: Visit `https://<your-backend-host>/health`. It should report `"db": "ok"`, `"llm": "nim-hosted"` and `"demo_mode": false` (`"clip": "disabled"` is expected).
- **Model Check**: Generate English playbooks for a threat and confirm `generator` is `llm`. If it says `template`, read the backend log for `LLM failed`.
- **E2E Test**: Run a manual check through your Vercel frontend. Make sure the resulting in-app alert successfully triggers on your mobile device.
- **Failover Preparedness**: If the hosted backend goes down, run it on a laptop (`uvicorn app.main:app --port 8080`, optionally with `DEMO_MODE=true`) and change `HALISI_API_URL` to the laptop's address, or leave `DEMO_FALLBACK=true` so the frontend serves its frozen fixtures.
