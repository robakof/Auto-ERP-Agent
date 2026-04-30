"""KSeF report CLI — generate and send daily invoice reports.

    py tools/ksef_report.py --send-email          # send via SMTP
    py tools/ksef_report.py --stdout               # print to terminal
    py tools/ksef_report.py --file raport.txt      # save to file
    py tools/ksef_report.py --since 7d --stdout    # last 7 days
    py tools/ksef_report.py --no-coverage --stdout  # skip ERP coverage check
"""
from __future__ import annotations

import argparse
import logging
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.ksef.adapters.email_sender import SmtpEmailSender
from core.ksef.adapters.repo import ShipmentRepository
from core.ksef.adapters.report_renderer import render_html, render_plain, render_subject
from core.ksef.config import load_smtp_config
from core.ksef.usecases.report import build_report

from core.ksef import paths as ksef_paths

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_LOG = logging.getLogger(__name__)


def _parse_since(value: str) -> datetime:
    """Parse --since value: 'today', '24h', '7d', or ISO date."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if value == "today":
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    match = re.match(r"^(\d+)([hd])$", value)
    if match:
        n, unit = int(match.group(1)), match.group(2)
        delta = timedelta(hours=n) if unit == "h" else timedelta(days=n)
        return now - delta
    return datetime.fromisoformat(value)


def _send_email(report_data) -> None:
    cfg = load_smtp_config()
    sender = SmtpEmailSender(
        host=cfg.host, port=cfg.port, user=cfg.user,
        password=cfg.password, use_ssl=cfg.use_ssl,
    )
    subject = render_subject(report_data, prefix=cfg.subject_prefix)
    html = render_html(report_data)
    plain = render_plain(report_data)
    sender.send(
        to=cfg.report_to, from_=cfg.report_from,
        subject=subject, html=html, plain=plain,
    )
    print(f"Email sent to {cfg.report_to}")


def _try_fetch_eligible(since: datetime):
    """Try to fetch eligible docs from Comarch ERP. Returns list or None on failure."""
    try:
        from sql_query import run_query  # noqa: PLC0415
        from core.ksef.adapters.erp_counter import fetch_eligible
        return fetch_eligible(
            lambda sql: run_query(sql, inject_top=None),
            since=since.date(),
        )
    except Exception as exc:
        _LOG.warning("ERP coverage check skipped: %s", exc)
        return None


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    args = _parse_args()

    repo = ShipmentRepository(ksef_paths.db_path())
    since = _parse_since(args.since)

    erp_eligible = None
    if not args.no_coverage:
        erp_eligible = _try_fetch_eligible(since)

    report_data = build_report(repo, since=since, erp_eligible=erp_eligible)

    if args.send_email:
        _send_email(report_data)
    elif args.file:
        path = Path(args.file)
        path.write_text(render_plain(report_data), encoding="utf-8")
        print(f"Report saved to {path}")
    else:
        print(render_plain(report_data))

    return 0


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="KSeF report — daily invoice summary")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--send-email", action="store_true",
                      help="Send report via SMTP (config from .env)")
    mode.add_argument("--file", type=str, help="Save plain text report to file")
    mode.add_argument("--stdout", action="store_true", default=True,
                      help="Print to terminal (default)")
    p.add_argument("--since", type=str, default="today",
                   help="Time range: 'today' (default), '24h', '7d', or ISO date")
    p.add_argument("--no-coverage", action="store_true",
                   help="Skip ERP coverage check (Comarch vs KSeF)")
    return p.parse_args()


if __name__ == "__main__":
    sys.exit(main())
