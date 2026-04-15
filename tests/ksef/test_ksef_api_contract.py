"""Contract tests for KSeFApiClient — mocked httpx via respx.

One test file per API. Scenarios per endpoint:
- Happy path (200/201/202/204) → typed dataclass
- 4xx → KSefApiError with error_code + message
- 5xx → KSefTransportError (after retries)
- 429 → respects Retry-After then success
- Timeout / transport → KSefTransportError
"""
from __future__ import annotations

import httpx
import pytest
import respx

from core.ksef.adapters.http import KSefHttp
from core.ksef.adapters.ksef_api import KSeFApiClient
from core.ksef.exceptions import KSefApiError, KSefTransportError
from core.ksef.models import (
    AccessToken,
    AuthChallenge,
    AuthInitResponse,
    AuthOperationStatus,
    InvoiceStatus,
    OnlineSession,
    PublicKeyCertificate,
    SendInvoiceAck,
    TokenPair,
    Upo,
)

BASE_URL = "https://api-demo.ksef.mf.gov.pl/v2"


# ---- Fixtures ------------------------------------------------------------

@pytest.fixture
def client(monkeypatch):
    """KSeFApiClient with fast httpx (no sleep on 429 retry-after inside tests)."""
    monkeypatch.setattr("core.ksef.adapters.http.time.sleep", lambda _: None)
    http_client = httpx.Client(base_url=BASE_URL, timeout=5.0)
    http = KSefHttp(BASE_URL, client=http_client)
    api = KSeFApiClient(http)
    yield api
    http.close()


@pytest.fixture
def api_error_payload():
    return {
        "exception": {
            "exceptionDetailList": [
                {
                    "exceptionCode": "21304",
                    "exceptionDescription": "Brak uwierzytelnienia.",
                    "details": ["Operacja nie została znaleziona."],
                }
            ]
        }
    }


def _sample_challenge_body() -> dict:
    return {
        "challenge": "20250514-CR-226FB7B000-3ACF9BE4C0-10",
        "timestamp": "2025-07-11T12:23:56.015430+00:00",
        "timestampMs": 1752236636015,
        "clientIp": "127.0.0.1",
    }


def _sample_auth_init_body() -> dict:
    return {
        "referenceNumber": "20250514-AU-2DFC46C000-3AC6D5877F-D4",
        "authenticationToken": {
            "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.payload.sig",
            "validUntil": "2025-07-11T12:23:56.015430+00:00",
        },
    }


def _sample_redeem_body() -> dict:
    return {
        "accessToken": {"token": "access-jwt", "validUntil": "2025-07-11T12:23:56.015430+00:00"},
        "refreshToken": {"token": "refresh-jwt", "validUntil": "2025-07-11T13:23:56.015430+00:00"},
    }


# ---- /security/public-key-certificates -----------------------------------

@respx.mock
def test_public_key_certificates_happy(client):
    respx.get(f"{BASE_URL}/security/public-key-certificates").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "certificate": "MIIBIjANBgkqhkig",
                    "validFrom": "2024-07-11T12:23:56.015430+00:00",
                    "validTo": "2028-07-11T12:23:56.015430+00:00",
                    "usage": ["KsefTokenEncryption", "SymmetricKeyEncryption"],
                }
            ],
        )
    )
    result = client.get_public_key_certificates()
    assert len(result) == 1
    cert = result[0]
    assert isinstance(cert, PublicKeyCertificate)
    assert "KsefTokenEncryption" in cert.usage


@respx.mock
def test_public_key_certificates_500_then_retry_exhausted(client):
    route = respx.get(f"{BASE_URL}/security/public-key-certificates").mock(
        return_value=httpx.Response(503, json={})
    )
    with pytest.raises(KSefTransportError):
        client.get_public_key_certificates()
    assert route.call_count == 3  # 3 retries


@respx.mock
def test_public_key_certificates_timeout(client):
    respx.get(f"{BASE_URL}/security/public-key-certificates").mock(
        side_effect=httpx.ConnectTimeout("timeout")
    )
    with pytest.raises(KSefTransportError):
        client.get_public_key_certificates()


