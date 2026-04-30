"""Unit tests ErpReader — SQL error handling, row mapping, grouping."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from core.ksef.adapters.erp_reader import ErpReader, ErpReaderError
from core.ksef.domain.invoice import Pozycja


def _fake_query(columns: list[str], rows: list[list]) -> object:
    def _q(_sql: str) -> dict:
        return {"ok": True, "data": {"columns": columns, "rows": rows}, "error": None}
    return _q


def _err_query(msg: str) -> object:
    def _q(_sql: str) -> dict:
        return {"ok": False, "data": None, "error": {"message": msg}}
    return _q


# ---- fake SQL result helpers ---------------------------------------------

_FS_COLUMNS = [
    "_GIDNumer",
    "P1_NIP", "P1_PelnaNazwa", "P1_KodKraju", "P1_AdresL1", "P1_AdresL2",
    "P2_NIP", "P2_PelnaNazwa", "P2_KodKraju", "P2_AdresL1", "P2_AdresL2",
    "Fa_KodWaluty", "Fa_P1_DataWystawienia", "Fa_P2_DataSprzedazy",
    "Fa_P2A_NumerFaktury", "Fa_RodzajFaktury",
    "Fa_P13_1_Podstawa23", "Fa_P14_1_VAT23",
    "Fa_P13_2_Podstawa8", "Fa_P14_2_VAT8",
    "Fa_P13_3_Podstawa5", "Fa_P14_3_VAT5",
    "Fa_P13_5_Podstawa0", "Fa_P14_5_VAT0",
    "Fa_P13_6_PodstawaZW", "Fa_P13_7_PodstawaNP",
    "Fa_P15_KwotaNaleznosci", "Fa_P16_MPP",
    "Wiersz_NrPozycji", "Wiersz_P7_NazwaTowaru", "Wiersz_GTIN",
    "Wiersz_P8A_JM", "Wiersz_P8B_Ilosc",
    "Wiersz_P9A_CenaNettoJedn", "Wiersz_P10_WartoscNetto", "Wiersz_P11_StawkaVAT",
    "Plat_TerminPlatnosci", "Plat_KodFormyPlatnosci", "Plat_NrRachunkuBankowego",
]


def _fs_row(gid: int, nr_poz: int, *, p2_adres_l2: str | None = "41-100 Miasto",
            gtin: str | None = "5906927280738") -> list:
    return [
        gid,
        "7871003063", "Sprzedawca SA", "PL", "Leśna 14", "64-551 Otorowo",
        "7822564956", "Nabywca sp. z o.o.", "PL", "ul. Jagiełły 4", p2_adres_l2,
        "PLN", date(2026, 4, 14), date(2026, 4, 14),
        f"FS-{gid}/04/26/SPKR", "VAT",
        Decimal("100.00"), Decimal("23.00"),
        None, None, None, None, None, None, None, None,
        Decimal("123.00"), "2",
        nr_poz, "Towar A", gtin,
        "szt.", Decimal("1"),
        Decimal("100.00"), Decimal("100.00"), "23",
        date(2026, 5, 14), "6", "65109013910000000039004697",
    ]


# ---- SQL error -----------------------------------------------------------

def test_fetch_faktury_sql_error_raises() -> None:
    reader = ErpReader(run_query=_err_query("connection lost"))
    with pytest.raises(ErpReaderError, match="connection lost"):
        reader.fetch_faktury()


# ---- empty results -------------------------------------------------------

def test_fetch_faktury_empty_returns_empty_list() -> None:
    reader = ErpReader(run_query=_fake_query(_FS_COLUMNS, []))
    assert reader.fetch_faktury() == []


def test_fetch_korekty_empty_returns_empty_list() -> None:
    cols = _FS_COLUMNS + ["Kor_PrzyczynaKorekty", "Kor_DataWystFaKorygowanej",
                          "Kor_NrFaKorygowanej", "Wiersz_StanPrzed",
                          "Wiersz_DataKorekty", "Wiersz_Indeks", "Wiersz_PKWiU",
                          "Wiersz_P9A_CenaNettoJedn", "Wiersz_P11_WartoscNetto",
                          "Wiersz_P12_StawkaVAT"]
    reader = ErpReader(run_query=_fake_query(cols, []))
    assert reader.fetch_korekty() == []


# ---- single row mapping --------------------------------------------------

def test_row_to_pozycja_maps_decimals() -> None:
    reader = ErpReader(run_query=_fake_query(_FS_COLUMNS, [_fs_row(59, 1)]))
    faktura = reader.fetch_faktury()[0]
    poz = faktura.wiersze[0]
    assert isinstance(poz, Pozycja)
    assert poz.ilosc == Decimal("1")
    assert poz.cena_netto_jedn == Decimal("100.00")
    assert poz.stawka_vat == "23"
    assert poz.gtin == "5906927280738"


def test_row_to_podmiot2_with_none_adres_l2() -> None:
    reader = ErpReader(run_query=_fake_query(_FS_COLUMNS, [_fs_row(60, 1, p2_adres_l2=None)]))
    faktura = reader.fetch_faktury()[0]
    assert faktura.podmiot2.adres_l2 is None



def test_row_to_pozycja_with_null_gtin() -> None:
    reader = ErpReader(run_query=_fake_query(_FS_COLUMNS, [_fs_row(61, 1, gtin=None)]))
    faktura = reader.fetch_faktury()[0]
    assert faktura.wiersze[0].gtin is None


# ---- rodzsumowanie VAT (tylko obecne stawki) -----------------------------

def test_podsumowanie_only_present_rates_non_none() -> None:
    reader = ErpReader(run_query=_fake_query(_FS_COLUMNS, [_fs_row(62, 1)]))
    faktura = reader.fetch_faktury()[0]
    assert faktura.podsumowanie.vat_23_podstawa == Decimal("100.00")
    assert faktura.podsumowanie.vat_8_podstawa is None
    assert faktura.podsumowanie.vat_5_podstawa is None
    assert faktura.podsumowanie.zw_podstawa is None


# ---- grouping multiple rows per faktura ----------------------------------

def test_fetch_faktury_groups_rows_by_gid() -> None:
    rows = [_fs_row(59, 1), _fs_row(59, 2), _fs_row(60, 1)]
    reader = ErpReader(run_query=_fake_query(_FS_COLUMNS, rows))
    faktury = reader.fetch_faktury()
    assert len(faktury) == 2
    assert len(faktury[0].wiersze) == 2
    assert len(faktury[1].wiersze) == 1


# ---- korekta StanPrzed/StanPo splitting ----------------------------------

_FSK_COLUMNS = [
    "_GIDNumer",
    "P1_NIP", "P1_PelnaNazwa", "P1_KodKraju", "P1_AdresL1", "P1_AdresL2",
    "P2_NIP", "P2_PelnaNazwa", "P2_KodKraju", "P2_AdresL1", "P2_AdresL2",
    "Fa_KodWaluty", "Fa_P1_DataWystawienia", "Fa_P2_DataSprzedazy",
    "Fa_P2A_NumerFaktury", "Fa_RodzajFaktury",
    "Fa_P13_1_Podstawa23", "Fa_P14_1_VAT23",
    "Fa_P13_2_Podstawa8", "Fa_P14_2_VAT8",
    "Fa_P13_3_Podstawa5", "Fa_P14_3_VAT5",
    "Fa_P13_5_Podstawa0", "Fa_P14_5_VAT0",
    "Fa_P13_6_PodstawaZW", "Fa_P13_7_PodstawaNP",
    "Fa_P15_KwotaNaleznosci", "Fa_P16_MPP",
    "Kor_PrzyczynaKorekty", "Kor_DataWystFaKorygowanej", "Kor_NrFaKorygowanej",
    "Wiersz_NrPozycji", "Wiersz_StanPrzed", "Wiersz_DataKorekty",
    "Wiersz_P7_NazwaTowaru", "Wiersz_Indeks", "Wiersz_GTIN", "Wiersz_PKWiU",
    "Wiersz_P8A_JM", "Wiersz_P8B_Ilosc",
    "Wiersz_P9A_CenaNettoJedn", "Wiersz_P11_WartoscNetto",
    "Wiersz_P12_StawkaVAT",
    "Plat_TerminPlatnosci", "Plat_KodFormyPlatnosci", "Plat_NrRachunkuBankowego",
]


def _fsk_row(gid: int, nr_poz: int, stan_przed: int, data_kor: date | None = None) -> list:
    return [
        gid,
        "7871003063", "Sprzedawca", "PL", "L 14", "64-551 O",
        "7822508194", "SOLEI", "PL", "Aleja 34", "59-700 B",
        "PLN", date(2026, 4, 14), date(2026, 4, 14),
        f"FSK-{gid}/04/26/SPKRK", "KOR",
        Decimal("-49.10"), Decimal("-11.29"),
        None, None, None, None, None, None, None, None,
        Decimal("-60.39"), "2",
        "Uszkodzenie towaru", date(2026, 3, 25), "FS-228/03/26/SPKR",
        nr_poz, stan_przed, data_kor,
        "Towar", "IDX1", "5903293726167", None,
        "opak.", Decimal("1"),
        Decimal("9.74"), Decimal("10.00"),
        "23",
        date(2026, 5, 29), "6", None,
    ]


def test_fetch_korekty_splits_stan_przed_and_stan_po() -> None:
    rows = [
        _fsk_row(1, 12, stan_przed=1),
        _fsk_row(1, 12, stan_przed=0, data_kor=date(2026, 4, 14)),
    ]
    reader = ErpReader(run_query=_fake_query(_FSK_COLUMNS, rows))
    kor = reader.fetch_korekty()[0]
    assert len(kor.stan_przed.wiersze) == 1
    assert len(kor.stan_po.wiersze) == 1
    assert kor.stan_przed.wiersze[0].stan_przed is True
    assert kor.stan_po.wiersze[0].stan_przed is False
    assert kor.stan_po.wiersze[0].data_korekty == date(2026, 4, 14)


def test_fetch_korekty_reads_przyczyna_and_dane_fa_korygowanej() -> None:
    rows = [_fsk_row(1, 12, stan_przed=1)]
    reader = ErpReader(run_query=_fake_query(_FSK_COLUMNS, rows))
    kor = reader.fetch_korekty()[0]
    assert kor.przyczyna_korekty == "Uszkodzenie towaru"
    assert kor.dane_fa_korygowanej.numer_faktury_org == "FS-228/03/26/SPKR"
    assert kor.dane_fa_korygowanej.data_wystawienia_org == date(2026, 3, 25)


# ---- SQL building --------------------------------------------------------

def test_build_sql_adds_gid_filter() -> None:
    captured = []

    def _capture(sql: str) -> dict:
        captured.append(sql)
        return {"ok": True, "data": {"columns": _FS_COLUMNS, "rows": []}}

    ErpReader(run_query=_capture).fetch_faktury(gids=[59, 60])
    assert "TrN_GIDNumer IN (59, 60)" in captured[0]


def test_build_sql_adds_date_filters() -> None:
    captured = []

    def _capture(sql: str) -> dict:
        captured.append(sql)
        return {"ok": True, "data": {"columns": _FS_COLUMNS, "rows": []}}

    ErpReader(run_query=_capture).fetch_faktury(
        date_from="2026-04-01", date_to="2026-04-30",
    )
    assert "'2026-04-01'" in captured[0]
    assert "'2026-04-30'" in captured[0]
