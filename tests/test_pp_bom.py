"""Testy pp_bom.load_bom — fixture bez prawdziwego pliku + integration z xlsm."""
import sys
import warnings
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.lib.pp_bom import load_bom, load_efficiency, BomEntry, EfficiencyEntry, _is_valid_number

_REAL_XLSM = Path(__file__).parent.parent / "documents/human/ar/dokumenty/Wycena 2026 Otorowo PQ.xlsm"


# ── Testy _is_valid_number ────────────────────────────────────────────────

def test_valid_number_int():
    assert _is_valid_number(1) is True

def test_valid_number_float():
    assert _is_valid_number(0.98) is True

def test_valid_number_string_dash():
    assert _is_valid_number("-") is False

def test_valid_number_value_error():
    assert _is_valid_number("#VALUE!") is False

def test_valid_number_none():
    assert _is_valid_number(None) is False


# ── Fixture helper — mock openpyxl ────────────────────────────────────────

def _make_wb_mock(rows):
    """Tworzy mock workbook z podanymi wierszami (tuple 14 elementów)."""
    ws_mock = MagicMock()
    ws_mock.iter_rows.return_value = iter(rows)
    wb_mock = MagicMock()
    wb_mock.__enter__ = MagicMock(return_value=wb_mock)
    wb_mock.__exit__ = MagicMock(return_value=False)
    wb_mock.sheetnames = ["Wycena Zniczy"]
    wb_mock.__getitem__ = MagicMock(return_value=ws_mock)
    return wb_mock


def _row(czni, grupa, sur_kod, sur_nazwa, mianownik):
    """Buduje tuple wiersza: 14 pól, wypełnione None poza B,F,H,I,J."""
    r = [None] * 14
    r[1] = czni      # B
    r[5] = grupa     # F
    r[7] = sur_kod   # H
    r[8] = sur_nazwa # I
    r[9] = mianownik # J
    return tuple(r)


# ── Testy load_bom z mockiem ──────────────────────────────────────────────

def _patched_load(rows, tmp_path):
    dummy = tmp_path / "dummy.xlsm"
    dummy.write_bytes(b"dummy")
    wb = _make_wb_mock(rows)
    with patch("tools.lib.pp_bom.openpyxl.load_workbook", return_value=wb):
        return load_bom(dummy)


def test_load_bom_podstawowy(tmp_path):
    rows = [
        _row("CZNI001", "Podstawowa", "SZ0324", "Szkło SZ0324", 0.98),
        _row("CZNI001", "Pakowanie",  "FO0003", "Folia FO0003", 125),
    ]
    bom = _patched_load(rows, tmp_path)
    assert "CZNI001" in bom
    assert len(bom["CZNI001"]) == 2
    assert bom["CZNI001"][0].surowiec_kod == "SZ0324"
    assert bom["CZNI001"][0].mianownik == 0.98


def test_load_bom_pomija_brak_surowca(tmp_path):
    rows = [
        _row("CZNI002", "Robocizna", None, None, 30),
        _row("CZNI002", "Podstawowa", "WK0001", "Wkład", 1),
    ]
    bom = _patched_load(rows, tmp_path)
    assert len(bom["CZNI002"]) == 1
    assert bom["CZNI002"][0].surowiec_kod == "WK0001"


def test_load_bom_pomija_koszt_grupa(tmp_path):
    rows = [
        _row("CZNI003", "Koszt robocizny", "KSZ001", "Koszt", 1),
        _row("CZNI003", "Podstawowa", "SZ0001", "Szkło", 1),
    ]
    bom = _patched_load(rows, tmp_path)
    assert len(bom["CZNI003"]) == 1
    assert bom["CZNI003"][0].surowiec_kod == "SZ0001"


def test_load_bom_pomija_zly_mianownik(tmp_path):
    rows = [
        _row("CZNI004", "Podstawowa", "SZ0001", "Szkło", "#VALUE!"),
        _row("CZNI004", "Podstawowa", "WK0001", "Wkład", 1),
    ]
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        bom = _patched_load(rows, tmp_path)
    assert len(bom["CZNI004"]) == 1
    assert any("Mianownik" in str(x.message) for x in w)


