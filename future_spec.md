# Halisi: Future Specification (v1.0.0+)

This document outlines the planned but currently unscoped features, integrations, and architectural improvements for Halisi once the MVP (v0.2.0) proves successful. These items were originally considered for the hackathon but moved to `[P2]` or dropped to ensure a streamlined core experience.

---

## 1. Multi-Channel Alerting & Reach

### 1.1 Africa's Talking Integrations (TSK-013, TSK-036)
- **SMS Alerts**: Merchants receive critical impersonation alerts instantly via SMS, bypassing the need to have the dashboard open or rely purely on web-push notifications.
- **USSD Checker (*Stretch*)**: A feature-phone accessible USSD menu (e.g., `*123#`) allowing standard consumers to input a till or phone number and receive a Halisi verification status in text format. This vastly expands reach beyond the web interface.

### 1.2 Telegram Bot for Consumers (TSK-030)
- Allow consumers to forward Instagram/TikTok profiles or links directly to a Halisi Telegram Bot.
- The bot parses the URL, runs the Halisi checker, and responds instantly with the Forensic Verdict. 

---

## 2. Advanced Remediation & Takedowns

### 2.1 Automated Takedown Integrations
- Move from "human-in-the-loop" LLM email/form drafting to direct API integrations.
- **Meta Rights Manager API**: Automatically submit takedown requests for verified clones exceeding a strict 95+ score.
- **Safaricom Daraja / Fraud APIs**: Directly flag malicious tills/paybills identified in the clone network.

### 2.2 Takedown Tracker (TSK-029)
- Implement an `APScheduler` loop that periodically re-checks previously identified threat URLs.
- Track "Time to Takedown" metrics on the merchant dashboard (e.g., "Threat neutralized after 14 hours").
- Escalate alerts if a blatant threat remains online for more than 48 hours.

### 2.3 Evidence Dossier PDF (TSK-028)
- Generate a legally binding, cleanly formatted PDF report of a threat.
- Includes a SHA-256 hash of the evidence bundle (screenshots, scraped text, timestamp) for chain-of-custody verification.
- Ideal for merchants pursuing legal action or escalating to KE-CIRT/CC.

---

## 3. Deep Ingestion & Validation

### 3.1 Live M-Pesa API Validation
- Currently, payment signals are extracted from page text and checked against self-declared merchant records.
- **Future**: Connect to the Safaricom Daraja API to query the actual registered owner name for a given till/paybill, providing 100% authoritative mismatch detection.

### 3.2 Advanced Scraping
- Upgrade the tier-2 OpenGraph scraper to a full headless browser cluster (e.g., Playwright) to bypass aggressive anti-bot protections on modern social media platforms.
- Capture full-page visual screenshots to pass into the CLIP model, rather than relying solely on profile avatars.
