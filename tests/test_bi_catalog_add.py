"""Tests for bi_catalog_add.py — update_catalog logic."""

import json
from pathlib import Path

import pytest

from tools.bi_catalog_add import update_catalog


def make_catalog(*view_names):
    return {"views": [{"name": n, "columns": [], "description": ""} for n in view_names]}


class TestUpdateCatalog:
    def test_updates_existing_view(self):
        catalog = make_catalog("AIBI.Rezerwacje")
        columns = ["Id", "Data", "Ilosc"]

        def mock_fetch(view_name):
            return columns

        import tools.bi_catalog_add as mod
        original = mod.fetch_columns
        mod.fetch_columns = mock_fetch
        try:
            ok, msg = update_catalog("AIBI.Rezerwacje", catalog)
            assert ok is True
            assert catalog["views"][0]["columns"] == columns
            assert "zaktualizowano" in msg
        finally:
            mod.fetch_columns = original

    def test_returns_error_when_view_missing_no_add(self):
        catalog = make_catalog("AIBI.Rezerwacje")

        import tools.bi_catalog_add as mod
        mod.fetch_columns = lambda v: ["Col1"]
        try:
            ok, msg = update_catalog("AIBI.TraNag", catalog, add=False)
            assert ok is False
            assert "nie znaleziono" in msg
            assert "--add" in msg
        finally:
            mod.fetch_columns = original if 'original' in dir() else mod.fetch_columns

    def test_creates_new_entry_with_add_flag(self):
        catalog = make_catalog("AIBI.Rezerwacje")
        columns = ["Id", "Data", "Kontrahent"]

        import tools.bi_catalog_add as mod
        original = mod.fetch_columns
        mod.fetch_columns = lambda v: columns
        try:
            ok, msg = update_catalog("AIBI.TraNag", catalog, add=True)
            assert ok is True
            assert len(catalog["views"]) == 2
            new_entry = catalog["views"][1]
            assert new_entry["name"] == "AIBI.TraNag"
            assert new_entry["columns"] == columns
            assert "TraNag.sql" in new_entry["file"]
            assert "dodano" in msg
        finally:
            mod.fetch_columns = original

    def test_add_flag_stub_has_required_fields(self):
        catalog = make_catalog()

        import tools.bi_catalog_add as mod
        original = mod.fetch_columns
        mod.fetch_columns = lambda v: ["Col1"]
        try:
            update_catalog("AIBI.ZamNag", catalog, add=True)
            entry = catalog["views"][0]
            assert "name" in entry
            assert "file" in entry
            assert "description" in entry
            assert "columns" in entry
            assert "example_questions" in entry
        finally:
            mod.fetch_columns = original

    def test_returns_error_when_fetch_fails(self):
        catalog = make_catalog("AIBI.Rezerwacje")

        import tools.bi_catalog_add as mod
        original = mod.fetch_columns
        mod.fetch_columns = lambda v: None
        try:
            ok, msg = update_catalog("AIBI.Rezerwacje", catalog)
            assert ok is False
            assert "Nie można pobrać" in msg
        finally:
            mod.fetch_columns = original