# ---- /auth/challenge ------------------------------------------------------

@respx.mock
def test_challenge_happy(client):
    respx.post(f"{BASE_URL}/auth/challenge").mock(
        return_value=httpx.Response(200, json=_sample_challenge_body())
    )
    ch = client.get_challenge()
    assert isinstance(ch, AuthChallenge)
    assert ch.challenge == "20250514-CR-226FB7B000-3ACF9BE4C0-10"
    assert ch.timestamp_ms == 1752236636015


@respx.mock
def test_challenge_400(client, api_error_payload):
    respx.post(f"{BASE_URL}/auth/challenge").mock(
        return_value=httpx.Response(400, json=api_error_payload)
    )
    with pytest.raises(KSefApiError) as exc_info:
        client.get_challenge()
    assert exc_info.value.status_code == 400
    assert exc_info.value.error_code == "21304"


@respx.mock
def test_challenge_429_then_success(client):
    responses = [
        httpx.Response(429, headers={"Retry-After": "0"}, json={}),
        httpx.Response(200, json=_sample_challenge_body()),
    ]
    respx.post(f"{BASE_URL}/auth/challenge").mock(side_effect=responses)
    ch = client.get_challenge()
    assert ch.challenge.startswith("20250514-CR")


@respx.mock
def test_challenge_5xx_retry_exhausted(client):
    route = respx.post(f"{BASE_URL}/auth/challenge").mock(
        return_value=httpx.Response(500, json={})
    )
    with pytest.raises(KSefTransportError):
        client.get_challenge()
    assert route.call_count == 3


# ---- /auth/ksef-token -----------------------------------------------------

@respx.mock
def test_auth_with_token_happy(client):
    respx.post(f"{BASE_URL}/auth/ksef-token").mock(
        return_value=httpx.Response(202, json=_sample_auth_init_body())
    )
    result = client.auth_with_token(
        challenge="ch", nip="5260250274", encrypted_token_b64="enc=="
    )
    assert isinstance(result, AuthInitResponse)
    assert result.reference_number.startswith("20250514-AU")
    assert result.authentication_token.token.startswith("eyJ")


@respx.mock
def test_auth_with_token_400(client, api_error_payload):
    respx.post(f"{BASE_URL}/auth/ksef-token").mock(
        return_value=httpx.Response(400, json=api_error_payload)
    )
    with pytest.raises(KSefApiError):
        client.auth_with_token(challenge="c", nip="123", encrypted_token_b64="x")


@respx.mock
def test_auth_with_token_401(client):
    respx.post(f"{BASE_URL}/auth/ksef-token").mock(
        return_value=httpx.Response(
            401, json={"title": "Unauthorized", "detail": "Invalid token"}
        )
    )
    with pytest.raises(KSefApiError) as exc_info:
        client.auth_with_token(challenge="c", nip="123", encrypted_token_b64="x")
    assert exc_info.value.status_code == 401


@respx.mock
def test_auth_with_token_503(client):
    respx.post(f"{BASE_URL}/auth/ksef-token").mock(
        return_value=httpx.Response(503, json={})
    )
    with pytest.raises(KSefTransportError):
        client.auth_with_token(challenge="c", nip="123", encrypted_token_b64="x")


# ---- /auth/{referenceNumber} ---------------------------------------------

@respx.mock
def test_auth_status_in_progress(client):
    respx.get(f"{BASE_URL}/auth/REF-1").mock(
        return_value=httpx.Response(
            200,
            json={
                "startDate": "2025-07-11T12:23:56.015430+00:00",
                "authenticationMethod": "Token",
                "status": {"code": 100, "description": "Uwierzytelnianie w toku"},
            },
        )
    )
    st = client.auth_status("REF-1", auth_op_token="op")
    assert isinstance(st, AuthOperationStatus)
    assert st.in_progress


@respx.mock
def test_auth_status_success(client):
    respx.get(f"{BASE_URL}/auth/REF-1").mock(
        return_value=httpx.Response(
            200,
            json={
                "startDate": "2025-07-11T12:23:56.015430+00:00",
                "authenticationMethod": "Token",
                "status": {"code": 200, "description": "Sukces"},
            },
        )
    )
    st = client.auth_status("REF-1", auth_op_token="op")
    assert st.success


