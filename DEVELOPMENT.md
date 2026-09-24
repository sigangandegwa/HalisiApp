# Halisi: Step-by-Step Development Guide (DEVELOPMENT.md)

**Project**: Halisi \- AI-Powered Brand Impersonation Detection for Kenyan Businesses  
**Team**: Chiromo Tech Club, University of Nairobi  
**Target Delivery**: Hackathon Sprint & Open-Source MVP

---

## 1\. Project Overview & Repository Architecture

Halisi uses a unified monorepo structure separating the Python AI/Ingestion backend from the Next.js frontend.

halisi/  
├── backend/  
│   ├── app/  
│   │   ├── api/  
│   │   │   ├── v1/  
│   │   │   │   ├── endpoints/  
│   │   │   │   │   ├── check.py         \# Public link check endpoint  
│   │   │   │   │   ├── merchants.py     \# Merchant registration & management  
│   │   │   │   │   ├── threats.py       \# Threat feed & risk scores  
│   │   │   │   │   └── remediation.py   \# AI playbook triggers  
│   │   ├── core/  
│   │   │   ├── config.py                \# Environment variables & Pydantic settings  
│   │   │   ├── database.py              \# Supabase Postgres connection  
│   │   │   └── security.py              \# Auth & API key validation  
│   │   ├── engine/  
│   │   │   ├── hasher.py                \# pHash & dHash calculations  
│   │   │   ├── embeddings.py            \# CLIP ViT-B-32 & MiniLM vectorizer  
│   │   │   ├── matcher.py               \# RapidFuzz string & typosquatting analysis  
│   │   │   ├── scorer.py                \# Composite risk score calculation (0-100)  
│   │   │   └── remediation.py           \# AI prompt pipelines for takedowns & alerts  
│   │   ├── ingestion/  
│   │   │   ├── page\_scraper.py          \# Playwright / HTTPX OpenGraph extractor  
│   │   │   └── mock\_seeder.py           \# Demo dataset loader  
│   │   ├── alerts/  
│   │   │   ├── telegram\_bot.py          \# Telegram alert dispatcher  
│   │   │   └── africas\_talking.py       \# Kenyan SMS notification gateway  
│   │   ├── schemas/                     \# Pydantic request/response models  
│   │   └── main.py                      \# FastAPI entry point  
│   ├── tests/  
│   ├── Dockerfile  
│   ├── pyproject.toml / requirements.txt  
│   └── .env.example  
├── frontend/  
│   ├── src/  
│   │   ├── app/  
│   │   │   ├── page.tsx                 \# Landing page & Public Link Checker  
│   │   │   ├── dashboard/               \# Merchant protection control center  
│   │   │   │   ├── page.tsx             \# Live threat feed & metrics  
│   │   │   │   ├── threats/\[id\]/page.tsx\# Threat breakdown & AI playbooks  
│   │   │   │   └── register/page.tsx    \# Merchant onboarding flow  
│   │   │   └── layout.tsx  
│   │   ├── components/  
│   │   │   ├── threat-badge.tsx         \# Color-coded risk badge (Low/Med/High)  
│   │   │   ├── radar-chart.tsx          \# Multi-dimensional score visualizer  
│   │   │   ├── playbook-card.tsx        \# One-click remediation action cards  
│   │   │   └── ui/                      \# shadcn/ui primitive components  
│   │   └── lib/  
│   │       ├── api.ts                   \# Axios / fetch wrapper  
│   │       └── utils.ts  
│   ├── package.json  
│   ├── tailwind.config.ts  
│   └── .env.local.example  
└── README.md  
---

## 2\. Phase 1: Environment Setup & Prerequisites

### 2.1 Tooling & Software Requirements

- **Python**: Version 3.11 or higher  
- **Node.js**: Version 18.x or 20.x LTS \+ `pnpm` or `npm`  
- **Git**: For version control  
- **Docker** (Optional, for local ChromaDB or PostgreSQL containerization)

### 2.2 Account & API Key Acquisition (100% Free Tiers)

