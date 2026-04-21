"""Generuje Excel template z atrybutami produktów z CDN.AtrybutyKlasy (GIDTyp=16).

Użycie:
  python tools/xl_attribute_template.py
  python tools/xl_attribute_template.py --output sciezka/template.xlsx --cols 10
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Font, PatternFill

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.lib.sql_client import SqlClient

DEFAULT_OUTPUT = Path("documents/Wzory plików/Atrybuty produktów - template.xlsx")
DEFAULT_AKRONIM_COLS = 10

TYPE_LABELS = {1: "TAK / NIE", 2: "tekst", 3: "liczba", 4: "lista*"}

_QUERY_ATTRS = """
SELECT ak.AtK_Nazwa, ak.AtK_Typ, ak.AtK_Wielowart, ak.AtK_Zamknieta
FROM CDN.AtrybutyKlasy ak
INNER JOIN CDN.AtrybutyObiekty ao ON ao.AtO_AtKId = ak.AtK_ID
WHERE ao.AtO_GIDTyp = 16
ORDER BY ak.AtK_Nazwa
"""

_QUERY_LIST_VALUES = """
SELECT ak.AtK_Nazwa, aw.AtW_Wartosc
FROM CDN.AtrybutyWartosci aw
INNER JOIN CDN.AtrybutyKlasy ak ON ak.AtK_ID = aw.AtW_AtKId
INNER JOIN CDN.AtrybutyObiekty ao ON ao.AtO_AtKId = ak.AtK_ID
WHERE ao.AtO_GIDTyp = 16 AND ak.AtK_Typ = 4 AND aw.AtW_Wartosc != ''
ORDER BY ak.AtK_Nazwa, aw.AtW_Wartosc
"""

_HEADER_FILL = PatternFill("solid", fgColor="1F4E79")
_HEADER_FONT = Font(bold=True, color="FFFFFF", size=11)
_TYPE_FILL   = PatternFill("solid", fgColor="D6E4F0")
_TYPE_FONT   = Font(italic=True, color="2F5597", size=10)
_LIST_FILL   = PatternFill("solid", fgColor="FFF2CC")


def _fetch(client: SqlClient, query: str) -> list:
    result = client.execute(query, inject_top=None)
    if not result["ok"]:
        raise RuntimeError(result["error"]["message"])
    return result["rows"]


def generate_template(output: Path, akronim_cols: int) -> dict:
    client = SqlClient()

    attrs = _fetch(client, _QUERY_ATTRS)
    list_values_raw = _fetch(client, _QUERY_LIST_VALUES)

    list_values: dict[str, list[str]] = defaultdict(list)
    for name, val in list_values_raw:
        list_values[name.strip()].append(val)

    wb = Workbook()
    ws = wb.active
    ws.title = "Atrybuty produktów"

    # --- Wiersz 1: nagłówek ---
    ws.cell(1, 1, "Atrybut / Akronim →").font = Font(bold=True, size=11)
    ws.cell(1, 2, "Typ").font = Font(bold=True, size=11)
    for col in range(3, 3 + akronim_cols):
        cell = ws.cell(1, col, f"Akronim_{col - 2}")
        cell.fill = _HEADER_FILL
        cell.font = _HEADER_FONT
        cell.alignment = Alignment(horizontal="center")

    ws.cell(1, 1).fill = PatternFill("solid", fgColor="2E75B6")
    ws.cell(1, 1).font = Font(bold=True, color="FFFFFF", size=11)
    ws.cell(1, 2).fill = PatternFill("solid", fgColor="2E75B6")
    ws.cell(1, 2).font = Font(bold=True, color="FFFFFF", size=11)

    # --- Wiersze 2+: atrybuty ---
    for row_idx, (name, typ, wielowart, zamknieta) in enumerate(attrs, start=2):
        type_label = TYPE_LABELS.get(typ, str(typ))
        if zamknieta:
            type_label += " (zamknięta)"

        name_cell = ws.cell(row_idx, 1, name)
        name_cell.font = Font(bold=True, size=10)

        type_cell = ws.cell(row_idx, 2, type_label)
        type_cell.fill = _TYPE_FILL
        type_cell.font = _TYPE_FONT
        type_cell.alignment = Alignment(horizontal="center")

        if typ == 4 and name.strip() in list_values:
            values = list_values[name.strip()]
            comment_text = "Dopuszczalne wartości:\n" + "\n".join(f"• {v}" for v in values)
            comment = Comment(comment_text, "System")
            comment.width = 250
            comment.height = min(300, 20 + len(values) * 16)
            type_cell.comment = comment
            for col in range(3, 3 + akronim_cols):
                ws.cell(row_idx, col).fill = _LIST_FILL

    # --- Wymiary kolumn ---
    ws.column_dimensions["A"].width = 36
    ws.column_dimensions["B"].width = 20
    for col_letter in [chr(ord("C") + i) for i in range(akronim_cols)]:
        ws.column_dimensions[col_letter].width = 18

    ws.freeze_panes = "C2"
    ws.row_dimensions[1].height = 22

    output.parent.mkdir(parents=True, exist_ok=True)
    wb.save(output)

    return {
        "ok": True,
        "data": {"path": str(output), "attributes": len(attrs), "akronim_cols": akronim_cols},
        "error": None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generuj Excel template atrybutów produktów")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--cols", type=int, default=DEFAULT_AKRONIM_COLS,
                        help="Liczba kolumn na akronimy (domyślnie: 10)")
    args = parser.parse_args()

    result = generate_template(args.output, args.cols)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
