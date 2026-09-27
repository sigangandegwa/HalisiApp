# Comprehensive Halisi Deployment Guide (Cloud Web Version)

This guide provides end-to-end instructions for deploying the Halisi MVP. This architecture is optimized for a standard cloud web deployment (Render + Vercel), bypassing the need for a dedicated GPU instance or fragile ngrok tunnels.

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

## Phase 2: Engine & Backend Setup (Render Web Service)

We deploy the FastAPI backend to a cloud PaaS like [Render.com](https://render.com/) or [Railway](https://railway.app/). 

**Note on ML Models:** The CLIP image embeddings model (`clip-ViT-B-32`) is incredibly small and will run on the standard CPU provided by Render. While a GPU computes an image in ~15ms and a CPU takes ~200ms, removing the `ngrok` tunnel overhead actually *reduces* the overall network latency significantly, making this the best option for the MVP.

1. **Create Web Service**: In Render, create a new "Web Service" linked to your GitHub repository.
2. **Build Configuration**:
   - **Root Directory**: `backend` (Optional, depending on your setup)
   - **Environment**: Python 3.12
   - **Build Command**: 
     ```bash
     pip install -r requirements.txt -r requirements-ml.txt
     ```
   - **Start Command**:
     ```bash
     uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1
     ```
3. **Environment Variables**:
   In the Render dashboard, set the following environment variables:
   - `APP_ENV=production`
   - `DEMO_MODE=false`
   - `API_KEY=<a_secure_random_string>`
   - `CORS_ORIGINS=https://<your-vercel-app>.vercel.app`
   - `SUPABASE_URL`: <from Phase 1>
   - `SUPABASE_SERVICE_ROLE_KEY`: <from Phase 1>
   - `ENABLE_CLIP=true`
   - `ENGINE_DEVICE=cpu`
   - `LLM_ENABLED=true`
   - `LLM_API_KEY=<your_nvidia_build_key>` (Your NVIDIA NIM API key)
4. **Deploy**: Render will build and deploy your service, providing a stable and secure URL (e.g., `https://halisi-api.onrender.com`).

---

## Phase 3: Frontend Setup (Vercel)

1. **Create Vercel Project**: Import your GitHub repository into a new Vercel project.
2. **Configure Environment Variables**: In the Vercel project settings, add the following variables:
   - `HALISI_API_URL`: Your new Render backend URL (e.g., `https://halisi-api.onrender.com`)
   - `HALISI_API_KEY`: The exact same secure random string used in your Render `.env`
   - `DASHBOARD_PASSCODE`: A secure passcode for accessing the merchant dashboard
   - `SESSION_SECRET`: A 32-character random string used for session encryption
   - `DEMO_FALLBACK=false`
3. **Deploy**: Trigger a deployment. Vercel will automatically run `npm run build`, outputting the compiled Next.js App Router application.

---

## Phase 4: Verification & Demo Day Checks

- **Health Check**: Visit `https://halisi-api.onrender.com/health`. It should report `"db": "ok"` and `"clip": "cpu"`.
- **E2E Test**: Run a manual check through your Vercel frontend. Make sure the resulting in-app alert successfully triggers.
- **Failover Preparedness**: If the cloud deployment faces issues on demo day, remember you can always run the backend locally with `DEMO_MODE=false ENABLE_CLIP=false` and use ngrok to point the Vercel app to your laptop.
