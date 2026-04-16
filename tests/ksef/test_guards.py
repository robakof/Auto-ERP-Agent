"""Unit tests for RateLimiter and ErrorEscalator — pure logic, deterministic clock."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from core.ksef.domain.shipment import ShipmentStatus
from core.ksef.guards import ErrorEscalator, RateLimiter
from core.ksef.usecases.send_invoice import SendResult


class _FakeClock:
    def __init__(self, start: float = 0.0) -> None:
        self.t = start

    def __call__(self) -> float:
        return self.t

    def advance(self, seconds: float) -> None:
        self.t += seconds


# ---- RateLimiter ------------------------------------------------------------

def test_rate_limiter_allows_within_limit() -> None:
    clock = _FakeClock()
    rl = RateLimiter(max_per_minute=3, clock=clock)
    assert rl.acquire() is True
    assert rl.acquire() is True
    assert rl.acquire() is True


def test_rate_limiter_blocks_over_limit() -> None:
    clock = _FakeClock()
    rl = RateLimiter(max_per_minute=2, clock=clock)
    assert rl.acquire() is True
    assert rl.acquire() is True
    assert rl.acquire() is False


def test_rate_limiter_resets_after_window() -> None:
    clock = _FakeClock()
    rl = RateLimiter(max_per_minute=2, clock=clock)
    assert rl.acquire() is True
    assert rl.acquire() is True
    assert rl.acquire() is False
    clock.advance(61.0)
    assert rl.acquire() is True


def test_rate_limiter_zero_means_disabled() -> None:
    rl = RateLimiter(max_per_minute=0, clock=_FakeClock())
    assert rl.enabled is False
    for _ in range(100):
        assert rl.acquire() is True


def test_rate_limiter_sliding_window() -> None:
    """Tokens expire individually — not all at once at 60s mark."""
    clock = _FakeClock()
    rl = RateLimiter(max_per_minute=2, clock=clock)
    rl.acquire()          # t=0
    clock.advance(30.0)
    rl.acquire()          # t=30
    assert rl.acquire() is False
    clock.advance(31.0)   # t=61 — only first token expired
    assert rl.acquire() is True
    assert rl.acquire() is False  # second token (from t=30) still in window


def test_rate_limiter_wait_if_needed_blocks_until_free() -> None:
    clock = _FakeClock()
    sleeps: list[float] = []

    def fake_sleep(s: float) -> None:
        sleeps.append(s)
        clock.advance(s)

    rl = RateLimiter(max_per_minute=1, clock=clock)
    rl.acquire()  # t=0, window full
    rl.wait_if_needed(sleep=fake_sleep)
    assert len(sleeps) >= 1
    assert sleeps[0] == pytest.approx(60.0)


def test_rate_limiter_wait_if_needed_noop_when_disabled() -> None:
    rl = RateLimiter(max_per_minute=0, clock=_FakeClock())
    sleeps: list[float] = []
    rl.wait_if_needed(sleep=lambda s: sleeps.append(s))
    assert sleeps == []


def test_rate_limiter_negative_raises() -> None:
    with pytest.raises(ValueError):
        RateLimiter(max_per_minute=-1)


# ---- ErrorEscalator ---------------------------------------------------------

def _result(status: ShipmentStatus, wysylka_id: int = 1) -> SendResult:
    return SendResult(
        wysylka_id=wysylka_id, ksef_number=None, upo_path=None, status=status,
    )


def test_escalator_no_flag_below_threshold() -> None:
    flag_fn = MagicMock()
    esc = ErrorEscalator(threshold=3, flag_fn=flag_fn)
    esc.report(_result(ShipmentStatus.ERROR, 1))
    esc.report(_result(ShipmentStatus.ERROR, 2))
    flag_fn.assert_not_called()


def test_escalator_flags_at_threshold() -> None:
    flag_fn = MagicMock()
    esc = ErrorEscalator(threshold=3, flag_fn=flag_fn)
    esc.report(_result(ShipmentStatus.ERROR, 1))
    esc.report(_result(ShipmentStatus.ERROR, 2))
    esc.report(_result(ShipmentStatus.ERROR, 3))
    flag_fn.assert_called_once()
    reason = flag_fn.call_args[0][0]
    assert "3 bledow" in reason
    assert "wysylka_id=1" in reason
    assert "wysylka_id=3" in reason


def test_escalator_flags_only_once_per_tick() -> None:
    flag_fn = MagicMock()
    esc = ErrorEscalator(threshold=2, flag_fn=flag_fn)
    esc.report(_result(ShipmentStatus.ERROR, 1))
    esc.report(_result(ShipmentStatus.ERROR, 2))
    esc.report(_result(ShipmentStatus.ERROR, 3))
    esc.report(_result(ShipmentStatus.ERROR, 4))
    assert flag_fn.call_count == 1


def test_escalator_reset_clears_counter() -> None:
    flag_fn = MagicMock()
    esc = ErrorEscalator(threshold=2, flag_fn=flag_fn)
    esc.report(_result(ShipmentStatus.ERROR, 1))
    esc.reset()
    assert esc.error_count == 0
    esc.report(_result(ShipmentStatus.ERROR, 2))
    flag_fn.assert_not_called()


def test_escalator_reset_reenables_flagging() -> None:
    flag_fn = MagicMock()
    esc = ErrorEscalator(threshold=1, flag_fn=flag_fn)
    esc.report(_result(ShipmentStatus.ERROR, 1))
    assert flag_fn.call_count == 1
    esc.reset()
    esc.report(_result(ShipmentStatus.ERROR, 2))
    assert flag_fn.call_count == 2


def test_escalator_counts_only_errors() -> None:
    flag_fn = MagicMock()
    esc = ErrorEscalator(threshold=2, flag_fn=flag_fn)
    esc.report(_result(ShipmentStatus.ACCEPTED, 1))
    esc.report(_result(ShipmentStatus.ACCEPTED, 2))
    esc.report(_result(ShipmentStatus.ACCEPTED, 3))
    flag_fn.assert_not_called()
    assert esc.error_count == 0


def test_escalator_counts_rejected_as_error() -> None:
    flag_fn = MagicMock()
    esc = ErrorEscalator(threshold=2, flag_fn=flag_fn)
    esc.report(_result(ShipmentStatus.ERROR, 1))
    esc.report(_result(ShipmentStatus.REJECTED, 2))
    flag_fn.assert_called_once()


def test_escalator_zero_threshold_disabled() -> None:
    flag_fn = MagicMock()
    esc = ErrorEscalator(threshold=0, flag_fn=flag_fn)
    assert esc.enabled is False
    for i in range(10):
        esc.report(_result(ShipmentStatus.ERROR, i))
    flag_fn.assert_not_called()


def test_escalator_no_flag_fn_does_not_crash() -> None:
    esc = ErrorEscalator(threshold=1, flag_fn=None)
    esc.report(_result(ShipmentStatus.ERROR, 1))  # must not raise
    assert esc.error_count == 1


def test_escalator_negative_threshold_raises() -> None:
    with pytest.raises(ValueError):
        ErrorEscalator(threshold=-1)
