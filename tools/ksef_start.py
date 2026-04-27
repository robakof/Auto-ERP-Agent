"""KSeF master launcher — watchdog + daemon + scheduled daily report.

    py tools/ksef_start.py                     # default: report at 13:30
    py tools/ksef_start.py --report-time 17:00 # report at 17:00
    py tools/ksef_start.py --no-report         # daemon only, no report
    py tools/ksef_start.py --once              # one scan+send, no watchdog
    py tools/ksef_start.py --interval 300      # daemon tick every 5 min

Manages:
1. Watchdog (auto-restarts daemon on crash/stale heartbeat)
2. Daemon (scan ERP -> generate XML -> send to KSeF)
3. Daily report email at scheduled time
"""
from __future__ import annotations

import argparse
import logging
import os
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

load_dotenv(override=False)

from core.ksef import paths as ksef_paths
from core.ksef.config import load_config as load_ksef_config

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_LOG = logging.getLogger("ksef.start")

_shutdown = threading.Event()


def _send_report() -> bool:
    """Run ksef_report.py --send-email. Returns True on success."""
    cmd = [sys.executable, str(_PROJECT_ROOT / "tools" / "ksef_report.py"),
           "--send-email"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            _LOG.info("[KSeF] Raport wyslany. %s", result.stdout.strip())
            return True
        else:
            _LOG.error("[KSeF] Blad raportu: %s", result.stderr.strip())
            return False
    except Exception as exc:
        _LOG.error("[KSeF] Blad raportu: %s", exc)
        return False


def _report_scheduler(report_time: str) -> None:
    """Background thread — waits for report_time (HH:MM), sends report once per day."""
    hour, minute = (int(x) for x in report_time.split(":"))
    sent_today: str | None = None

    while not _shutdown.is_set():
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")

        if now.hour == hour and now.minute == minute and sent_today != today:
            _LOG.info("[KSeF] %s — Wysylam raport dzienny...", report_time)
            if _send_report():
                sent_today = today

        _shutdown.wait(30)


def _run_watchdog(args: argparse.Namespace) -> int:
    """Start watchdog as subprocess, wait for it."""
    cmd = [sys.executable, str(_PROJECT_ROOT / "tools" / "ksef_watchdog.py"),
           "--interval", str(args.interval),
           "--rate-limit", str(args.rate_limit),
           "--error-threshold", str(args.error_threshold)]
    if args.dry_run:
        cmd.append("--dry-run")

    _LOG.info("[KSeF] Watchdog + daemon uruchomiony (tick co %ds)", int(args.interval))
    proc = subprocess.Popen(cmd)

    def _handle_signal(sig, frame):
        _shutdown.set()
        proc.terminate()

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    return proc.wait()


def _run_once(args: argparse.Namespace) -> int:
    """Single scan+send, no watchdog."""
    cmd = [sys.executable, str(_PROJECT_ROOT / "tools" / "ksef_daemon.py"), "--once"]
    if args.rate_limit:
        cmd.extend(["--rate-limit", str(args.rate_limit)])
    if args.dry_run:
        cmd.append("--dry-run")
    _LOG.info("[KSeF] Jednorazowy scan + wysylka...")
    return subprocess.run(cmd).returncode


def _env_float(key: str, fallback: float) -> float:
    val = os.environ.get(key)
    return float(val) if val else fallback


def _env_int(key: str, fallback: int) -> int:
    val = os.environ.get(key)
    return int(val) if val else fallback


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="KSeF master launcher")
    p.add_argument("--once", action="store_true",
                   help="One scan+send, then exit (no watchdog, no report)")
    p.add_argument("--interval", type=float,
                   default=_env_float("KSEF_DAEMON_INTERVAL", 900.0),
                   help="Daemon tick interval in seconds (default: 900)")
    p.add_argument("--rate-limit", type=int,
                   default=_env_int("KSEF_DAEMON_RATE_LIMIT", 10),
                   help="Max invoices per tick (default: 10)")
    p.add_argument("--error-threshold", type=int,
                   default=_env_int("KSEF_DAEMON_ERROR_THRESHOLD", 3),
                   help="Errors per tick before escalation (default: 3)")
    p.add_argument("--dry-run", action="store_true",
                   help="Preview only, no actual sending")
    p.add_argument("--report-time", type=str,
                   default=os.environ.get("KSEF_REPORT_TIME", "13:30"),
                   help="Time to send daily report HH:MM (default: 13:30)")
    p.add_argument("--no-report", action="store_true",
                   help="Disable daily report email")
    return p.parse_args()


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    args = _parse_args()

    cfg = load_ksef_config()
    _LOG.info("[KSeF] Start — srodowisko: %s", cfg.env)

    if args.once:
        return _run_once(args)

    # Start report scheduler in background thread
    if not args.no_report:
        _LOG.info("[KSeF] Raport zaplanowany na %s", args.report_time)
        report_thread = threading.Thread(
            target=_report_scheduler, args=(args.report_time,),
            daemon=True,
        )
        report_thread.start()

    _LOG.info("[KSeF] Ctrl+C aby zatrzymac")
    return _run_watchdog(args)


if __name__ == "__main__":
    sys.exit(main())
