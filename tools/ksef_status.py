"""KSeF Shadow DB readonly status — podglad stanu wysylek.

Uzycie:
    py tools/ksef_status.py                              # --summary (default)
    py tools/ksef_status.py --summary                    # podsumowanie: dzis, 7 dni, total
    py tools/ksef_status.py --limit 50                   # lista ostatnich
    py tools/ksef_status.py --status ERROR
    py tools/ksef_status.py --gid 123456                 # wszystkie attempts (FS+FSK)
    py tools/ksef_status.py --gid 123456 --rodzaj FS
    py tools/ksef_status.py --today                      # tylko dzisiejsze (local date)

Filtry laczone addytywnie: kazdy kolejny filtr zawiera wynik poprzedniego.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.ksef import paths as ksef_paths
from core.ksef.adapters.repo import ShipmentRepository
from core.ksef.domain.shipment import ShipmentStatus, Wysylka
_COLS = ("id", "gid", "rodz", "nr", "status", "ksef_number", "att", "sent_at")

# Status list for summary — logical order (draft/active first, terminal last).
_SUMMARY_STATUS_ORDER = (
    ShipmentStatus.ACCEPTED,
    ShipmentStatus.SENT,
    ShipmentStatus.AUTH_PENDING,
    ShipmentStatus.QUEUED,
    ShipmentStatus.DRAFT,
    ShipmentStatus.ERROR,
    ShipmentStatus.REJECTED,
)
_ALERT_STATUSES = frozenset({ShipmentStatus.ERROR, ShipmentStatus.REJECTED})


def main() -> int:
    parser = argparse.ArgumentParser(description="KSeF Shadow DB status")
    parser.add_argument("--db", type=Path, default=None)
    parser.add_argument("--status", type=str, default=None, help="filtr po statusie")
    parser.add_argument("--gid", type=int, default=None, help="filtr po gid_erp")
    parser.add_argument("--rodzaj", choices=["FS", "FSK"], default=None,
                        help="zawez do typu dokumentu (tylko razem z --gid)")
    parser.add_argument("--today", action="store_true",
                        help="tylko dzisiejsze (created_at w lokalnej strefie)")
    parser.add_argument("--summary", action="store_true",
                        help="podsumowanie: dzis, ostatnie 7 dni, total")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()
    args.db = args.db or ksef_paths.db_path()

    if not args.db.exists():
        print(f"Brak DB: {args.db}. Uruchom: py tools/ksef_init_db.py", file=sys.stderr)
        return 1

    if args.rodzaj is not None and args.gid is None:
        print("Blad: --rodzaj wymaga --gid", file=sys.stderr)
        return 2

    repo = ShipmentRepository(args.db)

    # --summary is the default when no filters are provided.
    default_summary = not (
        args.status
        or args.gid is not None
        or args.today
        or args.limit != 20
    )
    if args.summary or default_summary:
        _render_summary(repo)
        return 0

    rows = _select(repo, args)
    if not rows:
        print("Brak wysylek.")
        return 0
    _render_table(rows)
    return 0


def _select(repo: ShipmentRepository, args: argparse.Namespace) -> list[Wysylka]:
    rows = _initial(repo, args)
    if args.status and args.gid is not None:
        rows = [w for w in rows if w.status.value == args.status.upper()]
    if args.today:
        rows = [w for w in rows if _to_local_date(w.created_at) == _today_local()]
    return rows


def _initial(repo: ShipmentRepository, args: argparse.Namespace) -> list[Wysylka]:
    if args.gid is not None:
        return repo.list_by_gid(args.gid, rodzaj=args.rodzaj, limit=args.limit)
    if args.status:
        try:
            status = ShipmentStatus(args.status.upper())
        except ValueError:
            print(f"Nieznany status: {args.status}", file=sys.stderr)
            return []
        return repo.list_by_status(status, limit=args.limit)
    return repo.list_recent(limit=args.limit)


def _render_table(rows: list[Wysylka]) -> None:
    data = [
        (str(w.id), str(w.gid_erp), w.rodzaj, w.nr_faktury, w.status.value,
         w.ksef_number or "-", str(w.attempt), _fmt_dt(w.sent_at))
        for w in rows
    ]
    widths = [max(len(c), max(len(r[i]) for r in data)) for i, c in enumerate(_COLS)]
    sep = "  "
    print(sep.join(c.ljust(w) for c, w in zip(_COLS, widths, strict=True)))
    print(sep.join("-" * w for w in widths))
    for r in data:
        print(sep.join(v.ljust(w) for v, w in zip(r, widths, strict=True)))


def _render_summary(repo: ShipmentRepository) -> None:
    now_local = datetime.now().astimezone()
    today_local = now_local.date()
    # created_at is naive UTC in DB — convert local boundaries to UTC for query.
    midnight_local = datetime.combine(today_local, datetime.min.time()).astimezone()
    since_today_utc = _to_naive_utc(midnight_local)
    since_week_utc = _to_naive_utc(now_local - timedelta(days=7))

    today = repo.count_by_status(since=since_today_utc)
    week = repo.count_by_status(since=since_week_utc)
    total = repo.count_by_status(since=None)
    recent = repo.list_recent(limit=1)

    print("=== KSeF Shadow DB — podsumowanie ===")
    print()
    print(f"Dzis ({today_local.isoformat()}):")
    _print_status_block(today)
    print()
    print("Ostatnie 7 dni:")
    _print_status_block(week)
    print()
    all_total = sum(total.values())
    print(f"Lacznie w DB:  {all_total}")
    if recent:
        last = recent[0]
        ts = _fmt_dt(last.sent_at or last.created_at)
        print(
            f"Ostatnia wysylka: {ts} "
            f"({last.nr_faktury} -> {last.status.value})"
        )


def _print_status_block(counts: dict[ShipmentStatus, int]) -> None:
    for status in _SUMMARY_STATUS_ORDER:
        n = counts.get(status, 0)
        if n == 0 and status not in _ALERT_STATUSES:
            continue  # skip empty non-alert rows to reduce noise
        alert = " <- UWAGA" if status in _ALERT_STATUSES and n > 0 else ""
        print(f"  {status.value:<13} {n:>3}{alert}")


def _to_naive_utc(dt: datetime) -> datetime:
    """Convert aware datetime to naive UTC (matching repo storage)."""
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def _to_local_date(naive_utc: datetime):
    return naive_utc.replace(tzinfo=timezone.utc).astimezone().date()


def _today_local():
    return datetime.now().astimezone().date()


def _fmt_dt(dt: datetime | None) -> str:
    return dt.strftime("%Y-%m-%d %H:%M") if dt else "-"


if __name__ == "__main__":
    raise SystemExit(main())
