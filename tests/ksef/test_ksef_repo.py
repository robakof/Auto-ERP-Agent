"""ShipmentRepository tests — happy, state machine, idempotency, audit, edges."""
from __future__ import annotations

import json
import sqlite3
import threading
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

from core.ksef.adapters.repo import ShipmentRepository
from core.ksef.domain.shipment import ShipmentStatus
from core.ksef.exceptions import (
    InvalidTransitionError,
    ShipmentAlreadyActiveError,
    ShipmentNotFoundError,
)

_NOW = datetime(2026, 4, 15, 12, 0, 0)


@pytest.fixture
def repo(tmp_path: Path) -> ShipmentRepository:
    ticker = iter(_NOW + timedelta(seconds=i) for i in range(1000))
    r = ShipmentRepository(tmp_path / "ksef.db", clock=lambda: next(ticker))
    r.init_schema()
    return r


def _create(repo: ShipmentRepository, *, gid: int = 100, rodzaj: str = "FS", attempt: int = 1):
    return repo.create(
        gid_erp=gid, rodzaj=rodzaj, nr_faktury=f"{rodzaj}/{gid}",
        data_wystawienia=date(2026, 4, 15), xml_path=f"output/ksef/{gid}.xml",
        xml_hash="a" * 64, attempt=attempt,
    )


# ---- happy path ----------------------------------------------------------

def test_create_inserts_draft_row(repo: ShipmentRepository) -> None:
    w = _create(repo)
    assert w.id > 0
    assert w.status is ShipmentStatus.DRAFT
    assert w.gid_erp == 100
    assert w.attempt == 1
    assert w.created_at is not None
    assert w.queued_at is None


def test_get_returns_existing(repo: ShipmentRepository) -> None:
    w = _create(repo)
    assert repo.get(w.id) == w


def test_get_latest_returns_highest_attempt(repo: ShipmentRepository) -> None:
    _create(repo, attempt=1)
    repo.transition(1, ShipmentStatus.ERROR, error_code="E1")
    w2 = _create(repo, attempt=2)
    assert repo.get_latest(100, "FS").id == w2.id


def test_transition_draft_to_queued_sets_timestamp(repo: ShipmentRepository) -> None:
    w = _create(repo)
    out = repo.transition(w.id, ShipmentStatus.QUEUED)
    assert out.status is ShipmentStatus.QUEUED
    assert out.queued_at is not None


def test_transition_sent_to_accepted_sets_fields(repo: ShipmentRepository) -> None:
    w = _create(repo)
    repo.transition(w.id, ShipmentStatus.QUEUED)
    repo.transition(w.id, ShipmentStatus.AUTH_PENDING)
    repo.transition(w.id, ShipmentStatus.SENT, ksef_session_ref="SES-1", ksef_invoice_ref="INV-1")
    out = repo.transition(w.id, ShipmentStatus.ACCEPTED, ksef_number="KSEF-1", upo_path="upo.xml")
    assert out.status is ShipmentStatus.ACCEPTED
    assert out.accepted_at is not None
    assert out.ksef_number == "KSEF-1"
    assert out.upo_path == "upo.xml"


def test_list_by_status_filters(repo: ShipmentRepository) -> None:
    _create(repo, gid=1)
    _create(repo, gid=2)
    repo.transition(1, ShipmentStatus.ERROR, error_code="E1")
    errors = repo.list_by_status(ShipmentStatus.ERROR)
    drafts = repo.list_by_status(ShipmentStatus.DRAFT)
    assert len(errors) == 1 and errors[0].gid_erp == 1
    assert len(drafts) == 1 and drafts[0].gid_erp == 2


def test_list_recent_orders_newest_first(repo: ShipmentRepository) -> None:
    for gid in range(1, 4):
        _create(repo, gid=gid)
    rows = repo.list_recent(limit=10)
    assert [w.gid_erp for w in rows] == [3, 2, 1]


# ---- state machine -------------------------------------------------------

def test_transition_skip_state_raises(repo: ShipmentRepository) -> None:
    w = _create(repo)
    with pytest.raises(InvalidTransitionError):
        repo.transition(w.id, ShipmentStatus.SENT)


def test_transition_from_terminal_accepted_raises(repo: ShipmentRepository) -> None:
    w = _create(repo)
    for s in (ShipmentStatus.QUEUED, ShipmentStatus.AUTH_PENDING,
              ShipmentStatus.SENT, ShipmentStatus.ACCEPTED):
        if s is ShipmentStatus.ACCEPTED:
            repo.transition(w.id, s, ksef_number="K")
        else:
            repo.transition(w.id, s)
    with pytest.raises(InvalidTransitionError):
        repo.transition(w.id, ShipmentStatus.QUEUED)


