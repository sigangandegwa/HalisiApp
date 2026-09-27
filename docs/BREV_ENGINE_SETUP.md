# Halisi on NVIDIA Brev: Engine Setup and Demo-Day Guide (docs/BREV_ENGINE_SETUP.md)

**Owner**: Collins (TSK-017) · **Audience**: the whole team, plus AI agents doing deployment work.
**Goal**: run the Halisi API + detection engine (CLIP ViT-B-32 on GPU) on an NVIDIA Brev instance, expose it at a **stable public HTTPS URL** that the Vercel frontend calls, and survive demo day even if Brev, Wi-Fi or the LLM fails.

> Brev's UI and CLI change often. Commands here match the Brev docs as of Sep 2026 ([CLI reference](https://docs.nvidia.com/brev/cli/cli-overview), [connectivity](https://docs.nvidia.com/brev/cli/connectivity)). If a label differs, trust the docs and update this file.

---

## 1. What runs where

```text
 Vercel (Next.js)  ──HTTPS──►  ngrok static domain  ──►  Brev GPU instance "halisi-engine"
  server proxy adds                                        ├── halisi-api  (uvicorn :8080, bound to 127.0.0.1)
  X-Halisi-Key                                             │     FastAPI + engine: pHash/dHash + CLIP on CUDA
                                                           ├── ngrok agent (systemd) → public URL
                                                           └── (optional) NIM LLM container :8000
                                                                          │
                     Supabase (Postgres + pgvector) ◄─────────────────────┘
                     NVIDIA NIM hosted API (build.nvidia.com) ◄── remediation LLM (default)
```

Why this shape:

- **One service** (API + engine together) means one deploy and no extra network hop. The same code runs on a laptop with `ENABLE_CLIP=false`, which is our hot spare.
- **Why not Brev's built-in tunnels?** Brev tunnels go through Cloudflare and **require a browser login on first access**. That's fine for sharing a Jupyter page with a teammate, but a server-to-server caller (our Vercel proxy) can't pass it. So we use an ngrok static domain for the public API, and `brev port-forward` for developers.
- **The LLM defaults to hosted NIM** (`integrate.api.nvidia.com`, OpenAI-compatible, free developer credits). That keeps the GPU small and cheap. Self-hosting a NIM on Brev is an optional upgrade for the "runs fully on NVIDIA infrastructure" pitch line (section 9).

---

## 2. Accounts and keys to get first

| # | What | Where | Goes into |
| :-- | :-- | :-- | :-- |
| 1 | Brev account + credits (ask hackathon organisers about sponsor credits) | brev.nvidia.com | — |
| 2 | NVIDIA API key (`nvapi-…`) | build.nvidia.com → any model → *Get API Key* | `LLM_API_KEY` |
| 3 | ngrok account, authtoken, and **one free static domain** | dashboard.ngrok.com → *Domains* | ngrok config, `HALISI_API_URL` |
| 4 | Supabase URL + service-role key | Supabase project → Settings → API | `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` |
| 5 | Telegram bot token | @BotFather | `TELEGRAM_BOT_TOKEN` |
| 6 | *(Optional, self-hosted NIM)* NGC API key | ngc.nvidia.com → Setup → API Key | `NGC_API_KEY` |
| 7 | GitHub access for the private repo | fine-grained PAT (read-only) or `gh auth login` | instance git |

Store keys in a shared password manager, never in the repo, chat or screenshots.

---

## 3. Choose the instance

| Use case | GPU | Disk | Notes |
| :-- | :-- | :-- | :-- |
| **Default: CLIP only, LLM via hosted NIM** | Smallest available NVIDIA GPU (T4 / L4 / A10-class, ≥ 16 GB VRAM) | 50 GB | CLIP ViT-B-32 needs < 2 GB VRAM. Cheapest option. |
| CLIP + self-hosted Llama 3.1 8B NIM | **L40S 48 GB** (safe) or A100 | 150 GB | Check the NIM model's support matrix for your GPU before paying for it. |

Name it **`halisi-engine`**. Use a plain Ubuntu base image (a "VM mode" instance if offered, so `systemd` and Docker are available). Invite Geoffrey and Ndegwa to the Brev organisation so they can `brev shell` and `brev port-forward` too.

Use `brev search` (CLI) to list the instance types available to your account.

---

## 4. Install the Brev CLI (each developer)