@respx.mock
def test_auth_status_failed(client):
    respx.get(f"{BASE_URL}/auth/REF-1").mock(
        return_value=httpx.Response(
            200,
            json={
                "startDate": "2025-07-11T12:23:56.015430+00:00",
                "authenticationMethod": "Token",
                "status": {"code": 400, "description": "Błąd", "details": ["Nieważny certyfikat."]},
            },
        )
    )
    st = client.auth_status("REF-1", auth_op_token="op")
    assert st.failed
    assert st.details == ["Nieważny certyfikat."]


@respx.mock
def test_auth_status_410_gone(client):
    respx.get(f"{BASE_URL}/auth/REF-GONE").mock(
        return_value=httpx.Response(410, json={"detail": "Operacja wygasła"})
    )
    with pytest.raises(KSefApiError) as exc_info:
        client.auth_status("REF-GONE", auth_op_token="op")
    assert exc_info.value.status_code == 410


@respx.mock
def test_auth_status_401(client):
    respx.get(f"{BASE_URL}/auth/REF-1").mock(
        return_value=httpx.Response(401, json={"detail": "Unauthorized"})
    )
    with pytest.raises(KSefApiError):
        client.auth_status("REF-1", auth_op_token="op")


# ---- /auth/token/redeem --------------------------------------------------

@respx.mock
def test_redeem_token_happy(client):
    respx.post(f"{BASE_URL}/auth/token/redeem").mock(
        return_value=httpx.Response(200, json=_sample_redeem_body())
    )
    pair = client.redeem_token(auth_op_token="op")
    assert isinstance(pair, TokenPair)
    assert pair.access.token == "access-jwt"
    assert pair.refresh.token == "refresh-jwt"


@respx.mock
def test_redeem_token_400_already_redeemed(client, api_error_payload):
    respx.post(f"{BASE_URL}/auth/token/redeem").mock(
        return_value=httpx.Response(400, json=api_error_payload)
    )
    with pytest.raises(KSefApiError):
        client.redeem_token(auth_op_token="op")


@respx.mock
def test_redeem_token_timeout(client):
    respx.post(f"{BASE_URL}/auth/token/redeem").mock(
        side_effect=httpx.ReadTimeout("timeout")
    )
    with pytest.raises(KSefTransportError):
        client.redeem_token(auth_op_token="op")


# ---- /auth/token/refresh -------------------------------------------------

@respx.mock
def test_refresh_token_happy(client):
    respx.post(f"{BASE_URL}/auth/token/refresh").mock(
        return_value=httpx.Response(
            200,
            json={
                "accessToken": {
                    "token": "new-access",
                    "validUntil": "2025-07-11T14:00:00+00:00",
                }
            },
        )
    )
    access = client.refresh_token(refresh_token="r")
    assert isinstance(access, AccessToken)
    assert access.token == "new-access"


@respx.mock
def test_refresh_token_400(client, api_error_payload):
    respx.post(f"{BASE_URL}/auth/token/refresh").mock(
        return_value=httpx.Response(400, json=api_error_payload)
    )
    with pytest.raises(KSefApiError):
        client.refresh_token(refresh_token="r")


@respx.mock
def test_refresh_token_429_then_success(client):
    respx.post(f"{BASE_URL}/auth/token/refresh").mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "0"}, json={}),
            httpx.Response(
                200,
                json={
                    "accessToken": {
                        "token": "new-access",
                        "validUntil": "2025-07-11T14:00:00+00:00",
                    }
                },
            ),
        ]
    )
    access = client.refresh_token(refresh_token="r")
    assert access.token == "new-access"


# ---- DELETE /auth/sessions/current ---------------------------------------

@respx.mock
def test_logout_happy(client):
    route = respx.delete(f"{BASE_URL}/auth/sessions/current").mock(
        return_value=httpx.Response(204)
    )
    client.logout(access_token="a")
    assert route.called


