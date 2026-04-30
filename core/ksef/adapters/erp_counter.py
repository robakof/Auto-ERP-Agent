"""Lightweight ERP counter — fetches eligible document GIDs for coverage check.

    from core.ksef.adapters.erp_counter import fetch_eligible
    docs = fetch_eligible(run_query, since=date(2026, 4, 1))

Returns list[EligibleDoc] — one per document in Comarch matching KSeF criteria.
Classification (FS / FSK / FSK_RABAT) based on TrN_GIDTyp + TrN_ZwrNumer.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Callable

_SQL_PATH = Path(__file__).resolve().parents[3] / "solutions" / "ksef" / "ksef_count_eligible.sql"
_WHERE_MARKER = "AND n.TrN_Stan IN (3, 4, 5)"


@dataclass(frozen=True)
class EligibleDoc:
    """One eligible document from Comarch ERP."""
    gid: int
    rodzaj: str          # 'FS' | 'FSK' | 'FSK_RABAT'
    nr_faktury: str
    data_wystawienia: date


def fetch_eligible(
    run_query: Callable[[str], dict],
    *,
    since: date | None = None,
) -> list[EligibleDoc]:
    """Fetch all eligible documents from Comarch ERP, optionally filtered by date."""
    sql = _build_sql(since)
    res = run_query(sql)
    if not res.get("ok"):
        raise RuntimeError(f"ERP count query failed: {res.get('error', res)}")
    return _parse_rows(res["data"]["columns"], res["data"]["rows"])


def _build_sql(since: date | None) -> str:
    base = _SQL_PATH.read_text(encoding="utf-8")
    if since is None:
        return base
    extra = f"\n  AND DATEADD(day, n.TrN_Data2, '1800-12-28') >= '{since}'"
    return base.replace(_WHERE_MARKER, _WHERE_MARKER + extra)


def _classify(typ: int, zwr_numer: int, gid: int) -> str:
    if typ == 2033:
        return "FS"
    if zwr_numer == 0 or zwr_numer == gid:
        return "FSK_RABAT"
    return "FSK"


def _parse_rows(columns: list[str], rows: list[list]) -> list[EligibleDoc]:
    result: list[EligibleDoc] = []
    for row in rows:
        rec = dict(zip(columns, row, strict=True))
        d = rec["data_wystawienia"]
        if isinstance(d, str):
            d = date.fromisoformat(d[:10])
        result.append(EligibleDoc(
            gid=int(rec["gid"]),
            rodzaj=_classify(int(rec["typ"]), int(rec["zwr_numer"]), int(rec["gid"])),
            nr_faktury=str(rec["nr_faktury"]).strip(),
            data_wystawienia=d,
        ))
    return result
