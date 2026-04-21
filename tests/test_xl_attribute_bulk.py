"""Testy dla tools/xl_attribute_bulk.py."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tools.lib.sql_client import SqlClient
import tools.xl_attribute_bulk as xb


def _make_class_map(*names):
    return {n.strip().lower(): n for n in names}


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


class TestDetectAkronimCols:
    def test_skips_first_col(self):
        header = ["Atrybut / Akronim →", "Typ", "FOTEL-01", "FOTEL-02"]
        result = xb._detect_akronim_cols(header)
        assert [(2, "FOTEL-01"), (3, "FOTEL-02")] == result

    def test_skips_typ_col(self):
        header = [None, "Typ", "CZNI001"]
        result = xb._detect_akronim_cols(header)
        assert result == [(2, "CZNI001")]

    def test_skips_empty_header(self):
        header = ["Atrybut", None, "FOTEL-01"]
        result = xb._detect_akronim_cols(header)
        assert result == [(2, "FOTEL-01")]

    def test_no_akronimy(self):
        header = ["Atrybut", "Typ"]
        assert xb._detect_akronim_cols(header) == []

    def test_skips_placeholder_akronim_cols(self):
        header = ["Atrybut", "Typ", "CZNI0010", "Akronim_2", "Akronim_3"]
        result = xb._detect_akronim_cols(header)
        assert result == [(2, "CZNI0010")]

    def test_skips_placeholder_case_insensitive(self):
        header = ["Atrybut", "Typ", "FOTEL-01", "AKRONIM_5", "akronim 6"]
        result = xb._detect_akronim_cols(header)
        assert result == [(2, "FOTEL-01")]


class TestBulkUpdate:
    def _mock_class_map(self, names):
        return {n.strip().lower(): n for n in names}

    def test_success(self, tmp_path):
        path = _make_excel(
            ["Atrybut", "Typ", "FOTEL-01"],
            [["WAGA PRODUKTU", "liczba", "1.5"]],
            tmp_path,
        )
        with patch.object(xb, "_load_class_map",
                          return_value=(self._mock_class_map(["WAGA PRODUKTU"]), None)):
            with patch.object(xb, "set_attribute",
                              return_value={"ok": True, "data": {}, "error": None}):
                result = xb.bulk_update(path)
        assert result["ok"] is True
        assert result["data"]["success"] == 1
        assert result["data"]["failed"] == 0
        assert result["data"]["skipped"] == 0

    def test_empty_cell_skipped(self, tmp_path):
        path = _make_excel(
            ["Atrybut", "Typ", "FOTEL-01"],
            [["WAGA PRODUKTU", "liczba", None]],
            tmp_path,
        )
        with patch.object(xb, "_load_class_map",
                          return_value=(self._mock_class_map(["WAGA PRODUKTU"]), None)):
            result = xb.bulk_update(path)
        assert result["data"]["skipped"] == 1
        assert result["data"]["success"] == 0

    def test_unknown_class_reported_as_failed(self, tmp_path):
        path = _make_excel(
            ["Atrybut", "Typ", "FOTEL-01"],
            [["NIEISTNIEJACY", "tekst", "wartość"]],
            tmp_path,
        )
        with patch.object(xb, "_load_class_map", return_value=({}, None)):
            result = xb.bulk_update(path)
        assert result["data"]["failed"] == 1
        assert result["data"]["results"][0]["status"] == "BŁĄD"

    def test_set_attribute_failure_counted(self, tmp_path):
        path = _make_excel(
            ["Atrybut", "Typ", "FOTEL-01"],
            [["WAGA PRODUKTU", "liczba", "1.5"]],
            tmp_path,
        )
        with patch.object(xb, "_load_class_map",
                          return_value=(self._mock_class_map(["WAGA PRODUKTU"]), None)):
            with patch.object(xb, "set_attribute",
                              return_value={"ok": False, "data": None,
                                            "error": {"type": "OBJECT_NOT_FOUND", "message": "brak"}}):
                result = xb.bulk_update(path)
        assert result["data"]["failed"] == 1

    def test_multiple_products_multiple_attrs(self, tmp_path):
        path = _make_excel(
            ["Atrybut", "Typ", "FOTEL-01", "FOTEL-02"],
            [
                ["WAGA PRODUKTU", "liczba", "1.5", "2.0"],
                ["KOLOR", "tekst", "czarny", None],
            ],
            tmp_path,
        )
        with patch.object(xb, "_load_class_map",
                          return_value=(self._mock_class_map(["WAGA PRODUKTU", "KOLOR"]), None)):
            with patch.object(xb, "set_attribute",
                              return_value={"ok": True, "data": {}, "error": None}):
                result = xb.bulk_update(path)
        assert result["data"]["total"] == 4
        assert result["data"]["success"] == 3
        assert result["data"]["skipped"] == 1

    def test_empty_file_returns_error(self, tmp_path):
        from openpyxl import Workbook
        path = tmp_path / "empty.xlsx"
        Workbook().save(path)
        result = xb.bulk_update(path)
        assert result["ok"] is False

    def test_no_akronimy_returns_error(self, tmp_path):
        path = _make_excel(["Atrybut", "Typ"], [["WAGA PRODUKTU", "liczba"]], tmp_path)
        with patch.object(xb, "_load_class_map", return_value=({}, None)):
            result = xb.bulk_update(path)
        assert result["ok"] is False
        assert result["error"]["type"] == "NO_AKRONIMY"

    def test_report_written(self, tmp_path):
        path = _make_excel(
            ["Atrybut", "Typ", "FOTEL-01"],
            [["WAGA PRODUKTU", "liczba", "1.5"]],
            tmp_path,
        )
        report_path = tmp_path / "raport.xlsx"
        with patch.object(xb, "_load_class_map",
                          return_value=(self._mock_class_map(["WAGA PRODUKTU"]), None)):
            with patch.object(xb, "set_attribute",
                              return_value={"ok": True, "data": {}, "error": None}):
                xb.bulk_update(path, report=report_path)
        assert report_path.exists()
