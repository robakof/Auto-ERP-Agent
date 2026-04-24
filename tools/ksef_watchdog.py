"""KSeF watchdog — monitors and auto-restarts ksef_daemon.py.

    py tools/ksef_watchdog.py                          # default: interval 900s
    py tools/ksef_watchdog.py --interval 300           # daemon tick co 5 min
    py tools/ksef_watchdog.py --max-restarts 3         # max 3 restarts/hour
    py tools/ksef_watchdog.py --heartbeat-stale 1200   # heartbeat stale after 20 min

Monitors:
- Process alive? If exit code != 0 → restart after cooldown
- Heartbeat fresh? If stale → kill + restart
- Max restarts/hour exceeded → flag to human, stop
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.ksef import paths as ksef_paths

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_TMP_DIR = _PROJECT_ROOT / "tmp"
_AGENT_BUS_CLI = _PROJECT_ROOT / "tools" / "agent_bus_cli.py"

_LOG = logging.getLogger("ksef.watchdog")

_RESTART_COOLDOWN_S = 30.0
_DEFAULT_MAX_RESTARTS_PER_HOUR = 5
_DEFAULT_HEARTBEAT_STALE_S = 1200.0  # 2 * 600s default


class KSeFWatchdog:
    """Supervises ksef_daemon.py — auto-restart on crash or stale heartbeat."""

    def __init__(
        self,
        daemon_args: list[str],
        *,
        heartbeat_path: Path | None = None,
        heartbeat_stale_s: float = _DEFAULT_HEARTBEAT_STALE_S,
        max_restarts_per_hour: int = _DEFAULT_MAX_RESTARTS_PER_HOUR,
        cooldown_s: float = _RESTART_COOLDOWN_S,
        flag_fn=None,
        clock=time.monotonic,
        sleep_fn=time.sleep,
    ) -> None:
        self._daemon_args = daemon_args
        self._heartbeat_path = heartbeat_path or ksef_paths.heartbeat_path()
        self._heartbeat_stale_s = heartbeat_stale_s
        self._max_restarts = max_restarts_per_hour
        self._cooldown = cooldown_s
        self._flag_fn = flag_fn or _flag_to_human
        self._clock = clock
        self._sleep = sleep_fn
        self._restart_times: list[float] = []
        self._process: subprocess.Popen | None = None
        self._shutdown = False
        self._total_restarts = 0

    def run(self) -> int:
        """Main watchdog loop. Returns exit code."""
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        _LOG.info('{"event": "watchdog_start", "daemon_args": %s}',
                  json.dumps(self._daemon_args))

        while not self._shutdown:
            self._start_daemon()
            while not self._shutdown:
                self._sleep(5.0)
                if self._shutdown:
                    break

                # Check if process died
                if self._process and self._process.poll() is not None:
                    exit_code = self._process.returncode
                    _LOG.warning(
                        '{"event": "daemon_exited", "exit_code": %d}', exit_code,
                    )
                    break

                # Check heartbeat staleness
                if self._is_heartbeat_stale():
                    _LOG.error('{"event": "heartbeat_stale", "stale_s": %.1f}',
                               self._heartbeat_stale_s)
                    self._kill_daemon()
                    break

            if self._shutdown:
                break

            # Restart logic
            if not self._can_restart():
                _LOG.error('{"event": "max_restarts_exceeded", "limit": %d}',
                           self._max_restarts)
                self._flag_fn(
                    f"KSeF watchdog: {self._max_restarts} restartow w ciagu godziny. "
                    f"Daemon zatrzymany. Sprawdz logi: {ksef_paths.watchdog_log()}"
                )
                return 2

            _LOG.info('{"event": "restart_cooldown", "seconds": %.1f}', self._cooldown)
            self._sleep_interruptible(self._cooldown)

        self._kill_daemon()
        _LOG.info('{"event": "watchdog_stop", "total_restarts": %d}',
                  self._total_restarts)
        return 0

    def _start_daemon(self) -> None:
        """Start daemon subprocess."""
        # Remove stale heartbeat so watchdog doesn't immediately kill the new daemon
        # (_is_heartbeat_stale returns False when file is missing — gives daemon
        # time to write its first heartbeat)
        if self._heartbeat_path.exists():
            try:
                self._heartbeat_path.unlink()
                _LOG.info('{"event": "heartbeat_cleared"}')
            except OSError:
                pass
        cmd = [sys.executable, str(_PROJECT_ROOT / "tools" / "ksef_daemon.py")]
        cmd.extend(self._daemon_args)
        _LOG.info('{"event": "daemon_start", "cmd": %s}', json.dumps(cmd))
        self._process = subprocess.Popen(cmd)
        self._total_restarts += 1
        now = self._clock()
        self._restart_times.append(now)
        # Prune restart times older than 1 hour
        cutoff = now - 3600.0
        self._restart_times = [t for t in self._restart_times if t > cutoff]

    def _kill_daemon(self) -> None:
        """Kill daemon process if running."""
        if self._process is None:
            return
        if self._process.poll() is not None:
            return
        _LOG.info('{"event": "daemon_kill", "pid": %d}', self._process.pid)
        self._process.terminate()
        try:
            self._process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self._process.kill()
            self._process.wait(timeout=5)

    def _is_heartbeat_stale(self) -> bool:
        """Check if heartbeat file is too old."""
        if not self._heartbeat_path.exists():
            return False  # No heartbeat yet — daemon may still be starting
        try:
            data = json.loads(self._heartbeat_path.read_text(encoding="utf-8"))
            last_tick = datetime.fromisoformat(data["last_tick_utc"])
            age_s = (datetime.now(timezone.utc) - last_tick).total_seconds()
            return age_s > self._heartbeat_stale_s
        except (json.JSONDecodeError, KeyError, ValueError):
            _LOG.warning('{"event": "heartbeat_parse_error"}')
            return False

    def _can_restart(self) -> bool:
        """Check if we haven't exceeded max restarts per hour."""
        now = self._clock()
        cutoff = now - 3600.0
        recent = [t for t in self._restart_times if t > cutoff]
        return len(recent) < self._max_restarts

    def _handle_shutdown(self, sig, frame) -> None:
        _LOG.info('{"event": "watchdog_shutdown_requested", "signal": %d}', sig)
        self._shutdown = True

    def _sleep_interruptible(self, seconds: float) -> None:
        elapsed = 0.0
        while elapsed < seconds and not self._shutdown:
            chunk = min(1.0, seconds - elapsed)
            self._sleep(chunk)
            elapsed += chunk


