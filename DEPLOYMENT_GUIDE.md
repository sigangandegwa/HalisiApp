# Comprehensive Halisi Deployment Guide

This guide provides end-to-end instructions for deploying the Halisi MVP, including setting up the Supabase database, deploying the backend on an NVIDIA Brev GPU instance, and launching the frontend on Vercel.

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

## Phase 2: Engine & Backend Setup (NVIDIA Brev)

The backend runs entirely on an NVIDIA Brev GPU instance to utilize CLIP embeddings and expose the FastAPI endpoints.

1. **Provision Instance**: On [brev.dev](https://brev.dev/), create a new instance named `halisi-engine`. A T4 or L4 GPU (≥ 16 GB VRAM) is sufficient if using hosted NIM for the LLM.
2. **Connect**: Install the Brev CLI locally, then SSH into the instance:
   ```bash
   brev shell halisi-engine
   ```
3. **Install Dependencies**:
   ```bash
   sudo apt-get update && sudo apt-get install -y git tmux build-essential libjpeg-dev zlib1g-dev
   curl -LsSf https://astral.sh/uv/install.sh | sh && source ~/.bashrc
   ```
4. **Clone & Setup Environment**:
   ```bash
   git clone https://github.com/chiromo-tech-club/halisi.git ~/halisi
   cd ~/halisi/backend
   uv venv --python 3.12
   source .venv/bin/activate
   uv pip install -r requirements.txt -r requirements-ml.txt
   ```
5. **Configure Environment Variables**:
   ```bash
   cp .env.example .env && chmod 600 .env && nano .env
   ```
   Set the following variables:
   - `APP_ENV=production`
   - `DEMO_MODE=false`
   - `API_KEY=<a_secure_random_string>`
   - `CORS_ORIGINS=https://<your-vercel-app>.vercel.app,http://localhost:3000`
   - `SUPABASE_URL` & `SUPABASE_SERVICE_ROLE_KEY`
   - `ENABLE_CLIP=true` and `ENGINE_DEVICE=cuda`
   - `LLM_API_KEY=<your_nvidia_build_key>`
6. **Set Up Systemd Services**:
   Create `halisi-api.service` to keep the FastAPI server running on `127.0.0.1:8080`, and `halisi-tunnel.service` using `ngrok` (with your ngrok authtoken and static domain) to securely expose port 8080. Start and enable both services. (See `docs/BREV_ENGINE_SETUP.md` for exact systemd configs).

---

## Phase 3: Frontend Setup (Vercel)

1. **Create Vercel Project**: Import your GitHub repository into a new Vercel project.
2. **Configure Environment Variables**: In the Vercel project settings, add the following variables:
   - `HALISI_API_URL`: Your ngrok static domain (e.g., `https://<your-name>.ngrok-free.app`)
   - `HALISI_API_KEY`: The exact same secure random string used in your Brev `.env`
   - `DASHBOARD_PASSCODE`: A secure passcode for accessing the merchant dashboard
   - `SESSION_SECRET`: A 32-character random string used for session encryption
   - `DEMO_FALLBACK=false`: Ensure the app routes to your live backend.
3. **Deploy**: Trigger a deployment. Vercel will automatically run `npm run build`, outputting the compiled Next.js App Router application.

---

## Phase 4: Verification & Demo Day Checks

- **Health Check**: Visit `https://<your-ngrok-domain>/health`. It should report `"db": "ok"` and `"clip": "cuda"`.
- **E2E Test**: Run a manual check through your Vercel frontend. Make sure the resulting in-app alert successfully triggers on your mobile device.
- **Failover Preparedness**: If Brev goes down, be prepared to spin up the backend locally (`uvicorn app.main:app --port 8080`) with `ENABLE_CLIP=false` and run the ngrok tunnel from your laptop to keep the same URL alive.
