"""Testy dla tools/xl_fko_set.py."""

import sys
from datetime import date
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.xl_invoice_parser import FzInvoice, FzPozycja
from tools.xl_fko_set import (
    _EPOCH_OFFSET, _RODZAJ_ZAKUPU, _SERIA,
    _resolve_towar_kod, _to_epoch, _vat_key, set_invoice,
)

# --- fixtures ---

_POZ1 = FzPozycja(nr=1, nazwa="Usługa A", ilosc=Decimal("1"), jm="szt",
                   cena_netto=Decimal("100.00"), wartosc_netto=Decimal("100.00"),
                   stawka_vat="23", wartosc_vat=Decimal("23.00"))

_POZ2 = FzPozycja(nr=2, nazwa="Usługa B", ilosc=Decimal("2"), jm="godz",
                   cena_netto=Decimal("50.00"), wartosc_netto=Decimal("100.00"),
                   stawka_vat="8", wartosc_vat=Decimal("8.00"))

_INV = FzInvoice(
    nr_obcy="FK/1/2026",
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
    nr_obcy="FK/2/2026",
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
_ERR    = {"ok": False, "error": {"type": "INVOKE_FAIL", "message": "kod=-1"}}


def _mock_sql(knt_row=(12345, 1464833), exists_count=0, towar_rows=None):
    conn    = MagicMock()
    cursor  = MagicMock()
    conn.cursor.return_value = cursor

    towar_map = towar_rows or {}
    call_idx  = [0]
    fixed     = [knt_row, (exists_count,)]

    def _fetchone():
        idx = call_idx[0]
        call_idx[0] += 1
        if idx < len(fixed):
            return fixed[idx]
        last_args = cursor.execute.call_args
        if last_args:
            params = last_args[0][1] if len(last_args[0]) > 1 else []
            nazwa  = params[1] if len(params) > 1 else ""
            kod    = towar_map.get(nazwa)
            return (kod,) if kod else None
        return None

    cursor.fetchone.side_effect = _fetchone
    return conn


def _mock_xl(doc=_OK_DOC, poz=_OK_POZ, zamknij=_OK_ZAM):
    client = MagicMock()

    def _invoke(method, **params):
        if method == "XLNowyDokument":
            return doc
        if method == "XLDodajPozycje":
            return poz
        return zamknij

    client.invoke.side_effect = _invoke
    client.zamknij_dokument.return_value = zamknij
    return client


# --- stałe ---

class TestStale:
    def test_seria_zkkr(self):
        assert _SERIA == "ZKKR"

    def test_rodzaj_zakupu_koszty(self):
        assert _RODZAJ_ZAKUPU == 2


# --- _resolve_towar_kod ---

class TestResolveTowarKod:
    def test_found_with_contractor_returns_kod(self):
        cursor = MagicMock()
        cursor.fetchone.return_value = ("KOD01",)
        assert _resolve_towar_kod(cursor, 12345, "Usługa A") == "KOD01"

    def test_fallback_when_contractor_missing(self):
        cursor = MagicMock()
        cursor.fetchone.side_effect = [None, ("KOD01",)]
        assert _resolve_towar_kod(cursor, 12345, "Usługa A") == "KOD01"
        assert cursor.execute.call_count == 2

    def test_not_found_returns_none(self):
        cursor = MagicMock()
        cursor.fetchone.return_value = None
        assert _resolve_towar_kod(cursor, 12345, "Nieznana usługa") is None

    def test_fallback_passes_only_nazwa(self):
        cursor = MagicMock()
        cursor.fetchone.side_effect = [None, None, None, None]
        _resolve_towar_kod(cursor, 99, "Usługa X")
        fallback_args = cursor.execute.call_args_list[1][0]
        assert fallback_args[1] == ["Usługa X"]


# --- _to_epoch ---

class TestToEpoch:
    def test_formula(self):
        d = date(2026, 4, 1)
        assert _to_epoch(d) == d.toordinal() - _EPOCH_OFFSET

    def test_epoch_anchor(self):
        assert _to_epoch(date(1800, 12, 28)) == 0

    def test_positive_for_modern_date(self):
        assert _to_epoch(date(2026, 1, 1)) > 0


# --- set_invoice ---

class TestSetInvoice:
    def test_unsupported_currency(self):
        result = set_invoice(_INV_EUR)
        assert result["ok"] is False
        assert result["error"]["type"] == "UNSUPPORTED_CURRENCY"

    def test_contractor_not_found(self):
        with patch("tools.xl_fko_set.SqlClient") as MockSql:
            conn = MagicMock()
            conn.cursor.return_value.fetchone.return_value = None
            MockSql.return_value.get_connection.return_value = conn
            result = set_invoice(_INV)
        assert result["ok"] is False
        assert result["error"]["type"] == "CONTRACTOR_NOT_FOUND"
        assert "1234567890" in result["error"]["message"]

    def test_duplicate_skipped(self):
        with patch("tools.xl_fko_set.SqlClient") as MockSql:
            MockSql.return_value.get_connection.return_value = _mock_sql(exists_count=1)
            result = set_invoice(_INV)
        assert result["ok"] is True
        assert result["data"]["action"] == "skipped"
        assert result["data"]["nr_obcy"] == "FK/1/2026"

    def test_xl_api_error_new_doc(self):
        with patch("tools.xl_fko_set.SqlClient") as MockSql, \
             patch("tools.xl_fko_set.XlClient") as MockXl:
            MockSql.return_value.get_connection.return_value = _mock_sql()
            MockXl.return_value = _mock_xl(doc=_ERR)
            result = set_invoice(_INV)
        assert result["ok"] is False
        assert result["error"]["type"] == "XL_API_ERROR"
        assert "XLNowyDokument" in result["error"]["message"]

    def test_xl_api_error_add_pozycja(self):
        with patch("tools.xl_fko_set.SqlClient") as MockSql, \
             patch("tools.xl_fko_set.XlClient") as MockXl:
            MockSql.return_value.get_connection.return_value = _mock_sql()
            MockXl.return_value = _mock_xl(poz=_ERR)
            result = set_invoice(_INV)
        assert result["ok"] is False
        assert result["error"]["type"] == "XL_API_ERROR"
        assert "XLDodajPozycje" in result["error"]["message"]

    def test_xl_api_error_zamknij(self):
        with patch("tools.xl_fko_set.SqlClient") as MockSql, \
             patch("tools.xl_fko_set.XlClient") as MockXl:
            MockSql.return_value.get_connection.return_value = _mock_sql()
            MockXl.return_value = _mock_xl(zamknij=_ERR)
            result = set_invoice(_INV)
        assert result["ok"] is False
        assert result["error"]["type"] == "XL_API_ERROR"
        assert "XLZamknijDokument" in result["error"]["message"]

    def test_happy_path_inserted(self):
        with patch("tools.xl_fko_set.SqlClient") as MockSql, \
             patch("tools.xl_fko_set.XlClient") as MockXl:
            MockSql.return_value.get_connection.return_value = _mock_sql()
            MockXl.return_value = _mock_xl()
            result = set_invoice(_INV)
        assert result["ok"] is True
        assert result["data"]["action"] == "inserted"
        assert result["data"]["doc_id"] == 999
        assert result["data"]["nr_obcy"] == "FK/1/2026"

    def test_happy_path_calls_pozycje_for_each(self):
        with patch("tools.xl_fko_set.SqlClient") as MockSql, \
             patch("tools.xl_fko_set.XlClient") as MockXl:
            MockSql.return_value.get_connection.return_value = _mock_sql()
            xl = _mock_xl()
            MockXl.return_value = xl
            set_invoice(_INV)
        poz_calls = [c for c in xl.invoke.call_args_list
                     if c.args and c.args[0] == "XLDodajPozycje"]
        assert len(poz_calls) == 2

    def test_no_modyfikuj_naglowek(self):
        """FKo nie ma magazynu — XLModyfikujNaglowek nie może być wywołany."""
        with patch("tools.xl_fko_set.SqlClient") as MockSql, \
             patch("tools.xl_fko_set.XlClient") as MockXl:
            MockSql.return_value.get_connection.return_value = _mock_sql()
            xl = _mock_xl()
            MockXl.return_value = xl
            set_invoice(_INV)
        mod_calls = [c for c in xl.invoke.call_args_list
                     if c.args and c.args[0] == "XLModyfikujNaglowek"]
        assert mod_calls == []

    def test_no_magazyn_in_pozycje(self):
        """FKo — brak pola Magazyn w XLDodajPozycje."""
        with patch("tools.xl_fko_set.SqlClient") as MockSql, \
             patch("tools.xl_fko_set.XlClient") as MockXl:
            MockSql.return_value.get_connection.return_value = _mock_sql()
            xl = _mock_xl()
            MockXl.return_value = xl
            set_invoice(_INV)
        poz_call = next(c for c in xl.invoke.call_args_list
                        if c.args and c.args[0] == "XLDodajPozycje")
        assert "Magazyn" not in poz_call.kwargs

    def test_seria_zkkr_passed_to_nowy_dokument(self):
        with patch("tools.xl_fko_set.SqlClient") as MockSql, \
             patch("tools.xl_fko_set.XlClient") as MockXl:
            MockSql.return_value.get_connection.return_value = _mock_sql()
            xl = _mock_xl()
            MockXl.return_value = xl
            set_invoice(_INV)
        nowy_call = next(c for c in xl.invoke.call_args_list
                         if c.args and c.args[0] == "XLNowyDokument")
        assert nowy_call.kwargs["Seria"] == "ZKKR"

    def test_rodzaj_zakupu_2_passed_to_nowy_dokument(self):
        with patch("tools.xl_fko_set.SqlClient") as MockSql, \
             patch("tools.xl_fko_set.XlClient") as MockXl:
            MockSql.return_value.get_connection.return_value = _mock_sql()
            xl = _mock_xl()
            MockXl.return_value = xl
            set_invoice(_INV)
        nowy_call = next(c for c in xl.invoke.call_args_list
                         if c.args and c.args[0] == "XLNowyDokument")
        assert nowy_call.kwargs["RodzajZakupu"] == 2

    def test_doc_id_passed_to_pozycje(self):
        with patch("tools.xl_fko_set.SqlClient") as MockSql, \
             patch("tools.xl_fko_set.XlClient") as MockXl:
            MockSql.return_value.get_connection.return_value = _mock_sql()
            xl = _mock_xl()
            MockXl.return_value = xl
            set_invoice(_INV)
        poz_call = next(c for c in xl.invoke.call_args_list
                        if c.args and c.args[0] == "XLDodajPozycje")
        assert poz_call.kwargs["_lDokumentID"] == 999

    def test_avista_when_towar_not_found(self):
        with patch("tools.xl_fko_set.SqlClient") as MockSql, \
             patch("tools.xl_fko_set.XlClient") as MockXl:
            MockSql.return_value.get_connection.return_value = _mock_sql()
            MockXl.return_value = _mock_xl()
            result = set_invoice(_INV)
        assert "Usługa A" in result["data"]["avista"]
        assert "Usługa B" in result["data"]["avista"]

    def test_no_avista_when_towar_found(self):
        towar_rows = {"Usługa A": "KOD01", "Usługa B": "KOD02"}
        with patch("tools.xl_fko_set.SqlClient") as MockSql, \
             patch("tools.xl_fko_set.XlClient") as MockXl:
            MockSql.return_value.get_connection.return_value = _mock_sql(towar_rows=towar_rows)
            MockXl.return_value = _mock_xl()
            result = set_invoice(_INV)
        assert result["data"]["avista"] == []

    def test_cleanup_tryb0_on_pozycja_error(self):
        with patch("tools.xl_fko_set.SqlClient") as MockSql, \
             patch("tools.xl_fko_set.XlClient") as MockXl:
            MockSql.return_value.get_connection.return_value = _mock_sql()
            xl = _mock_xl(poz=_ERR)
            MockXl.return_value = xl
            set_invoice(_INV)
        xl.zamknij_dokument.assert_called_with(lDokumentID=999, Tryb=0)

    def test_result_has_duration_ms(self):
        with patch("tools.xl_fko_set.SqlClient") as MockSql, \
             patch("tools.xl_fko_set.XlClient") as MockXl:
            MockSql.return_value.get_connection.return_value = _mock_sql()
            MockXl.return_value = _mock_xl()
            result = set_invoice(_INV)
        assert "duration_ms" in result["meta"]


# --- _vat_key ---

class TestVatKey:
    def test_23_opodatkowany(self):
        assert _vat_key("23") == (23, 1)

    def test_zw_lowercase(self):
        assert _vat_key("zw") == (0, 0)

    def test_np_uppercase(self):
        assert _vat_key("NP") == (0, 2)

    def test_unknown_fallback(self):
        assert _vat_key("99") == (0, 1)


class TestPositionVAT:
    def test_stawka_pod_23pct_passed(self):
        with patch("tools.xl_fko_set.SqlClient") as MockSql, \
             patch("tools.xl_fko_set.XlClient") as MockXl:
            MockSql.return_value.get_connection.return_value = _mock_sql()
            xl = _mock_xl()
            MockXl.return_value = xl
            set_invoice(_INV)
        poz_call = next(c for c in xl.invoke.call_args_list
                        if c.args and c.args[0] == "XLDodajPozycje")
        assert poz_call.kwargs["StawkaPod"] == 2300
        assert poz_call.kwargs["FlagaVAT"] == 1