```bash
# macOS
brew install brevdev/homebrew-brev/brev

# Linux
bash -c "$(curl -fsSL https://raw.githubusercontent.com/brevdev/brev-cli/main/bin/install-latest.sh)"

# Windows: use WSL (PowerShell as admin), then run the Linux command inside Ubuntu
wsl --install -d Ubuntu-22.04

brev --version
brev login          # opens a browser for OAuth; creates ~/.brev/ with credentials + SSH keys
brev ls             # you should see halisi-engine once it's created
```

Everyday commands:

| Command | Purpose |
| :-- | :-- |
| `brev shell halisi-engine` | SSH into the instance |
| `brev open halisi-engine` | Open the instance in VS Code (remote) |
| `brev port-forward halisi-engine --port 8080:8080` | Call the API at `http://localhost:8080` from your laptop (dev only) |
| `brev start halisi-engine` / `brev stop halisi-engine` | Start / stop (stopped = no compute charges; storage may still bill) |
| `brev copy …` | Copy files to or from the instance |
| `brev refresh` | Re-sync after console changes |

---

## 5. First-time instance setup

Everything below runs **on the instance** (`brev shell halisi-engine`).

### 5.1 Verify the GPU

```bash
nvidia-smi                      # must list the GPU; note the driver's max CUDA version (top right)
```

### 5.2 System packages + uv + repo

```bash
sudo apt-get update && sudo apt-get install -y git tmux build-essential libjpeg-dev zlib1g-dev
curl -LsSf https://astral.sh/uv/install.sh | sh && source ~/.bashrc      # uv manages Python 3.12

git clone https://github.com/chiromo-tech-club/halisi.git ~/halisi       # create the GitHub repo first (AGENTS.md M1)
cd ~/halisi/backend
uv venv --python 3.12
source .venv/bin/activate
uv pip install -r requirements.txt -r requirements-ml.txt
# On Linux x86_64 the default torch wheel bundles CUDA. If torch can't see the GPU, see section 13.
```

### 5.3 Verify CUDA and pre-download CLIP (so the demo never downloads weights)

```bash
python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))"
python -c "from sentence_transformers import SentenceTransformer as S; m = S('clip-ViT-B-32', device='cuda'); print(m.encode(['warm-up']).shape)"
# expected: (1, 512). Weights are now cached in ~/.cache/huggingface
```

### 5.4 Configure `.env`

```bash
cp .env.example .env && chmod 600 .env && nano .env
```

Set at least:

```text
APP_ENV=production
DEMO_MODE=false
API_KEY=<long random; same value as Vercel HALISI_API_KEY>
CORS_ORIGINS=https://<your-app>.vercel.app,http://localhost:3000
SUPABASE_URL=...
SUPABASE_SERVICE_ROLE_KEY=...
ENABLE_CLIP=true
ENGINE_DEVICE=cuda
LLM_ENABLED=true
LLM_BASE_URL=https://integrate.api.nvidia.com/v1
LLM_API_KEY=nvapi-...
LLM_MODEL=meta/llama-3.1-8b-instruct
TELEGRAM_BOT_TOKEN=...
```

Generate a key with `python -c "import secrets; print(secrets.token_urlsafe(32))"`.

### 5.5 Smoke test

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8080
# in a second shell (tmux split):
curl -s localhost:8080/health
# expect: "engine": {"clip": "cuda", ...}, "db": "ok", "llm": "nim-hosted"
```

### 5.6 Seed the database (once, and again after resets)

```bash
python -m app.ingestion.mock_seeder --target supabase --reset
```

---

## 6. Keep it running (systemd)

Bind the API to `127.0.0.1`. Only the tunnel and `brev port-forward` can reach it, so there's no open port on the internet.

> The app reads `backend/.env` itself (pydantic-settings). **Don't** use systemd `EnvironmentFile=`: it doesn't strip the inline `# comments` in our `.env`, so values would silently include the comment text.

```bash
sudo tee /etc/systemd/system/halisi-api.service >/dev/null <<EOF
[Unit]
Description=Halisi API + detection engine
After=network-online.target
Wants=network-online.target

[Service]
User=$USER
WorkingDirectory=$HOME/halisi/backend
ExecStart=$HOME/halisi/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8080 --workers 1 --proxy-headers
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now halisi-api
journalctl -u halisi-api -f          # live logs
```

Use `--workers 1`: every worker would load its own copy of CLIP into VRAM, and async I/O is enough for demo traffic.

No systemd (container-mode instance)? Use tmux instead: `tmux new -s api 'cd ~/halisi/backend && .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8080'`, and detach with `Ctrl-b d`.

---

## 7. Public HTTPS URL (ngrok static domain)

