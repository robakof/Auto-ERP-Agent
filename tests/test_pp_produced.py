"""Testy pp_produced.fetch_produced — mockuje SqlClient."""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.lib.pp_produced import fetch_produced

_COLS = ["Czni_Kod", "Suma_Qty"]
_ROWS = [
    ["CZNI001", 1200.0],
    ["CZNI002", 500.0],
    ["CZNI003", 0.0],
]
_MOCK_OK = {"ok": True, "columns": _COLS, "rows": _ROWS}
_MOCK_ERR = {"ok": False, "error": {"message": "Connection failed"}}


def _mock_sql(result):
    mock = MagicMock()
    mock.return_value.execute.return_value = result
    return mock


def test_fetch_produced_zwraca_dict(tmp_path):
    with patch("tools.lib.pp_produced.SqlClient", _mock_sql(_MOCK_OK)):
        result = fetch_produced(2025)
    assert isinstance(result, dict)
    assert result["CZNI001"] == 1200.0
    assert result["CZNI002"] == 500.0


def test_fetch_produced_zero_qty(tmp_path):
    with patch("tools.lib.pp_produced.SqlClient", _mock_sql(_MOCK_OK)):
        result = fetch_produced(2025)
    assert result["CZNI003"] == 0.0


def test_fetch_produced_sql_error():
    with patch("tools.lib.pp_produced.SqlClient", _mock_sql(_MOCK_ERR)):
        with pytest.raises(RuntimeError, match="Connection failed"):
            fetch_produced(2025)


def test_fetch_produced_puste_wyniki():
    mock_empty = {"ok": True, "columns": _COLS, "rows": []}
    with patch("tools.lib.pp_produced.SqlClient", _mock_sql(mock_empty)):
        result = fetch_produced(2025)
    assert result == {}


def test_fetch_produced_pomija_null_kod():
    mock_null = {"ok": True, "columns": _COLS, "rows": [[None, 100.0], ["CZNI001", 50.0]]}
    with patch("tools.lib.pp_produced.SqlClient", _mock_sql(mock_null)):
        result = fetch_produced(2025)
    assert None not in result
    assert "CZNI001" in result
