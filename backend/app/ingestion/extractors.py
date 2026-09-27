import re
from typing import List, Dict

KE_PHONE = re.compile(r"(?<!\d)(?:\+?254[\s-]?|0)([17](?:[\s-]?\d){8})(?!\d)")
TILL     = re.compile(r"(?:till|buy\s*goods|\bb\.?g\.(?!\w)|\bbg\b)\s*(?:no\.?|number|#|:)?\s*(\d{5,7})(?!\d)", re.I)
PAYBILL  = re.compile(r"pay\s*bill\s*(?:no\.?|number|#|:)?\s*(\d{5,7})(?!\d)", re.I)
WA_LINK  = re.compile(r"wa\.me/(\d{10,13})")
POCHI    = re.compile(r"pochi\s*la\s*biashara|send\s*money\s*to|tuma\s*pesa", re.I)

def normalize_phone(match: str) -> str:
    clean = re.sub(r'[\s-]', '', match)
    return "+254" + clean

def extract_phones(text: str) -> List[str]:
    results = []
    for match in KE_PHONE.findall(text):
        results.append(normalize_phone(match))
    
    for wa in WA_LINK.findall(text):
        if wa.startswith("254") and len(wa) == 12:
            results.append("+" + wa)
            
    return list(set(results))

def extract_tills(text: str) -> List[str]:
    return list(set(TILL.findall(text)))

def extract_paybills(text: str) -> List[str]:
    return list(set(PAYBILL.findall(text)))

def has_pochi(text: str) -> bool:
    return bool(POCHI.search(text))

def extract_payment_signals(text: str) -> Dict[str, any]:
    if not text:
        return {"phones": [], "tills": [], "paybills": [], "has_pochi": False}
    return {
        "phones": extract_phones(text),
        "tills": extract_tills(text),
        "paybills": extract_paybills(text),
        "has_pochi": has_pochi(text)
    }
