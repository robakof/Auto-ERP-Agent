"""Tests for KSeF report aggregator."""
from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import pytest

from core.ksef.domain.shipment import ShipmentStatus, Wysylka
from core.ksef.usecases.report import ReportData, build_report


# ---- helpers -----------------------------------------------------------------

def _wysylka(
    id: int = 1,
    status: ShipmentStatus = ShipmentStatus.ACCEPTED,
    created_at: datetime = datetime(2026, 4, 22, 10, 0),
    error_msg: str | None = None,
    **kw,
) -> Wysylka:
    defaults = dict(
        id=id, gid_erp=100 + id, rodzaj="FS",
        nr_faktury=f"FS-{id}/04/26", data_wystawienia=date(2026, 4, 22),
        xml_path=f"out/ksef_{id}.xml", xml_hash=f"hash{id}",
        status=status,
        ksef_session_ref=None, ksef_invoice_ref=None, ksef_number=None,
        upo_path=None, error_code=None, error_msg=error_msg,
        attempt=1, created_at=created_at,
        queued_at=None, sent_at=None, accepted_at=None,
        rejected_at=None, errored_at=None,
    )
    defaults.update(kw)
    return Wysylka(**defaults)


class FakeRepo:
    """Minimal fake ShipmentRepository for report tests."""

    def __init__(self, wysylki: list[Wysylka] | None = None):
        self._all = wysylki or []

    def count_by_status(self, since=None):
        counts = {s: 0 for s in ShipmentStatus}
        for w in self._all:
            if since is None or w.created_at >= since:
                counts[w.status] += 1
        return counts

    def list_by_status(self, status, limit=100):
        return [w for w in self._all if w.status == status][:limit]

    def list_recent(self, limit=50):
        return sorted(self._all, key=lambda w: w.id, reverse=True)[:limit]


# ---- tests -------------------------------------------------------------------

_SINCE = datetime(2026, 4, 22, 0, 0)
_NOW = datetime(2026, 4, 22, 13, 30)


def test_empty_report():
    repo = FakeRepo([])
    report = build_report(repo, since=_SINCE, clock=_NOW)

    assert report.total == 0
    assert report.all_sent_today is True
    assert report.has_problems is False
    assert report.errors == []
    assert report.pending == []


def test_all_accepted():
    wysylki = [
        _wysylka(1, ShipmentStatus.ACCEPTED),
        _wysylka(2, ShipmentStatus.ACCEPTED),
        _wysylka(3, ShipmentStatus.ACCEPTED),
    ]
    repo = FakeRepo(wysylki)
    report = build_report(repo, since=_SINCE, clock=_NOW)

    assert report.total == 3
    assert report.counts[ShipmentStatus.ACCEPTED] == 3
    assert report.all_sent_today is True
    assert report.has_problems is False


def test_errors_flagged():
    wysylki = [
        _wysylka(1, ShipmentStatus.ACCEPTED),
        _wysylka(2, ShipmentStatus.ERROR, error_msg="API timeout"),
        _wysylka(3, ShipmentStatus.ERROR, error_msg="Schema error"),
    ]
    repo = FakeRepo(wysylki)
    report = build_report(repo, since=_SINCE, clock=_NOW)

    assert report.all_sent_today is False
    assert report.has_problems is True
    assert len(report.errors) == 2
    assert report.counts[ShipmentStatus.ERROR] == 2


def test_pending_documents():
    wysylki = [
        _wysylka(1, ShipmentStatus.ACCEPTED),
        _wysylka(2, ShipmentStatus.QUEUED),
        _wysylka(3, ShipmentStatus.SENT),
    ]
    repo = FakeRepo(wysylki)
    report = build_report(repo, since=_SINCE, clock=_NOW)

    assert report.all_sent_today is False
    assert len(report.pending) == 2


def test_rejected_flagged():
    wysylki = [
        _wysylka(1, ShipmentStatus.ACCEPTED),
        _wysylka(2, ShipmentStatus.REJECTED),
    ]
    repo = FakeRepo(wysylki)
    report = build_report(repo, since=_SINCE, clock=_NOW)

    assert report.all_sent_today is False
    assert report.has_problems is True
    assert len(report.rejected) == 1


def test_old_errors_excluded():
    """Errors from before 'since' should not appear in errors list."""
    old = datetime(2026, 4, 20, 10, 0)  # 2 days ago
    wysylki = [
        _wysylka(1, ShipmentStatus.ERROR, created_at=old, error_msg="old error"),
        _wysylka(2, ShipmentStatus.ACCEPTED),
    ]
    repo = FakeRepo(wysylki)
    report = build_report(repo, since=_SINCE, clock=_NOW)

    assert len(report.errors) == 0


def test_report_timestamps():
    repo = FakeRepo([])
    report = build_report(repo, since=_SINCE, clock=_NOW)

    assert report.since == _SINCE
    assert report.generated_at == _NOW


def test_mixed_scenario():
    """Realistic scenario: some accepted, some errors, some pending."""
    wysylki = [
        _wysylka(1, ShipmentStatus.ACCEPTED),
        _wysylka(2, ShipmentStatus.ACCEPTED),
        _wysylka(3, ShipmentStatus.ACCEPTED),
        _wysylka(4, ShipmentStatus.ERROR, error_msg="timeout"),
        _wysylka(5, ShipmentStatus.QUEUED),
    ]
    repo = FakeRepo(wysylki)
    report = build_report(repo, since=_SINCE, clock=_NOW)

    assert report.total == 5
    assert report.counts[ShipmentStatus.ACCEPTED] == 3
    assert report.counts[ShipmentStatus.ERROR] == 1
    assert report.counts[ShipmentStatus.QUEUED] == 1
    assert report.all_sent_today is False
    assert report.has_problems is True
    assert len(report.errors) == 1
    assert len(report.pending) == 1
