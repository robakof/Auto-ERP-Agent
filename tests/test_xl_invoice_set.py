"""Testy dla tools/xl_invoice_set.py."""

import os
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.xl_invoice_parser import FzInvoice, FzPozycja
from tools.xl_invoice_set import (
    _EPOCH_OFFSET, _resolve_magazyn, _resolve_towar_kod, _to_epoch, _vat_key, set_invoice,
)

# --- fixtures ---

_POZ1 = FzPozycja(nr=1, nazwa="Surowiec A", ilosc=Decimal("10"), jm="szt",
                   cena_netto=Decimal("10.00"), wartosc_netto=Decimal("100.00"),
                   stawka_vat="23", wartosc_vat=Decimal("23.00"))

_POZ2 = FzPozycja(nr=2, nazwa="Surowiec B", ilosc=Decimal("5"), jm="kg",
                   cena_netto=Decimal("20.00"), wartosc_netto=Decimal("100.00"),
                   stawka_vat="8", wartosc_vat=Decimal("8.00"))

_INV = FzInvoice(
    nr_obcy="FV/1/2026",
    nip_sprzedawcy="1234567890",
    nazwa_sprzedawcy="Dostawca Sp. z o.o.",
    data_wystawienia=date(2026, 4, 1),
    termin_platnosci=date(2026, 4, 15),
    waluta="PLN",
    suma_netto=Decimal("200.00"),
    suma_vat=Decimal("31.00"),
    suma_brutto=Decimal("231.00"),
    pozycje=(_POZ1, _POZ2),
)

_INV_EUR = FzInvoice(
    nr_obcy="FV/2/2026",
    nip_sprzedawcy="1234567890",
    nazwa_sprzedawcy="Dostawca Sp. z o.o.",
    data_wystawienia=date(2026, 4, 1),
    termin_platnosci=date(2026, 4, 15),
    waluta="EUR",
    suma_netto=Decimal("100.00"),
    suma_vat=Decimal("23.00"),
    suma_brutto=Decimal("123.00"),
    pozycje=(_POZ1,),
)

_OK_DOC = {"ok": True, "data": {"_lDokumentID": 999}}
_OK_POZ = {"ok": True, "data": {}}
_OK_ZAM = {"ok": True, "data": {}}
_ERR = {"ok": False, "error": {"type": "INVOKE_FAIL", "message": "kod=-1"}}


def _mock_sql(knt_row=(12345, 1464833), exists_count=0, towar_rows=None):
    """towar_rows: dict {nazwa: Twr_Kod} dla pozycji — None = nie znaleziono."""
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value = cursor

    towar_map = towar_rows or {}
    call_idx = [0]
    fixed = [knt_row, (exists_count,)]

    def _fetchone():
        idx = call_idx[0]
        call_idx[0] += 1
        if idx < len(fixed):
            return fixed[idx]
        # kolejne wywołania to _resolve_towar_kod — zwróć wynik lub None
        # execute() poprzedza fetchone() więc sprawdzamy ostatnie args execute
        last_args = cursor.execute.call_args
        if last_args:
            params = last_args[0][1] if len(last_args[0]) > 1 else []
            nazwa = params[1] if len(params) > 1 else ""
            kod = towar_map.get(nazwa)
            return (kod,) if kod else None
        return None

    cursor.fetchone.side_effect = _fetchone
    return conn


_OK_MOD = {"ok": True, "data": {}}


def _mock_xl(doc=_OK_DOC, poz=_OK_POZ, mod=_OK_MOD, zamknij=_OK_ZAM):
    client = MagicMock()
    def _invoke(method, **params):
        if method == "XLNowyDokument":
            return doc
        if method == "XLDodajPozycje":
            return poz
        if method == "XLModyfikujNaglowek":
            return mod
        return zamknij
    client.invoke.side_effect = _invoke
    client.zamknij_dokument.return_value = zamknij
    return client


# --- testy ---

