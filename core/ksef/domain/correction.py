"""Domain model — korekta KSeF FA(3) KOR.

Korekta ma wiersze w modelu StanPrzed/StanPo — każda pozycja jest parą
(wartosc oryginalna + wartosc po korekcie). Podsumowanie na root Fa zawiera
roznice kwotowe (moze byc ujemne).

Decyzja projektowa (developer, 2026-04-15): plan architekta proponuje
StanPrzed/StanPo z osobnym podsumowaniem. Obecny XML (output/ksef/ksef_kor_*.xml)
ma jedno podsumowanie na root Fa. Model trzyma sie XML — StanPrzed/StanPo zawiera
tylko wiersze. Do zglosenia w code review.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from core.ksef.domain.invoice import (
    Adnotacje,
    Naglowek,
    Platnosc,
    Podmiot,
    PodsumowanieVat,
)


@dataclass(frozen=True)
class PozycjaKorekta:
    """Wiersz korekty FSK — inne pola niz FS (P_9B, P_11A, P_11Vat, opcjonalny
    P_6A/Indeks/PKWiU/StanPrzed)."""
    nr_pozycji: int
    nazwa_towaru: str
    indeks: str | None
    gtin: str | None
    pkwiu: str | None
    jednostka_miary: str
    ilosc: Decimal
    cena_brutto_jedn: Decimal
    wartosc_netto: Decimal
    kwota_vat: Decimal
    stawka_vat: str
    stan_przed: bool
    data_korekty: date | None


@dataclass(frozen=True)
class DaneFaKorygowanej:
    data_wystawienia_org: date
    numer_faktury_org: str


@dataclass(frozen=True)
class StanPrzed:
    wiersze: tuple[PozycjaKorekta, ...]


@dataclass(frozen=True)
class StanPo:
    wiersze: tuple[PozycjaKorekta, ...]


@dataclass(frozen=True)
class Korekta:
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
    przyczyna_korekty: str
    dane_fa_korygowanej: DaneFaKorygowanej
    stan_przed: StanPrzed
    stan_po: StanPo
    platnosc: Platnosc
