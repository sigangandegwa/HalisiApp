# Halisi: End-to-End Data Flow & AI Remediation Engine (data-flow.md)

**Project**: Halisi \- AI-Powered Brand Impersonation Detection for Kenyan Businesses  
**Team**: Chiromo Tech Club, University of Nairobi

---

## 1\. System Architecture & Data Flow Overview

                                 \[ AUTHENTIC MERCHANT \]  
                                            |  
                                            | (1) Onboarding: Handle, Logo,  
                                            |     Catalog, M-Pesa Till, Phone  
                                            v  
                             \+-------------------------------+  
                             |    Halisi Merchant Ingestion  |  
                             |  \- Hash Logos (pHash/dHash)   |  
                             |  \- Embed Catalog (CLIP ViT)   |  
                             |  \- Store Baseline in Postgres |  
                             \+---------------+---------------+  
                                             |  
       \+-------------------------------------+-------------------------------------+  
       |                                                                           |  
       v (Periodic Scan)                                                           v (On-Demand Check)  
\+-------------------------------+                                   \+-------------------------------+  
|    OpenGraph Web Scraper      |                                   |    Public Link Checker UI     |  
| \- Queries Public Metadata     |                                   | \- Customer pastes target URL  |  
| \- Filters by Brand Keywords   |                                   | \- On-the-fly Page Scraper     |  
\+---------------+---------------+                                   \+---------------+---------------+  
                |                                                                   |  
                \+---------------------------------+---------------------------------+  
                                                  |  
                                                  v  
                                  \+-------------------------------+  
                                  |    Target Feature Extraction  |  
                                  | \- Avatar pHash & CLIP Vector  |  
                                  | \- Handle & Name Levenshtein   |  
                                  | \- Page Creation & Name History|  
                                  | \- Extracted Phone / M-Pesa    |  
                                  \+---------------+---------------+  
                                                  |  
                                                  v  
                                  \+-------------------------------+  
                                  |   AI Similarity & Scoring     |  
                                  | \- Visual Match (Weight: 25%)  |  
                                  | \- Name Match   (Weight: 20%)  |  
                                  | \- Page History (Weight: 25%)  |  
                                  | \- Payment Risk (Weight: 20%)  |  
                                  | \- Engagement   (Weight: 10%)  |  
                                  \+---------------+---------------+  
                                                  |  
                         \+------------------------+------------------------+  
                         |                                                 |  
                         v (Risk Score \< 75\)                               v (Risk Score \>= 75: Threat Detected)  
          \+-------------------------------+                 \+-------------------------------+  
          |       Verdict: Low Risk       |                 |  AI Remediation Recommender   |  
          | \- Display verification proof  |                 | \- Contextual Threat Analysis  |  
          | \- Cache result in Redis/PG    |                 | \- Multi-Stage Playbook Engine |  
          \+-------------------------------+                 \+---------------+---------------+  
                                                                            |  
                                            \+-------------------------------+-------------------------------+  
                                            |                               |                               |  
                                            v                               v                               v  
                             \[ Playbook 1: Consumer Defense \] \[ Playbook 2: Platform Takedown \] \[ Playbook 3: Financial Action \]  
                             \- Tailored Social Broadcasts      \- Meta/TikTok Infringement Report \- Safaricom M-Pesa Escalation  
                             \- WhatsApp Status Warnings        \- Cryptographic Evidence PDF      \- Police/KE-CERT Incident Log  
---

## 2\. Detailed Lifecycle Stages

### Stage 1: Ground Truth Ingestion (Merchant Onboarding)

1. **Business Profile Creation**: The authentic merchant submits their operational credentials:  
   - Official brand name, aliases, and official social handles (`@store_ke`).  
   - Official customer care phone numbers and physical store location (e.g., Nairobi CBD).  
   - Official M-Pesa Buy Goods Till or Paybill number.  
2. **Asset Normalization & Indexing**:  
   - The logo is normalized to 512x512 grayscale and RGB.  
   - Computes 64-bit `pHash` and `dHash` stored in PostgreSQL `merchants` table.  
   - Computes a 512-dimensional CLIP embedding using `clip-ViT-B-32` and stores it in ChromaDB with metadata tags.  
   - Catalog photos are embedded and added to the merchant's vector namespace.

### Stage 2: Target Discovery & Ingestion Channels

- **Channel A: Background Polling (OpenGraph & Mock Dataset)**:  
  - Every 6 hours, Celery/FastAPI queries mock target lists or uses Playwright to scrape public OpenGraph metadata for suspected scam URLs.  
  - Extracts public profile names, creation dates (if available), ad copy snippets, and media URLs.  
- **Channel B: Public Link Checker (Customer Triggered)**:  
  - Customers paste a link (e.g., `https://instagram.com/nairobi_shoes_official_ke`) into the Halisi web or WhatsApp checker.  
  - An asynchronous Playwright/HTTPX scraper fetches the page's OpenGraph metadata, profile avatar, account bio, and recent posts.

### Stage 3: Multi-Dimensional Threat Scoring Engine