def test_transition_from_terminal_rejected_raises(repo: ShipmentRepository) -> None:
    w = _create(repo)
    repo.transition(w.id, ShipmentStatus.QUEUED)
    repo.transition(w.id, ShipmentStatus.AUTH_PENDING)
    repo.transition(w.id, ShipmentStatus.SENT)
    repo.transition(w.id, ShipmentStatus.REJECTED, error_code="VAL-1")
    with pytest.raises(InvalidTransitionError):
        repo.transition(w.id, ShipmentStatus.ERROR)


def test_transition_from_error_is_terminal(repo: ShipmentRepository) -> None:
    w = _create(repo)
    repo.transition(w.id, ShipmentStatus.ERROR, error_code="BOOM")
    with pytest.raises(InvalidTransitionError):
        repo.transition(w.id, ShipmentStatus.QUEUED)


def test_transition_invalid_queued_to_sent(repo: ShipmentRepository) -> None:
    w = _create(repo)
    repo.transition(w.id, ShipmentStatus.QUEUED)
    with pytest.raises(InvalidTransitionError):
        repo.transition(w.id, ShipmentStatus.SENT)


def test_transition_reject_unknown_field(repo: ShipmentRepository) -> None:
    w = _create(repo)
    with pytest.raises(ValueError):
        repo.transition(w.id, ShipmentStatus.QUEUED, not_a_column="x")


# ---- idempotency ---------------------------------------------------------

def test_create_while_queued_raises(repo: ShipmentRepository) -> None:
    _create(repo)
    repo.transition(1, ShipmentStatus.QUEUED)
    with pytest.raises(ShipmentAlreadyActiveError):
        _create(repo, attempt=2)


def test_create_while_accepted_raises(repo: ShipmentRepository) -> None:
    _create(repo)
    for s in (ShipmentStatus.QUEUED, ShipmentStatus.AUTH_PENDING, ShipmentStatus.SENT):
        repo.transition(1, s)
    repo.transition(1, ShipmentStatus.ACCEPTED, ksef_number="K1")
    with pytest.raises(ShipmentAlreadyActiveError):
        _create(repo, attempt=2)


def test_create_after_error_via_new_attempt_ok(repo: ShipmentRepository) -> None:
    _create(repo)
    repo.transition(1, ShipmentStatus.ERROR, error_code="E")
    w = repo.new_attempt(
        100, "FS", nr_faktury="FS/100", data_wystawienia=date(2026, 4, 15),
        xml_path="x.xml", xml_hash="h" * 64,
    )
    assert w.attempt == 2
    assert w.status is ShipmentStatus.DRAFT


def test_new_attempt_without_prior_raises(repo: ShipmentRepository) -> None:
    with pytest.raises(ShipmentNotFoundError):
        repo.new_attempt(
            999, "FS", nr_faktury="FS/999",
            data_wystawienia=date(2026, 4, 15),
            xml_path="x.xml", xml_hash="h" * 64,
        )


def test_new_attempt_while_active_raises(repo: ShipmentRepository) -> None:
    _create(repo)
    repo.transition(1, ShipmentStatus.QUEUED)
    with pytest.raises(ShipmentAlreadyActiveError):
        repo.new_attempt(
            100, "FS", nr_faktury="FS/100", data_wystawienia=date(2026, 4, 15),
            xml_path="x.xml", xml_hash="h" * 64,
        )


def test_has_pending_or_sent_truth_table(repo: ShipmentRepository) -> None:
    _create(repo, gid=1)
    assert repo.has_pending_or_sent(1, "FS") is False
    repo.transition(1, ShipmentStatus.QUEUED)
    assert repo.has_pending_or_sent(1, "FS") is True


def test_has_pending_or_sent_false_after_error(repo: ShipmentRepository) -> None:
    _create(repo, gid=2)
    repo.transition(1, ShipmentStatus.ERROR, error_code="E")
    assert repo.has_pending_or_sent(2, "FS") is False


def test_has_pending_or_sent_false_after_rejected(repo: ShipmentRepository) -> None:
    _create(repo, gid=3)
    repo.transition(1, ShipmentStatus.QUEUED)
    repo.transition(1, ShipmentStatus.AUTH_PENDING)
    repo.transition(1, ShipmentStatus.SENT)
    repo.transition(1, ShipmentStatus.REJECTED, error_code="V")
    assert repo.has_pending_or_sent(3, "FS") is False


