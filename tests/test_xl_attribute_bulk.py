"""Testy dla tools/xl_attribute_bulk.py."""

from pathlib import Path
from unittest.mock import patch

import pytest

from tools.lib.sql_client import SqlClient
import tools.xl_attribute_bulk as xb

_DEL_OK = {"ok": True, "data": {"deleted": 0}, "error": None, "meta": {"duration_ms": 1}}


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


class TestDetectAttrCols:
    def test_skips_first_col(self):
        header = ["Kod XL", "KOLOR", "WAGA PRODUKTU"]
        result = xb._detect_attr_cols(header)
        assert result == [(1, "KOLOR"), (2, "WAGA PRODUKTU")]

    def test_skips_empty_header(self):
        header = ["Kod XL", None, "KOLOR"]
        result = xb._detect_attr_cols(header)
        assert result == [(2, "KOLOR")]

    def test_no_attrs(self):
        header = ["Kod XL"]
        assert xb._detect_attr_cols(header) == []

    def test_all_empty_skipped(self):
        header = ["Kod XL", "", None]
        assert xb._detect_attr_cols(header) == []


class TestBulkUpdate:
    def _mock_class_map(self, names):
        return {n.strip().lower(): n for n in names}

    def test_success(self, tmp_path):
        path = _make_excel(
            ["Kod XL", "WAGA PRODUKTU"],
            [["FOTEL-01", "1.5"]],
            tmp_path,
        )
        with patch.object(xb, "_load_class_map",
                          return_value=(self._mock_class_map(["WAGA PRODUKTU"]), None)):
            with patch.object(xb, "delete_attributes", return_value=_DEL_OK):
                with patch.object(xb, "set_attribute",
                                  return_value={"ok": True, "data": {}, "error": None}):
                    result = xb.bulk_update(path)
        assert result["ok"] is True
        assert result["data"]["success"] == 1
        assert result["data"]["failed"] == 0
        assert result["data"]["skipped"] == 0

    def test_empty_cell_skipped(self, tmp_path):
        path = _make_excel(
            ["Kod XL", "WAGA PRODUKTU"],
            [["FOTEL-01", None]],
            tmp_path,
        )
        with patch.object(xb, "_load_class_map",
                          return_value=(self._mock_class_map(["WAGA PRODUKTU"]), None)):
            result = xb.bulk_update(path)
        assert result["data"]["skipped"] == 1
        assert result["data"]["success"] == 0

    def test_unknown_class_reported_as_failed(self, tmp_path):
        path = _make_excel(
            ["Kod XL", "NIEISTNIEJACY"],
            [["FOTEL-01", "wartość"]],
            tmp_path,
        )
        with patch.object(xb, "_load_class_map", return_value=({}, None)):
            with patch.object(xb, "delete_attributes", return_value=_DEL_OK):
                result = xb.bulk_update(path)
        assert result["data"]["failed"] == 1
        assert result["data"]["results"][0]["status"] == "BŁĄD"

    def test_set_attribute_failure_counted(self, tmp_path):
        path = _make_excel(
            ["Kod XL", "WAGA PRODUKTU"],
            [["FOTEL-01", "1.5"]],
            tmp_path,
        )
        with patch.object(xb, "_load_class_map",
                          return_value=(self._mock_class_map(["WAGA PRODUKTU"]), None)):
            with patch.object(xb, "delete_attributes", return_value=_DEL_OK):
                with patch.object(xb, "set_attribute",
                                  return_value={"ok": False, "data": None,
                                                "error": {"type": "OBJECT_NOT_FOUND", "message": "brak"}}):
                    result = xb.bulk_update(path)
        assert result["data"]["failed"] == 1

    def test_multiple_products_multiple_attrs(self, tmp_path):
        path = _make_excel(
            ["Kod XL", "WAGA PRODUKTU", "KOLOR"],
            [
                ["FOTEL-01", "1.5", "czarny"],
                ["FOTEL-02", "2.0", None],
            ],
            tmp_path,
        )
        with patch.object(xb, "_load_class_map",
                          return_value=(self._mock_class_map(["WAGA PRODUKTU", "KOLOR"]), None)):
            with patch.object(xb, "delete_attributes", return_value=_DEL_OK):
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

    def test_no_attrs_returns_error(self, tmp_path):
        path = _make_excel(["Kod XL"], [["FOTEL-01"]], tmp_path)
        with patch.object(xb, "_load_class_map", return_value=({}, None)):
            result = xb.bulk_update(path)
        assert result["ok"] is False
        assert result["error"]["type"] == "NO_ATTRS"

    def test_report_written(self, tmp_path):
        path = _make_excel(
            ["Kod XL", "WAGA PRODUKTU"],
            [["FOTEL-01", "1.5"]],
            tmp_path,
        )
        report_path = tmp_path / "raport.xlsx"
        with patch.object(xb, "_load_class_map",
                          return_value=(self._mock_class_map(["WAGA PRODUKTU"]), None)):
            with patch.object(xb, "delete_attributes", return_value=_DEL_OK):
                with patch.object(xb, "set_attribute",
                                  return_value={"ok": True, "data": {}, "error": None}):
                    xb.bulk_update(path, report=report_path)
        assert report_path.exists()
