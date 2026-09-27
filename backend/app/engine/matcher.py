import re
import unicodedata
from rapidfuzz import fuzz
from rapidfuzz.distance import JaroWinkler
from typing import List, Optional, Tuple

AFFIXES = {"official", "real", "original", "genuine", "the", "ke", "kenya", "254", "nairobi_official",
           "shop", "store", "online", "deals", "offers", "hq", "team", "care", "support"}

HOMOGLYPHS = [("rn", "m"), ("vv", "w"), ("0", "o"), ("1", "l"), ("i", "l"), ("|", "l"), ("3", "e"), ("5", "s"), ("@", "a")]

LANGUAGE_TOKENS = [
    (40, ["pay before delivery", "lipa kwanza", "lipa kabla", "pochi la biashara", "send money to", "tuma pesa", "deposit required", "pay via m-pesa before"]),
    (25, ["payment with order", "no refunds", "non-refundable", "offer ends today", "leo tu", "whatsapp only", "dm for price", "limited stock"]),
    (10, ["strictly delivery", "no physical shop", "inbox to order", "delivery countrywide", "order now"])
]

class IdentityResult:
    def __init__(self, score: float, evidence: str):
        self.score = score
        self.evidence = evidence

class LanguageResult:
    def __init__(self, score: Optional[float], evidence: Optional[str]):
        self.score = score
        self.evidence = evidence

def normalize_handle(h: str) -> str:
    if not h:
        return ""
    h = h.lower().lstrip('@').rstrip('/')
    h = unicodedata.normalize('NFKC', h)
    return re.sub(r'[\._\-\s]', '', h)

def fold_homoglyphs(s: str) -> str:
    for old, new in HOMOGLYPHS:
        s = s.replace(old, new)
    return s

def get_tokens(s: str) -> List[str]:
    # Splitting by non-alphanumeric to get tokens
    return [t for t in re.split(r'[^a-z0-9]', s) if t]

def strip_affixes(tokens: List[str]) -> List[str]:
    return [t for t in tokens if t not in AFFIXES]

def compare_identity(target_folded: str, target_tokens: List[str], ref_str: str) -> Tuple[float, str]:
    if not ref_str:
        return 0.0, ""
    
    # Clean ref
    ref_norm = normalize_handle(ref_str)
    ref_folded = fold_homoglyphs(ref_norm)
    ref_tokens = get_tokens(ref_norm)
    ref_stripped = strip_affixes(ref_tokens)
    
    if not ref_folded:
        return 0.0, ""

    # a) 0.5*JaroWinkler + 0.5*fuzz.ratio on fold(normalize(x))
    jw = JaroWinkler.similarity(ref_folded, target_folded) * 100
    fr = fuzz.ratio(ref_folded, target_folded)
    score_a = 0.5 * jw + 0.5 * fr
    
    # b) fuzz.token_set_ratio on affix-stripped tokens
    target_stripped_str = " ".join(target_tokens)
    ref_stripped_str = " ".join(ref_stripped)
    score_b = fuzz.token_set_ratio(ref_stripped_str, target_stripped_str) if ref_stripped_str and target_stripped_str else 0.0
    
    # c) containment: 95 if fold(ref) in fold(target) and len(ref) >= 6
    score_c = 95.0 if len(ref_folded) >= 6 and ref_folded in target_folded else 0.0
    
    max_score = max(score_a, score_b, score_c)
    
    evidence = ""
    if max_score == score_a:
        evidence = f"'{target_folded}' vs '{ref_folded}' (JW/Ratio)"
    elif max_score == score_b:
        evidence = f"Tokens '{target_stripped_str}' matches '{ref_stripped_str}'"
    elif max_score == score_c:
        evidence = f"'{target_folded}' contains '{ref_folded}'"
        
    return max_score, evidence

def identity_score(target_handle: Optional[str], target_name: Optional[str], merchant) -> IdentityResult:
    """
    merchant is expected to have:
    - official_handles: list of objects with a 'handle' attribute
    - business_name: string
    - aliases: list of strings
    """
    best_score = 0.0
    best_evidence = "No match"
    
    targets_to_test = []
    if target_handle:
        targets_to_test.append(target_handle)
    if target_name:
        targets_to_test.append(target_name)
        
    if not targets_to_test:
        return IdentityResult(0.0, best_evidence)
        
    refs = []
    if hasattr(merchant, 'official_handles') and merchant.official_handles:
        for h in merchant.official_handles:
            if hasattr(h, 'handle') and h.handle:
                refs.append(h.handle)
            elif isinstance(h, str):
                refs.append(h)
    if hasattr(merchant, 'business_name') and merchant.business_name:
        refs.append(merchant.business_name)
    if hasattr(merchant, 'aliases') and merchant.aliases:
        refs.extend(merchant.aliases)
        
    for t_raw in targets_to_test:
        t_norm = normalize_handle(t_raw)
        t_folded = fold_homoglyphs(t_norm)
        
        # Original tokens for affix stripping
        # Using a slightly different approach: extract tokens before removing dots/underscores to preserve word boundaries
        # Wait, normalize_handle removes dots and underscores, so we should tokenise before that.
        t_clean_for_tokens = str(t_raw).lower().lstrip('@').rstrip('/')
        t_clean_for_tokens = unicodedata.normalize('NFKC', t_clean_for_tokens)
        t_tokens = get_tokens(t_clean_for_tokens)
        t_stripped_tokens = strip_affixes(t_tokens)
        
        for r_raw in refs:
            score, ev = compare_identity(t_folded, t_stripped_tokens, r_raw)
            if score > best_score:
                best_score = score
                best_evidence = ev
                
    return IdentityResult(round(best_score, 2), best_evidence)

def language_score(bio_text: Optional[str]) -> LanguageResult:
    if not bio_text:
        return LanguageResult(None, None)
        
    bio_lower = bio_text.lower()
    total_score = 0
    matched_phrases = []
    
    for weight, phrases in LANGUAGE_TOKENS:
        for phrase in phrases:
            if phrase in bio_lower:
                total_score += weight
                matched_phrases.append(f"'{phrase}'")
                
    if not matched_phrases:
        return LanguageResult(None, None)
        
    final_score = min(100.0, float(total_score))
    evidence = ", ".join(matched_phrases)
    return LanguageResult(final_score, evidence)
