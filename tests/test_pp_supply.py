"""Testy pp_supply.fetch_supply — mockuje SqlClient."""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.lib.pp_supply import fetch_supply

_COLS = ["Towar_Kod", "Towar_Nazwa", "Jednostka", "Stan"]
_ROWS = [
    ["SZ0324", "Szkło SZ0324", "szt", 5000],
    ["DK0003", "Dekiel DK0003", "szt", 12000],
    ["FO0003", "Folia FO0003", "rol", 80],
]
_MOCK_RESULT = {"ok": True, "columns": _COLS, "rows": _ROWS}


def _mock_sql():
    mock = MagicMock()
    mock.return_value.execute.return_value = _MOCK_RESULT
    return mock


def test_fetch_supply_zwraca_dict():
    with patch("tools.lib.pp_supply.SqlClient", _mock_sql()):
        result = fetch_supply()
    assert isinstance(result, dict)
    assert result["SZ0324"] == 5000.0
    assert result["DK0003"] == 12000.0
    assert result["FO0003"] == 80.0


def test_fetch_supply_wartosci_float():
    with patch("tools.lib.pp_supply.SqlClient", _mock_sql()):
        result = fetch_supply()
    for v in result.values():
        assert isinstance(v, float)


def test_fetch_supply_sql_error():
    mock = MagicMock()
    mock.return_value.execute.return_value = {
        "ok": False, "error": {"message": "Timeout"}
    }
    with patch("tools.lib.pp_supply.SqlClient", mock):
        try:
            fetch_supply()
            assert False, "Powinien rzucić RuntimeError"
        except RuntimeError as e:
            assert "Timeout" in str(e)


def test_fetch_supply_pomija_puste_kody():
    rows_with_empty = _ROWS + [["", "Brak kodu", "szt", 10], [None, "Null kod", "szt", 5]]
    mock = MagicMock()
    mock.return_value.execute.return_value = {
        "ok": True, "columns": _COLS, "rows": rows_with_empty
    }
    with patch("tools.lib.pp_supply.SqlClient", mock):
        result = fetch_supply()
    assert "" not in result
    assert None not in result
    assert len(result) == 3
