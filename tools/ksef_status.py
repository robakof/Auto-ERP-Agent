"""KSeF Shadow DB readonly status — podglad stanu wysylek.

Uzycie:
    py tools/ksef_status.py                              # ostatnie 20 wysylek
    py tools/ksef_status.py --limit 50
    py tools/ksef_status.py --status ERROR
    py tools/ksef_status.py --gid 123456                 # wszystkie attempts (FS+FSK)
    py tools/ksef_status.py --gid 123456 --rodzaj FS
    py tools/ksef_status.py --today                      # tylko dzisiejsze (local date)

Filtry laczone addytywnie: kazdy kolejny filtr zawiera wynik poprzedniego.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.ksef.adapters.repo import ShipmentRepository
from core.ksef.domain.shipment import ShipmentStatus, Wysylka

_DEFAULT_DB = Path("data/ksef.db")
_COLS = ("id", "gid", "rodz", "nr", "status", "ksef_number", "att", "sent_at")


def main() -> int:
    parser = argparse.ArgumentParser(description="KSeF Shadow DB status")
    parser.add_argument("--db", type=Path, default=_DEFAULT_DB)
    parser.add_argument("--status", type=str, default=None, help="filtr po statusie")
    parser.add_argument("--gid", type=int, default=None, help="filtr po gid_erp")
    parser.add_argument("--rodzaj", choices=["FS", "FSK"], default=None,
                        help="zawez do typu dokumentu (tylko razem z --gid)")
    parser.add_argument("--today", action="store_true",
                        help="tylko dzisiejsze (created_at w lokalnej strefie)")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    if not args.db.exists():
        print(f"Brak DB: {args.db}. Uruchom: py tools/ksef_init_db.py", file=sys.stderr)
        return 1

    rows = _select(ShipmentRepository(args.db), args)
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


def _to_local_date(naive_utc: datetime):
    return naive_utc.replace(tzinfo=timezone.utc).astimezone().date()


def _today_local():
    return datetime.now().astimezone().date()


def _fmt_dt(dt: datetime | None) -> str:
    return dt.strftime("%Y-%m-%d %H:%M") if dt else "-"


if __name__ == "__main__":
    raise SystemExit(main())
