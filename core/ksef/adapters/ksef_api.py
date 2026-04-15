"""KSeF 2.0 API client — one method per endpoint, typed dataclass results.

Scope (Block 1): auth + online session primitives only. No XML content logic,
no DB, no retries on top of KSefHttp.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from core.ksef.adapters.http import KSefHttp
from core.ksef.models import (
    AccessToken,
    AuthChallenge,
    AuthInitResponse,
    AuthOperationStatus,
    AuthOperationToken,
    InvoiceStatus,
    OnlineSession,
    PublicKeyCertificate,
    RefreshToken,
    SendInvoiceAck,
    TokenPair,
    Upo,
)


def _parse_dt(value: str) -> datetime:
    """Parse ISO-8601 (with or without trailing 'Z'; fractional seconds allowed)."""
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class KSeFApiClient:
    """Thin typed wrapper around KSeF 2.0 REST endpoints."""

    def __init__(self, http: KSefHttp) -> None:
        self._http = http

    # ---- Public-key certificates -----------------------------------

    def get_public_key_certificates(self) -> list[PublicKeyCertificate]:
        data = self._http.request_json(
            "GET", "/security/public-key-certificates", expected_statuses=(200,)
        )
        return [
            PublicKeyCertificate(
                certificate_b64=item["certificate"],
                valid_from=_parse_dt(item["validFrom"]),
                valid_to=_parse_dt(item["validTo"]),
                usage=list(item.get("usage") or []),
            )
            for item in data
        ]

    # ---- Auth ------------------------------------------------------

    def get_challenge(self) -> AuthChallenge:
        data = self._http.request_json("POST", "/auth/challenge", expected_statuses=(200,))
        return AuthChallenge(
            challenge=data["challenge"],
            timestamp=_parse_dt(data["timestamp"]),
            timestamp_ms=int(data["timestampMs"]),
        )

    def auth_with_token(
        self,
        *,
        challenge: str,
        nip: str,
        encrypted_token_b64: str,
    ) -> AuthInitResponse:
        body: dict[str, Any] = {
            "challenge": challenge,
            "contextIdentifier": {"type": "Nip", "value": nip},
            "encryptedToken": encrypted_token_b64,
        }
        data = self._http.request_json(
            "POST", "/auth/ksef-token", json_body=body, expected_statuses=(202,)
        )
        return _parse_auth_init(data)


    def auth_status(self, reference_number: str, *, auth_op_token: str) -> AuthOperationStatus:
        data = self._http.request_json(
            "GET",
            f"/auth/{reference_number}",
            bearer=auth_op_token,
            expected_statuses=(200,),
        )
        status = data.get("status") or {}
        return AuthOperationStatus(
            start_date=_parse_dt(data["startDate"]),
            authentication_method=str(data.get("authenticationMethod") or ""),
            code=int(status.get("code") or 0),
            description=str(status.get("description") or ""),
            details=[str(x) for x in (status.get("details") or [])],
        )

    def redeem_token(self, *, auth_op_token: str) -> TokenPair:
        data = self._http.request_json(
            "POST", "/auth/token/redeem", bearer=auth_op_token, expected_statuses=(200,)
        )
        access = data["accessToken"]
        refresh = data["refreshToken"]
        return TokenPair(
            access=AccessToken(token=access["token"], valid_until=_parse_dt(access["validUntil"])),
            refresh=RefreshToken(token=refresh["token"], valid_until=_parse_dt(refresh["validUntil"])),
        )

    def refresh_token(self, *, refresh_token: str) -> AccessToken:
        data = self._http.request_json(
            "POST", "/auth/token/refresh", bearer=refresh_token, expected_statuses=(200,)
        )
        access = data["accessToken"]
        return AccessToken(token=access["token"], valid_until=_parse_dt(access["validUntil"]))

    def logout(self, *, access_token: str) -> None:
        """DELETE /auth/sessions/current — invalidate current auth session."""
        self._http.request_empty(
            "DELETE",
            "/auth/sessions/current",
            bearer=access_token,
            expected_statuses=(204,),
        )

    # ---- Online session --------------------------------------------

    def open_online_session(
        self,
        *,
        access_token: str,
        form_code: dict[str, str],
        encryption: dict[str, str],
    ) -> OnlineSession:
        """POST /sessions/online.

        `form_code` example: {"systemCode": "FA (3)", "schemaVersion": "1-0E", "value": "FA"}.
        `encryption` example: {"encryptedSymmetricKey": "...", "initializationVector": "..."}.
        """
        body = {"formCode": form_code, "encryption": encryption}
        data = self._http.request_json(
            "POST",
            "/sessions/online",
            bearer=access_token,
            json_body=body,
            expected_statuses=(201,),
        )
        return OnlineSession(
            reference_number=data["referenceNumber"],
            valid_until=_parse_dt(data["validUntil"]),
        )

    def send_invoice(
        self,
        *,
        access_token: str,
        session_ref: str,
        payload: dict[str, Any],
    ) -> SendInvoiceAck:
        """POST /sessions/online/{ref}/invoices. `payload` is passed through as-is."""
        data = self._http.request_json(
            "POST",
            f"/sessions/online/{session_ref}/invoices",
            bearer=access_token,
            json_body=payload,
            expected_statuses=(202,),
        )
        return SendInvoiceAck(reference_number=data["referenceNumber"])

    def close_online_session(self, *, access_token: str, session_ref: str) -> None:
        self._http.request_empty(
            "POST",
            f"/sessions/online/{session_ref}/close",
            bearer=access_token,
            expected_statuses=(204,),
        )

    def invoice_status(
        self,
        *,
        access_token: str,
        session_ref: str,
        invoice_ref: str,
    ) -> InvoiceStatus:
        data = self._http.request_json(
            "GET",
            f"/sessions/{session_ref}/invoices/{invoice_ref}",
            bearer=access_token,
            expected_statuses=(200,),
        )
        status = data.get("status") or {}
        return InvoiceStatus(
            reference_number=data.get("referenceNumber") or invoice_ref,
            ksef_number=data.get("ksefNumber"),
            status_code=int(status.get("code") or 0),
            status_description=str(status.get("description") or ""),
            details=[str(x) for x in (status.get("details") or [])],
        )

    def get_upo_by_ksef_number(
        self,
        *,
        access_token: str,
        session_ref: str,
        ksef_number: str,
    ) -> Upo:
        content, ctype = self._http.request_bytes(
            "GET",
            f"/sessions/{session_ref}/invoices/ksef/{ksef_number}/upo",
            bearer=access_token,
            expected_statuses=(200,),
        )
        return Upo(content=content, content_type=ctype)


def _parse_auth_init(data: dict[str, Any]) -> AuthInitResponse:
    token = data["authenticationToken"]
    return AuthInitResponse(
        reference_number=data["referenceNumber"],
        authentication_token=AuthOperationToken(
            token=token["token"],
            valid_until=_parse_dt(token["validUntil"]),
        ),
    )
