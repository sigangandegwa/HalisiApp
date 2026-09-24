# Halisi: Tech Stack Specification (tech-stack.md)

**Project**: Halisi \- AI-Powered Brand Impersonation Detection for Kenyan Businesses  
**Team**: Chiromo Tech Club, University of Nairobi  
**Target Environment**: Hackathon MVP & Production Free-Tier Bootstrap  
---

## 1\. Architecture Philosophy & Design Principles

* **Zero-Cost Infrastructure**: Every layer utilizes open-source libraries or high-allowance free developer tiers (Vercel, Supabase, Render, Hugging Face, Telegram).  
* **Sub-Second Forensic Checks**: Customer-facing link checks must resolve within 1,200ms using local perceptual hashing and vector indexing.  
* **Kenyan Financial Context First**: Prioritizes local threat signals, specifically Safaricom M-Pesa Till/Paybill mismatch detection and Kenyan social commerce operational habits.  
* **Fail-Safe Operation**: Avoids fragile live scrapers during live demos by heavily utilizing the mock dataset simulator and robust fallback OpenGraph parsers.

---

## 2\. Frontend Layer (Merchant Control Center & Public Checker)

* **Framework**: Next.js 14 (React 18, App Router, Server Components)  
* **Language**: TypeScript (Strict typing for threat and signal contracts)  
* **Styling**: Tailwind CSS with custom glassmorphism and bento-grid layouts  
* **Component UI**: shadcn/ui (Accessible Radix UI primitives)  
* **Icons & Visuals**: Lucide React \+ Recharts (for risk distribution charts and telemetry)  
* **Data Fetching**: TanStack Query v5 (React Query) for optimistic updates and polling  
* **Hosting & Edge Routing**: Vercel Hobby Tier (Global CDN, Serverless Functions, 100% Free)

---

## 3\. Backend API & Ingestion Engine

* **Core Framework**: Python FastAPI 0.111+ (Asynchronous, high-performance, OpenAPI compliant)  
* **Language**: Python 3.11+  
* **Task Runner**: FastAPI BackgroundTasks (MVP) / Celery with Redis (Production worker scaling)  
* **Networking Client**: HTTPX (Asynchronous HTTP requests with connection pooling)  
* **Data Validation**: Pydantic v2 (Strict schema validation for inputs, risk vectors, and alerts)  
* **Hosting**: Render.com Free Web Service or Railway Free Tier

---

## 4\. AI, Machine Learning & Similarity Pipeline

* **Visual Duplicate Detection**:  
  * **imagehash** 4.3+: Computes 64-bit Perceptual Hash (pHash), Difference Hash (dHash), and Average Hash (aHash). Sub-2ms execution on commodity CPU.  
  * **Pillow (PIL)**: Image resizing, normalization, and grayscale pre-processing.  
* **Multimodal Visual & Semantic Embeddings**:  
  * **sentence-transformers**: Running clip-ViT-B-32 (OpenAI CLIP weights via Hugging Face). Produces 512-dimensional normalized vectors to capture cropped, recolored, or edited logos.  
* **Text & Lexical Analysis**:  
  * **rapidfuzz** 3.8+: C++ accelerated string matching. Computes Jaro-Winkler distance, Levenshtein distance, and Token Sort Ratio for handle and name typosquting detection.  
  * **sentence-transformers** running all-MiniLM-L6-v2: Semantic embeddings for bio descriptions and post captions.  
* **Remediation & Advisory Engine**: Open-source lightweight LLM or Gemini API (Free tier) with structured prompts to generate customized takedown notices, customer broadcast copies, and Safaricom fraud escalations.

---

## 5\. Database, Vectors & Storage Layer

* **Relational Storage**: PostgreSQL on Supabase (Free tier includes 500 MB database, built-in Auth, Row-Level Security, and automated backups).  
* **Vector Search Engine**:  
  * *Local / Hackathon Stage*: ChromaDB (In-memory / SQLite file, embedded in Python, zero configuration).  
  * *Distributed Cloud Stage*: Qdrant Cloud (Free 1GB cluster tier) or Supabase pgvector.  
* **Media Asset Storage**: Supabase Storage (Free tier includes 1 GB storage with public image CDN for reference logos and flagged screenshots).

---

## 6\. External APIs, Registries & Ingestion Feeds

* **Public Page Metadata Scraper**: Playwright Python / BeautifulSoup4 for OpenGraph tag extraction on public profiles.  
* **Domain WHOIS**: python-whois for .ke domain age and nameserver verification via Kenic.  
* **M-Pesa Verification Sandbox**: Safaricom Daraja API C2B/B2C validation endpoints for account name reconciliation.

---

## 7\. Multi-Channel Alert & Remediation Infrastructure

* **Telegram Bot API**: Instant real-time alerts with screenshot previews, risk score badges, and action buttons (python-telegram-bot). 100% Free.  
* **SMS Notifications**: Africa's Talking SMS API (Free sandbox credits for Kenyan phone number testing).  
* **Email Dispatch**: Resend API (Free tier: 3,000 emails/month) for official takedown dossiers and merchant onboarding summaries.  
* **Document Export**: Jinja2 \+ WeasyPrint / ReportLab for compiling formal forensic PDF evidence reports for KE-CERT and Meta Brand Rights Enforcement.

