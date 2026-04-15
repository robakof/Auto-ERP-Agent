"""KSeF authentication orchestrator.

Flow:
    1. GET /security/public-key-certificates   (cached per instance)
    2. POST /auth/challenge                    → challenge + timestampMs
    3. Encrypt "token|timestampMs" with RSA-OAEP SHA-256 using KsefTokenEncryption cert
    4. POST /auth/ksef-token                   → authenticationToken (operation JWT)
    5. Poll GET /auth/{ref} with operation JWT → status code 200 | 400 | 500
    6. POST /auth/token/redeem with operation JWT → (accessToken, refreshToken)
    7. Cache access/refresh in memory; refresh when TTL < 5 minutes.

No disk cache in Block 1 — in-memory only (plan §Persistence cache: not in Block 1).
"""
from __future__ import annotations

import base64
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Protocol

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.x509 import load_der_x509_certificate

from core.ksef.adapters.ksef_api import KSeFApiClient
from core.ksef.exceptions import KSefAuthError, KSefAuthTimeoutError
from core.ksef.models import AccessToken, PublicKeyCertificate, RefreshToken, TokenPair

_LOG = logging.getLogger("ksef.auth")

_REFRESH_THRESHOLD_SECONDS = 5 * 60
_POLL_INITIAL_SECONDS = 1.0
_POLL_MAX_SECONDS = 5.0
_POLL_TIMEOUT_SECONDS = 30.0


class TokenProvider(Protocol):
    """Supplies the long-lived KSeF token (from portal) and the NIP context."""

    def get_token(self) -> str: ...
    def get_nip(self) -> str: ...


@dataclass
class EnvTokenProvider:
    """Reads KSEF_TOKEN and KSEF_NIP from the loaded config."""

    token: str
    nip: str

    def get_token(self) -> str:
        return self.token

    def get_nip(self) -> str:
        return self.nip


class KSefAuth:
    """Authentication orchestration — owns auth state for one API client."""

    def __init__(
        self,
        api: KSeFApiClient,
        token_provider: TokenProvider,
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
        sleep: Callable[[float], None] = time.sleep,
        poll_timeout_s: float = _POLL_TIMEOUT_SECONDS,
    ) -> None:
        self._api = api
        self._provider = token_provider
        self._clock = clock
        self._sleep = sleep
        self._poll_timeout = poll_timeout_s
        self._token_cert: PublicKeyCertificate | None = None
        self._access: AccessToken | None = None
        self._refresh: RefreshToken | None = None

    # ---- public ------------------------------------------------------

    def authenticate(self) -> AccessToken:
        """Full auth flow. Returns a cached AccessToken."""
        _LOG.info('{"event": "ksef_auth_start"}')
        cert = self._get_token_cert()
        challenge = self._api.get_challenge()
        payload = f"{self._provider.get_token()}|{challenge.timestamp_ms}".encode("utf-8")
        encrypted = _rsa_oaep_encrypt(cert.certificate_b64, payload)
        encrypted_b64 = base64.b64encode(encrypted).decode("ascii")

        init = self._api.auth_with_token(
            challenge=challenge.challenge,
            nip=self._provider.get_nip(),
            encrypted_token_b64=encrypted_b64,
        )
        op_token = init.authentication_token.token
        self._poll_until_success(init.reference_number, op_token)
        pair = self._api.redeem_token(auth_op_token=op_token)
        self._access = pair.access
        self._refresh = pair.refresh
        _LOG.info(
            '{"event": "ksef_auth_ok", "access_tail": "%s", "valid_until": "%s"}',
            pair.access.token[-4:],
            pair.access.valid_until.isoformat(),
        )
        return pair.access

    def ensure_valid(self) -> AccessToken:
        """Return a valid access token, refreshing or re-authenticating if needed."""
        if self._access is None or self._refresh is None:
            return self.authenticate()
        remaining = (self._access.valid_until - self._clock()).total_seconds()
        if remaining >= _REFRESH_THRESHOLD_SECONDS:
            return self._access
        try:
            access = self._api.refresh_token(refresh_token=self._refresh.token)
        except Exception as exc:
            _LOG.warning('{"event": "ksef_refresh_failed", "err": "%r"}', exc)
            return self.authenticate()
        self._access = access
        return access

    def logout(self) -> None:
        if self._access is None:
            return
        try:
            self._api.logout(access_token=self._access.token)
        finally:
            self._access = None
            self._refresh = None

    @property
    def current_access_token(self) -> str | None:
        return self._access.token if self._access else None

    @property
    def token_pair(self) -> TokenPair | None:
        if self._access is None or self._refresh is None:
            return None
        return TokenPair(access=self._access, refresh=self._refresh)

    # ---- internals ---------------------------------------------------

    def _get_token_cert(self) -> PublicKeyCertificate:
        if self._token_cert is not None:
            return self._token_cert
        certs = self._api.get_public_key_certificates()
        match = next((c for c in certs if "KsefTokenEncryption" in c.usage), None)
        if match is None:
            raise KSefAuthError("No KsefTokenEncryption certificate returned by KSeF")
        self._token_cert = match
        return match

    def _poll_until_success(self, reference_number: str, op_token: str) -> None:
        deadline = self._clock().timestamp() + self._poll_timeout
        interval = _POLL_INITIAL_SECONDS
        while True:
            status = self._api.auth_status(reference_number, auth_op_token=op_token)
            if status.success:
                return
            if status.failed:
                raise KSefAuthError(
                    f"auth failed: {status.description}" + (f" ({'; '.join(status.details)})" if status.details else ""),
                    code=status.code,
                )
            if not status.in_progress:
                raise KSefAuthError(f"unexpected auth status code {status.code}")
            if self._clock().timestamp() >= deadline:
                raise KSefAuthTimeoutError(
                    f"auth polling timeout after {self._poll_timeout}s (ref={reference_number})"
                )
            self._sleep(interval)
            interval = min(interval * 2, _POLL_MAX_SECONDS)


def _rsa_oaep_encrypt(cert_b64: str, data: bytes) -> bytes:
    """Encrypt `data` with the cert's public key using RSA-OAEP(SHA-256)."""
    der = base64.b64decode(cert_b64)
    cert = load_der_x509_certificate(der)
    public_key = cert.public_key()
    return public_key.encrypt(
        data,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )


