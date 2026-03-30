"""pp_export.py — Eksport planowania produkcji do Excel (4 arkusze).

Arkusz 1: Zamówienia CZNI
Arkusz 2: Zapotrzebowanie surowców
Arkusz 3: Stany OTOR_SUR
Arkusz 4: Gap Analysis (czerwone wiersze gdzie Brak > 0)
"""
from pathlib import Path

from openpyxl.styles import PatternFill

from tools.lib.excel_writer import ExcelWriter
from tools.lib.pp_gap import GapRow

_RED_FILL = PatternFill("solid", fgColor="FFFF9999")  # ARGB: alpha=FF, R=FF, G=99, B=99

_COLS_ORDERS = [
    "Nr_Zamowienia", "Data_Realizacji", "Kontrahent_Kod", "Kontrahent_Nazwa",
    "Towar_Kod", "Towar_Nazwa", "Ilosc", "Jednostka", "Opis",
]
_COLS_DEMAND = ["Surowiec_Kod", "Surowiec_Nazwa", "Ilosc_Potrzebna"]
_COLS_SUPPLY = ["Towar_Kod", "Towar_Nazwa", "Jednostka", "Stan"]
_COLS_GAP    = ["Surowiec_Kod", "Surowiec_Nazwa", "Potrzeba", "Dostepne", "Brak"]


def export_plan(
    demand_rows: list[dict],
    supply: dict[str, float],
    gaps: list[GapRow],
    supply_rows: list[dict],
    output_path: Path,
) -> None:
    """Zapisuje Excel z 4 arkuszami."""
    writer = ExcelWriter()
    _add_orders(writer, demand_rows)
    _add_demand(writer, gaps)
    _add_supply(writer, supply_rows)
    _add_gap(writer, gaps)
    try:
        writer.save(output_path)
    except PermissionError:
        raise RuntimeError(f"Nie można zapisać: {output_path}. Zamknij plik w Excelu.")


def _add_orders(writer: ExcelWriter, rows: list[dict]) -> None:
    data = [[r.get(c) for c in _COLS_ORDERS] for r in rows]
    data.sort(key=lambda r: (r[1] is None, r[1]))
    writer.add_sheet("Zamówienia CZNI", _COLS_ORDERS, data)


def _add_demand(writer: ExcelWriter, gaps: list[GapRow]) -> None:
    data = [[g.surowiec_kod, g.surowiec_nazwa, g.potrzeba] for g in gaps]
    data.sort(key=lambda r: r[0])
    writer.add_sheet("Zapotrzebowanie surowców", _COLS_DEMAND, data)


def _add_supply(writer: ExcelWriter, supply_rows: list[dict]) -> None:
    data = [[r.get(c) for c in _COLS_SUPPLY] for r in supply_rows]
    data.sort(key=lambda r: (r[0] or ""))
    writer.add_sheet("Stany OTOR_SUR", _COLS_SUPPLY, data)


def _add_gap(writer: ExcelWriter, gaps: list[GapRow]) -> None:
    data = [
        [g.surowiec_kod, g.surowiec_nazwa, g.potrzeba, g.dostepne, g.brak]
        for g in gaps
    ]
    writer.add_sheet("Gap Analysis", _COLS_GAP, data)
    _highlight_gap_rows(writer, gaps)


def _highlight_gap_rows(writer: ExcelWriter, gaps: list[GapRow]) -> None:
    """Czerwone tło dla wierszy gdzie Brak > 0 w arkuszu Gap Analysis."""
    wb = writer._wb
    ws = wb["Gap Analysis"]
    n_cols = len(_COLS_GAP)
    for row_idx, gap in enumerate(gaps, start=2):
        if gap.brak > 0:
            for col_idx in range(1, n_cols + 1):
                ws.cell(row=row_idx, column=col_idx).fill = _RED_FILL