def test_load_bom_product_12_surowcow(tmp_path):
    rows = [_row("CZNI005", "Podstawowa", f"SZ{i:04d}", f"Surowiec {i}", i + 1)
            for i in range(12)]
    bom = _patched_load(rows, tmp_path)
    assert len(bom["CZNI005"]) == 12


def test_load_bom_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_bom(tmp_path / "nieistniejacy.xlsm")


# ── Integration test z prawdziwym plikiem ─────────────────────────────────

@pytest.mark.skipif(not _REAL_XLSM.exists(), reason="Brak pliku Wycena PQ.xlsm")
def test_load_bom_integration():
    bom = load_bom(_REAL_XLSM)
    assert len(bom) > 0, "BOM powinien zawierać produkty"
    sample = next(iter(bom.values()))
    assert len(sample) > 0
    entry = sample[0]
    assert isinstance(entry, BomEntry)
    assert entry.czni_kod.startswith("CZNI")
    assert entry.mianownik > 0


# ── Testy load_efficiency z mockiem ──────────────────────────────────────────

def _row_eff(czni, grupa, mianownik):
    """Buduje tuple wiersza dla load_efficiency: 10 pól, B=czni, F=grupa, J=mianownik."""
    r = [None] * 10
    r[1] = czni
    r[5] = grupa
    r[9] = mianownik
    return tuple(r)


def _patched_load_eff(rows, tmp_path):
    dummy = tmp_path / "dummy.xlsm"
    dummy.write_bytes(b"dummy")
    wb = _make_wb_mock(rows)
    with patch("tools.lib.pp_bom.openpyxl.load_workbook", return_value=wb):
        return load_efficiency(dummy)


def test_load_efficiency_podstawowy(tmp_path):
    rows = [
        _row_eff("CZNI001", "Robocizna", 30),
    ]
    eff = _patched_load_eff(rows, tmp_path)
    assert "CZNI001" in eff
    assert eff["CZNI001"].units_per_hour == 30.0


def test_load_efficiency_pomija_inne_grupy(tmp_path):
    rows = [
        _row_eff("CZNI001", "Podstawowa", 1),
        _row_eff("CZNI001", "Robocizna", 30),
        _row_eff("CZNI002", "Koszt robocizny", 10),
    ]
    eff = _patched_load_eff(rows, tmp_path)
    assert "CZNI001" in eff
    assert "CZNI002" not in eff


def test_load_efficiency_pomija_brak_czni(tmp_path):
    rows = [
        _row_eff(None, "Robocizna", 30),
    ]
    eff = _patched_load_eff(rows, tmp_path)
    assert len(eff) == 0


def test_load_efficiency_warn_zly_mianownik(tmp_path):
    rows = [
        _row_eff("CZNI001", "Robocizna", "#VALUE!"),
        _row_eff("CZNI002", "Robocizna", 25),
    ]
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        eff = _patched_load_eff(rows, tmp_path)
    assert "CZNI001" not in eff
    assert "CZNI002" in eff
    assert any("units_per_hour" in str(x.message) for x in w)


def test_load_efficiency_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_efficiency(tmp_path / "nieistniejacy.xlsm")


def test_load_efficiency_dwa_wiersze_bierze_max(tmp_path):
    """Symuluje realny plik: J=1 (stawka kosztu) + J=30 (wydajność). Max wygrywa."""
    rows = [
        _row_eff("CZNI001", "Robocizna", 1),
        _row_eff("CZNI001", "Robocizna", 30),
    ]
    eff = _patched_load_eff(rows, tmp_path)
    assert eff["CZNI001"].units_per_hour == 30.0


# ── Integration test load_efficiency ─────────────────────────────────────────

@pytest.mark.skipif(not _REAL_XLSM.exists(), reason="Brak pliku Wycena PQ.xlsm")
def test_load_efficiency_integration():
    eff = load_efficiency(_REAL_XLSM)
    assert len(eff) > 0, "Oczekiwano wierszy Roboczogodzina Otorowo"
    sample = next(iter(eff.values()))
    assert isinstance(sample, EfficiencyEntry)
    assert sample.units_per_hour > 0
