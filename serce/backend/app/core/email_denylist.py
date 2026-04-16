"""Disposable / temporary email domain denylist.

Blocks registrations from known throw-away email services.
Extend DENYLIST as needed — sorted alphabetically for easy maintenance.
"""
from __future__ import annotations

# Common disposable email providers (top ~50 by volume).
# Source: aggregated from multiple public denylist repos.
DENYLIST: frozenset[str] = frozenset({
    "10minutemail.com",
    "burpcollaborator.net",
    "clipmail.eu",
    "dispostable.com",
    "emailondeck.com",
    "fakeinbox.com",
    "getnada.com",
    "guerrillamail.com",
    "guerrillamail.info",
    "guerrillamailblock.com",
    "harakirimail.com",
    "mailcatch.com",
    "maildrop.cc",
    "mailexpire.com",
    "mailinator.com",
    "mailnesia.com",
    "mailsac.com",
    "minutemail.com",
    "mohmal.com",
    "mytemp.email",
    "sharklasers.com",
    "spam4.me",
    "spamgourmet.com",
    "temp-mail.org",
    "tempail.com",
    "tempm.com",
    "tempmail.com",
    "throwaway.email",
    "tmpmail.net",
    "tmpmail.org",
    "trashmail.com",
    "trashmail.me",
    "trashmail.net",
    "yopmail.com",
    "yopmail.fr",
})


def is_disposable_email(email: str) -> bool:
    """Return True if the email domain is on the denylist."""
    domain = email.rsplit("@", 1)[-1].lower()
    return domain in DENYLIST
