"""Testy jednostkowe dla tools/update_window_catalog.py."""

import json

import pytest

import tools.windows_update as uwc


@pytest.fixture
def sol_base(tmp_path):
    """Pusty katalog solutions/ jako baza testowa."""
    base = tmp_path / "solutions"
    base.mkdir()
    return base


@pytest.fixture
def sol_with_window(sol_base):
    """solutions/ z jednym istniejącym wpisem."""
    windows = [
        {
            "id": "okno_towary",
            "name": "Okno towary",
            "aliases": ["towary"],
            "primary_table": "CDN.TwrKarty",
            "config_types": ["columns", "filters"],
        }
    ]
    (sol_base / "erp_windows.json").write_text(
        json.dumps(windows), encoding="utf-8"
    )
    return sol_base


# ── Tworzenie nowego wpisu ────────────────────────────────────────────────────


class TestCreateWindow:
    def test_creates_new_entry(self, sol_base):
        result = uwc.update_window(
            window_id="okno_zamowien",
            name="Okno zamówień",
            primary_table="CDN.ZamNag",
            config_types=["columns", "filters"],
            solutions_path=str(sol_base),
        )
        assert result["ok"] is True
        assert result["data"]["created"] is True
        assert result["data"]["window"]["id"] == "okno_zamowien"

    def test_creates_file_if_not_exists(self, sol_base):
        uwc.update_window(
            window_id="okno_zamowien",
            name="Okno zamówień",
            solutions_path=str(sol_base),
        )
        assert (sol_base / "erp_windows.json").exists()

    def test_new_entry_persisted(self, sol_base):
        uwc.update_window(
            window_id="okno_zamowien",
            name="Okno zamówień",
            primary_table="CDN.ZamNag",
            solutions_path=str(sol_base),
        )
        windows = json.loads((sol_base / "erp_windows.json").read_text(encoding="utf-8"))
        assert any(w["id"] == "okno_zamowien" for w in windows)

    def test_creates_with_aliases(self, sol_base):
        result = uwc.update_window(
            window_id="okno_zamowien",
            add_aliases=["lista ZO", "zamówienia"],
            solutions_path=str(sol_base),
        )
        assert result["ok"] is True
        assert "lista ZO" in result["data"]["window"]["aliases"]
        assert "zamówienia" in result["data"]["window"]["aliases"]


# ── Aktualizacja istniejącego wpisu ──────────────────────────────────────────


class TestUpdateWindow:
    def test_update_returns_created_false(self, sol_with_window):
        result = uwc.update_window(
            window_id="okno_towary",
            solutions_path=str(sol_with_window),
        )
        assert result["ok"] is True
        assert result["data"]["created"] is False

    def test_update_name(self, sol_with_window):
        uwc.update_window(
            window_id="okno_towary",
            name="Okno towarów (nowa nazwa)",
            solutions_path=str(sol_with_window),
        )
        windows = json.loads((sol_with_window / "erp_windows.json").read_text(encoding="utf-8"))
        entry = next(w for w in windows if w["id"] == "okno_towary")
        assert entry["name"] == "Okno towarów (nowa nazwa)"

    def test_update_primary_table(self, sol_with_window):
        result = uwc.update_window(
            window_id="okno_towary",
            primary_table="CDN.TwrGrupy",
            solutions_path=str(sol_with_window),
        )
        assert result["data"]["window"]["primary_table"] == "CDN.TwrGrupy"

    def test_does_not_overwrite_other_fields(self, sol_with_window):
        uwc.update_window(
            window_id="okno_towary",
            name="Nowa nazwa",
            solutions_path=str(sol_with_window),
        )
        windows = json.loads((sol_with_window / "erp_windows.json").read_text(encoding="utf-8"))
        entry = next(w for w in windows if w["id"] == "okno_towary")
        assert entry["primary_table"] == "CDN.TwrKarty"
        assert entry["config_types"] == ["columns", "filters"]


# ── Zarządzanie aliasami ──────────────────────────────────────────────────────


class TestAliases:
    def test_add_alias(self, sol_with_window):
        uwc.update_window(
            window_id="okno_towary",
            add_aliases=["kartoteki"],
            solutions_path=str(sol_with_window),
        )
        windows = json.loads((sol_with_window / "erp_windows.json").read_text(encoding="utf-8"))
        entry = next(w for w in windows if w["id"] == "okno_towary")
        assert "kartoteki" in entry["aliases"]
        assert "towary" in entry["aliases"]  # stary alias zachowany

    def test_no_duplicate_alias(self, sol_with_window):
        uwc.update_window(
            window_id="okno_towary",
            add_aliases=["towary"],  # już istnieje
            solutions_path=str(sol_with_window),
        )
        windows = json.loads((sol_with_window / "erp_windows.json").read_text(encoding="utf-8"))
        entry = next(w for w in windows if w["id"] == "okno_towary")
        assert entry["aliases"].count("towary") == 1

    def test_case_insensitive_dedup(self, sol_with_window):
        uwc.update_window(
            window_id="okno_towary",
            add_aliases=["Towary"],  # "towary" już istnieje
            solutions_path=str(sol_with_window),
        )
        windows = json.loads((sol_with_window / "erp_windows.json").read_text(encoding="utf-8"))
        entry = next(w for w in windows if w["id"] == "okno_towary")
        lower_aliases = [a.lower() for a in entry["aliases"]]
        assert lower_aliases.count("towary") == 1

    def test_multiple_aliases_at_once(self, sol_with_window):
        result = uwc.update_window(
            window_id="okno_towary",
            add_aliases=["kartoteki", "lista towarów"],
            solutions_path=str(sol_with_window),
        )
        aliases = result["data"]["window"]["aliases"]
        assert "kartoteki" in aliases
        assert "lista towarów" in aliases


# ── Obsługa błędów ────────────────────────────────────────────────────────────


class TestErrors:
    def test_invalid_json_returns_error(self, sol_base):
        (sol_base / "erp_windows.json").write_text("not valid json", encoding="utf-8")
        result = uwc.update_window(
            window_id="okno_towary",
            solutions_path=str(sol_base),
        )
        assert result["ok"] is False
        assert result["error"]["type"] == "PARSE_ERROR"
