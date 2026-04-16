"""Unit tests ScanErpUseCase — mock run_query + repo."""
from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

import pytest

from core.ksef.usecases.scan_erp import PendingDocument, ScanErpUseCase


# ---- helpers ----------------------------------------------------------------

def _make_erp_response(rows: list[dict]) -> dict:
    if not rows:
        return {"ok": True, "data": {"columns": ["gid", "nr_faktury", "data_wystawienia"], "rows": []}}
    columns = list(rows[0].keys())
    return {
        "ok": True,
        "data": {
            "columns": columns,
            "rows": [[r[c] for c in columns] for r in rows],
        },
    }


def _erp_error() -> dict:
    return {"ok": False, "error": {"message": "connection refused"}}


@pytest.fixture
def repo():
    r = MagicMock()
    r.get_latest.return_value = None  # nothing known by default
    return r


# ---- tests ------------------------------------------------------------------

def test_scan_returns_pending_fs(repo):
    rows = [{"gid": 59, "nr_faktury": "FS-59/04/26/SPKR", "data_wystawienia": "2026-04-14"}]
    run_query = MagicMock(side_effect=[_make_erp_response(rows), _make_erp_response([])])
    uc = ScanErpUseCase(run_query, repo)

    result = uc.scan()

    assert len(result) == 1
    assert result[0].gid == 59
    assert result[0].rodzaj == "FS"
    assert result[0].nr_faktury == "FS-59/04/26/SPKR"


def test_scan_returns_pending_fsk(repo):
    rows_fsk = [{"gid": 1, "nr_faktury": "FSK-1/04/26/SPKRK", "data_wystawienia": "2026-04-14"}]
    run_query = MagicMock(side_effect=[_make_erp_response([]), _make_erp_response(rows_fsk)])
    uc = ScanErpUseCase(run_query, repo)

    result = uc.scan()

    assert len(result) == 1
    assert result[0].rodzaj == "FSK"


def test_scan_excludes_already_in_shadow_db(repo):
    rows = [
        {"gid": 59, "nr_faktury": "FS-59/04/26/SPKR", "data_wystawienia": "2026-04-14"},
        {"gid": 60, "nr_faktury": "FS-60/04/26/SPKR", "data_wystawienia": "2026-04-14"},
    ]
    run_query = MagicMock(side_effect=[_make_erp_response(rows), _make_erp_response([])])
    repo.get_latest.side_effect = lambda gid, rodzaj: MagicMock() if gid == 59 else None
    uc = ScanErpUseCase(run_query, repo)

    result = uc.scan()

    assert len(result) == 1
    assert result[0].gid == 60


def test_scan_excludes_accepted(repo):
    rows = [{"gid": 59, "nr_faktury": "FS-59/04/26/SPKR", "data_wystawienia": "2026-04-14"}]
    run_query = MagicMock(side_effect=[_make_erp_response(rows), _make_erp_response([])])
    repo.get_latest.return_value = MagicMock()  # known = skip
    uc = ScanErpUseCase(run_query, repo)

    result = uc.scan()

    assert len(result) == 0


def test_scan_excludes_error(repo):
    rows = [{"gid": 99, "nr_faktury": "FS-99/04/26/SPKR", "data_wystawienia": "2026-04-14"}]
    run_query = MagicMock(side_effect=[_make_erp_response(rows), _make_erp_response([])])
    repo.get_latest.return_value = MagicMock()  # known (even ERROR) = skip
    uc = ScanErpUseCase(run_query, repo)

    result = uc.scan()

    assert len(result) == 0


def test_scan_empty_erp_returns_empty(repo):
    run_query = MagicMock(side_effect=[_make_erp_response([]), _make_erp_response([])])
    uc = ScanErpUseCase(run_query, repo)

    result = uc.scan()

    assert result == []


def test_scan_sql_error_returns_empty(repo):
    run_query = MagicMock(side_effect=[_erp_error(), _erp_error()])
    uc = ScanErpUseCase(run_query, repo)

    result = uc.scan()

    assert result == []


def test_scan_sorted_by_date_asc(repo):
    rows = [
        {"gid": 60, "nr_faktury": "FS-60", "data_wystawienia": "2026-04-15"},
        {"gid": 59, "nr_faktury": "FS-59", "data_wystawienia": "2026-04-14"},
        {"gid": 61, "nr_faktury": "FS-61", "data_wystawienia": "2026-04-16"},
    ]
    run_query = MagicMock(side_effect=[_make_erp_response(rows), _make_erp_response([])])
    uc = ScanErpUseCase(run_query, repo)

    result = uc.scan()

    dates = [d.data_wystawienia for d in result]
    assert dates == sorted(dates)


def test_scan_date_as_date_object(repo):
    rows = [{"gid": 59, "nr_faktury": "FS-59", "data_wystawienia": date(2026, 4, 14)}]
    run_query = MagicMock(side_effect=[_make_erp_response(rows), _make_erp_response([])])
    uc = ScanErpUseCase(run_query, repo)

    result = uc.scan()

    assert result[0].data_wystawienia == date(2026, 4, 14)
