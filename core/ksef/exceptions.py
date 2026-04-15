"""KSeF error hierarchy.

Boundary validation — API responses mapped to typed exceptions once at the
transport layer; upper layers trust the types (PATTERNS.md §Validation at Boundary).
"""
from __future__ import annotations


class KSefError(Exception):
    """Base class for all KSeF-related errors."""


class KSefApiError(KSefError):
    """API returned a business-level error (4xx)."""

    def __init__(
        self,
        status_code: int,
        error_code: str | None,
        message: str,
        details: list[str] | None = None,
    ) -> None:
        super().__init__(f"[{status_code}] {error_code or '?'}: {message}")
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        self.details = details or []


class KSefTransportError(KSefError):
    """Network/infrastructure failure (5xx, timeout, connection)."""

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.cause = cause


class KSefAuthError(KSefError):
    """Authentication flow failed (token invalid, auth operation failed/expired)."""

    def __init__(self, message: str, code: int | None = None) -> None:
        super().__init__(message)
        self.code = code


class KSefAuthTimeoutError(KSefAuthError):
    """Auth status polling exceeded timeout without reaching a terminal state."""


class KSefRepoError(KSefError):
    """Persistence-layer error (shadow DB)."""


class ShipmentAlreadyActiveError(KSefRepoError):
    """Próba utworzenia nowej wysyłki dla (gid, rodzaj) z aktywnym wpisem."""


class InvalidTransitionError(KSefRepoError):
    """Przejście stanu niedozwolone w state machine."""


class ShipmentNotFoundError(KSefRepoError):
    """Brak wiersza o podanym id / (gid, rodzaj)."""
