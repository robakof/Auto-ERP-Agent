"""Typed response/request models for KSeF 2.0 API.

Dataclasses are the boundary output — responses are parsed once in adapters,
upstream code never sees raw dicts (PATTERNS.md §Validation at Boundary).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


# ---- Auth ----------------------------------------------------------------

@dataclass(frozen=True)
class AuthChallenge:
    challenge: str
    timestamp: datetime
    timestamp_ms: int


@dataclass(frozen=True)
class AuthOperationToken:
    """Short-lived token returned by /auth/ksef-token (and /auth/xades-signature).

    Used as Bearer for /auth/{ref} (status) and /auth/token/redeem.
    """

    token: str
    valid_until: datetime


@dataclass(frozen=True)
class AuthInitResponse:
    reference_number: str
    authentication_token: AuthOperationToken


@dataclass(frozen=True)
class AuthOperationStatus:
    start_date: datetime
    authentication_method: str
    code: int
    description: str
    details: list[str] = field(default_factory=list)

    @property
    def in_progress(self) -> bool:
        return self.code == 100

    @property
    def success(self) -> bool:
        return self.code == 200

    @property
    def failed(self) -> bool:
        return self.code >= 400


@dataclass(frozen=True)
class AccessToken:
    """Context token for operations under /sessions/*."""

    token: str
    valid_until: datetime


@dataclass(frozen=True)
class RefreshToken:
    token: str
    valid_until: datetime


@dataclass(frozen=True)
class TokenPair:
    access: AccessToken
    refresh: RefreshToken


# ---- Public-key certificate ---------------------------------------------

@dataclass(frozen=True)
class PublicKeyCertificate:
    """One entry from GET /security/public-key-certificates.

    `usage` carries identifiers like `KsefTokenEncryption` and `SymmetricKeyEncryption`.
    """

    certificate_b64: str
    valid_from: datetime
    valid_to: datetime
    usage: list[str]


# ---- Sessions -----------------------------------------------------------

@dataclass(frozen=True)
class OnlineSession:
    reference_number: str
    valid_until: datetime


@dataclass(frozen=True)
class SendInvoiceAck:
    """Acknowledgement returned by POST /sessions/online/{ref}/invoices (202)."""

    reference_number: str


@dataclass(frozen=True)
class InvoiceStatus:
    reference_number: str
    ksef_number: str | None
    status_code: int
    status_description: str
    details: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Upo:
    """UPO (Urzędowe Poświadczenie Odbioru) — receipt XML returned by KSeF."""

    content: bytes
    content_type: str
