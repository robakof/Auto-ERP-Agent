"""Generuje Excel template z atrybutami produktów z CDN.AtrybutyKlasy (GIDTyp=16).

Format:
  Wiersz 1: "Kod XL" | nazwa_atrybutu_1 | nazwa_atrybutu_2 | ...
  Wiersze 2+: twr_kod | wartość_1 | wartość_2 | ...

Użycie:
  python tools/xl_attribute_template.py
  python tools/xl_attribute_template.py --output sciezka/template.xlsx
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.lib.sql_client import SqlClient

DEFAULT_OUTPUT = Path("documents/Wzory plików/Atrybuty produktów - template.xlsx")

TYPE_LABELS = {1: "TAK / NIE", 2: "tekst", 3: "liczba", 4: "lista*"}

_QUERY_ATTRS = """
SELECT ak.AtK_Nazwa, ak.AtK_Typ, ak.AtK_Wielowart, ak.AtK_Zamknieta
FROM CDN.AtrybutyKlasy ak
INNER JOIN CDN.AtrybutyObiekty ao ON ao.AtO_AtKId = ak.AtK_ID
WHERE ao.AtO_GIDTyp = 16
ORDER BY ak.AtK_Nazwa
"""

_QUERY_PRODUCTS = """
SELECT Twr_Kod, Twr_Nazwa1
FROM CDN.TwrKarty
WHERE Twr_Archiwalny = 0
ORDER BY Twr_Kod
"""

_QUERY_LIST_VALUES = """
SELECT ak.AtK_Nazwa, aw.AtW_Wartosc
FROM CDN.AtrybutyWartosci aw
INNER JOIN CDN.AtrybutyKlasy ak ON ak.AtK_ID = aw.AtW_AtKId
INNER JOIN CDN.AtrybutyObiekty ao ON ao.AtO_AtKId = ak.AtK_ID
WHERE ao.AtO_GIDTyp = 16 AND ak.AtK_Typ = 4 AND aw.AtW_Wartosc != ''
ORDER BY ak.AtK_Nazwa, aw.AtW_Wartosc
"""

_QUERY_EXISTING_VALUES = """
SELECT tk.Twr_Kod, ak.AtK_Nazwa, a.Atr_Wartosc
FROM CDN.Atrybuty a
JOIN CDN.AtrybutyKlasy ak ON ak.AtK_Id = a.Atr_AtkId
JOIN CDN.TwrKarty tk ON tk.Twr_GIDNumer = a.Atr_ObiNumer AND tk.Twr_GIDTyp = a.Atr_ObiTyp
WHERE a.Atr_ObiTyp = 16
ORDER BY tk.Twr_Kod, ak.AtK_Nazwa
"""

_HEADER_FILL = PatternFill("solid", fgColor="1F4E79")
_HEADER_FONT = Font(bold=True, color="FFFFFF", size=11)
_LIST_FILL   = PatternFill("solid", fgColor="FFF2CC")


def _fetch(client: SqlClient, query: str) -> list:
    result = client.execute(query, inject_top=None)
    if not result["ok"]:
        raise RuntimeError(result["error"]["message"])
    return result["rows"]


def generate_template(output: Path) -> dict:
    client = SqlClient()

    attrs = _fetch(client, _QUERY_ATTRS)
    products = _fetch(client, _QUERY_PRODUCTS)
    list_values_raw = _fetch(client, _QUERY_LIST_VALUES)
    existing_raw = _fetch(client, _QUERY_EXISTING_VALUES)

    list_values: dict[str, list[str]] = defaultdict(list)
    for name, val in list_values_raw:
        list_values[name.strip()].append(val)

    existing: dict[tuple, list] = defaultdict(list)
    for twr_kod, attr_name, val in existing_raw:
        existing[(twr_kod.strip(), attr_name.strip())].append(val or "")

    wb = Workbook()
    ws = wb.active
    ws.title = "Atrybuty produktów"

    # --- Wiersz 1: "Kod XL" | attr_name_1 | attr_name_2 | ... ---
    code_cell = ws.cell(1, 1, "Kod XL")
    code_cell.fill = PatternFill("solid", fgColor="2E75B6")
    code_cell.font = Font(bold=True, color="FFFFFF", size=11)
    code_cell.alignment = Alignment(horizontal="center")

    for col_idx, (name, typ, wielowart, zamknieta) in enumerate(attrs, start=2):
        type_label = TYPE_LABELS.get(typ, str(typ))
        cell = ws.cell(1, col_idx, name)
        cell.fill = _HEADER_FILL
        cell.font = _HEADER_FONT
        cell.alignment = Alignment(horizontal="center")

        comment_lines = [f"Typ: {type_label}"]
        if zamknieta:
            comment_lines.append("(lista zamknięta)")
        if typ == 4 and name.strip() in list_values:
            values = list_values[name.strip()]
            comment_lines.append("Dopuszczalne wartości:")
            comment_lines.extend(f"• {v}" for v in values)
        comment = Comment("\n".join(comment_lines), "System")
        comment.width = 250
        comment.height = min(300, 20 + len(comment_lines) * 16)
        cell.comment = comment

    # --- Wiersze 2+: twr_kod | wartości atrybutów ---
    for row_idx, (twr_kod, twr_nazwa) in enumerate(products, start=2):
        kod_cell = ws.cell(row_idx, 1, twr_kod)
        kod_cell.font = Font(bold=True, size=10)
        if twr_nazwa and twr_nazwa.strip():
            comment = Comment(twr_nazwa.strip(), "System")
            comment.width = 200
            comment.height = 40
            kod_cell.comment = comment

        for col_idx, (name, typ, wielowart, zamknieta) in enumerate(attrs, start=2):
            if typ == 4:
                ws.cell(row_idx, col_idx).fill = _LIST_FILL
            vals = existing.get((twr_kod.strip(), name.strip()), [])
            if vals:
                ws.cell(row_idx, col_idx, ", ".join(str(v) for v in vals if v))

    # --- Wymiary kolumn ---
    ws.column_dimensions["A"].width = 18
    for i in range(len(attrs)):
        ws.column_dimensions[get_column_letter(2 + i)].width = 20

    ws.freeze_panes = "B2"
    ws.row_dimensions[1].height = 22

    output.parent.mkdir(parents=True, exist_ok=True)
    wb.save(output)

    return {
        "ok": True,
        "data": {"path": str(output), "attributes": len(attrs), "products": len(products)},
        "error": None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generuj Excel template atrybutów produktów")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    result = generate_template(args.output)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
