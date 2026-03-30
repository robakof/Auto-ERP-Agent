"""pp_capacity.py — Odczyt mocy produkcyjnych z pliku xlsx.

Kolumny (0-indexed w tuple):
  0: Data
  1: Godziny pracy
  2: Nadgodziny
  3: Osoby
  4: Ilość godzin na dzień  (pre-computed = Godziny*Osoby + Nadgodziny)

Nagłówki w wierszu 1, dane od wiersza 2.
"""
import warnings
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import openpyxl


@dataclass
class DayCapacity:
    date: date
    hours_per_day: float        # Ilość godzin na dzień (pre-wyliczone)
    persons: int
    regular_hours: float
    overtime_hours: float


def load_capacity(xlsx_path: Path) -> dict[date, DayCapacity]:
    """Wczytuje moce produkcyjne z pliku xlsx.

    Klucz: date. Wartość: DayCapacity.
    Rzuca FileNotFoundError jeśli plik nie istnieje.
    Wiersze z nieprawidłową datą → warn + pomiń.
    """
    xlsx_path = Path(xlsx_path)
    if not xlsx_path.exists():
        raise FileNotFoundError(f"Plik mocy produkcyjnych nie istnieje: {xlsx_path}")

    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    ws = wb.active
    result: dict[date, DayCapacity] = {}
    first_row = True

    for row in ws.iter_rows(values_only=True):
        if first_row:
            first_row = False
            continue

        if not row[0]:
            continue

        d = _parse_date(row[0])
        if d is None:
            warnings.warn(
                f"[CAPACITY] Nieprawidłowa data: {row[0]!r} — pominięto",
                stacklevel=2,
            )
            continue

        result[d] = DayCapacity(
            date=d,
            hours_per_day=float(row[4] or 0),
            persons=int(row[3] or 0),
            regular_hours=float(row[1] or 0),
            overtime_hours=float(row[2] or 0),
        )

    wb.close()
    return result


def _parse_date(val) -> date | None:
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    if isinstance(val, str):
        try:
            return datetime.fromisoformat(val.split()[0]).date()
        except ValueError:
            return None
    return None
