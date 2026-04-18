"""Unit tests XmlBuilder — helpery, formatery, edge cases."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

import pytest
from lxml import etree

from core.ksef.adapters.xml_builder import NS, XmlBuilder
from core.ksef.domain.invoice import (
    Adnotacje, Faktura, Naglowek, Platnosc, Podmiot, PodsumowanieVat, Pozycja,
)

_CLOCK = lambda: datetime(2026, 4, 14, 12, 0, 0)


@pytest.fixture
def builder() -> XmlBuilder:
    return XmlBuilder(clock=_CLOCK)


# ---- formatery -----------------------------------------------------------

def test_format_decimal_none_returns_none(builder: XmlBuilder) -> None:
    assert builder._format_decimal(None) is None


def test_format_decimal_2_places_default(builder: XmlBuilder) -> None:
    assert builder._format_decimal(Decimal("12.3")) == "12.30"


def test_format_decimal_rounds_half_up(builder: XmlBuilder) -> None:
    assert builder._format_decimal(Decimal("1.005")) == "1.01"


def test_format_decimal_negative(builder: XmlBuilder) -> None:
    assert builder._format_decimal(Decimal("-49.10")) == "-49.10"


def test_format_ilosc_strips_trailing_zeros(builder: XmlBuilder) -> None:
    assert builder._format_ilosc(Decimal("1.5000")) == "1.5"


def test_format_ilosc_strips_dot_for_whole(builder: XmlBuilder) -> None:
    assert builder._format_ilosc(Decimal("2.0000")) == "2"
    assert builder._format_ilosc(Decimal("120")) == "120"


def test_format_ilosc_preserves_fractional(builder: XmlBuilder) -> None:
    assert builder._format_ilosc(Decimal("1.0050")) == "1.005"


def test_format_ilosc_zero_fallback(builder: XmlBuilder) -> None:
    assert builder._format_ilosc(Decimal("0")) == "0"


# ---- podmiot omitowanie NIP/AdresL2 --------------------------------------

def _mk_min_faktura(p2: Podmiot) -> Faktura:
    return Faktura(
        gid_numer=1, naglowek=Naglowek(),
        podmiot1=Podmiot(nip="0000000000", pelna_nazwa="S",
                          kod_kraju="PL", adres_l1="A", adres_l2="B"),
        podmiot2=p2, kod_waluty="PLN",
        data_wystawienia=date(2026, 4, 14),
        data_sprzedazy=None, numer_faktury="X/1",
        podsumowanie=PodsumowanieVat(
            vat_23_podstawa=Decimal("100.00"), vat_23_kwota=Decimal("23.00"),
            vat_8_podstawa=None, vat_8_kwota=None, vat_5_podstawa=None,
            vat_5_kwota=None, vat_0_podstawa=None, vat_0_kwota=None,
            zw_podstawa=None, np_podstawa=None,
            kwota_naleznosci=Decimal("123.00"),
        ),
        adnotacje=Adnotacje(mpp="2"), rodzaj="VAT",
        wiersze=(Pozycja(nr_pozycji=1, nazwa_towaru="X", gtin=None,
                          jednostka_miary="szt.", ilosc=Decimal("1"),
                          cena_netto_jedn=Decimal("100"),
                          wartosc_netto=Decimal("100"), stawka_vat="23"),),
        platnosc=Platnosc(termin_platnosci=None,
                          kod_formy_platnosci=None,
                          nr_rachunku_bankowego=None),
    )


def test_podmiot_without_nip_omits_tag(builder: XmlBuilder) -> None:
    p2 = Podmiot(nip=None, pelna_nazwa="Zagraniczny klient",
                 kod_kraju="DE", adres_l1="Strasse 1", adres_l2=None)
    xml = builder.build_faktura(_mk_min_faktura(p2))
    root = etree.fromstring(xml)
    nip_elements = root.findall(f".//{{{NS}}}Podmiot2/{{{NS}}}DaneIdentyfikacyjne/{{{NS}}}NIP")
    assert nip_elements == []


def test_podmiot_without_adres_l2_omits_tag(builder: XmlBuilder) -> None:
    p2 = Podmiot(nip="1234567890", pelna_nazwa="N", kod_kraju="PL",
                 adres_l1="A", adres_l2=None)
    xml = builder.build_faktura(_mk_min_faktura(p2))
    root = etree.fromstring(xml)
    l2 = root.findall(f".//{{{NS}}}Podmiot2/{{{NS}}}Adres/{{{NS}}}AdresL2")
    assert l2 == []


# ---- data sprzedazy ------------------------------------------------------

def test_p6_omitted_when_data_sprzedazy_equal_to_wystawienia(builder: XmlBuilder) -> None:
    f = _mk_min_faktura(Podmiot(nip="1", pelna_nazwa="N", kod_kraju="PL",
                                 adres_l1="A", adres_l2=None))
    xml = builder.build_faktura(f)
    root = etree.fromstring(xml)
    assert root.findall(f".//{{{NS}}}Fa/{{{NS}}}P_6") == []


def test_p6_emitted_when_data_sprzedazy_differs(builder: XmlBuilder) -> None:
    base = _mk_min_faktura(Podmiot(nip="1", pelna_nazwa="N", kod_kraju="PL",
                                    adres_l1="A", adres_l2=None))
    import dataclasses
    f = dataclasses.replace(base, data_sprzedazy=date(2026, 4, 10))
    xml = builder.build_faktura(f)
    root = etree.fromstring(xml)
    p6 = root.find(f".//{{{NS}}}Fa/{{{NS}}}P_6")
    assert p6 is not None and p6.text == "2026-04-10"


# ---- clock injection -----------------------------------------------------

def test_data_wytworzenia_uses_clock(builder: XmlBuilder) -> None:
    f = _mk_min_faktura(Podmiot(nip="1", pelna_nazwa="N", kod_kraju="PL",
                                 adres_l1="A", adres_l2=None))
    xml = builder.build_faktura(f)
    root = etree.fromstring(xml)
    dw = root.find(f".//{{{NS}}}Naglowek/{{{NS}}}DataWytworzeniaFa")
    assert dw.text == "2026-04-14T12:00:00Z"


# ---- namespace + declaration ---------------------------------------------

def test_output_has_xml_declaration(builder: XmlBuilder) -> None:
    f = _mk_min_faktura(Podmiot(nip="1", pelna_nazwa="N", kod_kraju="PL",
                                 adres_l1="A", adres_l2=None))
    xml = builder.build_faktura(f)
    assert xml.startswith(b"<?xml version='1.0' encoding='UTF-8'?>")


def test_output_has_correct_namespace(builder: XmlBuilder) -> None:
    f = _mk_min_faktura(Podmiot(nip="1", pelna_nazwa="N", kod_kraju="PL",
                                 adres_l1="A", adres_l2=None))
    xml = builder.build_faktura(f)
    root = etree.fromstring(xml)
    assert root.nsmap[None] == "http://crd.gov.pl/wzor/2025/06/25/13775/"


# ---- platnosc ------------------------------------------------------------


def test_platnosc_empty_emits_empty_element(builder: XmlBuilder) -> None:
    f = _mk_min_faktura(Podmiot(nip="1", pelna_nazwa="N", kod_kraju="PL",
                                 adres_l1="A", adres_l2=None))
    xml = builder.build_faktura(f)
    assert b"<Platnosc/>" in xml or b"<Platnosc></Platnosc>" in xml