@respx.mock
def test_logout_401(client):
    respx.delete(f"{BASE_URL}/auth/sessions/current").mock(
        return_value=httpx.Response(401, json={"detail": "Unauthorized"})
    )
    with pytest.raises(KSefApiError):
        client.logout(access_token="a")


@respx.mock
def test_logout_500(client):
    respx.delete(f"{BASE_URL}/auth/sessions/current").mock(
        return_value=httpx.Response(500, json={})
    )
    with pytest.raises(KSefTransportError):
        client.logout(access_token="a")


# ---- POST /sessions/online -----------------------------------------------

@respx.mock
def test_open_online_session_happy(client):
    respx.post(f"{BASE_URL}/sessions/online").mock(
        return_value=httpx.Response(
            201,
            json={
                "referenceNumber": "20250625-SO-2C3E6C8000-B675CF5D68-07",
                "validUntil": "2025-07-11T12:23:56.015430+00:00",
            },
        )
    )
    session = client.open_online_session(
        access_token="a",
        form_code={"systemCode": "FA (3)", "schemaVersion": "1-0E", "value": "FA"},
        encryption={"encryptedSymmetricKey": "...", "initializationVector": "..."},
    )
    assert isinstance(session, OnlineSession)
    assert session.reference_number.startswith("20250625-SO")


@respx.mock
def test_open_online_session_400(client, api_error_payload):
    respx.post(f"{BASE_URL}/sessions/online").mock(
        return_value=httpx.Response(400, json=api_error_payload)
    )
    with pytest.raises(KSefApiError):
        client.open_online_session(access_token="a", form_code={}, encryption={})


@respx.mock
def test_open_online_session_403(client):
    respx.post(f"{BASE_URL}/sessions/online").mock(
        return_value=httpx.Response(403, json={"detail": "Forbidden"})
    )
    with pytest.raises(KSefApiError) as exc_info:
        client.open_online_session(access_token="a", form_code={}, encryption={})
    assert exc_info.value.status_code == 403


@respx.mock
def test_open_online_session_timeout(client):
    respx.post(f"{BASE_URL}/sessions/online").mock(
        side_effect=httpx.ConnectError("conn")
    )
    with pytest.raises(KSefTransportError):
        client.open_online_session(access_token="a", form_code={}, encryption={})


# ---- POST /sessions/online/{ref}/invoices --------------------------------

@respx.mock
def test_send_invoice_happy(client):
    respx.post(f"{BASE_URL}/sessions/online/SESSION-1/invoices").mock(
        return_value=httpx.Response(
            202, json={"referenceNumber": "20250625-EE-319D7EE000-B67F415CDC-2C"}
        )
    )
    ack = client.send_invoice(
        access_token="a",
        session_ref="SESSION-1",
        payload={
            "invoiceHash": "x",
            "invoiceSize": 100,
            "encryptedInvoiceHash": "x",
            "encryptedInvoiceSize": 100,
            "encryptedInvoiceContent": "...",
        },
    )
    assert isinstance(ack, SendInvoiceAck)
    assert ack.reference_number.startswith("20250625-EE")


@respx.mock
def test_send_invoice_400(client, api_error_payload):
    respx.post(f"{BASE_URL}/sessions/online/SESSION-1/invoices").mock(
        return_value=httpx.Response(400, json=api_error_payload)
    )
    with pytest.raises(KSefApiError):
        client.send_invoice(access_token="a", session_ref="SESSION-1", payload={})


@respx.mock
def test_send_invoice_429_then_success(client):
    respx.post(f"{BASE_URL}/sessions/online/SESSION-1/invoices").mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "0"}, json={}),
            httpx.Response(202, json={"referenceNumber": "OK"}),
        ]
    )
    ack = client.send_invoice(access_token="a", session_ref="SESSION-1", payload={})
    assert ack.reference_number == "OK"


# ---- POST /sessions/online/{ref}/close -----------------------------------

@respx.mock
def test_close_online_session_happy(client):
    route = respx.post(f"{BASE_URL}/sessions/online/SESSION-1/close").mock(
        return_value=httpx.Response(204)
    )
    client.close_online_session(access_token="a", session_ref="SESSION-1")
    assert route.called


