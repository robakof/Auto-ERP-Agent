"""Rate limiting with slowapi (decyzja #114).

Limits:
- register: 5/hour per IP (anti-farming)
- login:    10/minute per IP (brute-force protection)
- refresh:  20/minute per IP
"""
from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