1. **Supabase**: Create a free project at [supabase.com](https://supabase.com). Copy the PostgreSQL Connection URI, API URL, and Service Role Key.  
2. **Telegram Bot**: Start a chat with `@BotFather` on Telegram, run `/newbot`, name it `HalisiAlertBot`, and save the API token.  
3. **Africa's Talking Sandbox**: Sign up at [africastalking.com](https://africastalking.com), activate Sandbox mode, and obtain your Sandbox API Key and Username (`sandbox`).  
4. **Google AI Studio / Gemini API**: Obtain a free API key at [aistudio.google.com](https://aistudio.google.com) for the AI remediation text generation prompts.

---

## 3\. Phase 2: Database Schema Implementation (Supabase PostgreSQL)

Execute the following DDL script inside the Supabase SQL Editor:

\-- Enable UUID and Vector extensions  
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";  
CREATE EXTENSION IF NOT EXISTS "vector";

\-- 1\. Verified Merchants Table  
CREATE TABLE merchants (  
    id UUID PRIMARY KEY DEFAULT uuid\_generate\_v4(),  
    business\_name VARCHAR(255) NOT NULL,  
    official\_handle VARCHAR(100) NOT NULL UNIQUE,  
    official\_platform VARCHAR(50) DEFAULT 'instagram',  
    official\_url TEXT NOT NULL,  
    phone\_number VARCHAR(50) NOT NULL,  
    mpesa\_type VARCHAR(20) CHECK (mpesa\_type IN ('till', 'paybill', 'none')),  
    mpesa\_identifier VARCHAR(50),  
    logo\_phash VARCHAR(64) NOT NULL,  
    logo\_url TEXT NOT NULL,  
    created\_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()  
);

\-- 2\. Scanned Target Pages / Threat Table  
CREATE TABLE threats (  
    id UUID PRIMARY KEY DEFAULT uuid\_generate\_v4(),  
    merchant\_id UUID REFERENCES merchants(id) ON DELETE CASCADE,  
    target\_handle VARCHAR(100) NOT NULL,  
    target\_platform VARCHAR(50) NOT NULL,  
    target\_url TEXT NOT NULL,  
    target\_avatar\_url TEXT,  
    target\_avatar\_phash VARCHAR(64),  
    target\_creation\_date DATE,  
    extracted\_phone VARCHAR(50),  
    extracted\_payment\_info TEXT,  
      
    \-- Sub-scores (0 to 100\)  
    visual\_score NUMERIC(5,2) DEFAULT 0,  
    lexical\_score NUMERIC(5,2) DEFAULT 0,  
    temporal\_score NUMERIC(5,2) DEFAULT 0,  
    payment\_score NUMERIC(5,2) DEFAULT 0,  
    engagement\_score NUMERIC(5,2) DEFAULT 0,  
    composite\_score NUMERIC(5,2) NOT NULL,  
      
    status VARCHAR(50) DEFAULT 'detected' CHECK (status IN ('detected', 'advisory\_sent', 'takedown\_filed', 'resolved', 'false\_positive')),  
    created\_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()  
);

\-- 3\. Remediation Actions Log  
CREATE TABLE remediation\_logs (  
    id UUID PRIMARY KEY DEFAULT uuid\_generate\_v4(),  
    threat\_id UUID REFERENCES threats(id) ON DELETE CASCADE,  
    playbook\_type VARCHAR(50) NOT NULL,  
    generated\_content TEXT NOT NULL,  
    dispatched\_to VARCHAR(100),  
    dispatched\_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()  
);

\-- Indexes for rapid lookup  
CREATE INDEX idx\_merchants\_handle ON merchants(official\_handle);  
CREATE INDEX idx\_threats\_score ON threats(composite\_score DESC);  
---

## 4\. Phase 3: AI Similarity Engine Implementation

### 4.1 Visual Hashing (`backend/app/engine/hasher.py`)

import imagehash  
from PIL import Image  
import io

def calculate\_phash(image\_bytes: bytes) \-\> str:  
    image \= Image.open(io.BytesIO(image\_bytes)).convert("RGB")  
    hash\_val \= imagehash.phash(image, hash\_size=8)  
    return str(hash\_val)

def compare\_phashes(hash\_str1: str, hash\_str2: str) \-\> float:  
    h1 \= imagehash.hex\_to\_hash(hash\_str1)  
    h2 \= imagehash.hex\_to\_hash(hash\_str2)  
    hamming\_dist \= h1 \- h2  \# 0 to 64  
    \# Distance \<= 5 is near identical, \> 15 is distinct  
    similarity \= max(0.0, 1.0 \- (hamming\_dist / 20.0)) \* 100.0  
    return round(similarity, 2\)

### 4.2 Multimodal Embedding Engine (`backend/app/engine/embeddings.py`)

from sentence\_transformers import SentenceTransformer  
from PIL import Image  
import io

\# clip-ViT-B-32 handles both text and images in the same vector space  
clip\_model \= SentenceTransformer("clip-ViT-B-32")

def get\_image\_embedding(image\_bytes: bytes):  
    image \= Image.open(io.BytesIO(image\_bytes)).convert("RGB")  
    embedding \= clip\_model.encode(image, normalize\_embeddings=True)  
    return embedding.tolist()

def get\_text\_embedding(text: str):  
    embedding \= clip\_model.encode(text, normalize\_embeddings=True)  
    return embedding.tolist()

### 4.3 Lexical & Typosquatting Matcher (`backend/app/engine/matcher.py`)

from rapidfuzz import distance

def calculate\_name\_similarity(official\_name: str, target\_name: str) \-\> float:  
    \# Jaro-Winkler gives higher weight to prefix matches  
    jw\_score \= distance.JaroWinkler.similarity(official\_name.lower(), target\_name.lower()) \* 100.0  
      
    \# Check for known scam suffixes common in Kenya  
    suspicious\_suffixes \= \["official", "ke", "kenya", "deals", "store", "online", "offers"\]  
    target\_tokens \= target\_name.lower().replace("\_", " ").replace(".", " ").split()  
      
    if any(suffix in target\_tokens for suffix in suspicious\_suffixes):  
        jw\_score \= min(100.0, jw\_score \+ 15.0)  
          
    return round(jw\_score, 2\)

### 4.4 Composite Risk Scoring (`backend/app/engine/scorer.py`)

from datetime import date

def calculate\_composite\_risk(  
    visual\_score: float,  
    lexical\_score: float,  
    account\_created\_date: date,  
    merchant\_created\_date: date,  
    has\_payment\_mismatch: bool,  
    engagement\_anomaly: bool \= False  
) \-\> dict:  
    \# Temporal Score  
    account\_age\_days \= (date.today() \- account\_created\_date).days  
    if account\_age\_days \< 7:  
        temporal\_score \= 95.0  
    elif account\_age\_days \< 30:  
        temporal\_score \= 80.0  
    elif account\_age\_days \< 90:  
        temporal\_score \= 50.0  
    else:  
        temporal\_score \= 15.0

    \# Payment Score  
    payment\_score \= 90.0 if has\_payment\_mismatch else 10.0  
      
    \# Engagement Score  
    engagement\_score \= 75.0 if engagement\_anomaly else 20.0

    \# Weighted Formula  
    composite \= (  
        (visual\_score \* 0.25) \+  
        (lexical\_score \* 0.20) \+  
        (temporal\_score \* 0.25) \+  
        (payment\_score \* 0.20) \+  
        (engagement\_score \* 0.10)  
    )

    return {  
        "visual\_score": round(visual\_score, 2),  
        "lexical\_score": round(lexical\_score, 2),  
        "temporal\_score": round(temporal\_score, 2),  
        "payment\_score": round(payment\_score, 2),  
        "engagement\_score": round(engagement\_score, 2),  
        "composite\_score": round(composite, 2),  
        "is\_threat": composite \>= 75.0  
    }  
---

## 5\. Phase 4: AI Remediation Engine Implementation (`backend/app/engine/remediation.py`)

When a threat is flagged ($Score \\ge 75$), Halisi activates dynamic remediation generation using structured LLM prompting:

def generate\_remediation\_playbooks(merchant\_name: str, real\_handle: str, real\_till: str,  
                                   fake\_handle: str, fake\_phone: str, evidence\_summary: str) \-\> dict:  
      
    \# Playbook 1: Social Media Warning Copy  
    social\_warning\_copy \= (  
        f"🚨 FRAUD ALERT / ILANI YA UTAPELI 🚨\\n\\n"  
        f"A clone page impersonating {merchant\_name} has been detected: @{fake\_handle}.\\n"  
        f"They are illegally using our logo and product photos to solicit deposits.\\n\\n"  
        f"⚠️ DO NOT send money to {fake\_phone}.\\n"  
        f"✅ OUR ONLY OFFICIAL PAGE: @{real\_handle}\\n"  
        f"✅ OUR ONLY OFFICIAL PAYMENT CHANNEL: Buy Goods Till {real\_till}\\n\\n"  
        f"Please help us report @{fake\_handle} to Instagram/Facebook."  
    )

    \# Playbook 2: Meta Brand Rights Takedown Notice  
    meta\_takedown\_notice \= (  
        f"FORMAL NOTICE OF BRAND IMPERSONATION & TRADEMARK INFRINGEMENT\\n"  
        f"To: Meta Brand Rights Protection / Instagram Trust & Safety\\n\\n"  
        f"Complainant: {merchant\_name} (Official Account: @{real\_handle})\\n"  
        f"Infringing URL: https://instagram.com/{fake\_handle}\\n\\n"  
        f"Detailed Grounds for Removal:\\n"  
        f"1. Identity Theft: Target account cloned our official avatar (pHash similarity: 96%).\\n"  
        f"2. Fraudulent Activity: Target account was created recently and solicits deposits under false pretenses.\\n"  
        f"3. Forensic Evidence: {evidence\_summary}\\n\\n"  
        f"We request immediate suspension under Meta Community Guidelines on Inauthentic Behavior."  
    )

    \# Playbook 3: Safaricom Fraud Escalation Template  
    safaricom\_fraud\_report \= (  
        f"ATTN: Safaricom Fraud Investigation Desk (fraud@safaricom.co.ke)\\n"  
        f"SUBJECT: Fraudulent Mobile Money Solicitation Impersonating {merchant\_name}\\n\\n"  
        f"Dear Safaricom Fraud Team,\\n"  
        f"We are reporting an active scam using mobile line {fake\_phone} to collect fraudulent payments "  
        f"by impersonating registered merchant {merchant\_name} (Official Till: {real\_till}).\\n"  
        f"Victims are directed from the imposter Instagram page @{fake\_handle}.\\n"  
        f"We request an urgent audit and precautionary hold on mobile money transactions for {fake\_phone}."  
    )

    return {  
        "social\_broadcast": social\_warning\_copy,  
        "platform\_takedown": meta\_takedown\_notice,  
        "financial\_escalation": safaricom\_fraud\_report  
    }  
---

## 6\. Phase 5: Multi-Channel Alert Dispatch

### 6.1 Telegram Dispatcher (`backend/app/alerts/telegram_bot.py`)

import httpx  
from app.core.config import settings

async def dispatch\_telegram\_alert(merchant\_chat\_id: str, threat\_data: dict):  
    message \= (  
        f"🚨 \*HALISI THREAT DETECTED\* 🚨\\n\\n"  
        f"\*Target Handle\*: \`@{threat\_data\['target\_handle'\]}\`\\n"  
        f"\*Composite Risk\*: \`{threat\_data\['composite\_score'\]}/100\` (CRITICAL)\\n"  
        f"\*Visual Similarity\*: \`{threat\_data\['visual\_score'\]}%\`\\n"  
        f"\*Account Age\*: \`{threat\_data\['account\_age\_days'\]} days\`\\n"  
        f"\*Payment Mismatch\*: \`Send-Money to {threat\_data\['extracted\_phone'\]}\`\\n\\n"  
        f"⚡ \*AI Remediation Ready\*: View pre-drafted takedown and customer warning in your dashboard."  
    )  
    url \= f"https://api.telegram.org/bot{settings.TELEGRAM\_BOT\_TOKEN}/sendMessage"  
    payload \= {  
        "chat\_id": merchant\_chat\_id,  
        "text": message,  
        "parse\_mode": "Markdown"  
    }  
    async with httpx.AsyncClient() as client:  
        await client.post(url, json=payload)

### 6.2 Africa's Talking SMS Gateway (`backend/app/alerts/africas_talking.py`)

import africastalking  
from app.core.config import settings

def initialize\_sms():  
    africastalking.initialize(username=settings.AT\_USERNAME, api\_key=settings.AT\_API\_KEY)  
    return africastalking.SMS

def send\_sms\_alert(phone\_number: str, fake\_handle: str):  
    sms \= initialize\_sms()  
    recipients \= \[phone\_number\]  
    message \= (  
        f"HALISI ALERT: An impersonator page (@{fake\_handle}) has been detected using your logo. "  
        f"Log in to your Halisi dashboard to broadcast a warning to your customers."  
    )  
    sms.send(message, recipients)  
---

## 7\. Phase 6: Frontend Interface (Next.js 14 \+ Tailwind)

### 7.1 Key Pages to Implement

1. **Public Verification Hub (`/`)**:  
   - Hero section with search input: *"Paste any Facebook or Instagram page link before sending M-Pesa"*.  
   - Instant response card showing verification badge (Green: Official Merchant, Yellow: Unverified/Unknown, Red: Impersonator Detected).  
2. **Merchant Control Dashboard (`/dashboard`)**:  
   - Active protected profiles overview.  
   - Live threat radar table showing flagged pages, risk score breakdown, and detection timestamp.  
3. **Threat Detail & Remediation Hub (`/dashboard/threats/[id]`)**:  
   - Side-by-side logo comparison visualizer with pHash distance readout.  
   - Three tabbed AI remediation playbooks (Consumer Advisory, Meta Takedown, Safaricom Fraud Report) with a one-click *"Copy Copy"* button and *"Export PDF Dossier"* button.

---

## 8\. Phase 7: Demo Data Seeder & Presentation Script

To guarantee a reliable live hackathon demo without network or scraping failures, build a dedicated mock seeder (`backend/app/ingestion/mock_seeder.py`):

MOCK\_MERCHANT \= {  
    "business\_name": "Nairobi Sneaker Vault",  
    "official\_handle": "nairobisneakervault",  
    "official\_url": "https://instagram.com/nairobisneakervault",  
    "phone\_number": "+254712345678",  
    "mpesa\_type": "till",  
    "mpesa\_identifier": "543210",  
    "logo\_url": "https://storage.halisi.app/logos/real\_nsv.png"  
}

MOCK\_CLONE\_PAGE \= {  
    "target\_handle": "nairobi\_sneakervault\_official\_ke",  
    "target\_url": "https://instagram.com/nairobi\_sneakervault\_official\_ke",  
    "target\_avatar\_url": "https://storage.halisi.app/logos/clone\_nsv.png",  
    "target\_creation\_date": "2026-09-19",  \# 4 days old  
    "extracted\_phone": "0798-999-111",      \# Personal M-Pesa Send Money  
    "visual\_score": 97.5,  
    "lexical\_score": 91.2,  
    "temporal\_score": 95.0,  
    "payment\_score": 90.0,  
    "composite\_score": 93.6  
}

### Presentation Script (3 Minutes for Judges)

1. **Minute 1: The Problem (Hook)**:  
   - *"In Kenya, over 70% of social commerce transactions run through Instagram and Facebook pages, followed by M-Pesa. Scammers clone trusted shop pages in 5 minutes, collect deposits via personal phone numbers, and vanish. The customer loses money; the merchant loses their reputation."*  
2. **Minute 2: The Live Demonstration**:  
   - Show the authentic business profile in the Halisi dashboard (`Nairobi Sneaker Vault`).  
   - Trigger the public link check with a live clone page (`@nairobi_sneakervault_official_ke`).  
   - Show Halisi breaking down the 5 dimensions in real time (97% logo match, 4 days old, unverified personal phone number).  
   - Display the resulting risk score (94/100).  
3. **Minute 3: The AI Remediation Engine**:  
   - Showcase the 3 generated playbooks: The Instagram Story advisory ready to copy, the official Meta IP takedown filing, and the Safaricom fraud report.  
   - Emphasize that Halisi doesn't just sound an alarm; it arms the Kenyan business owner with instant, automated legal and operational countermeasures.

---

## 9\. Hackathon Sprint Checklist

- [ ] Day 1, Morning: Clone repo, configure Supabase schema, test database connectivity.  
- [ ] Day 1, Afternoon: Implement `hasher.py`, `embeddings.py`, and `matcher.py`. Verify pHash distance on sample images.  
- [ ] Day 1, Evening: Wire up FastAPI endpoints (`/api/v1/check` and `/api/v1/merchants`).  
- [ ] Day 2, Morning: Build Next.js Public Checker UI and integrate with backend API.  
- [ ] Day 2, Afternoon: Build AI Remediation Playbook generator and Telegram Bot alert dispatcher.  
- [ ] Day 2, Evening: Load mock seeder dataset, rehearse live demo transitions, and verify responsive mobile views.