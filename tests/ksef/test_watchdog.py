"""Tests for KSeF watchdog and daemon heartbeat."""
from __future__ import annotations

import json
import time
from datetime import date, datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from core.ksef.usecases.scan_erp import PendingDocument
from core.ksef.usecases.send_invoice import SendResult
from core.ksef.domain.shipment import ShipmentStatus

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.ksef_daemon import KSeFDaemon
from tools.ksef_watchdog import KSeFWatchdog


# ---- daemon heartbeat --------------------------------------------------------

_DOC1 = PendingDocument(
    gid=59, rodzaj="FS", nr_faktury="FS-59",
    data_wystawienia=date(2026, 4, 14),
)
_RESULT_OK = SendResult(
    wysylka_id=1, ksef_number="KSeF-123",
    upo_path=Path("upo.xml"), status=ShipmentStatus.ACCEPTED,
)


def test_daemon_writes_heartbeat_on_tick(tmp_path):
    hb_path = tmp_path / "heartbeat.json"
    scan = MagicMock()
    scan.scan.return_value = [_DOC1]
    factory = MagicMock(return_value=_RESULT_OK)

    mock_repo = MagicMock()
    mock_repo.list_stuck.return_value = []
    daemon = KSeFDaemon(
        scan, factory, mock_repo,
        sleep=lambda _: None,
        heartbeat_path=hb_path,
    )
    daemon.run_once()

    assert hb_path.exists()
    data = json.loads(hb_path.read_text(encoding="utf-8"))
    assert data["tick_count"] == 1
    assert data["status"] == "ok"
    assert "last_tick_utc" in data
    assert "pid" in data


def test_daemon_heartbeat_status_slow_when_tick_exceeds_timeout(tmp_path):
    hb_path = tmp_path / "heartbeat.json"
    scan = MagicMock()
    scan.scan.return_value = []

    fake_time = [0.0]
    def fake_clock():
        return fake_time[0]

    def slow_scan():
        # Simulate scan taking 400s (> 300s timeout)
        fake_time[0] += 400.0
        return []

    scan.scan.side_effect = slow_scan

    mock_repo = MagicMock()
    mock_repo.list_stuck.return_value = []
    daemon = KSeFDaemon(
        scan, MagicMock(), mock_repo,
        sleep=lambda _: None,
        heartbeat_path=hb_path,
        tick_timeout_s=300.0,
        clock=fake_clock,
    )
    daemon.run_once()

    data = json.loads(hb_path.read_text(encoding="utf-8"))
    assert data["status"] == "slow"
    assert data["last_tick_duration_s"] == 400.0


def test_daemon_heartbeat_updates_each_tick(tmp_path):
    hb_path = tmp_path / "heartbeat.json"
    scan = MagicMock()
    scan.scan.return_value = []

    mock_repo = MagicMock()
    mock_repo.list_stuck.return_value = []
    daemon = KSeFDaemon(
        scan, MagicMock(), mock_repo,
        sleep=lambda _: None,
        heartbeat_path=hb_path,
    )
    daemon.run_once()
    daemon.run_once()
    daemon.run_once()

    data = json.loads(hb_path.read_text(encoding="utf-8"))
    assert data["tick_count"] == 3


# ---- watchdog ----------------------------------------------------------------

class _FakeProcess:
    """Simulates subprocess.Popen for watchdog tests."""
    def __init__(self, *, exit_after_polls=None, returncode=1):
        self._polls = 0
        self._exit_after = exit_after_polls
        self._returncode = returncode
        self.pid = 12345
        self._terminated = False
        self._killed = False

    def poll(self):
        self._polls += 1
        if self._exit_after is not None and self._polls >= self._exit_after:
            return self._returncode
        return None

    @property
    def returncode(self):
        return self._returncode

    def terminate(self):
        self._terminated = True

    def kill(self):
        self._killed = True

    def wait(self, timeout=None):
        pass


def test_watchdog_detects_stale_heartbeat(tmp_path):
    hb_path = tmp_path / "heartbeat.json"
    # Write heartbeat 30 minutes ago
    old_time = datetime.now(timezone.utc) - timedelta(minutes=30)
    hb_path.write_text(json.dumps({
        "last_tick_utc": old_time.isoformat(),
        "tick_count": 5,
        "last_tick_duration_s": 1.0,
        "status": "ok",
        "pid": 999,
    }), encoding="utf-8")

    watchdog = KSeFWatchdog(
        ["--interval", "60"],
        heartbeat_path=hb_path,
        heartbeat_stale_s=600.0,  # 10 min
    )
    assert watchdog._is_heartbeat_stale() is True


def test_watchdog_fresh_heartbeat_not_stale(tmp_path):
    hb_path = tmp_path / "heartbeat.json"
    now = datetime.now(timezone.utc)
    hb_path.write_text(json.dumps({
        "last_tick_utc": now.isoformat(),
        "tick_count": 5,
        "last_tick_duration_s": 1.0,
        "status": "ok",
        "pid": 999,
    }), encoding="utf-8")

    watchdog = KSeFWatchdog(
        ["--interval", "60"],
        heartbeat_path=hb_path,
        heartbeat_stale_s=600.0,
    )
    assert watchdog._is_heartbeat_stale() is False


def test_watchdog_no_heartbeat_file_not_stale(tmp_path):
    hb_path = tmp_path / "nonexistent.json"
    watchdog = KSeFWatchdog(
        ["--interval", "60"],
        heartbeat_path=hb_path,
        heartbeat_stale_s=600.0,
    )
    assert watchdog._is_heartbeat_stale() is False


def test_watchdog_can_restart_respects_limit():
    clock_time = [0.0]
    watchdog = KSeFWatchdog(
        ["--interval", "60"],
        max_restarts_per_hour=3,
        clock=lambda: clock_time[0],
    )
    # Simulate 3 restarts
    watchdog._restart_times = [0.0, 100.0, 200.0]
    assert watchdog._can_restart() is False

    # After 1 hour, old restarts expire
    clock_time[0] = 3700.0
    assert watchdog._can_restart() is True


def test_watchdog_flags_human_on_max_restarts(tmp_path):
    flag_fn = MagicMock()
    sleep_calls = []

    iteration = [0]
    fake_process = _FakeProcess(exit_after_polls=1, returncode=1)

    watchdog = KSeFWatchdog(
        ["--interval", "60"],
        heartbeat_path=tmp_path / "hb.json",
        max_restarts_per_hour=2,
        cooldown_s=0.0,
        flag_fn=flag_fn,
        sleep_fn=lambda _: sleep_calls.append(1),
    )

    # Monkey-patch _start_daemon to use fake process
    orig_start = watchdog._start_daemon

    def fake_start():
        watchdog._process = fake_process
        watchdog._total_restarts += 1
        now = watchdog._clock()
        watchdog._restart_times.append(now)

    watchdog._start_daemon = fake_start

    result = watchdog.run()

    assert result == 2
    flag_fn.assert_called_once()
    assert "restartow" in flag_fn.call_args[0][0]