class TestResolveTowarKod:
    def test_found_with_contractor_returns_kod(self):
        cursor = MagicMock()
        cursor.fetchone.return_value = ("AP0189",)
        assert _resolve_towar_kod(cursor, 12345, "Aplikacja wz. 1") == "AP0189"

    def test_fallback_when_contractor_missing(self):
        # pierwsze zapytanie (z kontrahentem) zwraca None, drugie (fallback) zwraca wynik
        cursor = MagicMock()
        cursor.fetchone.side_effect = [None, ("AP0189",)]
        assert _resolve_towar_kod(cursor, 12345, "Aplikacja wz. 1") == "AP0189"
        assert cursor.execute.call_count == 2

    def test_not_found_returns_none(self):
        cursor = MagicMock()
        cursor.fetchone.return_value = None
        assert _resolve_towar_kod(cursor, 12345, "Nieznany towar") is None

    def test_fallback_passes_only_nazwa(self):
        # drugie zapytanie (fallback) używa tylko nazwy, bez knt_numer
        cursor = MagicMock()
        cursor.fetchone.side_effect = [None, None]
        _resolve_towar_kod(cursor, 99, "Towar X")
        fallback_args = cursor.execute.call_args_list[1][0]
        assert fallback_args[1] == ["Towar X"]


class TestResolveMagazyn:
    def test_nip_found_in_csv(self, tmp_path):
        csv_path = tmp_path / "fz_magazyn.csv"
        csv_path.write_text("nip;magazyn\n7811921223;Pias_SUR\n", encoding="utf-8")
        with patch("tools.xl_invoice_set._MAGAZYN_CSV", csv_path):
            assert _resolve_magazyn("7811921223") == "Pias_SUR"

    def test_nip_not_in_csv_returns_env_default(self, tmp_path):
        csv_path = tmp_path / "fz_magazyn.csv"
        csv_path.write_text("nip;magazyn\n9999999999;Pias_SUR\n", encoding="utf-8")
        with patch("tools.xl_invoice_set._MAGAZYN_CSV", csv_path), \
             patch.dict("os.environ", {"FZ_MAGAZYN_DEFAULT": "OTO_SUR"}):
            assert _resolve_magazyn("1234567890") == "OTO_SUR"

    def test_no_csv_returns_env_default(self, tmp_path):
        missing = tmp_path / "nonexistent.csv"
        with patch("tools.xl_invoice_set._MAGAZYN_CSV", missing), \
             patch.dict("os.environ", {"FZ_MAGAZYN_DEFAULT": "TEST_MAG"}):
            assert _resolve_magazyn("1234567890") == "TEST_MAG"

    def test_empty_csv_returns_default(self, tmp_path):
        csv_path = tmp_path / "fz_magazyn.csv"
        csv_path.write_text("nip;magazyn\n", encoding="utf-8")
        with patch("tools.xl_invoice_set._MAGAZYN_CSV", csv_path), \
             patch.dict("os.environ", {"FZ_MAGAZYN_DEFAULT": "OTO_SUR"}):
            assert _resolve_magazyn("1234567890") == "OTO_SUR"

    def test_first_match_wins(self, tmp_path):
        csv_path = tmp_path / "fz_magazyn.csv"
        csv_path.write_text("nip;magazyn\n1111111111;MAG_A\n1111111111;MAG_B\n", encoding="utf-8")
        with patch("tools.xl_invoice_set._MAGAZYN_CSV", csv_path):
            assert _resolve_magazyn("1111111111") == "MAG_A"


class TestToEpoch:
    def test_formula(self):
        d = date(2026, 4, 1)
        assert _to_epoch(d) == d.toordinal() - _EPOCH_OFFSET

    def test_epoch_anchor(self):
        assert _to_epoch(date(1800, 12, 28)) == 0

    def test_positive_for_modern_date(self):
        assert _to_epoch(date(2026, 1, 1)) > 0


