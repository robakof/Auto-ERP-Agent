"""Testy dla tools/search_bi.py."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.search_bi import search_bi

CATALOG = {
    "views": [
        {
            "name": "AIBI.ZamNag",
            "file": "views/ZamNag.sql",
            "description": "Nagłówki zamówień sprzedaży i zakupu z danymi kontrahenta.",
            "primary_table": "CDN.ZamNag",
            "joins": ["CDN.KntKarty"],
            "columns": ["ID_Zamowienia", "Nazwa_Kontrahenta", "Data_Wystawienia", "Stan"],
            "example_questions": ["zamówienia kontrahenta X", "niezrealizowane zamówienia"],
            "notes": "Stan: 2=Zamówienie, 21=Zrealizowane."
        },
        {
            "name": "AIBI.KntKarty",
            "file": "views/KntKarty.sql",
            "description": "Kartoteka kontrahentów z danymi adresowymi i handlowymi.",
            "primary_table": "CDN.KntKarty",
            "joins": ["CDN.KntAdresy"],
            "columns": ["ID_Kontrahenta", "Akronim", "Nazwa1", "NIP", "Miasto"],
            "example_questions": ["dane kontrahenta X", "jaki NIP ma firma X"],
            "notes": "Archiwalny='Tak' — nieaktywne."
        },
        {
            "name": "AIBI.Rezerwacje",
            "file": "views/Rezerwacje.sql",
            "description": "Rezerwacje towarów z danymi towaru, kontrahenta i magazynu.",
            "primary_table": "CDN.Rezerwacje",
            "joins": ["CDN.TwrKarty", "CDN.KntKarty"],
            "columns": ["ID_Rezerwacji", "Kod_Towaru", "Ilosc_Zarezerwowana", "Aktywna"],
            "example_questions": ["rezerwacje towaru X", "ile sztuk zarezerwowane"],
            "notes": "Aktywna='Tak' AND Ilosc_Do_Pokrycia>0 — bieżące."
        }
    ]
}


# --- dopasowania ---

def test_finds_by_view_name():
    results = search_bi("ZamNag", catalog=CATALOG)
    assert results["ok"] is True
    assert len(results["data"]["results"]) == 1
    assert results["data"]["results"][0]["name"] == "AIBI.ZamNag"


def test_finds_by_description_keyword():
    results = search_bi("kontrahent", catalog=CATALOG)
    assert results["ok"] is True
    names = [r["name"] for r in results["data"]["results"]]
    assert "AIBI.ZamNag" in names
    assert "AIBI.KntKarty" in names


def test_finds_by_example_question():
    results = search_bi("niezrealizowane zamówienia", catalog=CATALOG)
    assert results["ok"] is True
    names = [r["name"] for r in results["data"]["results"]]
    assert "AIBI.ZamNag" in names


def test_finds_by_column_name():
    results = search_bi("NIP", catalog=CATALOG)
    assert results["ok"] is True
    names = [r["name"] for r in results["data"]["results"]]
    assert "AIBI.KntKarty" in names


def test_case_insensitive():
    results = search_bi("zamówienia", catalog=CATALOG)
    upper = search_bi("ZAMÓWIENIA", catalog=CATALOG)
    assert results["data"]["results"] == upper["data"]["results"]


def test_no_results():
    results = search_bi("nieistniejące_xyz", catalog=CATALOG)
    assert results["ok"] is True
    assert results["data"]["results"] == []
    assert results["data"]["count"] == 0


def test_empty_query_returns_all():
    results = search_bi("", catalog=CATALOG)
    assert results["ok"] is True
    assert results["data"]["count"] == 3


def test_result_contains_required_fields():
    results = search_bi("ZamNag", catalog=CATALOG)
    r = results["data"]["results"][0]
    assert "name" in r
    assert "description" in r
    assert "columns" in r
    assert "example_questions" in r
    assert "file" in r


def test_meta_contains_count():
    results = search_bi("kontrahent", catalog=CATALOG)
    assert "count" in results["data"]
    assert results["data"]["count"] == results["data"]["results"].__len__()


# --- błędy ---

def test_missing_catalog_file(tmp_path):
    result = search_bi("zamówienia", catalog_path=str(tmp_path / "brak.json"))
    assert result["ok"] is False
    assert result["error"]["type"] == "CATALOG_NOT_FOUND"


def test_invalid_catalog_json(tmp_path):
    bad = tmp_path / "catalog.json"
    bad.write_text("nie json", encoding="utf-8")
    result = search_bi("zamówienia", catalog_path=str(bad))
    assert result["ok"] is False
    assert result["error"]["type"] == "CATALOG_INVALID"
