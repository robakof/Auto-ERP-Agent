"""Operational guards for KSeF daemon — rate limiting and error escalation.

Pure safety layer above the core pipeline. Zero domain knowledge, zero I/O
except optional subprocess flag call. Deterministic via injected clock.
"""
from __future__ import annotations

import time
from collections import deque
from typing import Callable

from core.ksef.domain.shipment import ShipmentStatus
from core.ksef.usecases.send_invoice import SendResult


class RateLimiter:
    """Sliding-window token bucket — max N operations per 60s window.

    `max_per_minute=0` disables the limiter (acquire() always returns True).
    Uses `clock` DI for deterministic testing.
    """

    def __init__(
        self,
        max_per_minute: int = 10,
        *,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if max_per_minute < 0:
            raise ValueError("max_per_minute must be >= 0")
        self._max = max_per_minute
        self._clock = clock
        self._window_s = 60.0
        self._timestamps: deque[float] = deque()

    @property
    def enabled(self) -> bool:
        return self._max > 0

    def acquire(self) -> bool:
        """Return True if operation allowed, False if rate limited."""
        if not self.enabled:
            return True
        now = self._clock()
        self._evict_expired(now)
        if len(self._timestamps) >= self._max:
            return False
        self._timestamps.append(now)
        return True

    def wait_if_needed(
        self, sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        """Block until an operation slot is available."""
        if not self.enabled:
            return
        while True:
            now = self._clock()
            self._evict_expired(now)
            if len(self._timestamps) < self._max:
                self._timestamps.append(now)
                return
            # Wait until the oldest timestamp falls outside the window.
            oldest = self._timestamps[0]
            sleep(max(0.0, self._window_s - (now - oldest)))

    def _evict_expired(self, now: float) -> None:
        cutoff = now - self._window_s
        while self._timestamps and self._timestamps[0] <= cutoff:
            self._timestamps.popleft()


class ErrorEscalator:
    """Tracks ERROR/REJECTED per tick, flags human when threshold crossed.

    `threshold=0` disables escalation. `flag_fn` is called once per tick
    when the count reaches threshold. Counter resets on `reset()`.
    """

    _ERROR_STATUSES = frozenset({ShipmentStatus.ERROR, ShipmentStatus.REJECTED})

    def __init__(
        self,
        threshold: int = 3,
        *,
        flag_fn: Callable[[str], None] | None = None,
    ) -> None:
        if threshold < 0:
            raise ValueError("threshold must be >= 0")
        self._threshold = threshold
        self._flag_fn = flag_fn
        self._errors: list[SendResult] = []
        self._flagged = False

    @property
    def enabled(self) -> bool:
        return self._threshold > 0

    @property
    def error_count(self) -> int:
        return len(self._errors)

    def report(self, result: SendResult) -> None:
        """Track result. If error count reaches threshold → flag once."""
        if not self.enabled:
            return
        if result.status not in self._ERROR_STATUSES:
            return
        self._errors.append(result)
        if not self._flagged and len(self._errors) >= self._threshold:
            self._flagged = True
            if self._flag_fn is not None:
                self._flag_fn(self._format_reason())

    def reset(self) -> None:
        """Reset counter — call between ticks with no errors."""
        self._errors.clear()
        self._flagged = False

    def _format_reason(self) -> str:
        lines = [
            f"KSeF daemon: {len(self._errors)} bledow w jednym ticku"
            f" (threshold={self._threshold}).",
            "",
            "Wysylki:",
        ]
        for r in self._errors:
            lines.append(
                f"  wysylka_id={r.wysylka_id} status={r.status.value}"
                f" ksef_number={r.ksef_number or '-'}"
            )
        return "\n".join(lines)
