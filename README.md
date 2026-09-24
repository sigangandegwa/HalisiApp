<div align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=timeGradient&height=280&section=header&text=Halisi&fontSize=90&animation=twinkling&fontAlignY=38&desc=AI-Powered%20Brand%20Impersonation%20Detection%20for%20Kenya&descAlignY=55&descAlign=50" alt="Halisi Banner" width="100%" />

  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=22&duration=3000&pause=1000&color=27ae60&center=true&vCenter=true&width=600&lines=Stopping+M-Pesa+Fraud+Before+It+Happens;Detecting+Scam+Clones+with+AI;Automated+Safaricom+%26+Meta+Takedowns" alt="Typing SVG" />
</div>

<p align="center">
  <a href="https://fastapi.tiangolo.com"><img src="https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi" alt="FastAPI"></a>
  <a href="https://nextjs.org/"><img src="https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white" alt="Next.js"></a>
  <a href="https://supabase.com/"><img src="https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white" alt="Supabase"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://tailwindcss.com/"><img src="https://img.shields.io/badge/Tailwind-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white" alt="Tailwind CSS"></a>
</p>

---

## 🚨 The Problem: The "Send to Till" Scam
In Kenya, social commerce is exploding, but so is impersonation fraud. Scammers clone legitimate Instagram and Facebook storefronts, steal their product photos, and funnel desperate customers into paying fraudulent M-Pesa Till numbers. The authentic brands lose their reputation, and customers lose their hard-earned money.

## 🛡️ The Solution: Halisi
**Halisi** *(Swahili for Authentic/Real)* is a multi-modal AI detection engine built to automatically discover, score, and remediate brand impersonation across Kenyan social commerce. We bridge the gap between AI threat detection and actual financial/legal takedown workflows.

<br>

<div align="center">
  <img src="https://raw.githubusercontent.com/tandpfun/skill-icons/main/icons/Shield-Dark.svg" width="60" />
  <h3>5-Dimensional Risk Scoring</h3>
</div>

Instead of just looking at the account name, Halisi's AI Engine computes a holistic `0-100` threat score using five concurrent modules:
1. **Logo Perceptual Hashing:** Compares the target's avatar against the merchant's registered logo using pHash/dHash (`imagehash`).
2. **Handle Typosquatting:** Evaluates Jaro-Winkler string distance (`rapidfuzz`) to catch sneaky username shifts (e.g., `nairobi_shoes` vs `nairobl_shoes`).
3. **M-Pesa Till Verification:** Checks if the requested payment Till matches the merchant's official Safaricom records.
4. **Bio Keyword Analysis:** Flags suspicious Kenyan scam tokens ("Pay before delivery", "Delivery countrywide").
5. **Creation Date Discrepancy:** Flags brand new accounts pretending to be established 5-year-old brands.

---

## 🏗️ Architecture & Data Flow

```mermaid
graph TD
    A[Mock Target Profiles / OpenGraph Scraper] -->|Raw Metadata| B(FastAPI Ingestion Engine)
    B -->|Extract Image/Text| C{AI Scoring Matrix}
    
    C -->|pHash Matching| D[Logo Similarity]
    C -->|Jaro-Winkler| E[Username Typosquatting]
    C -->|Regex Matching| F[M-Pesa Verification]
    
    D --> G(Composite Risk Score 0-100)
    E --> G
    F --> G
    
    G -->|Score > 80| H[High Threat Alert]
    
    H -->|Push Notification| I[Telegram Alert Bot]
    H -->|Generative AI| J[Automated Remediation Playbooks]
    
    J --> K(Safaricom Fraud Report)
    J --> L(Meta Takedown Notice)
    J --> M(Consumer Social Warning)
```

---

## 🚀 Key Features
* 🔍 **Public Link Checker:** Consumers can paste an Instagram/Facebook link and instantly get a Trust/Danger badge before sending any money.
* 📊 **Merchant Dashboard:** A centralized radar for brands to track who is impersonating them in real-time.
* 📝 **AI Playbook Generation:** Automatically drafts official Meta Copyright Takedown notices and Safaricom Fraud Escalation reports, ready to send with one click.
* 🔔 **Instant Alerts:** Pushes critical threat alerts directly to the merchant's Telegram or via Africa's Talking SMS.

---

## 💻 Tech Stack Highlights
- **Frontend:** Next.js 14, Tailwind CSS, shadcn/ui, Recharts
- **Backend Core:** FastAPI, Pydantic, Celery (Async Tasks)
- **AI Engine:** CLIP ViT-B-32 (Nvidia Brev GPUs), RapidFuzz, ImageHash
- **Database:** Supabase PostgreSQL
- **Integrations:** Telegram Bot API, Africa's Talking Sandbox, Playwright

---

## 🛠️ Quick Start (Developer Setup)

1. **Clone the Repository**
   ```bash
   git clone https://github.com/chiromo-tech-club/halisi.git
   cd halisi
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Start the FastAPI Server**
   ```bash
   uvicorn app.main:app --reload
   ```

4. **Frontend Setup** *(Coming Soon)*
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

---

## 👥 The Team
Built with ❤️ by the **Chiromo Tech Club (University of Nairobi)** for the Hackathon:
* **Collins Kimanzi** - Lead Architect, AI Pipeline & UI/UX
* **Geoffrey** - Ingestion Pipelines & External Integrations
* **Ndegwa** - Frontend Application & Design System
* **Dennis** - Full-Stack QA & Cross-module Integration

<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=rect&color=27ae60&height=40&text=Securing%20Kenya's%20Digital%20Economy&fontColor=ffffff&fontSize=20&fontAlignY=65" />
</p>