The target metadata passes through the evaluation matrix:

1. **Visual Score ($S\_{visual}$)**: Computes hamming distance of pHash ($\<10 \= 100%$ match) and cosine similarity of CLIP embeddings ($\>0.88 \= 95%$ match).  
2. **Lexical Score ($S\_{lexical}$)**: Computes Jaro-Winkler and Levenshtein token similarity between brand names and handles.  
3. **Temporal Score ($S\_{temporal}$)**: Evaluates account age. Accounts $\<30$ days old receive maximum penalty when mimicking established brands.  
4. **Payment Signal Score ($S\_{payment}$)**: Scans bio and captions for phone numbers. If an unverified personal phone number is found instead of the registered Till/Paybill, flags high fraud probability.  
5. **Composite Score Formulation**: $$S\_{risk} \= 0.25 \\cdot S\_{visual} \+ 0.20 \\cdot S\_{lexical} \+ 0.25 \\cdot S\_{temporal} \+ 0.20 \\cdot S\_{payment} \+ 0.10 \\cdot S\_{engagement}$$

---

## 3\. AI-Recommended Remediation Engine

When $S\_{risk} \\ge 75$, Halisi activates the AI Remediation Engine. Scammers act fast; businesses need immediate, customized remediation workflows rather than generic alerts.

The AI analyzes the extracted evidence and dynamically generates three customized remediation playbooks:

\+-----------------------------------------------------------------------------------+  
|                        AI REMEDIATION PLAYBOOK MATRIX                             |  
\+---------------------+-------------------------------+-----------------------------+  
| Playbook            | Target Channel / Stakeholder  | AI Generated Deliverable    |  
\+---------------------+-------------------------------+-----------------------------+  
| 1\. Consumer Defense | Customers, Followers, Public  | Pre-written warning posts,  |  
|                     |                               | WhatsApp status graphics,   |  
|                     |                               | M-Pesa safety reminders.    |  
\+---------------------+-------------------------------+-----------------------------+  
| 2\. Platform Take-   | Meta, TikTok, X, Web Hosts    | Formal infringement notice, |  
|    down Notice      |                               | pHash visual comparison,    |  
|                     |                               | timestamp evidence dossier. |  
\+---------------------+-------------------------------+-----------------------------+  
| 3\. Financial & Legal| Safaricom Fraud Desk,         | M-Pesa account freeze form, |  
|    Escalation       | KE-CERT, DCI Cybercrime       | NC4 incident log filing.    |  
\+---------------------+-------------------------------+-----------------------------+

### Playbook 1: Immediate Consumer Defense Broadcasts

The AI auto-generates platform-ready copy matching the merchant's brand voice to warn customers before money is sent:

- **Instagram/Facebook Story Copy**:  
  > *"ALERT: A scam page impersonating us has been detected under the handle `[Target_Handle]`. They are using our logo and pictures to collect payments. Our ONLY official page is `[Real_Handle]`. We ONLY accept payments via Buy Goods Till `[Real_Till]`. Do NOT send money to `[Scammer_Phone]`. Please report their page."*  
- **Direct WhatsApp Blast Copy**: Formatted for the merchant's VIP customer broadcast lists.

### Playbook 2: Automated Platform Takedown Dossier

The AI drafts an exact, platform-compliant IP and Trademark Impersonation report:

- **Target Platform Formatter**:  
  - Meta: Generates the exact payload for the Meta Brand Rights Protection Portal.  
  - TikTok / X: Generates the formal DMCA/Impersonation claim.  
- **Cryptographic & Visual Evidence Attached**:  
  - Side-by-side comparison of authentic logo vs. scammer avatar.  
  - Hash proof ($pHash\_{target}$ vs $pHash\_{source}$).  
  - Proof of prior use (Original account creation timestamp vs. scammer creation timestamp).

### Playbook 3: Kenyan Financial & Cybercrime Escalation

Because financial harm in Kenya materializes through mobile money, Halisi bridges brand impersonation to financial remediation:

- **Safaricom Fraud Escalation Dispatch**:  
  - Pre-populates an official report to `fraud@safaricom.co.ke` and the Safaricom 333 fraud channel requesting an audit and precautionary freeze on the destination mobile number or fraudulent agent line used by the scammer.  
- **National KE-CERT Incident Submission**:  
  - Compiles an incident report under the Computer Misuse and Cybercrimes Act, 2018 for submission to the National KE-CERT Coordination Centre (`incidents@ke-cert.go.ke`).

### Playbook 4: Automated Remediation Tracking Loop

1. Halisi registers the infringing URL in an active monitoring queue.  
2. The crawler re-checks the target page every 12 hours (HTTP 404, account suspended, or content removed).  
3. If the page is still active after 48 hours:  
   - The AI auto-generates a Second-Tier Legal Notice.  
   - Halisi prompts the merchant to trigger a Community Report Action where verified customers receive a one-click link to report the page simultaneously on Instagram/Facebook.  
4. Once takedown is confirmed:  
   - System logs time-to-takedown metrics.  
   - Sends resolution confirmation to the merchant dashboard.