```bash
curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt-get update && sudo apt-get install -y ngrok
ngrok config add-authtoken <NGROK_AUTHTOKEN>

export NGROK_DOMAIN=<your-name>.ngrok-free.app     # the static domain from the ngrok dashboard
ngrok http --url=https://$NGROK_DOMAIN 8080        # older agents: --domain=$NGROK_DOMAIN
```

Run it as a service:

```bash
sudo tee /etc/systemd/system/halisi-tunnel.service >/dev/null <<EOF
[Unit]
Description=Halisi ngrok tunnel
After=network-online.target halisi-api.service

[Service]
User=$USER
ExecStart=$(command -v ngrok) http --url=https://$NGROK_DOMAIN 8080 --log=stdout
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload && sudo systemctl enable --now halisi-tunnel
curl -s https://$NGROK_DOMAIN/health -H "ngrok-skip-browser-warning: 1"
```

Then set on Vercel (Project → Settings → Environment Variables) and **redeploy**:

```text
HALISI_API_URL=https://<your-name>.ngrok-free.app
HALISI_API_KEY=<same as backend API_KEY>
```

The free ngrok tier shows an interstitial page to browsers. Our Next.js proxy sends `ngrok-skip-browser-warning: 1` server-side, so users never see it.

**Fallback tunnel (no account needed, but the URL changes every restart, which means a Vercel env change and a redeploy each time):**

```bash
wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb
cloudflared tunnel --url http://127.0.0.1:8080    # prints https://<random>.trycloudflare.com
```

---

## 8. Developer workflow against the Brev engine

- **Backend devs** work locally (`ENABLE_CLIP=false`, `DEMO_MODE=true` or the Supabase dev project) and push. To test GPU code, `brev shell` in, then `cd ~/halisi && git pull && sudo systemctl restart halisi-api`.
- **Frontend devs** point `HALISI_API_URL` at `http://localhost:8080` and run `brev port-forward halisi-engine --port 8080:8080`, or use the ngrok URL directly.
- **Deploying a change:** `git pull` → `uv pip install -r requirements.txt -r requirements-ml.txt` (if deps changed) → `sudo systemctl restart halisi-api` → `curl /health`. Write it as `deploy/update.sh`.
- Only one person restarts the service at a time. Announce it in the team chat.

---

## 9. LLM options for remediation (TSK-009)

**A. Hosted NIM (default).** Nothing to run. Test it:

```bash
curl -s https://integrate.api.nvidia.com/v1/chat/completions \
  -H "Authorization: Bearer $LLM_API_KEY" -H "Content-Type: application/json" \
  -d '{"model":"meta/llama-3.1-8b-instruct","max_tokens":80,
       "messages":[{"role":"user","content":"Andika onyo fupi la utapeli kwa wateja kwa Kiswahili."}]}'
```

If the Swahili quality isn't good enough, try `meta/llama-3.3-70b-instruct` (same API, just change `LLM_MODEL`).

**B. Self-hosted NIM on Brev (optional upgrade, needs the L40S-class instance from section 3):**

```bash
export NGC_API_KEY=<key>
echo "$NGC_API_KEY" | docker login nvcr.io --username '$oauthtoken' --password-stdin
mkdir -p ~/.cache/nim
docker run -d --name nim-llm --restart unless-stopped --gpus all --shm-size=16GB \
  -e NGC_API_KEY -v ~/.cache/nim:/opt/nim/.cache -u $(id -u) \
  -p 127.0.0.1:8000:8000 nvcr.io/nim/meta/llama-3.1-8b-instruct:latest
docker logs -f nim-llm                 # first start downloads weights: allow 10-20 min
curl -s localhost:8000/v1/models
```

Then set `LLM_BASE_URL=http://localhost:8000/v1`, `LLM_API_KEY=unused`, and restart `halisi-api`. The API is on port **8080**, so it doesn't clash with NIM's default port 8000. If `docker` needs sudo, run `sudo usermod -aG docker $USER` and log in again.

**C. No LLM.** `LLM_ENABLED=false` uses the deterministic templates. Always keep this path working.

---

## 10. Calibrate the visual thresholds (TSK-017, do this once seeded)

The starting thresholds (pHash: 100 at ≤ 4 bits, 0 at ≥ 24; CLIP cosine: 100 at ≥ 0.93, 0 at ≤ 0.80) are guesses until measured. After the seeder generates its logo variants:

```bash
python -m app.engine.calibrate --fixtures app/ingestion/fixtures --out ../docs/calibration.md
```

