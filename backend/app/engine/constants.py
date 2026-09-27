"""Engine constants: image limits and visual-similarity calibration.

Every value here is a scoring heuristic. Changing one requires a new version row in
AGENTS.md section 7.2 (Prompt & Heuristic Registry).

The visual thresholds are starting values (HASH_SIMILARITY v2, CLIP_SIMILARITY v1). They are
calibrated against the seed logo variants in TSK-017 and the results recorded in docs/calibration.md.
Scorer weights and verdict thresholds are added here by TSK-008.
"""

from typing import Final

# --- Image normalisation (imaging.py) ---------------------------------------------------------
MAX_IMAGE_BYTES: Final = 5 * 1024 * 1024       # reject larger uploads / downloads
MAX_IMAGE_PIXELS: Final = 25_000_000            # decompression-bomb guard (width * height)
NORMALIZED_SIZE: Final = 256                    # square side after normalisation
PAD_COLOR: Final = (255, 255, 255)              # alpha flatten + letterbox colour

# --- Perceptual hashing (hasher.py): HASH_SIMILARITY v2 ---------------------------------------
HASH_SIZE: Final = 8                            # 8x8 -> 64-bit hashes, 16 hex chars
HASH_BITS: Final = HASH_SIZE * HASH_SIZE
HASH_FULL_MATCH_BITS: Final = 4                 # Hamming distance <= this -> similarity 100
HASH_NO_MATCH_BITS: Final = 24                  # Hamming distance >= this -> similarity 0
# Unrelated images average ~32 differing bits (each bit is roughly a coin flip), so v1's
# `100 - d/64*100` gave them ~50 %. The linear ramp between 4 and 24 puts them at 0.

# --- CLIP embeddings: CLIP_SIMILARITY v1 -------------------------------------------------------
CLIP_FULL_MATCH_COSINE: Final = 0.93            # cosine >= this -> similarity 100
CLIP_NO_MATCH_COSINE: Final = 0.80              # cosine <= this -> similarity 0

# --- Payment signal (payment.py): PAYMENT v2 ---------------------------------------------------
PAYMENT_RESEMBLANCE_MIN: Final = 60.0           # below this the page barely resembles the merchant
# visual <= LOGO_CONTRADICTS means a clearly different logo, so name-only resemblance
# must then reach STRONG_IDENTITY before unregistered numbers count as a hijack.
LOGO_CONTRADICTS: Final = 20.0
PAYMENT_OFFICIAL_ONLY: Final = 0.0              # only the merchant's registered numbers appear
PAYMENT_UNREGISTERED_PHONE: Final = 100.0       # personal line not registered to the resembled merchant
PAYMENT_UNREGISTERED_PHONE_LOW_RESEMBLANCE: Final = 60.0
PAYMENT_UNREGISTERED_TILL: Final = 50.0         # tills/paybills need a registered business: weaker
PAYMENT_UNREGISTERED_TILL_LOW_RESEMBLANCE: Final = 25.0

# --- Composite scorer (scorer.py): WEIGHTS v2, THRESHOLDS v2, OVERRIDES v2 -----------------------
WEIGHTS: Final = {"visual": 0.30, "identity": 0.25, "payment": 0.25, "language": 0.10, "account": 0.10}
THREAT_THRESHOLD: Final = 70.0                  # >= impersonation (overridable via settings)
SUSPICIOUS_THRESHOLD: Final = 40.0              # >= suspicious
RESEMBLANCE_GATE: Final = 50.0                  # G1: below this the page is not imitating the merchant
NO_MATCH_CAP: Final = 39.0                      # G1 cap
STRONG_VISUAL: Final = 80.0                     # O2 needs a copied logo (visual >= this) ...
STRONG_IDENTITY: Final = 90.0                   # ... or a near-identical handle (identity >= this)
PAYMENT_HIJACK_FLOOR: Final = 90.0              # O2 floor
REPORTED_FLOOR: Final = 85.0                    # O3 floor
MIN_CONFIDENCE_FOR_IMPERSONATION: Final = 0.5   # O4
REASON_MIN_SCORE: Final = 60.0                  # a dimension at/above this emits a plain-language reason
LANGUAGE_REASON_MIN: Final = 40.0               # one strong scam phrase ("lipa kwanza") is worth a reason
REASON_HIGH_SEVERITY: Final = 85.0

# --- Remediation channels (remediation.py, TSK-009) -------------------------------------------
# TODO(TSK-009, before the demo): verify every channel below from the organisation's own current
# website, fill in the value, and set VERIFIED_ON to that date. Until then the playbooks show these
# placeholders and `contacts_verified: false`, and the merchant must confirm the address before sending.
# Do NOT guess addresses: a wrong fraud-report address wastes a victim's time.
VERIFIED_ON: Final[str | None] = None
SAFARICOM_REPORT_CHANNEL: Final = "email"
SAFARICOM_REPORT_TO: Final = "<Safaricom fraud-reporting address: confirm on safaricom.co.ke before sending>"
SAFARICOM_SMS_SHORTCODE_NOTE: Final = (
    "<Safaricom scam-SMS forwarding short code: confirm on safaricom.co.ke (commonly cited as 333)>"
)
KECIRT_REPORT_TO: Final = "<National KE-CIRT/CC incident address: confirm on ke-cirt.go.ke before sending>"
# Public help centres; link the exact impersonation form once verified.
PLATFORM_REPORT_URLS: Final = {
    "instagram": "https://help.instagram.com/",
    "facebook": "https://www.facebook.com/help/",
    "tiktok": "https://support.tiktok.com/",
    "x": "https://help.x.com/",
}

# --- Account signal (scorer.py): ACCOUNT v2 ----------------------------------------------------
ACCOUNT_AGE_SCORES: Final = ((30, 90.0), (90, 60.0), (365, 30.0))   # (max age in days, score); older -> 10
ACCOUNT_AGE_OLD: Final = 10.0
LOW_POST_COUNT: Final = 12                      # fewer posts than this ...
LOW_POST_SCORE: Final = 60.0
LOW_FOLLOWER_COUNT: Final = 300                 # fewer followers than this while resemblance >= STRONG_VISUAL
LOW_FOLLOWER_SCORE: Final = 70.0
