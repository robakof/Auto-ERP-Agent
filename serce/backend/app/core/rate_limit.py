"""Rate limiting with slowapi (decyzja #114).

Limits:
- register: 5/hour per IP (anti-farming)
- login:    10/minute per IP (brute-force protection)
- refresh:  20/minute per IP
"""
from __future__ import annotations

from starlette.requests import Request

from slowapi import Limiter


def _get_client_ip(request: Request) -> str:
    """Extract real client IP, respecting X-Forwarded-For behind reverse proxy."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


limiter = Limiter(key_func=_get_client_ip)
