from urllib.parse import urlparse, parse_qs
import re
from fastapi import HTTPException
from pydantic import BaseModel
from typing import Optional
from app.ingestion.extractors import KE_PHONE, TILL, WA_LINK, normalize_phone

class ParsedInput(BaseModel):
    kind: str  # "handle", "url", "phone", "till"
    platform: Optional[str] = None
    handle: Optional[str] = None
    phone: Optional[str] = None
    till: Optional[str] = None
    url: Optional[str] = None

def parse_input(value: str) -> ParsedInput:
    value = value.strip()
    if not value:
        raise HTTPException(status_code=422, detail="UNSUPPORTED_PLATFORM")

    # Limit length
    if len(value) > 2048:
        raise HTTPException(status_code=422, detail="UNSUPPORTED_PLATFORM")

    # Check for wa.me link
    wa_match = WA_LINK.search(value)
    if wa_match:
        phone = wa_match.group(1)
        if phone.startswith("254") and len(phone) == 12:
            return ParsedInput(kind="phone", phone="+" + phone)
        # fallback for other numbers on wa.me if needed
        return ParsedInput(kind="phone", phone="+" + phone)

    # Check if raw handle
    if value.startswith("@"):
        handle = value[1:].lower().strip()
        return ParsedInput(kind="handle", platform="instagram", handle=handle)

    # Check if pure phone
    phone_match = KE_PHONE.fullmatch(value)
    if phone_match:
        return ParsedInput(kind="phone", phone=normalize_phone(phone_match.group(1)))
        
    # Check if pure till
    # TILL regex expects things like "till no 12345", but a raw number might just be "123456"
    if re.fullmatch(r"\d{5,7}", value):
        return ParsedInput(kind="till", till=value)

    # Try parsing as URL
    url_to_parse = value
    if not url_to_parse.startswith("http"):
        url_to_parse = "https://" + url_to_parse

    parsed_url = urlparse(url_to_parse)
    domain = parsed_url.netloc.lower()
    path = parsed_url.path.strip("/")

    if domain.startswith("www."):
        domain = domain[4:]

    if domain == "instagram.com":
        if not path:
            raise HTTPException(status_code=422, detail="UNSUPPORTED_PLATFORM")
        handle = path.split("/")[0]
        return ParsedInput(kind="url", platform="instagram", handle=handle, url=value)

    if domain in ("facebook.com", "m.facebook.com", "fb.com"):
        if path == "profile.php":
            qs = parse_qs(parsed_url.query)
            if "id" in qs:
                return ParsedInput(kind="url", platform="facebook", handle=qs["id"][0], url=value)
            raise HTTPException(status_code=422, detail="UNSUPPORTED_PLATFORM")
        if not path:
            raise HTTPException(status_code=422, detail="UNSUPPORTED_PLATFORM")
        handle = path.split("/")[0]
        return ParsedInput(kind="url", platform="facebook", handle=handle, url=value)

    if domain == "tiktok.com":
        if path.startswith("@"):
            handle = path[1:].split("/")[0]
            return ParsedInput(kind="url", platform="tiktok", handle=handle, url=value)
        raise HTTPException(status_code=422, detail="UNSUPPORTED_PLATFORM")

    if domain in ("twitter.com", "x.com"):
        if not path:
            raise HTTPException(status_code=422, detail="UNSUPPORTED_PLATFORM")
        handle = path.split("/")[0]
        return ParsedInput(kind="url", platform="twitter", handle=handle, url=value)

    raise HTTPException(status_code=422, detail="UNSUPPORTED_PLATFORM")