class TestSetInvoice:
    def test_unsupported_currency(self):
        result = set_invoice(_INV_EUR)
        assert result["ok"] is False
        assert result["error"]["type"] == "UNSUPPORTED_CURRENCY"

    def test_contractor_not_found(self):
        with patch("tools.xl_invoice_set.SqlClient") as MockSql:
            conn = MagicMock()
            conn.cursor.return_value.fetchone.return_value = None
            MockSql.return_value.get_connection.return_value = conn
            result = set_invoice(_INV)
        assert result["ok"] is False
        assert result["error"]["type"] == "CONTRACTOR_NOT_FOUND"
        assert "1234567890" in result["error"]["message"]

    def test_duplicate_skipped(self):
        with patch("tools.xl_invoice_set.SqlClient") as MockSql:
            MockSql.return_value.get_connection.return_value = _mock_sql(exists_count=1)
            result = set_invoice(_INV)
        assert result["ok"] is True
        assert result["data"]["action"] == "skipped"
        assert result["data"]["nr_obcy"] == "FV/1/2026"

    def test_xl_api_error_new_doc(self):
        with patch("tools.xl_invoice_set.SqlClient") as MockSql, \
             patch("tools.xl_invoice_set.XlClient") as MockXl:
            MockSql.return_value.get_connection.return_value = _mock_sql()
            MockXl.return_value = _mock_xl(doc=_ERR)
            result = set_invoice(_INV)
        assert result["ok"] is False
        assert result["error"]["type"] == "XL_API_ERROR"
        assert "XLNowyDokument" in result["error"]["message"]

    def test_xl_api_error_add_pozycja(self):
        with patch("tools.xl_invoice_set.SqlClient") as MockSql, \
             patch("tools.xl_invoice_set.XlClient") as MockXl:
            MockSql.return_value.get_connection.return_value = _mock_sql()
            MockXl.return_value = _mock_xl(poz=_ERR)
            result = set_invoice(_INV)
        assert result["ok"] is False
        assert result["error"]["type"] == "XL_API_ERROR"
        assert "XLDodajPozycje" in result["error"]["message"]

    def test_xl_api_error_modyfikuj(self):
        with patch("tools.xl_invoice_set.SqlClient") as MockSql, \
             patch("tools.xl_invoice_set.XlClient") as MockXl:
            MockSql.return_value.get_connection.return_value = _mock_sql()
            MockXl.return_value = _mock_xl(mod=_ERR)
            result = set_invoice(_INV)
        assert result["ok"] is False
        assert result["error"]["type"] == "XL_API_ERROR"
        assert "XLModyfikujNaglowek" in result["error"]["message"]

    def test_xl_api_error_zamknij(self):
        with patch("tools.xl_invoice_set.SqlClient") as MockSql, \
             patch("tools.xl_invoice_set.XlClient") as MockXl:
            MockSql.return_value.get_connection.return_value = _mock_sql()
            MockXl.return_value = _mock_xl(zamknij=_ERR)
            result = set_invoice(_INV)
        assert result["ok"] is False
        assert result["error"]["type"] == "XL_API_ERROR"
        assert "XLZamknijDokument" in result["error"]["message"]

    def test_happy_path_inserted(self):
        with patch("tools.xl_invoice_set.SqlClient") as MockSql, \
             patch("tools.xl_invoice_set.XlClient") as MockXl:
            MockSql.return_value.get_connection.return_value = _mock_sql()
            xl = _mock_xl()
            MockXl.return_value = xl
            result = set_invoice(_INV)
        assert result["ok"] is True
        assert result["data"]["action"] == "inserted"
        assert result["data"]["doc_id"] == 999
        assert result["data"]["nr_obcy"] == "FV/1/2026"

    def test_happy_path_calls_pozycje_for_each(self):
        with patch("tools.xl_invoice_set.SqlClient") as MockSql, \
             patch("tools.xl_invoice_set.XlClient") as MockXl:
            MockSql.return_value.get_connection.return_value = _mock_sql()
            xl = _mock_xl()
            MockXl.return_value = xl
            set_invoice(_INV)
        poz_calls = [c for c in xl.invoke.call_args_list
                     if c.args and c.args[0] == "XLDodajPozycje"]
        assert len(poz_calls) == 2

    def test_happy_path_doc_id_passed_to_pozycje(self):
        with patch("tools.xl_invoice_set.SqlClient") as MockSql, \
             patch("tools.xl_invoice_set.XlClient") as MockXl:
            MockSql.return_value.get_connection.return_value = _mock_sql()
            xl = _mock_xl()
            MockXl.return_value = xl
            set_invoice(_INV)
        poz_call = next(c for c in xl.invoke.call_args_list
                        if c.args and c.args[0] == "XLDodajPozycje")
        assert poz_call.kwargs["_lDokumentID"] == 999

    def test_magazyn_passed_to_pozycje(self, tmp_path):
        csv_path = tmp_path / "fz_magazyn.csv"
        csv_path.write_text("nip;magazyn\n1234567890;Pias_SUR\n", encoding="utf-8")
        with patch("tools.xl_invoice_set.SqlClient") as MockSql, \
             patch("tools.xl_invoice_set.XlClient") as MockXl, \
             patch("tools.xl_invoice_set._MAGAZYN_CSV", csv_path):
            MockSql.return_value.get_connection.return_value = _mock_sql()
            xl = _mock_xl()
            MockXl.return_value = xl
            set_invoice(_INV)
        poz_call = next(c for c in xl.invoke.call_args_list
                        if c.args and c.args[0] == "XLDodajPozycje")
        assert poz_call.kwargs["Magazyn"] == "Pias_SUR"

    def test_towar_kod_passed_when_found(self):
        towar_rows = {"Surowiec A": "AP0189", "Surowiec B": "AP0190"}
        with patch("tools.xl_invoice_set.SqlClient") as MockSql, \
             patch("tools.xl_invoice_set.XlClient") as MockXl:
            MockSql.return_value.get_connection.return_value = _mock_sql(towar_rows=towar_rows)
            xl = _mock_xl()
            MockXl.return_value = xl
            result = set_invoice(_INV)
        poz_call = next(c for c in xl.invoke.call_args_list
                        if c.args and c.args[0] == "XLDodajPozycje")
        assert poz_call.kwargs.get("TowarKod") == "AP0189"
        assert result["data"]["avista"] == []

    def test_avista_when_towar_not_found(self):
        with patch("tools.xl_invoice_set.SqlClient") as MockSql, \
             patch("tools.xl_invoice_set.XlClient") as MockXl:
            MockSql.return_value.get_connection.return_value = _mock_sql()
            MockXl.return_value = _mock_xl()
            result = set_invoice(_INV)
        assert "Surowiec A" in result["data"]["avista"]
        assert "Surowiec B" in result["data"]["avista"]

    def test_no_towar_kod_when_not_found(self):
        with patch("tools.xl_invoice_set.SqlClient") as MockSql, \
             patch("tools.xl_invoice_set.XlClient") as MockXl:
            MockSql.return_value.get_connection.return_value = _mock_sql()
            xl = _mock_xl()
            MockXl.return_value = xl
            set_invoice(_INV)
        poz_call = next(c for c in xl.invoke.call_args_list
                        if c.args and c.args[0] == "XLDodajPozycje")
        assert "TowarKod" not in poz_call.kwargs

    def test_result_has_duration_ms(self):
        with patch("tools.xl_invoice_set.SqlClient") as MockSql, \
             patch("tools.xl_invoice_set.XlClient") as MockXl:
            MockSql.return_value.get_connection.return_value = _mock_sql()
            MockXl.return_value = _mock_xl()
            result = set_invoice(_INV)
        assert "duration_ms" in result["meta"]


