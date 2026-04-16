"""Contract tests SendInvoiceUseCase — full mock orchestration."""
from __future__ import annotations

import hashlib
from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from core.ksef.adapters.encryption import EncryptedInvoice, SessionEncryption
from core.ksef.domain.shipment import ShipmentStatus, Wysylka
from core.ksef.exceptions import KSefApiError, KSefAuthError
from core.ksef.models import (
    AccessToken,
    InvoiceStatus,
    OnlineSession,
    SendInvoiceAck,
    Upo,
)
from core.ksef.usecases.send_invoice import SendInvoiceUseCase, SendResult


# ---- fixtures ----------------------------------------------------------------

_NOW = datetime(2026, 4, 16, 12, 0, 0, tzinfo=timezone.utc)
_XML = b"<Faktura>test</Faktura>"
_XML_HASH = hashlib.sha256(_XML).hexdigest()
_GID = 59
_RODZAJ = "FS"
_NR = "FS-59/04/2026"
_DATA = date(2026, 4, 14)

_ACCESS = AccessToken(token="acc-token-123", valid_until=_NOW)
_SESSION = OnlineSession(reference_number="ses-ref-001", valid_until=_NOW)
_ACK = SendInvoiceAck(reference_number="inv-ref-001")
_STATUS_ACCEPTED = InvoiceStatus(
    reference_number="inv-ref-001",
    ksef_number="1234567890-20260414-ABC-D01-23",
    status_code=200,
    status_description="Accepted",
)
_STATUS_REJECTED = InvoiceStatus(
    reference_number="inv-ref-001",
    ksef_number=None,
    status_code=400,
    status_description="Invalid format",
)
_STATUS_PENDING = InvoiceStatus(
    reference_number="inv-ref-001",
    ksef_number=None,
    status_code=100,
    status_description="Processing",
)
_UPO = Upo(content=b"<UPO>receipt</UPO>", content_type="application/xml")
_SESSION_ENC = SessionEncryption(
    symmetric_key=b"\x00" * 32,
    iv=b"\x00" * 16,
    encrypted_key_b64="AAAA",
    iv_b64="BBBB",
)
_ENCRYPTED = EncryptedInvoice(
    encrypted_content_b64="ZW5jcnlwdGVk",
    encrypted_hash_b64="aGFzaA==",
    encrypted_size=100,
    plain_hash_b64="cGxhaW4=",
    plain_size=len(_XML),
)


def _make_wysylka(
    wid: int = 1,
    status: ShipmentStatus = ShipmentStatus.DRAFT,
    ksef_number: str | None = None,
    upo_path: str | None = None,
) -> Wysylka:
    return Wysylka(
        id=wid, gid_erp=_GID, rodzaj=_RODZAJ, nr_faktury=_NR,
        data_wystawienia=_DATA, xml_path="test.xml", xml_hash=_XML_HASH,
        status=status, ksef_session_ref=None, ksef_invoice_ref=None,
        ksef_number=ksef_number, upo_path=upo_path,
        error_code=None, error_msg=None, attempt=1,
        created_at=_NOW, queued_at=None, sent_at=None,
        accepted_at=None, rejected_at=None, errored_at=None,
    )


@pytest.fixture
def mocks(tmp_path: Path):
    xml_file = tmp_path / "test.xml"
    xml_file.write_bytes(_XML)
    upo_dir = tmp_path / "upo"

    api = MagicMock()
    auth = MagicMock()
    repo = MagicMock()
    encryption = MagicMock()

    auth.ensure_valid.return_value = _ACCESS
    api.open_online_session.return_value = _SESSION
    api.send_invoice.return_value = _ACK
    encryption.prepare_session.return_value = _SESSION_ENC
    encryption.encrypt_invoice.return_value = _ENCRYPTED

    # repo defaults
    repo.has_pending_or_sent.return_value = False
    _draft = _make_wysylka(1, ShipmentStatus.DRAFT)
    repo.create.return_value = _draft
    repo.transition.return_value = _draft  # simplified

    uc = SendInvoiceUseCase(
        api=api, auth=auth, repo=repo, encryption=encryption,
        upo_dir=upo_dir, sleep=lambda _: None,
    )
    return uc, api, auth, repo, encryption, xml_file, upo_dir


# ---- happy path --------------------------------------------------------------

def test_send_happy_path_transitions_to_accepted(mocks):
    uc, api, auth, repo, enc, xml_file, upo_dir = mocks
    api.invoice_status.return_value = _STATUS_ACCEPTED
    api.get_upo_by_ksef_number.return_value = _UPO

    result = uc.execute(xml_file, _GID, _RODZAJ, _NR, _DATA)

    assert result.status == ShipmentStatus.ACCEPTED
    assert result.ksef_number == _STATUS_ACCEPTED.ksef_number
    assert result.upo_path is not None
    assert result.upo_path.exists()


