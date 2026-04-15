"""Domain model — faktura KSeF FA(3).

Typowane dataclasses (frozen) mapujące strukturę XML FA(3). Decimal dla kwot, Enum
dla rodzajow. Podmiot/Pozycja/Podsumowanie/Adnotacje/Platnosc wspoldzielone z korekta
(core/ksef/domain/correction.py).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum


class RodzajFaktury(str, Enum):
    VAT = "VAT"
    KOR = "KOR"
    ZAL = "ZAL"
    ROZ = "ROZ"


@dataclass(frozen=True)
class Podmiot:
    nip: str | None
    pelna_nazwa: str
    kod_kraju: str
    adres_l1: str
    adres_l2: str | None


@dataclass(frozen=True)
class Pozycja:
    """Wiersz faktury sprzedaży (FS)."""
    nr_pozycji: int
    nazwa_towaru: str
    gtin: str | None
    jednostka_miary: str
    ilosc: Decimal
    cena_netto_jedn: Decimal
    wartosc_netto: Decimal
    stawka_vat: str


@dataclass(frozen=True)
class PodsumowanieVat:
    """Sumy per stawka VAT — None gdy stawka nie występuje."""
    vat_23_podstawa: Decimal | None
    vat_23_kwota: Decimal | None
    vat_8_podstawa: Decimal | None
    vat_8_kwota: Decimal | None
    vat_5_podstawa: Decimal | None
    vat_5_kwota: Decimal | None
    vat_0_podstawa: Decimal | None
    vat_0_kwota: Decimal | None
    zw_podstawa: Decimal | None
    np_podstawa: Decimal | None
    kwota_naleznosci: Decimal


@dataclass(frozen=True)
class Adnotacje:
    mpp: str
    p_17: str = "2"
    p_18: str = "2"
    p_18a: str = "2"
    zwolnienie_p19n: str = "1"
    nst_p22n: str = "1"
    p_23: str = "2"
    p_marzy_n: str = "1"


@dataclass(frozen=True)
class Platnosc:
    termin_platnosci: date | None
    kod_formy_platnosci: str | None
    nr_rachunku_bankowego: str | None


@dataclass(frozen=True)
class Naglowek:
    kod_formularza: str = "FA"
    kod_systemowy: str = "FA (3)"
    wersja_schemy: str = "1-0E"
    wariant_formularza: str = "3"
    system_info: str = "Comarch ERP XL"


@dataclass(frozen=True)
class Faktura:
    gid_numer: int
    naglowek: Naglowek
    podmiot1: Podmiot
    podmiot2: Podmiot
    kod_waluty: str
    data_wystawienia: date
    data_sprzedazy: date | None
    numer_faktury: str
    podsumowanie: PodsumowanieVat
    adnotacje: Adnotacje
    rodzaj: str
    wiersze: tuple[Pozycja, ...]
    platnosc: Platnosc
