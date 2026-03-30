"""Testy filter_rows — filtr roku Data_Realizacji. Filtry CZNI/Opis robi SQL."""
import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.planowanie_produkcji import filter_rows

D2025 = datetime.date(2025, 4, 11)
D2026 = datetime.date(2026, 6, 15)

SAMPLE = [
    {"Towar_Kod": "CZNI001", "Data_Realizacji": D2025},
    {"Towar_Kod": "CZNI002", "Data_Realizacji": D2026},
    {"Towar_Kod": "CZNI003", "Data_Realizacji": D2025},
    {"Towar_Kod": "CZNI004", "Data_Realizacji": None},
    {"Towar_Kod": "CZNI005", "Data_Realizacji": D2026},
]


def test_filtr_roku_2025():
    result = filter_rows(SAMPLE, 2025)
    kody = [r["Towar_Kod"] for r in result]
    assert "CZNI001" in kody
    assert "CZNI003" in kody
    assert "CZNI002" not in kody
    assert "CZNI005" not in kody


def test_filtr_roku_2026():
    result = filter_rows(SAMPLE, 2026)
    kody = [r["Towar_Kod"] for r in result]
    assert "CZNI002" in kody
    assert "CZNI005" in kody
    assert "CZNI001" not in kody
    assert "CZNI003" not in kody


def test_brak_daty_odfiltrowany():
    result = filter_rows(SAMPLE, 2025)
    kody = [r["Towar_Kod"] for r in result]
    assert "CZNI004" not in kody


def test_pusty_wejscie():
    assert filter_rows([], 2025) == []


def test_zly_rok_zwraca_puste():
    assert filter_rows(SAMPLE, 2099) == []
