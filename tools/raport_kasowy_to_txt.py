"""
raport_kasowy_to_txt.py — konwerter Raport kasowy XLSX → TXT (format CDN POSS).

Wzorzec: documents/Wzory plików/kasaFranowoprzykład.txt (15 pól, CP1250).

CLI:
    py tools/raport_kasowy_to_txt.py --input raport.xlsx --output raport.txt
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

import openpyxl


# Indeksy kolumn xlsx (0-based, z values_only=True tuple)
# Kolejność: Numer, Nr kwitu, Dokument, Data, Czas, Przychód, Rozchód, Akronim, Miasto, Treść, Konto
COL_DOKUMENT = 2
COL_DATA = 3
COL_CZAS = 4
COL_PRZYCHOD = 5
COL_ROZCHOD = 6
COL_AKRONIM = 7
COL_TRESC = 9

# Mapowanie typu (pole 3 w TXT)
TYP_BY_PREFIX = {"FS-": 1, "PA-": 1, "KW/": 2}

DOC_RE = re.compile(r"^([A-Z]+[-/])(\d+)(.*)$")


def _split_dokument(dok: str) -> tuple[str, int, str]:
    """Rozbija 'PA-1441/03/26/CME' → ('PA-', 1441, '/03/26/CME')."""
    m = DOC_RE.match(dok)
    if not m:
        raise ValueError(f"Nieznany format dokumentu: {dok!r}")
    return m.group(1), int(m.group(2)), m.group(3)


def _fmt_data(dt: datetime) -> str:
    """datetime → 'yy/MM/dd' (np. '26/03/11')."""
    return dt.strftime("%y/%m/%d")


def _fmt_czas(czas) -> str:
    """'12:35:05' → '12:35:05'; '6:23:28' → ' 6:23:28' (pad spacją gdy H<10)."""
    s = str(czas).strip()
    h, _, rest = s.partition(":")
    if len(h) == 1:
        return f" {h}:{rest}"
    return s


def _fmt_kwota(val) -> str:
    """Liczba → string bez zbędnych zer ('8' nie '8.0', '79.96' bez zmian)."""
    if val is None:
        return "0"
    f = float(val)
    if f == int(f):
        return str(int(f))
    return f"{f:g}"


def _row_to_txt(row: tuple) -> str:
    """Konwertuje wiersz xlsx na 1 linię TXT (15 pól)."""
    dok = row[COL_DOKUMENT]
    if not dok or not isinstance(dok, str):
        return ""
    prefix, numer, sufix = _split_dokument(dok)
    typ = TYP_BY_PREFIX.get(prefix, 1)

    data = _fmt_data(row[COL_DATA])
    czas = _fmt_czas(row[COL_CZAS])
    akronim = (row[COL_AKRONIM] or "").strip()
    tresc = (row[COL_TRESC] or "").strip()
    przychod = float(row[COL_PRZYCHOD] or 0)
    rozchod = float(row[COL_ROZCHOD] or 0)
    kwota = _fmt_kwota(przychod if przychod > 0 else rozchod)

    return (
        f'0,"{data}","{czas}",{typ},"{akronim}","{prefix}",{numer},'
        f'"{sufix}","{tresc}","","POSS",{kwota},0,0,0'
    )


def convert(input_path: Path, output_path: Path) -> dict:
    """Konwertuje xlsx → txt (CP1250). Zwraca statystyki."""
    wb = openpyxl.load_workbook(input_path, data_only=True)
    ws = wb.worksheets[0]  # pierwszy arkusz (np. "8301")

    lines = []
    skipped = 0
    for row in ws.iter_rows(min_row=3, values_only=True):
        line = _row_to_txt(row)
        if line:
            lines.append(line)
        else:
            skipped += 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    # newline="" — bez translacji (piszemy \r\n explicite; inaczej \n → \r\r\n)
    with open(output_path, "w", encoding="cp1250", newline="") as f:
        f.write("\r\n".join(lines) + "\r\n")

    return {"rows_written": len(lines), "rows_skipped": skipped}


def main():
    parser = argparse.ArgumentParser(description="Raport kasowy XLSX → TXT (CDN POSS).")
    parser.add_argument("--input", required=True, help="Ścieżka do xlsx")
    parser.add_argument("--output", required=True, help="Ścieżka wynikowego txt")
    args = parser.parse_args()

    stats = convert(Path(args.input), Path(args.output))
    print(f"OK: zapisano {stats['rows_written']} wierszy do {args.output}")
    if stats["rows_skipped"]:
        print(f"   pominięto {stats['rows_skipped']} pustych wierszy")


if __name__ == "__main__":
    main()
