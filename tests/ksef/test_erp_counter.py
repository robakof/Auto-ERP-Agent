"""Tests for core.ksef.adapters.erp_counter — ERP coverage counting."""
from __future__ import annotations

from datetime import date

import pytest

from core.ksef.adapters.erp_counter import EligibleDoc, _classify, _parse_rows, fetch_eligible


# ---- _classify ---------------------------------------------------------------

@pytest.mark.parametrize("typ, zwr, expected", [
    (2033, 0, "FS"),
    (2033, 99, "FS"),        # FS regardless of ZwrNumer
    (2041, 1, "FSK"),
    (2041, 42, "FSK"),
    (2041, 0, "FSK_SKONTO"),
])
def test_classify(typ, zwr, expected):
    assert _classify(typ, zwr) == expected


# ---- _parse_rows -------------------------------------------------------------

_COLUMNS = ["gid", "typ", "zwr_numer", "nr_faktury", "data_wystawienia"]

def test_parse_rows_basic():
    rows = [
        [101, 2033, 0, "FS-1/04/26/S", "2026-04-22"],
        [201, 2041, 5, "FSK-1/04/26/S", "2026-04-22"],
        [301, 2041, 0, "FSK-2/04/26/S", "2026-04-23"],
    ]
    docs = _parse_rows(_COLUMNS, rows)

    assert len(docs) == 3
    assert docs[0] == EligibleDoc(gid=101, rodzaj="FS", nr_faktury="FS-1/04/26/S", data_wystawienia=date(2026, 4, 22))
    assert docs[1].rodzaj == "FSK"
    assert docs[2].rodzaj == "FSK_SKONTO"


def test_parse_rows_empty():
    assert _parse_rows(_COLUMNS, []) == []


def test_parse_rows_date_object():
    """If SQL driver returns date objects instead of strings."""
    rows = [[101, 2033, 0, "FS-1/04/26/S", date(2026, 4, 22)]]
    docs = _parse_rows(_COLUMNS, rows)
    assert docs[0].data_wystawienia == date(2026, 4, 22)


# ---- fetch_eligible ----------------------------------------------------------

def test_fetch_eligible_success():
    def fake_run_query(sql):
        return {
            "ok": True,
            "data": {
                "columns": _COLUMNS,
                "rows": [
                    [10, 2033, 0, "FS-10/04/26/S", "2026-04-22"],
                    [20, 2041, 3, "FSK-20/04/26/S", "2026-04-22"],
                ],
            },
        }

    docs = fetch_eligible(fake_run_query, since=date(2026, 4, 1))
    assert len(docs) == 2
    assert docs[0].rodzaj == "FS"
    assert docs[1].rodzaj == "FSK"


def test_fetch_eligible_error():
    def failing_query(sql):
        return {"ok": False, "error": {"message": "Connection refused"}}

    with pytest.raises(RuntimeError, match="Connection refused"):
        fetch_eligible(failing_query)


def test_fetch_eligible_date_filter_in_sql():
    """Verify the date filter is injected into SQL."""
    captured_sql = []
    def spy_query(sql):
        captured_sql.append(sql)
        return {"ok": True, "data": {"columns": _COLUMNS, "rows": []}}

    fetch_eligible(spy_query, since=date(2026, 4, 15))
    assert "2026-04-15" in captured_sql[0]


def test_fetch_eligible_no_date():
    """No date filter — SQL should not contain date condition."""
    captured_sql = []
    def spy_query(sql):
        captured_sql.append(sql)
        return {"ok": True, "data": {"columns": _COLUMNS, "rows": []}}

    fetch_eligible(spy_query, since=None)
    assert "DATEADD(day, n.TrN_Data2" not in captured_sql[0] or "1800-12-28') >= '" not in captured_sql[0]