def test_send_creates_draft_then_queued(mocks):
    uc, api, auth, repo, enc, xml_file, upo_dir = mocks
    api.invoice_status.return_value = _STATUS_ACCEPTED
    api.get_upo_by_ksef_number.return_value = _UPO

    uc.execute(xml_file, _GID, _RODZAJ, _NR, _DATA)

    repo.create.assert_called_once()
    transition_statuses = [call.args[1] for call in repo.transition.call_args_list]
    assert ShipmentStatus.QUEUED in transition_statuses
    assert ShipmentStatus.AUTH_PENDING in transition_statuses
    assert ShipmentStatus.SENT in transition_statuses
    assert ShipmentStatus.ACCEPTED in transition_statuses


# ---- idempotency -------------------------------------------------------------

def test_send_idempotent_skip_when_already_sent(mocks):
    uc, api, auth, repo, enc, xml_file, upo_dir = mocks
    repo.has_pending_or_sent.return_value = True
    existing = _make_wysylka(5, ShipmentStatus.ACCEPTED, ksef_number="KSeF-123")
    repo.get_latest.return_value = existing

    result = uc.execute(xml_file, _GID, _RODZAJ, _NR, _DATA)

    assert result.status == ShipmentStatus.ACCEPTED
    assert result.wysylka_id == 5
    repo.create.assert_not_called()
    api.send_invoice.assert_not_called()


# ---- rejection ---------------------------------------------------------------

def test_send_rejected_transitions_to_rejected(mocks):
    uc, api, auth, repo, enc, xml_file, upo_dir = mocks
    api.invoice_status.return_value = _STATUS_REJECTED

    result = uc.execute(xml_file, _GID, _RODZAJ, _NR, _DATA)

    assert result.status == ShipmentStatus.REJECTED
    assert result.ksef_number is None
    transition_statuses = [call.args[1] for call in repo.transition.call_args_list]
    assert ShipmentStatus.REJECTED in transition_statuses


# ---- errors ------------------------------------------------------------------

def test_send_api_error_transitions_to_error(mocks):
    uc, api, auth, repo, enc, xml_file, upo_dir = mocks
    api.send_invoice.side_effect = KSefApiError(500, "ERR", "server error")

    result = uc.execute(xml_file, _GID, _RODZAJ, _NR, _DATA)

    assert result.status == ShipmentStatus.ERROR
    transition_statuses = [call.args[1] for call in repo.transition.call_args_list]
    assert ShipmentStatus.ERROR in transition_statuses


def test_send_auth_failure_transitions_to_error(mocks):
    uc, api, auth, repo, enc, xml_file, upo_dir = mocks
    auth.ensure_valid.side_effect = KSefAuthError("auth failed")

    result = uc.execute(xml_file, _GID, _RODZAJ, _NR, _DATA)

    assert result.status == ShipmentStatus.ERROR


# ---- session close -----------------------------------------------------------

def test_send_closes_session_on_success(mocks):
    uc, api, auth, repo, enc, xml_file, upo_dir = mocks
    api.invoice_status.return_value = _STATUS_ACCEPTED
    api.get_upo_by_ksef_number.return_value = _UPO

    uc.execute(xml_file, _GID, _RODZAJ, _NR, _DATA)

    api.close_online_session.assert_called_once()


def test_send_closes_session_on_error(mocks):
    uc, api, auth, repo, enc, xml_file, upo_dir = mocks
    api.send_invoice.side_effect = KSefApiError(500, "ERR", "fail")

    uc.execute(xml_file, _GID, _RODZAJ, _NR, _DATA)

    api.close_online_session.assert_called_once()


# ---- UPO ---------------------------------------------------------------------

def test_send_saves_upo_on_accepted(mocks):
    uc, api, auth, repo, enc, xml_file, upo_dir = mocks
    api.invoice_status.return_value = _STATUS_ACCEPTED
    api.get_upo_by_ksef_number.return_value = _UPO

    result = uc.execute(xml_file, _GID, _RODZAJ, _NR, _DATA)

    assert result.upo_path is not None
    assert result.upo_path.read_bytes() == _UPO.content


def test_send_records_ksef_number(mocks):
    uc, api, auth, repo, enc, xml_file, upo_dir = mocks
    api.invoice_status.return_value = _STATUS_ACCEPTED
    api.get_upo_by_ksef_number.return_value = _UPO

    result = uc.execute(xml_file, _GID, _RODZAJ, _NR, _DATA)

    assert result.ksef_number == "1234567890-20260414-ABC-D01-23"
    # verify ksef_number passed to repo transition
    accepted_calls = [
        c for c in repo.transition.call_args_list
        if c.args[1] == ShipmentStatus.ACCEPTED
    ]
    assert len(accepted_calls) == 1
    assert accepted_calls[0].kwargs.get("ksef_number") == result.ksef_number