def _flag_to_human(reason: str) -> None:
    """Escalate to human via agent_bus. Best-effort."""
    try:
        _TMP_DIR.mkdir(parents=True, exist_ok=True)
        reason_file = _TMP_DIR / "ksef_watchdog_flag.md"
        reason_file.write_text(reason, encoding="utf-8")
        subprocess.run(
            [sys.executable, str(_AGENT_BUS_CLI), "flag",
             "--from", "daemon", "--reason-file", str(reason_file)],
            capture_output=True, text=True, timeout=30,
        )
    except Exception:
        _LOG.warning('{"event": "flag_failed"}', exc_info=True)


def _env_float(key: str, fallback: float) -> float:
    val = os.environ.get(key)
    return float(val) if val else fallback


def _env_int(key: str, fallback: int) -> int:
    val = os.environ.get(key)
    return int(val) if val else fallback


def _parse_args():
    p = argparse.ArgumentParser(description="KSeF watchdog — auto-restart daemon")
    p.add_argument("--interval", type=float,
                   default=_env_float("KSEF_DAEMON_INTERVAL", 900.0))
    p.add_argument("--tick-timeout", type=float,
                   default=_env_float("KSEF_DAEMON_TICK_TIMEOUT", 300.0))
    p.add_argument("--max-restarts", type=int,
                   default=_env_int("KSEF_WATCHDOG_MAX_RESTARTS", 5))
    p.add_argument("--heartbeat-stale", type=float,
                   default=_env_float("KSEF_WATCHDOG_HEARTBEAT_STALE", 1200.0))
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--rate-limit", type=int,
                   default=_env_int("KSEF_DAEMON_RATE_LIMIT", 10))
    p.add_argument("--error-threshold", type=int,
                   default=_env_int("KSEF_DAEMON_ERROR_THRESHOLD", 3))
    return p.parse_args()


def main() -> int:
    from dotenv import load_dotenv
    load_dotenv(override=False)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(str(ksef_paths.watchdog_log()), encoding="utf-8"),
        ],
    )

    args = _parse_args()

    # Build daemon args from watchdog args
    daemon_args = [
        "--interval", str(args.interval),
        "--tick-timeout", str(args.tick_timeout),
        "--rate-limit", str(args.rate_limit),
        "--error-threshold", str(args.error_threshold),
    ]
    if args.dry_run:
        daemon_args.append("--dry-run")

    # Auto-calculate heartbeat stale threshold if user didn't override
    auto_stale = 2 * args.interval + args.tick_timeout
    heartbeat_stale = max(args.heartbeat_stale, auto_stale)

    watchdog = KSeFWatchdog(
        daemon_args,
        heartbeat_stale_s=heartbeat_stale,
        max_restarts_per_hour=args.max_restarts,
    )
    return watchdog.run()


if __name__ == "__main__":
    sys.exit(main())
