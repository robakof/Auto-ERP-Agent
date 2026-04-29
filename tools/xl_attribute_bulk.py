"""Bulk update atrybutów produktów z pliku Excel.

Format pliku:
  Wiersz 1: "Kod XL" | nazwa_atrybutu_1 | nazwa_atrybutu_2 | ...
  Wiersze 2+: twr_kod | wartość_1 | wartość_2 | ...
  Pusta komórka = pomiń (nie aktualizuj).

Użycie:
  python tools/xl_attribute_bulk.py --file atrybuty.xlsx
  python tools/xl_attribute_bulk.py --file atrybuty.xlsx --operator ADMIN --report raport.xlsx
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.lib.sql_client import SqlClient
from tools.xl_attribute_set import delete_attributes, set_attribute

_QUERY_CLASS_NAMES = """
SELECT DISTINCT ak.AtK_Nazwa
FROM CDN.AtrybutyKlasy ak
INNER JOIN CDN.AtrybutyObiekty ao ON ao.AtO_AtKId = ak.AtK_ID
WHERE ao.AtO_GIDTyp = 16
"""

_STATUS_FILLS = {
    "OK":        PatternFill("solid", fgColor="C6EFCE"),
    "BŁĄD":      PatternFill("solid", fgColor="FFC7CE"),
    "POMINIĘTY": PatternFill("solid", fgColor="FFEB9C"),
}


def _load_class_map(client: SqlClient) -> tuple[dict, dict | None]:
    result = client.execute(_QUERY_CLASS_NAMES, inject_top=None)
    if not result["ok"]:
        return {}, result["error"]
    return {row[0].strip().lower(): row[0] for row in result["rows"]}, None


def _parse_excel(path: Path) -> tuple[list, list]:
    wb = load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    if not rows:
        return [], []
    return list(rows[0]), [list(r) for r in rows[1:]]


def _detect_attr_cols(header: list) -> list[tuple[int, str]]:
    """Zwraca [(col_idx, attr_name), ...] dla kolumn 1+ (pomija kolumnę 0 = Kod XL)."""
    result = []
    for i, h in enumerate(header):
        if i == 0:
            continue
        if h is None or str(h).strip() == "":
            continue
        result.append((i, str(h).strip()))
    return result


def _write_report(path: Path, results: list) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Raport"

    headers = ["Akronim", "Atrybut", "Wartość", "Status", "Komunikat"]
    for col, h in enumerate(headers, 1):
        cell = ws.cell(1, col, h)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="1F4E79")

    for row_idx, r in enumerate(results, 2):
        ws.cell(row_idx, 1, r["akronim"])
        ws.cell(row_idx, 2, r["class"])
        ws.cell(row_idx, 3, r["value"] if r["value"] is not None else "(pusta)")
        ws.cell(row_idx, 4, r["status"])
        ws.cell(row_idx, 5, r.get("message", ""))
        fill = _STATUS_FILLS.get(r["status"])
        if fill:
            for col in range(1, 6):
                ws.cell(row_idx, col).fill = fill

    for col, width in zip(range(1, 6), [18, 34, 20, 12, 40]):
        ws.column_dimensions[ws.cell(1, col).column_letter].width = width

    wb.save(path)


def bulk_update(file: Path, operator: str | None = None, report: Path | None = None) -> dict:
    header, data_rows = _parse_excel(file)

    if not header or not data_rows:
        return {"ok": False, "data": None, "error": {"type": "EMPTY_FILE", "message": "Plik jest pusty"}}

    attr_cols = _detect_attr_cols(header)
    if not attr_cols:
        return {"ok": False, "data": None, "error": {"type": "NO_ATTRS", "message": "Brak kolumn z atrybutami w wierszu 1"}}

    client = SqlClient()
    class_map, err = _load_class_map(client)
    if err:
        return {"ok": False, "data": None, "error": err}

    resolved: list[tuple[int, str | None, str]] = [
        (col_idx, class_map.get(raw.lower()), raw)
        for col_idx, raw in attr_cols
    ]

    # Faza 1: ustal które produkty mają conajmniej jedną niepustą wartość
    akronimy_to_update: set[str] = set()
    for row in data_rows:
        if not row or row[0] is None or str(row[0]).strip() == "":
            continue
        akronim = str(row[0]).strip()
        for col_idx, _, _ in resolved:
            value = row[col_idx] if col_idx < len(row) else None
            if value is not None and str(value).strip() != "":
                akronimy_to_update.add(akronim)

    # Faza 2: usuń wszystkie atrybuty dla tych produktów
    failed_akronimy: set[str] = set()
    for akronim in akronimy_to_update:
        del_res = delete_attributes(akronim)
        if not del_res["ok"]:
            failed_akronimy.add(akronim)

    # Faza 3: wstaw wartości z pliku
    results = []
    total = success = skipped = failed = 0

    for row in data_rows:
        if not row or row[0] is None or str(row[0]).strip() == "":
            continue
        akronim = str(row[0]).strip()

        for col_idx, exact_name, attr_raw in resolved:
            value = row[col_idx] if col_idx < len(row) else None
            total += 1

            if value is None or str(value).strip() == "":
                skipped += 1
                results.append({"akronim": akronim, "class": attr_raw, "value": None, "status": "POMINIĘTY"})
                continue

            value_str = str(value).strip()

            if akronim in failed_akronimy:
                failed += 1
                results.append({"akronim": akronim, "class": attr_raw, "value": value_str,
                                 "status": "BŁĄD", "message": f"Błąd usuwania atrybutów: {akronim}"})
                continue

            if exact_name is None:
                failed += 1
                results.append({"akronim": akronim, "class": attr_raw, "value": value_str,
                                 "status": "BŁĄD", "message": f"Nieznana klasa atrybutu: '{attr_raw}'"})
                continue

            res = set_attribute(exact_name, value_str, akronim, obj_type=16, operator=operator)
            if res["ok"]:
                success += 1
                results.append({"akronim": akronim, "class": attr_raw, "value": value_str, "status": "OK"})
            else:
                failed += 1
                results.append({"akronim": akronim, "class": attr_raw, "value": value_str,
                                 "status": "BŁĄD", "message": res["error"]["message"]})

    if report:
        _write_report(path=report, results=results)

    return {
        "ok": True,
        "data": {
            "total": total, "success": success, "skipped": skipped, "failed": failed,
            "report": str(report) if report else None,
            "results": results,
        },
        "error": None,
    }


def main() -> None:
    today = date.today().strftime("%Y%m%d")
    default_report = Path(f"documents/human/reports/xl_attribute_bulk_{today}.xlsx")

    parser = argparse.ArgumentParser(description="Bulk update atrybutów produktów z Excel")
    parser.add_argument("--file", required=True, type=Path, help="Ścieżka do pliku Excel z danymi")
    parser.add_argument("--operator", default=None, help="Identyfikator operatora ERP (opcjonalny)")
    parser.add_argument("--report", type=Path, default=default_report,
                        help=f"Ścieżka raportu wynikowego (domyślnie: {default_report})")
    args = parser.parse_args()

    result = bulk_update(args.file, args.operator, args.report)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
