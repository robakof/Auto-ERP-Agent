"""Testy dla tools/xl_attribute_bulk.py.

Format pliku: wiersz 1 = nagłówek, wiersze 2+ = KOD_XL | ATRYBUT | TYP | wartość1 | ...
"""

from pathlib import Path
from unittest.mock import patch

import pytest

import tools.xl_attribute_bulk as xb

_SET_OK = {"ok": True, "data": {}, "error": None}


def _make_excel(header, rows, tmp_path):
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.append(header)
    for r in rows:
        ws.append(r)
    path = tmp_path / "test.xlsx"
    wb.save(path)
    return path


def _cls(*names):
    return {n.strip().lower(): n for n in names}, None


class TestBulkUpdate:
    def test_success_single(self, tmp_path):
        path = _make_excel(
            [None, "Atrybut / Akronim →", "Typ"],
            [["FOTEL-01", "WAGA PRODUKTU", "liczba", "1.5"]],
            tmp_path,
        )
        with patch.object(xb, "_load_class_map", return_value=_cls("WAGA PRODUKTU")):
            with patch.object(xb, "set_attribute", return_value=_SET_OK):
                result = xb.bulk_update(path)
        assert result["ok"] is True
        assert result["data"]["success"] == 1
        assert result["data"]["failed"] == 0

    def test_empty_value_skipped(self, tmp_path):
        path = _make_excel(
            [None, "Atrybut / Akronim →", "Typ"],
            [["FOTEL-01", "WAGA PRODUKTU", "liczba"]],
            tmp_path,
        )
        with patch.object(xb, "_load_class_map", return_value=_cls("WAGA PRODUKTU")):
            result = xb.bulk_update(path)
        assert result["data"]["skipped"] == 1
        assert result["data"]["success"] == 0

    def test_unknown_class_failed(self, tmp_path):
        path = _make_excel(
            [None, "Atrybut / Akronim →", "Typ"],
            [["FOTEL-01", "NIEZNANY", "tekst", "wartość"]],
            tmp_path,
        )
        with patch.object(xb, "_load_class_map", return_value=({}, None)):
            result = xb.bulk_update(path)
        assert result["data"]["failed"] == 1
        assert result["data"]["results"][0]["status"] == "BŁĄD"

    def test_set_attribute_failure(self, tmp_path):
        path = _make_excel(
            [None, "Atrybut / Akronim →", "Typ"],
            [["FOTEL-01", "WAGA PRODUKTU", "liczba", "1.5"]],
            tmp_path,
        )
        _fail = {"ok": False, "data": None, "error": {"type": "X", "message": "brak"}}
        with patch.object(xb, "_load_class_map", return_value=_cls("WAGA PRODUKTU")):
            with patch.object(xb, "set_attribute", return_value=_fail):
                result = xb.bulk_update(path)
        assert result["data"]["failed"] == 1

    def test_multiple_products_multiple_attrs(self, tmp_path):
        path = _make_excel(
            [None, "Atrybut / Akronim →", "Typ"],
            [
                ["FOTEL-01", "WAGA PRODUKTU", "liczba", "1.5"],
                ["FOTEL-01", "KOLOR", "tekst", "czarny"],
                ["FOTEL-02", "WAGA PRODUKTU", "liczba", "2.0"],
                ["FOTEL-02", "KOLOR", "tekst"],   # pusta = skip
            ],
            tmp_path,
        )
        with patch.object(xb, "_load_class_map", return_value=_cls("WAGA PRODUKTU", "KOLOR")):
            with patch.object(xb, "set_attribute", return_value=_SET_OK):
                result = xb.bulk_update(path)
        assert result["data"]["total"] == 4
        assert result["data"]["success"] == 3
        assert result["data"]["skipped"] == 1

    def test_multival_inserts_each(self, tmp_path):
        path = _make_excel(
            [None, "Atrybut / Akronim →", "Typ"],
            [["FOTEL-01", "KOLOR", "lista*", "czerwony", "niebieski"]],
            tmp_path,
        )
        calls = []
        def fake_set(name, val, akr, **kw):
            calls.append(val)
            return _SET_OK
        with patch.object(xb, "_load_class_map", return_value=_cls("KOLOR")):
            with patch.object(xb, "set_attribute", side_effect=fake_set):
                result = xb.bulk_update(path)
        assert calls == ["czerwony", "niebieski"]
        assert result["data"]["success"] == 1

    def test_empty_file_returns_error(self, tmp_path):
        from openpyxl import Workbook
        path = tmp_path / "empty.xlsx"
        Workbook().save(path)
        result = xb.bulk_update(path)
        assert result["ok"] is False

    def test_all_empty_rows_all_skipped(self, tmp_path):
        path = _make_excel(
            [None, "Atrybut / Akronim →", "Typ"],
            [["FOTEL-01", "WAGA PRODUKTU", "liczba"]],
            tmp_path,
        )
        with patch.object(xb, "_load_class_map", return_value=_cls("WAGA PRODUKTU")):
            result = xb.bulk_update(path)
        assert result["ok"] is True
        assert result["data"]["skipped"] == 1
        assert result["data"]["success"] == 0

    def test_report_written(self, tmp_path):
        path = _make_excel(
            [None, "Atrybut / Akronim →", "Typ"],
            [["FOTEL-01", "WAGA PRODUKTU", "liczba", "1.5"]],
            tmp_path,
        )
        report_path = tmp_path / "raport.xlsx"
        with patch.object(xb, "_load_class_map", return_value=_cls("WAGA PRODUKTU")):
            with patch.object(xb, "set_attribute", return_value=_SET_OK):
                xb.bulk_update(path, report=report_path)
        assert report_path.exists()