@respx.mock
def test_close_online_session_404(client):
    respx.post(f"{BASE_URL}/sessions/online/SESSION-1/close").mock(
        return_value=httpx.Response(404, json={"detail": "Not found"})
    )
    with pytest.raises(KSefApiError) as exc_info:
        client.close_online_session(access_token="a", session_ref="SESSION-1")
    assert exc_info.value.status_code == 404


@respx.mock
def test_close_online_session_500(client):
    respx.post(f"{BASE_URL}/sessions/online/SESSION-1/close").mock(
        return_value=httpx.Response(500, json={})
    )
    with pytest.raises(KSefTransportError):
        client.close_online_session(access_token="a", session_ref="SESSION-1")


# ---- GET /sessions/{ref}/invoices/{invoiceRef} ---------------------------

@respx.mock
def test_invoice_status_happy(client):
    respx.get(f"{BASE_URL}/sessions/SESSION-1/invoices/INV-1").mock(
        return_value=httpx.Response(
            200,
            json={
                "ordinalNumber": 2,
                "referenceNumber": "INV-1",
                "invoicingDate": "2025-07-11T12:23:56.015430+00:00",
                "ksefNumber": "5265877635-20250626-010080DD2B5E-26",
                "status": {"code": 200, "description": "Przetworzona"},
            },
        )
    )
    status = client.invoice_status(
        access_token="a", session_ref="SESSION-1", invoice_ref="INV-1"
    )
    assert isinstance(status, InvoiceStatus)
    assert status.status_code == 200
    assert status.ksef_number is not None


@respx.mock
def test_invoice_status_400(client, api_error_payload):
    respx.get(f"{BASE_URL}/sessions/SESSION-1/invoices/INV-1").mock(
        return_value=httpx.Response(400, json=api_error_payload)
    )
    with pytest.raises(KSefApiError):
        client.invoice_status(access_token="a", session_ref="SESSION-1", invoice_ref="INV-1")


@respx.mock
def test_invoice_status_timeout(client):
    respx.get(f"{BASE_URL}/sessions/SESSION-1/invoices/INV-1").mock(
        side_effect=httpx.ReadTimeout("t")
    )
    with pytest.raises(KSefTransportError):
        client.invoice_status(access_token="a", session_ref="SESSION-1", invoice_ref="INV-1")


# ---- GET UPO -------------------------------------------------------------

@respx.mock
def test_get_upo_happy(client):
    ksef_number = "5265877635-20250626-010080DD2B5E-26"
    respx.get(
        f"{BASE_URL}/sessions/SESSION-1/invoices/ksef/{ksef_number}/upo"
    ).mock(
        return_value=httpx.Response(
            200,
            content=b"<UPO>...</UPO>",
            headers={"content-type": "application/xml"},
        )
    )
    upo = client.get_upo_by_ksef_number(
        access_token="a", session_ref="SESSION-1", ksef_number=ksef_number
    )
    assert isinstance(upo, Upo)
    assert upo.content.startswith(b"<UPO>")
    assert "xml" in upo.content_type


@respx.mock
def test_get_upo_400(client, api_error_payload):
    respx.get(f"{BASE_URL}/sessions/SESSION-1/invoices/ksef/KS-1/upo").mock(
        return_value=httpx.Response(400, json=api_error_payload)
    )
    with pytest.raises(KSefApiError):
        client.get_upo_by_ksef_number(
            access_token="a", session_ref="SESSION-1", ksef_number="KS-1"
        )


@respx.mock
def test_get_upo_429_then_success(client):
    respx.get(f"{BASE_URL}/sessions/SESSION-1/invoices/ksef/KS-1/upo").mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "0"}, json={}),
            httpx.Response(200, content=b"<UPO/>", headers={"content-type": "application/xml"}),
        ]
    )
    upo = client.get_upo_by_ksef_number(
        access_token="a", session_ref="SESSION-1", ksef_number="KS-1"
    )
    assert upo.content == b"<UPO/>"