`calibrate.py` (write it in TSK-017) prints, for each pair class (identical, recolor, crop, jpeg, downscale, "OFFICIAL" overlay, unrelated logo), the min, median and max pHash distance, dHash distance and CLIP cosine. Choose thresholds that separate "edited copy" from "unrelated". Commit `docs/calibration.md`, update `engine/constants.py`, and log the change in AGENTS.md section 7.

---

## 11. Cost and lifecycle

- **Stop the instance whenever nobody is using it:** `brev stop halisi-engine`. Stopped instances don't accrue compute charges, but storage may still bill. Check the credit balance and burn rate in the console daily.
- Starting takes a few minutes. systemd brings `halisi-api` and `halisi-tunnel` back automatically, and the ngrok static domain doesn't change, so Vercel needs no changes.
- Don't leave a self-hosted NIM instance (L40S) running overnight.
- Delete the instance (`brev delete`) only after the hackathon, once the team agrees.

---

## 12. Demo-day runbook

**T-60 min**

1. `brev start halisi-engine` → `brev shell halisi-engine` → `systemctl status halisi-api halisi-tunnel`.
2. `curl -s https://$NGROK_DOMAIN/health -H "ngrok-skip-browser-warning: 1"`. `clip` must be `cuda` and `db` must be `ok`.
3. Warm-up: run the 3 simulator presets once (this triggers CLIP, the DB and the LLM paths).
4. Confirm the Telegram alert arrives on the presenter's phone.

**Failover ladder (practise it once before the day)**

| Level | Trigger | Action | Time |
| :-- | :-- | :-- | :-- |
| 1. Brev (normal) | — | — | — |
| 2. Laptop hot spare | Brev down or credits exhausted | On a laptop: `DEMO_MODE=false ENABLE_CLIP=false uvicorn app.main:app --port 8080`, then stop ngrok on Brev and run `ngrok http --url=https://$NGROK_DOMAIN 8080` on the laptop. **Same domain, so no frontend change is needed.** | ~1 min |
| 3. Fully offline | Venue internet dead | Run the frontend locally (`npm run build && npm start`) with `DEMO_FALLBACK=true`, and the backend locally with `DEMO_MODE=true`. Everything is served from fixtures, with the "Offline demo data" chip visible. | ~2 min |

Keep a phone hotspot as a backup network, and a 60-second screen recording of the full demo as the last resort.

---

## 13. Troubleshooting

| Symptom | Likely cause | Fix |
| :-- | :-- | :-- |
| `torch.cuda.is_available()` is `False` | CPU wheel installed, or driver too old for the wheel's CUDA | `nvidia-smi` shows the driver's CUDA version; reinstall torch from the matching index at pytorch.org, e.g. `uv pip install torch --index-url https://download.pytorch.org/whl/cu12X` |
| `/health` shows `clip: disabled` | `ENABLE_CLIP` not `true`, or model load failed | `journalctl -u halisi-api -n 100`; check `~/.cache/huggingface` exists |
| First check after boot takes 5–10 s | CUDA lazy init / cold cache | The lifespan warm-up (BACKEND.md section 6.3) must run; hit `/health` and run one simulator preset after each start |
| Vercel gets HTML instead of JSON | ngrok interstitial | Proxy must send `ngrok-skip-browser-warning: 1` |
| `ERR_NGROK_…` domain already online | The domain is bound to another agent (e.g. a laptop) | Stop the other agent first; only one agent can hold a static domain |
| CORS errors in the browser | The browser is calling the API directly | All calls must go through `/api/halisi/*` (FRONTEND.md section 9.1). Also check `CORS_ORIGINS` |
| NIM container exits | Not enough VRAM/disk, or bad NGC key | `docker logs nim-llm`; check the model support matrix; use hosted NIM (option A) |
| Instagram fetches fail from Brev | Datacenter IP blocked / login wall | Expected. Use tier 1 (seeded) or tier 3 (manual fallback). See BACKEND.md section 7.2 |
| `CUDA out of memory` | Multiple workers or NIM + CLIP on a small GPU | `--workers 1`; move to hosted NIM |

---

## 14. Security notes

- The API listens on `127.0.0.1` only. Public access goes only through the tunnel, and every write endpoint needs `X-Halisi-Key`.
- `.env` has mode `600` and is never committed. Rotate `API_KEY` and `LLM_API_KEY` after the hackathon.
- Don't paste keys into Brev's shared notebooks or the team chat.
- Rate limiting reads the client IP from `X-Forwarded-For`. uvicorn's `--proxy-headers` is set, and it trusts only `127.0.0.1` (the ngrok agent) by default.
