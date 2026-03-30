"""Testy pp_capacity.load_capacity — fixture bez prawdziwego pliku + integration."""
import sys
import warnings
from datetime import date, datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.lib.pp_capacity import load_capacity, DayCapacity, _parse_date

_REAL_XLSX = Path(__file__).parent.parent / "documents/human/ar/dokumenty/moce produkcyjne.xlsx"


# ── Testy _parse_date ────────────────────────────────────────────────────────

def test_parse_date_datetime():
    dt = datetime(2026, 5, 2, 0, 0)
    assert _parse_date(dt) == date(2026, 5, 2)

def test_parse_date_date():
    d = date(2026, 5, 2)
    assert _parse_date(d) == date(2026, 5, 2)

def test_parse_date_string_iso():
    assert _parse_date("2026-05-02 00:00:00") == date(2026, 5, 2)

def test_parse_date_string_invalid():
    assert _parse_date("not-a-date") is None

def test_parse_date_none():
    assert _parse_date(None) is None

def test_parse_date_int():
    assert _parse_date(12345) is None


# ── Fixture helper — mock openpyxl ───────────────────────────────────────────

def _make_wb_mock(rows):
    ws_mock = MagicMock()
    ws_mock.iter_rows.return_value = iter(rows)
    wb_mock = MagicMock()
    wb_mock.active = ws_mock
    return wb_mock


def _row(data, godziny, nadgodziny, osoby, ilosc_na_dzien):
    """Buduje tuple wiersza: Data, Godziny pracy, Nadgodziny, Osoby, Ilość godzin na dzień."""
    return (data, godziny, nadgodziny, osoby, ilosc_na_dzien)


def _patched_load(rows, tmp_path):
    dummy = tmp_path / "moce.xlsx"
    dummy.write_bytes(b"dummy")
    wb = _make_wb_mock([
        ("Data", "Godziny pracy", "Nadgodziny", "Osoby", "Ilość godzin na dzień"),  # nagłówek
        *rows,
    ])
    with patch("tools.lib.pp_capacity.openpyxl.load_workbook", return_value=wb):
        return load_capacity(dummy)


# ── Testy load_capacity ──────────────────────────────────────────────────────

def test_load_capacity_podstawowy(tmp_path):
    rows = [
        _row(datetime(2026, 5, 2), 8, None, 3, 24),
    ]
    cap = _patched_load(rows, tmp_path)
    assert date(2026, 5, 2) in cap
    dc = cap[date(2026, 5, 2)]
    assert dc.hours_per_day == 24.0
    assert dc.persons == 3
    assert dc.regular_hours == 8.0
    assert dc.overtime_hours == 0.0


def test_load_capacity_nadgodziny(tmp_path):
    rows = [
        _row(datetime(2026, 5, 3), 8, 4, 5, 44),
    ]
    cap = _patched_load(rows, tmp_path)
    dc = cap[date(2026, 5, 3)]
    assert dc.overtime_hours == 4.0
    assert dc.hours_per_day == 44.0


def test_load_capacity_osoby_null(tmp_path):
    rows = [
        _row(datetime(2026, 5, 11), 8, None, None, 0),
    ]
    cap = _patched_load(rows, tmp_path)
    dc = cap[date(2026, 5, 11)]
    assert dc.persons == 0
    assert dc.hours_per_day == 0.0


def test_load_capacity_pomija_null_date(tmp_path):
    rows = [
        _row(None, 8, None, 3, 24),
        _row(datetime(2026, 5, 2), 8, None, 3, 24),
    ]
    cap = _patched_load(rows, tmp_path)
    assert len(cap) == 1


def test_load_capacity_warn_zla_data(tmp_path):
    rows = [
        _row("not-a-date", 8, None, 3, 24),
    ]
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        cap = _patched_load(rows, tmp_path)
    assert len(cap) == 0
    assert any("CAPACITY" in str(x.message) for x in w)


def test_load_capacity_wiele_dni(tmp_path):
    rows = [
        _row(datetime(2026, 5, d), 8, None, 3, 24)
        for d in range(2, 8)
    ]
    cap = _patched_load(rows, tmp_path)
    assert len(cap) == 6


def test_load_capacity_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_capacity(tmp_path / "nieistniejacy.xlsx")


def test_load_capacity_duplikat_daty_ostatni_wygrywa(tmp_path):
    rows = [
        _row(datetime(2026, 5, 2), 8, None, 3, 24),
        _row(datetime(2026, 5, 2), 8, None, 5, 40),  # ta sama data, inna obsada
    ]
    cap = _patched_load(rows, tmp_path)
    assert cap[date(2026, 5, 2)].persons == 5


# ── Integration test z prawdziwym plikiem ────────────────────────────────────

@pytest.mark.skipif(not _REAL_XLSX.exists(), reason="Brak pliku moce produkcyjne.xlsx")
def test_load_capacity_integration():
    cap = load_capacity(_REAL_XLSX)
    assert len(cap) > 0, "Oczekiwano wpisów z pliku mocy"
    sample = next(iter(cap.values()))
    assert isinstance(sample, DayCapacity)
    assert sample.hours_per_day >= 0