class TestVatKey:
    def test_23_opodatkowany(self):
        assert _vat_key("23") == (23, 1)

    def test_8_opodatkowany(self):
        assert _vat_key("8") == (8, 1)

    def test_5_opodatkowany(self):
        assert _vat_key("5") == (5, 1)

    def test_0_opodatkowany(self):
        assert _vat_key("0") == (0, 1)

    def test_zw_lowercase(self):
        assert _vat_key("zw") == (0, 0)

    def test_zw_uppercase(self):
        assert _vat_key("ZW") == (0, 0)

    def test_np_lowercase(self):
        assert _vat_key("np") == (0, 2)

    def test_np_uppercase(self):
        assert _vat_key("NP") == (0, 2)

    def test_unknown_fallback(self):
        assert _vat_key("99") == (0, 1)


class TestPositionVAT:
    def test_stawka_pod_23pct_passed(self):
        with patch("tools.xl_invoice_set.SqlClient") as MockSql, \
             patch("tools.xl_invoice_set.XlClient") as MockXl:
            MockSql.return_value.get_connection.return_value = _mock_sql()
            xl = _mock_xl()
            MockXl.return_value = xl
            set_invoice(_INV)
        poz_call = next(c for c in xl.invoke.call_args_list
                        if c.args and c.args[0] == "XLDodajPozycje")
        assert poz_call.kwargs["StawkaPod"] == 2300
        assert poz_call.kwargs["FlagaVAT"] == 1

    def test_stawka_pod_8pct_passed(self):
        with patch("tools.xl_invoice_set.SqlClient") as MockSql, \
             patch("tools.xl_invoice_set.XlClient") as MockXl:
            MockSql.return_value.get_connection.return_value = _mock_sql()
            xl = _mock_xl()
            MockXl.return_value = xl
            set_invoice(_INV)
        calls = [c for c in xl.invoke.call_args_list
                 if c.args and c.args[0] == "XLDodajPozycje"]
        assert calls[1].kwargs["StawkaPod"] == 800
        assert calls[1].kwargs["FlagaVAT"] == 1

    def test_cleanup_tryb0_on_pozycja_error(self):
        with patch("tools.xl_invoice_set.SqlClient") as MockSql, \
             patch("tools.xl_invoice_set.XlClient") as MockXl:
            MockSql.return_value.get_connection.return_value = _mock_sql()
            xl = _mock_xl(poz=_ERR)
            MockXl.return_value = xl
            set_invoice(_INV)
        xl.zamknij_dokument.assert_called_with(lDokumentID=999, Tryb=0)
