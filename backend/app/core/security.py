"""Security primitives (docs/BACKEND.md section 11): SSRF guard, API key, rate limiting, client IP."""

import asyncio
import ipaddress
import secrets
import socket
from collections.abc import Awaitable, Callable
from urllib.parse import urlsplit

from fastapi import Request
from limits import parse
from limits.storage import MemoryStorage
from limits.strategies import MovingWindowRateLimiter

from app.core.errors import RateLimited, Unauthorized

Resolver = Callable[[str], Awaitable[list[str]]]
API_KEY_HEADER = "X-Halisi-Key"


async def system_resolver(host: str) -> list[str]:
    """Resolve ``host`` to IP strings with the OS resolver (in a thread)."""
    infos = await asyncio.to_thread(socket.getaddrinfo, host, 443, proto=socket.IPPROTO_TCP)
    return sorted({str(info[4][0]) for info in infos})


def is_public_ip(value: str) -> bool:
    """False for private, loopback, link-local, multicast, reserved, unspecified and CGNAT addresses."""
    try:
        ip = ipaddress.ip_address(value.split("%", 1)[0])
    except ValueError:
        return False
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped
    return not (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
        or ip in ipaddress.ip_network("100.64.0.0/10")
    )


async def is_public_url(url: str, *, resolver: Resolver = system_resolver) -> bool:
    """SSRF guard: ``https`` only, no credentials, and every resolved address must be public.

    Call it for the first URL **and after every redirect** (the page scraper follows redirects
    manually for this reason). Known limitation: httpx resolves the host again when connecting,
    so a DNS-rebinding attacker with a very short TTL could still race this check.
    """
    try:
        parts = urlsplit(url)
    except ValueError:
        return False
    if parts.scheme != "https" or not parts.hostname or parts.username or parts.password:
        return False
    host = parts.hostname.strip("[]").lower()
    if host == "localhost" or host.endswith(".localhost") or host.endswith(".internal"):
        return False
    try:
        ipaddress.ip_address(host.split("%", 1)[0])
        addresses = [host]
    except ValueError:
        try:
            addresses = await resolver(host)
        except (OSError, UnicodeError):
            return False
    return bool(addresses) and all(is_public_ip(a) for a in addresses)


def check_api_key(provided: str | None, expected: str) -> bool:
    """Constant-time API-key comparison. An empty configured key never matches."""
    if not expected or not provided:
        return False
    return secrets.compare_digest(provided.encode(), expected.encode())


async def require_api_key(request: Request) -> None:
    """FastAPI dependency for key-protected endpoints (header ``X-Halisi-Key``)."""
    expected = request.app.state.settings.api_key
    if not check_api_key(request.headers.get(API_KEY_HEADER), expected):
        raise Unauthorized()


def has_valid_api_key(request: Request) -> bool:
    """Whether the request carries the API key (optional auth, e.g. merchant stats)."""
    return check_api_key(request.headers.get(API_KEY_HEADER), request.app.state.settings.api_key)


def client_ip(request: Request) -> str:
    """Rate-limit key. Trust ``X-Forwarded-For`` (first hop) when ``TRUST_FORWARDED_FOR`` is on."""
    peer = request.client.host if request.client else "unknown"
    settings = getattr(request.app.state, "settings", None)
    if settings is not None and settings.trust_forwarded_for:
        forwarded = request.headers.get("x-forwarded-for", "")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return peer


class RateLimiter:
    """Per-app moving-window limiter on the ``limits`` engine (the library slowapi is built on).

    A FastAPI dependency instead of slowapi's decorator so each app instance (and each test) reads
    its own settings and has its own counters.
    """

    def __init__(self) -> None:
        self.storage = MemoryStorage()
        self.strategy = MovingWindowRateLimiter(self.storage)

    def hit(self, scope: str, limit: str, key: str) -> bool:
        """Count one request; False when ``limit`` (e.g. ``"10/minute"``) is exceeded."""
        return self.strategy.hit(parse(limit), scope, key)

    def reset(self) -> None:
        """Clear all counters."""
        self.storage.reset()


def rate_limit(setting_name: str, scope: str) -> Callable[[Request], Awaitable[None]]:
    """Dependency factory: limit an endpoint per client IP using ``settings.<setting_name>``."""

    async def dependency(request: Request) -> None:
        settings = request.app.state.settings
        if not settings.rate_limit_enabled:
            return
        limiter: RateLimiter = request.app.state.rate_limiter
        if not limiter.hit(scope, getattr(settings, setting_name), client_ip(request)):
            raise RateLimited()

    return dependency
