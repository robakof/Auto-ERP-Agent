"""Testy pp_demand.fetch_demand — mockuje SqlClient."""
import datetime
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.lib.pp_demand import fetch_demand

D2025 = datetime.date(2025, 4, 11)
D2026 = datetime.date(2026, 6, 15)

_COLS = ["ID_Zamowienia", "Nr_Zamowienia", "Data_Wystawienia", "Data_Realizacji",
         "Kontrahent_Kod", "Kontrahent_Nazwa", "Nr_Pozycji",
         "Towar_Kod", "Towar_Nazwa", "Ilosc", "Jednostka", "Opis"]

_ROWS = [
    [1, "ZO/2025/001", D2025, D2025, "KNT1", "Firma A", 1, "CZNI001", "Znicz A", 100, "szt", "Zamówienie X"],
    [2, "ZO/2025/002", D2025, D2025, "KNT2", "Firma B", 1, "CZNI002", "Znicz B", 50,  "szt", "Zamówienie Y"],
    [3, "ZO/2026/001", D2026, D2026, "KNT1", "Firma A", 1, "CZNI003", "Znicz C", 200, "szt", "Zamówienie Z"],
]

_MOCK_RESULT = {"ok": True, "columns": _COLS, "rows": _ROWS}


def _mock_sql():
    mock = MagicMock()
    mock.return_value.execute.return_value = _MOCK_RESULT
    return mock


def test_fetch_demand_filtruje_rok_2025():
    with patch("tools.lib.pp_demand.SqlClient", _mock_sql()):
        result = fetch_demand(2025)
    kody = [r["Towar_Kod"] for r in result]
    assert "CZNI001" in kody
    assert "CZNI002" in kody
    assert "CZNI003" not in kody


def test_fetch_demand_filtruje_rok_2026():
    with patch("tools.lib.pp_demand.SqlClient", _mock_sql()):
        result = fetch_demand(2026)
    kody = [r["Towar_Kod"] for r in result]
    assert "CZNI003" in kody
    assert "CZNI001" not in kody


def test_fetch_demand_zwraca_dicts():
    with patch("tools.lib.pp_demand.SqlClient", _mock_sql()):
        result = fetch_demand(2025)
    assert isinstance(result[0], dict)
    assert "Towar_Kod" in result[0]
    assert "Ilosc" in result[0]


def test_fetch_demand_sql_error():
    mock = MagicMock()
    mock.return_value.execute.return_value = {
        "ok": False, "error": {"message": "Brak połączenia"}
    }
    with patch("tools.lib.pp_demand.SqlClient", mock):
        try:
            fetch_demand(2025)
            assert False, "Powinien rzucić RuntimeError"
        except RuntimeError as e:
            assert "Brak połączenia" in str(e)
