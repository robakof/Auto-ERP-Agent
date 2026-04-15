"""Auth orchestration tests for KSefAuth.

Covers:
- Happy flow (challenge → auth → polling → redeem)
- Polling timeout → KSefAuthTimeoutError
- Polling status=failed → KSefAuthError
- ensure_valid() — token valid (no refresh)
- ensure_valid() — token near expiry (refresh)
- ensure_valid() — refresh fails → re-authenticate
"""
from __future__ import annotations

import base64
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509 import CertificateBuilder, Name, NameAttribute, random_serial_number
from cryptography.x509.oid import NameOID

from core.ksef.adapters.ksef_auth import EnvTokenProvider, KSefAuth
from core.ksef.exceptions import KSefAuthError, KSefAuthTimeoutError
from core.ksef.models import (
    AccessToken,
    AuthChallenge,
    AuthInitResponse,
    AuthOperationStatus,
    AuthOperationToken,
    PublicKeyCertificate,
    RefreshToken,
    TokenPair,
)


# ---- helpers --------------------------------------------------------------

def _make_cert_b64() -> str:
    """Generate a real RSA cert (DER) Base64-encoded — used by _rsa_oaep_encrypt."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = Name([NameAttribute(NameOID.COMMON_NAME, "KSeF Test")])
    cert = (
        CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(random_serial_number())
        .not_valid_before(datetime(2024, 1, 1, tzinfo=timezone.utc))
        .not_valid_after(datetime(2028, 1, 1, tzinfo=timezone.utc))
        .sign(private_key=key, algorithm=hashes.SHA256())
    )
    der = cert.public_bytes(serialization.Encoding.DER)
    return base64.b64encode(der).decode("ascii")


@pytest.fixture
def fake_cert():
    return PublicKeyCertificate(
        certificate_b64=_make_cert_b64(),
        valid_from=datetime(2024, 1, 1, tzinfo=timezone.utc),
        valid_to=datetime(2028, 1, 1, tzinfo=timezone.utc),
        usage=["KsefTokenEncryption"],
    )


@pytest.fixture
def api(fake_cert):
    m = MagicMock()
    m.get_public_key_certificates.return_value = [fake_cert]
    m.get_challenge.return_value = AuthChallenge(
        challenge="CH-1",
        timestamp=datetime(2025, 7, 11, 12, tzinfo=timezone.utc),
        timestamp_ms=1752236636015,
    )
    m.auth_with_token.return_value = AuthInitResponse(
        reference_number="AUTH-REF-1",
        authentication_token=AuthOperationToken(
            token="op-token",
            valid_until=datetime(2025, 7, 11, 13, tzinfo=timezone.utc),
        ),
    )
    m.redeem_token.return_value = TokenPair(
        access=AccessToken(
            token="access-1",
            valid_until=datetime(2025, 7, 11, 13, tzinfo=timezone.utc),
        ),
        refresh=RefreshToken(
            token="refresh-1",
            valid_until=datetime(2025, 7, 11, 14, tzinfo=timezone.utc),
        ),
    )
    return m


@pytest.fixture
def provider():
    return EnvTokenProvider(token="KSEF-TOKEN-XYZ", nip="5260250274")


# ---- tests ---------------------------------------------------------------

def test_authenticate_happy_flow(api, provider):
    api.auth_status.side_effect = [
        _status(100, "w toku"),
        _status(200, "sukces"),
    ]
    auth = KSefAuth(api, provider, sleep=lambda _: None)
    access = auth.authenticate()

    assert access.token == "access-1"
    api.get_challenge.assert_called_once()
    api.auth_with_token.assert_called_once()
    assert api.auth_status.call_count == 2
    api.redeem_token.assert_called_once_with(auth_op_token="op-token")


def test_authenticate_encrypts_token_payload(api, provider):
    api.auth_status.return_value = _status(200, "sukces")
    auth = KSefAuth(api, provider, sleep=lambda _: None)
    auth.authenticate()

    call = api.auth_with_token.call_args
    assert call.kwargs["challenge"] == "CH-1"
    assert call.kwargs["nip"] == "5260250274"
    # encrypted_token_b64 is a non-empty base64 string
    enc = call.kwargs["encrypted_token_b64"]
    assert enc and base64.b64decode(enc)  # decodes without error


def test_polling_timeout_raises(api, provider):
    api.auth_status.return_value = _status(100, "w toku")
    now = [datetime(2025, 7, 11, 12, tzinfo=timezone.utc)]

    def clock() -> datetime:
        return now[0]

    def sleep(seconds: float) -> None:
        now[0] = now[0] + timedelta(seconds=seconds)

    auth = KSefAuth(api, provider, clock=clock, sleep=sleep, poll_timeout_s=3.0)
    with pytest.raises(KSefAuthTimeoutError):
        auth.authenticate()


def test_polling_failed_raises(api, provider):
    api.auth_status.return_value = _status(400, "Błąd", details=["Nieważny certyfikat."])
    auth = KSefAuth(api, provider, sleep=lambda _: None)
    with pytest.raises(KSefAuthError) as exc_info:
        auth.authenticate()
    assert "Nieważny certyfikat" in str(exc_info.value)
    assert exc_info.value.code == 400


def test_ensure_valid_no_refresh_when_token_fresh(api, provider):
    api.auth_status.return_value = _status(200, "sukces")
    future_valid_until = datetime(2025, 7, 11, 13, tzinfo=timezone.utc)
    api.redeem_token.return_value = TokenPair(
        access=AccessToken(token="a-1", valid_until=future_valid_until),
        refresh=RefreshToken(token="r-1", valid_until=future_valid_until + timedelta(hours=1)),
    )

    clock_now = datetime(2025, 7, 11, 12, tzinfo=timezone.utc)
    auth = KSefAuth(api, provider, sleep=lambda _: None, clock=lambda: clock_now)
    auth.authenticate()
    api.refresh_token.reset_mock()

    access = auth.ensure_valid()
    assert access.token == "a-1"
    api.refresh_token.assert_not_called()


def test_ensure_valid_refreshes_near_expiry(api, provider):
    api.auth_status.return_value = _status(200, "sukces")
    initial_until = datetime(2025, 7, 11, 12, 2, tzinfo=timezone.utc)
    api.redeem_token.return_value = TokenPair(
        access=AccessToken(token="a-1", valid_until=initial_until),
        refresh=RefreshToken(token="r-1", valid_until=initial_until + timedelta(hours=1)),
    )
    api.refresh_token.return_value = AccessToken(
        token="a-2",
        valid_until=datetime(2025, 7, 11, 13, tzinfo=timezone.utc),
    )

    clock_now = datetime(2025, 7, 11, 12, tzinfo=timezone.utc)  # 2 min before expiry
    auth = KSefAuth(api, provider, sleep=lambda _: None, clock=lambda: clock_now)
    auth.authenticate()

    access = auth.ensure_valid()
    assert access.token == "a-2"
    api.refresh_token.assert_called_once_with(refresh_token="r-1")


def test_ensure_valid_reauth_when_refresh_fails(api, provider):
    api.auth_status.return_value = _status(200, "sukces")
    initial_until = datetime(2025, 7, 11, 12, 2, tzinfo=timezone.utc)
    api.redeem_token.return_value = TokenPair(
        access=AccessToken(token="a-1", valid_until=initial_until),
        refresh=RefreshToken(token="r-1", valid_until=initial_until + timedelta(hours=1)),
    )
    api.refresh_token.side_effect = RuntimeError("refresh fail")

    clock_now = datetime(2025, 7, 11, 12, tzinfo=timezone.utc)
    auth = KSefAuth(api, provider, sleep=lambda _: None, clock=lambda: clock_now)
    auth.authenticate()  # first auth
    api.get_challenge.reset_mock()

    access = auth.ensure_valid()
    # re-authenticated → full flow ran again
    api.get_challenge.assert_called_once()
    assert access.token == "a-1"  # redeem_token returns same mock


def test_ensure_valid_authenticates_if_never_logged_in(api, provider):
    api.auth_status.return_value = _status(200, "sukces")
    auth = KSefAuth(api, provider, sleep=lambda _: None)

    access = auth.ensure_valid()

    api.get_challenge.assert_called_once()
    assert access.token == "access-1"


def test_logout_clears_state(api, provider):
    api.auth_status.return_value = _status(200, "sukces")
    auth = KSefAuth(api, provider, sleep=lambda _: None)
    auth.authenticate()

    auth.logout()
    api.logout.assert_called_once_with(access_token="access-1")
    assert auth.current_access_token is None


def test_missing_token_encryption_cert_raises(api, provider):
    api.get_public_key_certificates.return_value = []
    auth = KSefAuth(api, provider, sleep=lambda _: None)
    with pytest.raises(KSefAuthError):
        auth.authenticate()


# ---- internal helper -----------------------------------------------------

def _status(code: int, description: str, *, details: list[str] | None = None) -> AuthOperationStatus:
    return AuthOperationStatus(
        start_date=datetime(2025, 7, 11, 12, tzinfo=timezone.utc),
        authentication_method="Token",
        code=code,
        description=description,
        details=details or [],
    )
