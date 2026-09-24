from rapidfuzz.distance import JaroWinkler
import re
from typing import Dict

# Known high-risk tokens common in Kenyan social commerce scams
KENYAN_SCAM_TOKENS = [
    r"pay before delivery",
    r"strictly delivery",
    r"no physical shop",
    r"payment with order",
    r"delivery countrywide",
    r"send to till",
    r"deposit required",
    r"non-refundable",
    r"inbox to order",
    r"pay via m-pesa before"
]

def calculate_typosquatting_score(authentic_handle: str, suspicious_handle: str) -> float:
    """
    Calculates the similarity between two social media handles using Jaro-Winkler.
    Returns a score from 0.0 (completely different) to 100.0 (identical).
    """
    if not authentic_handle or not suspicious_handle:
        return 0.0
        
    # Clean up inputs: lowercase and strip common @ symbols
    auth = authentic_handle.lower().strip('@')
    susp = suspicious_handle.lower().strip('@')
    
    # Use Jaro-Winkler which heavily weights prefix similarities.
    # Excellent for catching tweaks like 'nairobi_shoes' vs 'nairobl_shoes'
    similarity = JaroWinkler.similarity(auth, susp)
    
    return round(similarity * 100, 2)

def analyze_bio_scam_tokens(bio_text: str) -> float:
    """
    Scans bio text for known Kenyan scam tokens.
    Returns a risk score from 0 to 100.
    """
    if not bio_text:
        return 0.0
        
    bio_lower = bio_text.lower()
    matches = 0
    
    for token in KENYAN_SCAM_TOKENS:
        if re.search(token, bio_lower):
            matches += 1
            
    # Arbitrary scoring: each flagged token adds 33.33% to the risk, capped at 100%
    risk_score = min(100.0, matches * 33.33)
    return round(risk_score, 2)
    
def analyze_text_match(authentic_handle: str, suspicious_handle: str, suspicious_bio: str) -> Dict[str, float]:
    """
    Composite function that returns both the typosquatting match and the bio risk.
    """
    typo_score = calculate_typosquatting_score(authentic_handle, suspicious_handle)
    token_risk = analyze_bio_scam_tokens(suspicious_bio)
    
    return {
        "typosquatting_similarity_score": typo_score,
        "bio_token_risk_score": token_risk
    }