def test_has_pending_or_sent_true_on_accepted(repo: ShipmentRepository) -> None:
    _create(repo, gid=4)
    for s in (ShipmentStatus.QUEUED, ShipmentStatus.AUTH_PENDING, ShipmentStatus.SENT):
        repo.transition(1, s)
    repo.transition(1, ShipmentStatus.ACCEPTED, ksef_number="K")
    assert repo.has_pending_or_sent(4, "FS") is True


# ---- audit trail ---------------------------------------------------------

def test_transition_writes_audit_row(repo: ShipmentRepository, tmp_path: Path) -> None:
    w = _create(repo)
    repo.transition(w.id, ShipmentStatus.QUEUED, meta={"by": "test"})
    with sqlite3.connect(tmp_path / "ksef.db") as conn:
        rows = conn.execute(
            "SELECT from_status, to_status, meta_json FROM ksef_transition"
            " WHERE wysylka_id = ?", (w.id,)
        ).fetchall()
    assert len(rows) == 1
    assert rows[0][0] == "DRAFT"
    assert rows[0][1] == "QUEUED"
    assert json.loads(rows[0][2]) == {"by": "test"}


def test_three_transitions_three_audit_rows(repo: ShipmentRepository, tmp_path: Path) -> None:
    w = _create(repo)
    repo.transition(w.id, ShipmentStatus.QUEUED)
    repo.transition(w.id, ShipmentStatus.AUTH_PENDING)
    repo.transition(w.id, ShipmentStatus.SENT)
    with sqlite3.connect(tmp_path / "ksef.db") as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM ksef_transition WHERE wysylka_id = ?", (w.id,)
        ).fetchone()[0]
    assert count == 3


def test_audit_meta_null_when_missing(repo: ShipmentRepository, tmp_path: Path) -> None:
    w = _create(repo)
    repo.transition(w.id, ShipmentStatus.QUEUED)
    with sqlite3.connect(tmp_path / "ksef.db") as conn:
        meta = conn.execute(
            "SELECT meta_json FROM ksef_transition WHERE wysylka_id = ?", (w.id,)
        ).fetchone()[0]
    assert meta is None


# ---- edge cases ----------------------------------------------------------

def test_get_nonexistent_returns_none(repo: ShipmentRepository) -> None:
    assert repo.get(9999) is None


def test_get_latest_nonexistent_returns_none(repo: ShipmentRepository) -> None:
    assert repo.get_latest(999, "FS") is None


def test_transition_nonexistent_id_raises(repo: ShipmentRepository) -> None:
    with pytest.raises(ShipmentNotFoundError):
        repo.transition(9999, ShipmentStatus.QUEUED)


def test_fsk_rodzaj_supported(repo: ShipmentRepository) -> None:
    w = _create(repo, rodzaj="FSK")
    assert w.rodzaj == "FSK"


def test_list_by_gid_returns_all_attempts_both_types(repo: ShipmentRepository) -> None:
    _create(repo, gid=500, rodzaj="FS")
    repo.transition(1, ShipmentStatus.ERROR, error_code="E1")
    repo.new_attempt(
        500, "FS", nr_faktury="FS/500", data_wystawienia=date(2026, 4, 15),
        xml_path="x.xml", xml_hash="h" * 64,
    )
    _create(repo, gid=500, rodzaj="FSK")
    rows = repo.list_by_gid(500)
    assert len(rows) == 3
    assert {w.rodzaj for w in rows} == {"FS", "FSK"}


def test_list_by_gid_filtered_by_rodzaj(repo: ShipmentRepository) -> None:
    _create(repo, gid=600, rodzaj="FS")
    _create(repo, gid=600, rodzaj="FSK")
    rows = repo.list_by_gid(600, rodzaj="FSK")
    assert len(rows) == 1 and rows[0].rodzaj == "FSK"


# ---- concurrency ---------------------------------------------------------

def test_concurrent_create_one_wins(tmp_path: Path) -> None:
    db = tmp_path / "ksef.db"
    ShipmentRepository(db).init_schema()
    errors: list[Exception] = []
    successes: list[int] = []

    def worker() -> None:
        repo = ShipmentRepository(db)
        try:
            w = repo.create(
                gid_erp=42, rodzaj="FS", nr_faktury="FS/42",
                data_wystawienia=date(2026, 4, 15),
                xml_path="x.xml", xml_hash="h" * 64, attempt=1,
            )
            successes.append(w.id)
        except ShipmentAlreadyActiveError as e:
            errors.append(e)

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(successes) == 1
    assert len(errors) == 1
