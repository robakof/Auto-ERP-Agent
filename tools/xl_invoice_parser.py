"""Parser KSeF FA(3) XML → FzInvoice dataclass.

Obsługuje: RodzajFaktury=VAT (faktury zwykłe).
Pomija: KOR (korekty) — zwraca ok=False z powodem.

Użycie:
  result = parse_ksef_xml(Path("faktura.xml"))
  if result["ok"]:
      invoice = result["data"]
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

_NS = "http://crd.gov.pl/wzor/2025/06/25/13775/"


def _tag(name: str) -> str:
    return f"{{{_NS}}}{name}"


def _text(el: ET.Element | None, tag: str, default: str = "") -> str:
    if el is None:
        return default
    child = el.find(_tag(tag))
    return (child.text or "").strip() if child is not None else default


def _decimal(el: ET.Element | None, tag: str) -> Decimal:
    raw = _text(el, tag, "0")
    try:
        return Decimal(raw)
    except InvalidOperation:
        return Decimal("0")


def _date(val: str) -> date:
    return datetime.strptime(val[:10], "%Y-%m-%d").date()


@dataclass(frozen=True)
class FzPozycja:
    nr: int
    nazwa: str
    ilosc: Decimal
    jm: str
    cena_netto: Decimal
    wartosc_netto: Decimal
    stawka_vat: str
    wartosc_vat: Decimal


@dataclass(frozen=True)
class FzInvoice:
    nr_obcy: str
    nip_sprzedawcy: str
    nazwa_sprzedawcy: str
    data_wystawienia: date
    termin_platnosci: date
    waluta: str
    suma_netto: Decimal
    suma_vat: Decimal
    suma_brutto: Decimal
    pozycje: tuple[FzPozycja, ...]


def parse_ksef_xml(path: Path) -> dict:
    """Parsuje plik KSeF FA(3). Zwraca {"ok": bool, "data": FzInvoice|None, "error": str|None}."""
    try:
        tree = ET.parse(path)
    except ET.ParseError as e:
        return {"ok": False, "data": None, "error": f"XML parse error: {e}"}

    root = tree.getroot()
    fa = root.find(_tag("Fa"))
    if fa is None:
        return {"ok": False, "data": None, "error": "Brak elementu <Fa>"}

    rodzaj = _text(fa, "RodzajFaktury")
    if rodzaj != "VAT":
        return {"ok": False, "data": None, "error": f"Nieobsługiwany rodzaj faktury: {rodzaj} (obsługiwane: VAT)"}

    podmiot1 = root.find(_tag("Podmiot1"))
    dane1 = podmiot1.find(_tag("DaneIdentyfikacyjne")) if podmiot1 is not None else None

    nip = _text(dane1, "NIP")
    nazwa = _text(dane1, "Nazwa")

    data_wyst_str = _text(fa, "P_1")
    if not data_wyst_str:
        return {"ok": False, "data": None, "error": "Brak daty wystawienia (P_1)"}

    platnosc = fa.find(_tag("Platnosc"))
    termin_el = platnosc.find(_tag("TerminPlatnosci")) if platnosc is not None else None
    termin_str = _text(termin_el, "Termin") if termin_el is not None else data_wyst_str

    nr_obcy = _text(fa, "P_2")
    waluta = _text(fa, "KodWaluty", "PLN")
    suma_brutto = _decimal(fa, "P_15")

    suma_netto = sum(
        (_decimal(fa, f"P_13_{i}") for i in (1, 2, 3, 5)),
        Decimal("0"),
    )
    suma_vat = sum(
        (_decimal(fa, f"P_14_{i}") for i in (1, 2, 3)),
        Decimal("0"),
    )

    pozycje = _parse_pozycje(fa)
    if not pozycje:
        return {"ok": False, "data": None, "error": "Faktura nie zawiera pozycji (FaWiersz)"}

    invoice = FzInvoice(
        nr_obcy=nr_obcy,
        nip_sprzedawcy=nip,
        nazwa_sprzedawcy=nazwa,
        data_wystawienia=_date(data_wyst_str),
        termin_platnosci=_date(termin_str),
        waluta=waluta,
        suma_netto=suma_netto,
        suma_vat=suma_vat,
        suma_brutto=suma_brutto,
        pozycje=tuple(pozycje),
    )
    return {"ok": True, "data": invoice, "error": None}


def _parse_pozycje(fa: ET.Element) -> list[FzPozycja]:
    pozycje = []
    for wiersz in fa.findall(_tag("FaWiersz")):
        if wiersz.find(_tag("StanPrzed")) is not None:
            continue
        nr_raw = _text(wiersz, "NrWierszaFa", "0")
        try:
            nr = int(nr_raw)
        except ValueError:
            nr = 0
        stawka_raw = _text(wiersz, "P_12")
        stawka = stawka_raw if stawka_raw else "ZW"
        pozycje.append(FzPozycja(
            nr=nr,
            nazwa=_text(wiersz, "P_7"),
            ilosc=_decimal(wiersz, "P_8B"),
            jm=_text(wiersz, "P_8A", "szt"),
            cena_netto=_decimal(wiersz, "P_9B"),
            wartosc_netto=_decimal(wiersz, "P_11A"),
            stawka_vat=stawka,
            wartosc_vat=_decimal(wiersz, "P_11Vat"),
        ))
    return pozycje
