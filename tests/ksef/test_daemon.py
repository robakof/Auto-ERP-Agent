"""Contract tests KSeFDaemon — full mock scan + send_factory."""
from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, call

import pytest

from core.ksef.domain.shipment import ShipmentStatus
from core.ksef.guards import ErrorEscalator, RateLimiter
from core.ksef.usecases.scan_erp import PendingDocument
from core.ksef.usecases.send_invoice import SendResult

# Import daemon class directly (avoid CLI wiring)
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.ksef_daemon import KSeFDaemon


# ---- fixtures ----------------------------------------------------------------

_DOC1 = PendingDocument(gid=59, rodzaj="FS", nr_faktury="FS-59/04/26/SPKR", data_wystawienia=date(2026, 4, 14))
_DOC2 = PendingDocument(gid=60, rodzaj="FS", nr_faktury="FS-60/04/26/SPKR", data_wystawienia=date(2026, 4, 14))
_DOC3 = PendingDocument(gid=1, rodzaj="FSK", nr_faktury="FSK-1/04/26/SPKRK", data_wystawienia=date(2026, 4, 14))

_RESULT_OK = SendResult(wysylka_id=1, ksef_number="KSeF-123", upo_path=Path("upo.xml"), status=ShipmentStatus.ACCEPTED)
_RESULT_ERR = SendResult(wysylka_id=2, ksef_number=None, upo_path=None, status=ShipmentStatus.ERROR)


@pytest.fixture
def scan():
    return MagicMock()


@pytest.fixture
def send_factory():
    return MagicMock(return_value=_RESULT_OK)


# ---- tests -------------------------------------------------------------------

def test_daemon_once_processes_all_pending(scan, send_factory):
    scan.scan.return_value = [_DOC1, _DOC2]
    daemon = KSeFDaemon(scan, send_factory, sleep=lambda _: None)

    results = daemon.run_once()

    assert len(results) == 2
    assert send_factory.call_count == 2


def test_daemon_once_returns_results(scan, send_factory):
    scan.scan.return_value = [_DOC1]
    send_factory.return_value = _RESULT_OK
    daemon = KSeFDaemon(scan, send_factory, sleep=lambda _: None)

    results = daemon.run_once()

    assert results[0].status == ShipmentStatus.ACCEPTED
    assert results[0].ksef_number == "KSeF-123"


def test_daemon_dry_run_no_send(scan):
    scan.scan.return_value = [_DOC1, _DOC2]
    factory = MagicMock(return_value=SendResult(0, None, None, ShipmentStatus.DRAFT))
    daemon = KSeFDaemon(scan, factory, sleep=lambda _: None)

    results = daemon.run_once()

    assert len(results) == 2
    # factory called but with dry-run factory it returns DRAFT
    assert all(r.status == ShipmentStatus.DRAFT for r in results)


def test_daemon_graceful_shutdown_mid_batch(scan, send_factory):
    scan.scan.return_value = [_DOC1, _DOC2, _DOC3]

    call_count = 0
    def factory_with_shutdown(doc):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            daemon._shutdown = True  # signal shutdown after first doc
        return _RESULT_OK

    daemon = KSeFDaemon(scan, factory_with_shutdown, sleep=lambda _: None)
    results = daemon.run_once()

    # Should process only 1 doc (shutdown after first)
    assert len(results) == 1


def test_daemon_error_one_continues_next(scan):
    scan.scan.return_value = [_DOC1, _DOC2]

    def factory_first_fails(doc):
        if doc.gid == 59:
            raise RuntimeError("API down")
        return _RESULT_OK

    daemon = KSeFDaemon(scan, factory_first_fails, sleep=lambda _: None)
    results = daemon.run_once()

    # First doc errored (None), second processed
    assert len(results) == 1
    assert results[0].status == ShipmentStatus.ACCEPTED


def test_daemon_empty_scan_no_send(scan, send_factory):
    scan.scan.return_value = []
    daemon = KSeFDaemon(scan, send_factory, sleep=lambda _: None)

    results = daemon.run_once()

    assert results == []
    send_factory.assert_not_called()


def test_daemon_tick_count_increments(scan, send_factory):
    scan.scan.return_value = []
    daemon = KSeFDaemon(scan, send_factory, sleep=lambda _: None)

    daemon.run_once()
    daemon.run_once()
    daemon.run_once()

    assert daemon._tick_count == 3


def test_daemon_on_tick_callback(scan, send_factory):
    scan.scan.return_value = [_DOC1]
    on_tick = MagicMock()
    daemon = KSeFDaemon(scan, send_factory, on_tick=on_tick, sleep=lambda _: None)

    daemon.run_once()

    on_tick.assert_called_once_with(0, [_DOC1])


# ---- guards integration ------------------------------------------------------

class _FakeClock:
    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        return self.t


def test_daemon_rate_limiter_blocks_excess(scan, send_factory):
    scan.scan.return_value = [_DOC1, _DOC2, _DOC3]
    limiter = RateLimiter(max_per_minute=2, clock=_FakeClock())
    daemon = KSeFDaemon(
        scan, send_factory, sleep=lambda _: None, rate_limiter=limiter,
    )

    results = daemon.run_once()

    # 2 sent, 3rd rate-limited
    assert len(results) == 2
    assert send_factory.call_count == 2


def test_daemon_rate_limiter_disabled_lets_all_through(scan, send_factory):
    scan.scan.return_value = [_DOC1, _DOC2, _DOC3]
    limiter = RateLimiter(max_per_minute=0, clock=_FakeClock())
    daemon = KSeFDaemon(
        scan, send_factory, sleep=lambda _: None, rate_limiter=limiter,
    )

    results = daemon.run_once()
    assert len(results) == 3


def test_daemon_escalator_flags_on_errors(scan):
    scan.scan.return_value = [_DOC1, _DOC2, _DOC3]
    factory = MagicMock(return_value=_RESULT_ERR)
    flag_fn = MagicMock()
    escalator = ErrorEscalator(threshold=3, flag_fn=flag_fn)
    daemon = KSeFDaemon(
        scan, factory, sleep=lambda _: None, error_escalator=escalator,
    )

    daemon.run_once()

    flag_fn.assert_called_once()


def test_daemon_escalator_resets_each_tick(scan):
    scan.scan.return_value = [_DOC1, _DOC2]
    factory = MagicMock(return_value=_RESULT_ERR)
    flag_fn = MagicMock()
    escalator = ErrorEscalator(threshold=3, flag_fn=flag_fn)
    daemon = KSeFDaemon(
        scan, factory, sleep=lambda _: None, error_escalator=escalator,
    )

    daemon.run_once()  # 2 errors, below threshold
    daemon.run_once()  # 2 more errors — but counter reset so still below

    flag_fn.assert_not_called()
