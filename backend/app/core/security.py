import socket
import ipaddress
from urllib.parse import urlparse
from fastapi import Security, HTTPException, status, Request
from fastapi.security.api_key import APIKeyHeader
from slowapi import Limiter
import secrets
from app.core.config import settings

def get_client_ip(request: Request) -> str:
    """Read the client IP from X-Forwarded-For if behind a proxy/ngrok, else fallback to client host."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"

limiter = Limiter(key_func=get_client_ip)

api_key_header = APIKeyHeader(name="X-Halisi-Key", auto_error=True)

def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    if not secrets.compare_digest(api_key, settings.api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    return api_key

def is_public_url(url: str) -> bool:
    """
    SSRF guard: resolves DNS and checks if the URL points to a public IP.
    Rejects private, loopback, link-local, multicast, and reserved IPs.
    Requires https scheme.
    """
    try:
        parsed = urlparse(url)
        if parsed.scheme != "https":
            return False
        
        hostname = parsed.hostname
        if not hostname:
            return False
        
        # Get all IPs for the hostname
        _, _, ip_addresses = socket.gethostbyname_ex(hostname)
        
        if not ip_addresses:
            return False
            
        for ip_str in ip_addresses:
            ip = ipaddress.ip_address(ip_str)
            if (ip.is_private or 
                ip.is_loopback or 
                ip.is_link_local or 
                ip.is_multicast or 
                ip.is_reserved or 
                not ip.is_global):
                return False
        
        return True
    except Exception:
        return False
