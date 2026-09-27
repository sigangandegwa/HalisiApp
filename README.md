<div align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=timeGradient&height=280&section=header&text=Halisi&fontSize=90&animation=twinkling&fontAlignY=38&desc=AI-Powered%20Brand%20Impersonation%20Detection%20for%20Kenya&descAlignY=55&descAlign=50" alt="Halisi Banner" width="100%" />

  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=22&duration=3000&pause=1000&color=27ae60&center=true&vCenter=true&width=600&lines=Stopping+M-Pesa+Fraud+Before+It+Happens;Detecting+Scam+Clones+with+AI;AI-Drafted+Takedown+Kits+in+English+%26+Swahili" alt="Typing SVG" />
</div>

<p align="center">
  <a href="https://fastapi.tiangolo.com"><img src="https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi" alt="FastAPI"></a>
  <a href="https://nextjs.org/"><img src="https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white" alt="Next.js"></a>
  <a href="https://supabase.com/"><img src="https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white" alt="Supabase"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://tailwindcss.com/"><img src="https://img.shields.io/badge/Tailwind-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white" alt="Tailwind CSS"></a>
  <a href="https://www.nvidia.com/en-us/"><img src="https://img.shields.io/badge/NVIDIA%20Brev%20%2B%20NIM-76B900?style=for-the-badge&logo=nvidia&logoColor=white" alt="NVIDIA Brev + NIM"></a>
</p>

---

## 🚨 The Problem: The Clone-and-Collect Scam
In Kenya, social commerce runs on Instagram, Facebook, TikTok and WhatsApp, and payments run on M-Pesa. Scammers clone a trusted shop's page in minutes: they copy the logo and product photos, pick a look-alike handle (`nairobi_sneakervault_official_ke`), and ask customers to pay a personal number or a Pochi la Biashara. The customer loses money. The real business loses its reputation.

## 🛡️ The Solution: Halisi
**Halisi** *(Swahili for "authentic")* gives customers a verdict **before they pay**, and gives businesses a response kit **within the first minute** of a clone appearing.

- 🔍 **Check a page**: paste a link and get **HALISI** (official), **FEKI** (impersonator), **TAHADHARI** (caution) or **HAIJULIKANI** (not verified), with plain-language reasons.
- 💳 **Check a till or phone**: is this number registered to a verified business, or reported by other customers?
- 🏅 **Halisi Verified**: a certificate page and QR story sticker merchants post, so customers have one trusted place to confirm the real page and till.
- 📡 **Live merchant alerts**: in-app alerts in the Halisi dashboard (bell, toasts, and opt-in phone/browser notifications) with the evidence attached.
- 📝 **AI-drafted response kit**: customer warnings in **English and Swahili**, Instagram/Facebook impersonation report text, and Safaricom and KE-CIRT/CC report drafts. The kit is grounded in computed evidence and **sent by the merchant**, never auto-filed.

---

## 🧠 How the engine decides

Halisi separates **"who is this imitating?"** from **"how dangerous is it?"**. That's how it avoids flagging honest shops that happen to have similar names.

| Dimension | Weight | Signal |
| :-- | :-: | :-- |
| Visual | 30% | Logo vs avatar: perceptual hashes (pHash/dHash) + CLIP ViT-B-32 embeddings on NVIDIA GPUs |
| Identity | 25% | Handle and name look-alikes: separators, homoglyphs (`l`/`1`, `rn`/`m`), `_official_ke`-style affixes |
| Payment | 25% | Phone numbers, tills, paybills or Pochi requests that aren't registered to the business |
| Language | 10% | Weighted English/Swahili/Sheng scam phrases ("lipa kwanza", "pay before delivery") |
| Account | 10% | New account, low activity, first seen recently |

Missing signals lower the **confidence** instead of being guessed. Score ≥ 70 means impersonation; 40–69 means suspicious. Halisi never tells a user a page is "safe".

```mermaid
graph TD
    A[Link / handle / till] --> B{Official handle?}
    B -- yes --> V[HALISI: official page]
    B -- no --> C[Acquire target: seeded / OpenGraph / manual upload]
    C --> D[Resemblance: logo hash + CLIP, handle look-alike]
    C --> E[Malice: payment mismatch, scam language, account signals]
    D --> F(Composite score 0-100 + confidence)
    E --> F
    F -->|>= 70| G[FEKI: threat created]
    F -->|40-69| H[TAHADHARI]
    F -->|< 40| I[HAIJULIKANI: not verified]
    G --> J[In-app alert + browser notification]
    G --> K[AI response kit via NVIDIA NIM, validated, human sends]
```

---

## 💻 Tech Stack
- **Frontend:** Next.js (App Router), TypeScript, Tailwind CSS v4, shadcn/ui, Motion + GSAP
- **Backend:** FastAPI, Pydantic v2, HTTPX
- **AI engine:** CLIP ViT-B-32 on **NVIDIA Brev** GPUs, imagehash, RapidFuzz; remediation LLM via **NVIDIA NIM** (Llama 3.1)
- **Data:** Supabase Postgres + pgvector
- **Alerts:** in-app (polling + service-worker notifications), no third-party messaging

---

## 📚 Documentation
| Doc | For |
| :-- | :-- |
| [AGENTS.md](AGENTS.md) | Tasks, owners, change log, review findings (start here) |
| [docs/BACKEND.md](docs/BACKEND.md) | API contract, engine maths, security |
| [docs/FRONTEND.md](docs/FRONTEND.md) | Design system, pages, motion |
| [docs/BREV_ENGINE_SETUP.md](docs/BREV_ENGINE_SETUP.md) | GPU deployment + demo-day failover |
| [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) | Local setup, build order, demo script |

---

## 🛠️ Quick Start

```bash
git clone https://github.com/chiromo-tech-club/halisi.git
cd halisi/backend
uv venv --python 3.12 && source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
uv pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env                                  # DEMO_MODE=true runs fully offline
uvicorn app.main:app --reload --port 8080             # http://localhost:8080/docs
```

Frontend *(coming soon, TSK-005)*:
```bash
cd frontend && npm install && npm run dev             # http://localhost:3000
```

---

## 👥 The Team
Built by the **Chiromo Tech Club (University of Nairobi)**:
* **Collins Kimanzi**: Lead, Detection Engine, AI Remediation & Design Direction
* **Geoffrey**: Backend API, Data, Ingestion & Alerts
* **Ndegwa**: Frontend Application & Experience

With thanks to **Dennis Kuria** for early architecture work.

<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=rect&color=27ae60&height=40&text=Securing%20Kenya's%20Digital%20Economy&fontColor=ffffff&fontSize=20&fontAlignY=65" />
</p>
