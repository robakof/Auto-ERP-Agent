"""ScanErp use case — detect newly approved FS/FSK in ERP, filter vs shadow DB.

Lightweight scan query (GID + nr + date only). Full document data loaded lazily
by ErpReader when daemon decides to send.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from typing import Callable

from core.ksef.adapters.erp_reader import RunQuery
from core.ksef.adapters.repo import ShipmentRepository

_LOG = logging.getLogger("ksef.scan")

_SQL_SCAN_FS = """\
SELECT
    n.TrN_GIDNumer                                          AS gid,
    'FS-' + CAST(n.TrN_TrNNumer AS VARCHAR(20))
        + '/' + RIGHT('0' + CAST(MONTH(DATEADD(day, n.TrN_Data2, '1800-12-28')) AS VARCHAR(2)), 2)
        + '/' + RIGHT(CAST(YEAR(DATEADD(day, n.TrN_Data2, '1800-12-28')) AS VARCHAR(4)), 2)
        + '/' + RTRIM(n.TrN_TrNSeria)                      AS nr_faktury,
    CONVERT(DATE, DATEADD(day, n.TrN_Data2, '1800-12-28'))  AS data_wystawienia
FROM CDN.TraNag n
WHERE n.TrN_GIDTyp = 2033
  AND n.TrN_Stan IN (3, 4, 5)
  AND n.TrN_Data2 = DATEDIFF(day, '1800-12-28', CAST(GETDATE() AS DATE))
ORDER BY n.TrN_Data2, n.TrN_GIDNumer
"""

_SQL_SCAN_FSK = """\
SELECT
    n.TrN_GIDNumer                                          AS gid,
    'FSK-' + CAST(n.TrN_TrNNumer AS VARCHAR(20))
        + '/' + RIGHT('0' + CAST(MONTH(DATEADD(day, n.TrN_Data2, '1800-12-28')) AS VARCHAR(2)), 2)
        + '/' + RIGHT(CAST(YEAR(DATEADD(day, n.TrN_Data2, '1800-12-28')) AS VARCHAR(4)), 2)
        + '/' + RTRIM(n.TrN_TrNSeria)                      AS nr_faktury,
    CONVERT(DATE, DATEADD(day, n.TrN_Data2, '1800-12-28'))  AS data_wystawienia,
    CASE WHEN n.TrN_ZwrNumer = 0 THEN 1 ELSE 0 END         AS is_skonto
FROM CDN.TraNag n
WHERE n.TrN_GIDTyp = 2041
  AND n.TrN_Stan IN (3, 4, 5)
  AND n.TrN_Data2 = DATEDIFF(day, '1800-12-28', CAST(GETDATE() AS DATE))
ORDER BY n.TrN_Data2, n.TrN_GIDNumer
"""


@dataclass(frozen=True)
class PendingDocument:
    """Dokument z ERP wykryty do wysylki."""

    gid: int
    rodzaj: str       # "FS" | "FSK"
    nr_faktury: str
    data_wystawienia: date


class ScanErpUseCase:
    """Wykrywa nowo zatwierdzone dokumenty z ERP nie obecne w shadow DB."""

    def __init__(
        self,
        run_query: RunQuery,
        repo: ShipmentRepository,
    ) -> None:
        self._run_query = run_query
        self._repo = repo

    def scan(self) -> list[PendingDocument]:
        """Scan ERP for approved FS+FSK, filter out those already in shadow DB."""
        fs_docs = self._query_erp(_SQL_SCAN_FS, "FS")
        fsk_docs = self._query_erp(_SQL_SCAN_FSK, "FSK")
        all_docs = fs_docs + fsk_docs

        pending = [d for d in all_docs if not self._is_known(d.gid, d.rodzaj)]
        pending.sort(key=lambda d: d.data_wystawienia)

        _LOG.info(
            '{"event": "scan_complete", "erp_total": %d, "pending": %d, "fs": %d, "fsk": %d, "fsk_skonto": %d}',
            len(all_docs), len(pending),
            sum(1 for d in pending if d.rodzaj == "FS"),
            sum(1 for d in pending if d.rodzaj == "FSK"),
            sum(1 for d in pending if d.rodzaj == "FSK_SKONTO"),
        )
        return pending

    def _query_erp(self, sql: str, rodzaj: str) -> list[PendingDocument]:
        """Execute scan SQL, map rows to PendingDocument."""
        res = self._run_query(sql)
        if not res.get("ok"):
            err = res.get("error", {})
            _LOG.error('{"event": "scan_erp_error", "rodzaj": "%s", "error": "%s"}', rodzaj, err)
            return []

        rows = res.get("data", {}).get("rows", [])
        columns = res.get("data", {}).get("columns", [])
        docs = []
        for row in rows:
            row_dict = dict(zip(columns, row)) if isinstance(row, (list, tuple)) else row
            try:
                actual_rodzaj = rodzaj
                if rodzaj == "FSK" and int(row_dict.get("is_skonto", 0)):
                    actual_rodzaj = "FSK_SKONTO"
                docs.append(PendingDocument(
                    gid=int(row_dict["gid"]),
                    rodzaj=actual_rodzaj,
                    nr_faktury=str(row_dict["nr_faktury"]),
                    data_wystawienia=_parse_date(row_dict["data_wystawienia"]),
                ))
            except (KeyError, ValueError, TypeError) as exc:
                _LOG.warning('{"event": "scan_row_skip", "row": "%s", "error": "%s"}', row_dict, exc)
        return docs

    def _is_known(self, gid: int, rodzaj: str) -> bool:
        """Check if GID already processed (any state in shadow DB)."""
        return self._repo.get_latest(gid, rodzaj) is not None


def _parse_date(value) -> date:
    """Parse date from SQL result (str or date object)."""
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])
