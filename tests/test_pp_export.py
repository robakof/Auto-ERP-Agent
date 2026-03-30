"""Testy pp_export.export_plan — weryfikacja struktury xlsx."""
import datetime
import sys
from pathlib import Path

import openpyxl
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.lib.pp_export import export_plan
from tools.lib.pp_gap import GapRow

_DEMAND = [
    {"Nr_Zamowienia": "ZO/2025/001", "Data_Realizacji": datetime.date(2025, 6, 1),
     "Kontrahent_Kod": "KNT1", "Kontrahent_Nazwa": "Firma A",
     "Towar_Kod": "CZNI001", "Towar_Nazwa": "Znicz A", "Ilosc": 100,
     "Jednostka": "szt", "Opis": "Zamówienie X"},
]

_SUPPLY_ROWS = [
    {"Towar_Kod": "SZ0324", "Towar_Nazwa": "Szkło", "Jednostka": "szt", "Stan": 5000},
]

_SUPPLY = {"SZ0324": 5000.0}

_GAPS = [
    GapRow("SZ0324", "Szkło", 1020.0, 5000.0, 0.0),
    GapRow("WK0001", "Wkład", 1000.0, 200.0, 800.0),
]


def test_export_tworzy_4_arkusze(tmp_path):
    out = tmp_path / "test.xlsx"
    export_plan(_DEMAND, _SUPPLY, _GAPS, _SUPPLY_ROWS, out)
    wb = openpyxl.load_workbook(out)
    assert len(wb.sheetnames) == 4
    assert "Zamówienia CZNI" in wb.sheetnames
    assert "Zapotrzebowanie surowców" in wb.sheetnames
    assert "Stany OTOR_SUR" in wb.sheetnames
    assert "Gap Analysis" in wb.sheetnames


def test_export_gap_czerwone_wiersze(tmp_path):
    out = tmp_path / "test.xlsx"
    export_plan(_DEMAND, _SUPPLY, _GAPS, _SUPPLY_ROWS, out)
    wb = openpyxl.load_workbook(out)
    ws = wb["Gap Analysis"]
    # WK0001 brak=800 → powinien być czerwony (sortowanie Brak DESC → wiersz 2)
    red_rows = []
    for row_idx in range(2, len(_GAPS) + 2):
        fill = ws.cell(row=row_idx, column=1).fill
        if fill and fill.fgColor and fill.fgColor.rgb == "FFFF9999":
            red_rows.append(row_idx)
    assert len(red_rows) >= 1, "Powinien być co najmniej 1 czerwony wiersz"


def test_export_permission_error(tmp_path):
    out = tmp_path / "test.xlsx"
    out.write_bytes(b"")
    out.chmod(0o444)
    try:
        export_plan(_DEMAND, _SUPPLY, _GAPS, _SUPPLY_ROWS, out)
    except RuntimeError as e:
        assert "Zamknij plik" in str(e)
    except PermissionError:
        pass  # też akceptowalny wynik na Windows
    finally:
        out.chmod(0o666)
