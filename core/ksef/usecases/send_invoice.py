"""SendInvoice use case — full e2e flow: auth -> session -> encrypt -> send -> poll -> UPO -> close.

One document = one session. No retry logic — caller decides.
State transitions logged via ShipmentRepository (audit trail).
"""
from __future__ import annotations

import hashlib
import logging
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Callable

from core.ksef.adapters.encryption import KSeFEncryption
from core.ksef.adapters.ksef_api import KSeFApiClient
from core.ksef.adapters.ksef_auth import KSefAuth
from core.ksef.adapters.repo import ShipmentRepository
from core.ksef.domain.shipment import ShipmentStatus
from core.ksef.exceptions import KSefError
from core.ksef.models import InvoiceStatus

_LOG = logging.getLogger("ksef.send")

_FORM_CODE = {"systemCode": "FA (3)", "schemaVersion": "1-0E", "value": "FA"}

_POLL_INITIAL_S = 2.0
_POLL_MAX_S = 8.0
_DEFAULT_POLL_TIMEOUT_S = 120.0


@dataclass(frozen=True)
class SendResult:
    """Wynik wysylki — wszystko co caller potrzebuje."""

    wysylka_id: int
    ksef_number: str | None
    upo_path: Path | None
    status: ShipmentStatus


class SendInvoiceUseCase:
    """Orchestrates sending a single invoice to KSeF."""

    def __init__(
        self,
        api: KSeFApiClient,
        auth: KSefAuth,
        repo: ShipmentRepository,
        encryption: KSeFEncryption,
        *,
        poll_timeout_s: float = _DEFAULT_POLL_TIMEOUT_S,
        upo_dir: Path = Path("output/ksef/upo"),
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._api = api
        self._auth = auth
        self._repo = repo
        self._encryption = encryption
        self._poll_timeout = poll_timeout_s
        self._upo_dir = upo_dir
        self._sleep = sleep

    def execute(
        self,
        xml_path: Path,
        gid: int,
        rodzaj: str,
        nr_faktury: str,
        data_wystawienia: date,
    ) -> SendResult:
        """Full send flow. Returns SendResult with terminal status."""
        if self._repo.has_pending_or_sent(gid, rodzaj):
            existing = self._repo.get_latest(gid, rodzaj)
            _LOG.info('{"event": "send_skip_idempotent", "gid": %d, "rodzaj": "%s"}', gid, rodzaj)
            return SendResult(
                wysylka_id=existing.id if existing else 0,
                ksef_number=existing.ksef_number if existing else None,
                upo_path=Path(existing.upo_path) if existing and existing.upo_path else None,
                status=existing.status if existing else ShipmentStatus.ERROR,
            )

        xml_bytes = xml_path.read_bytes()
        xml_hash = hashlib.sha256(xml_bytes).hexdigest()

        wysylka = self._repo.create(
            gid_erp=gid, rodzaj=rodzaj, nr_faktury=nr_faktury,
            data_wystawienia=data_wystawienia, xml_path=str(xml_path),
            xml_hash=xml_hash,
        )
        wid = wysylka.id
        self._repo.transition(wid, ShipmentStatus.QUEUED)

        session_ref: str | None = None
        access_token: str | None = None
        try:
            access = self._auth.ensure_valid()
            access_token = access.token
            self._repo.transition(wid, ShipmentStatus.AUTH_PENDING)

            session_enc = self._encryption.prepare_session()
            session = self._api.open_online_session(
                access_token=access_token,
                form_code=_FORM_CODE,
                encryption={
                    "encryptedSymmetricKey": session_enc.encrypted_key_b64,
                    "initializationVector": session_enc.iv_b64,
                },
            )
            session_ref = session.reference_number

            encrypted = self._encryption.encrypt_invoice(xml_bytes, session_enc)
            payload = {
                "invoiceHash": encrypted.plain_hash_b64,
                "invoiceSize": encrypted.plain_size,
                "encryptedInvoiceHash": encrypted.encrypted_hash_b64,
                "encryptedInvoiceSize": encrypted.encrypted_size,
                "encryptedInvoiceContent": encrypted.encrypted_content_b64,
            }
            ack = self._api.send_invoice(
                access_token=access_token,
                session_ref=session_ref,
                payload=payload,
            )
            invoice_ref = ack.reference_number
            self._repo.transition(
                wid, ShipmentStatus.SENT,
                ksef_session_ref=session_ref,
                ksef_invoice_ref=invoice_ref,
            )
            _LOG.info(
                '{"event": "invoice_sent", "wid": %d, "session_ref": "%s", "invoice_ref": "%s"}',
                wid, session_ref, invoice_ref,
            )

            result = self._poll_invoice(access_token, session_ref, invoice_ref)
            if result.ksef_number:
                upo_path = self._fetch_upo(access_token, session_ref, result.ksef_number)
                self._repo.transition(
                    wid, ShipmentStatus.ACCEPTED,
                    ksef_number=result.ksef_number,
                    upo_path=str(upo_path) if upo_path else None,
                )
                return SendResult(wid, result.ksef_number, upo_path, ShipmentStatus.ACCEPTED)
            else:
                self._repo.transition(
                    wid, ShipmentStatus.REJECTED,
                    error_msg=result.status_description,
                )
                return SendResult(wid, None, None, ShipmentStatus.REJECTED)

        except KSefError as exc:
            _LOG.error('{"event": "send_error", "wid": %d, "error": "%s"}', wid, exc)
            self._repo.transition(
                wid, ShipmentStatus.ERROR,
                error_msg=str(exc)[:500],
            )
            return SendResult(wid, None, None, ShipmentStatus.ERROR)
        finally:
            self._close_session(access_token, session_ref)

    def _poll_invoice(
        self, access_token: str, session_ref: str, invoice_ref: str,
    ) -> InvoiceStatus:
        """Poll invoice status until terminal. Returns InvoiceStatus."""
        deadline = time.monotonic() + self._poll_timeout
        interval = _POLL_INITIAL_S
        while True:
            status = self._api.invoice_status(
                access_token=access_token,
                session_ref=session_ref,
                invoice_ref=invoice_ref,
            )
            if status.status_code == 200 or status.ksef_number:
                return status
            if status.status_code >= 400:
                return status
            if time.monotonic() >= deadline:
                raise KSefError(f"Invoice status polling timeout after {self._poll_timeout}s")
            self._sleep(interval)
            interval = min(interval * 2, _POLL_MAX_S)

    def _fetch_upo(
        self, access_token: str, session_ref: str, ksef_number: str,
    ) -> Path | None:
        """Fetch UPO and save to disk. Returns path or None on failure."""
        try:
            upo = self._api.get_upo_by_ksef_number(
                access_token=access_token,
                session_ref=session_ref,
                ksef_number=ksef_number,
            )
            self._upo_dir.mkdir(parents=True, exist_ok=True)
            path = self._upo_dir / f"{ksef_number}.xml"
            path.write_bytes(upo.content)
            _LOG.info('{"event": "upo_saved", "path": "%s"}', path)
            return path
        except Exception as exc:
            _LOG.warning('{"event": "upo_fetch_failed", "error": "%s"}', exc)
            return None

    def _close_session(
        self, access_token: str | None, session_ref: str | None,
    ) -> None:
        """Best-effort session close."""
        if not access_token or not session_ref:
            return
        try:
            self._api.close_online_session(
                access_token=access_token, session_ref=session_ref,
            )
            _LOG.info('{"event": "session_closed", "ref": "%s"}', session_ref)
        except Exception as exc:
            _LOG.warning('{"event": "session_close_failed", "error": "%s"}', exc)
