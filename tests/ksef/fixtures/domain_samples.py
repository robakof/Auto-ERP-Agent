"""Faktura/Korekta literaly z prod XML — dla snapshot testow.

Snapshoty regenerowane z clock = datetime(2026, 4, 14, 12, 0, 0).
DataWytworzeniaFa = "2026-04-14T12:00:00Z" we wszystkich snapshotach.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from core.ksef.domain.correction import (
    DaneFaKorygowanej,
    Korekta,
    PozycjaKorekta,
    StanPo,
    StanPrzed,
)
from core.ksef.domain.invoice import (
    Adnotacje,
    Faktura,
    Naglowek,
    Platnosc,
    Podmiot,
    PodsumowanieVat,
    Pozycja,
)

_SPRZEDAWCA = Podmiot(
    nip="7871003063",
    pelna_nazwa="Produkcja Zniczy I Lampionów CEIM MAREK CYPROWSKI",
    kod_kraju="PL",
    adres_l1="Leśna 14",
    adres_l2="64-551 Otorowo",
)

_NAGLOWEK = Naglowek()
_ADNOTACJE_DEFAULT = Adnotacje(mpp="2")


def _vat23(podstawa: str, kwota: str, naleznosc: str) -> PodsumowanieVat:
    return PodsumowanieVat(
        vat_23_podstawa=Decimal(podstawa), vat_23_kwota=Decimal(kwota),
        vat_8_podstawa=None, vat_8_kwota=None,
        vat_5_podstawa=None, vat_5_kwota=None,
        vat_0_podstawa=None, vat_0_kwota=None,
        zw_podstawa=None, np_podstawa=None,
        kwota_naleznosci=Decimal(naleznosc),
    )


def _poz(nr: int, nazwa: str, gtin: str | None, jm: str, ilosc: str,
         cena: str, wartosc: str, vat: str = "23") -> Pozycja:
    return Pozycja(
        nr_pozycji=nr, nazwa_towaru=nazwa, gtin=gtin,
        jednostka_miary=jm, ilosc=Decimal(ilosc),
        cena_netto_jedn=Decimal(cena), wartosc_netto=Decimal(wartosc),
        stawka_vat=vat,
    )


def _poz_kor(nr: int, *, stan_przed: bool, data_kor: date | None,
             nazwa: str, indeks: str | None, gtin: str | None,
             ilosc: str, cena_netto: str, wartosc_netto: str) -> PozycjaKorekta:
    return PozycjaKorekta(
        nr_pozycji=nr, nazwa_towaru=nazwa, indeks=indeks, gtin=gtin, pkwiu=None,
        jednostka_miary="opak.", ilosc=Decimal(ilosc),
        cena_netto_jedn=Decimal(cena_netto),
        wartosc_netto=Decimal(wartosc_netto),
        stawka_vat="23",
        stan_przed=stan_przed, data_korekty=data_kor,
    )


# ---- FS-59 ----------------------------------------------------------------

def make_fs_59() -> Faktura:
    nabywca = Podmiot(
        nip="7822564956",
        pelna_nazwa="INDIRA SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ",
        kod_kraju="PL",
        adres_l1="ul. Władysława Jagiełły 4",
        adres_l2="41-100 Siemianowice Śląskie",
    )
    wiersze = (
        _poz(1, "Bis św. zapach. snk80 truskawka", "5906927280738", "opak.", "6", "8.58", "51.48"),
        _poz(2, "Bis podg. zapach.18 szt. wanilia", "5906927120676", "opak.", "6", "5.67", "34.02"),
        _poz(3, "Bis podg. maxi 6 szt. wanilia", "5906927530673", "opak.", "6", "6.65", "39.90"),
        _poz(4, "Olejek zapachowy 12 ml Nature", "5906948848009", "szt.", "120", "3.99", "478.80"),
        _poz(5, "Gol Kadzidełka długie Copal", "8901810026742", "opak.", "25", "0.99", "24.75"),
        _poz(6, "Gol Kadzidełka długie Kiwi", "8901810021563", "opak.", "25", "0.99", "24.75"),
        _poz(7, "Gol Kadzidełka długie Musk", "5904645941009", "opak.", "25", "0.99", "24.75"),
        _poz(8, "Gol Kadzidełka długie Precious Chandan", "5904645941009", "opak.", "25", "0.99", "24.75"),
        _poz(9, "Bis św. zapach. snk80 wanilia", "5906927280677", "opak.", "6", "8.58", "51.48"),
    )
    return Faktura(
        gid_numer=59, naglowek=_NAGLOWEK,
        podmiot1=_SPRZEDAWCA, podmiot2=nabywca,
        kod_waluty="PLN", data_wystawienia=date(2026, 4, 14),
        data_sprzedazy=None, numer_faktury="FS-59/04/26/SPKR",
        podsumowanie=_vat23("754.68", "173.58", "928.26"),
        adnotacje=_ADNOTACJE_DEFAULT, rodzaj="VAT", wiersze=wiersze,
        platnosc=Platnosc(
            termin_platnosci=date(2026, 5, 29),
            kod_formy_platnosci="6",
            nr_rachunku_bankowego="65109013910000000039004697",
        ),
    )


# ---- FS-60 ----------------------------------------------------------------

def make_fs_60() -> Faktura:
    nabywca = Podmiot(
        nip="7722298969",
        pelna_nazwa="Przedsiębiorstwo Handlowo- Usługowe \"Ave\"",
        kod_kraju="PL",
        adres_l1="ul. Kościelna 4",
        adres_l2="97-565 Lgota Wielka",
    )
    wiersze = (
        _poz(1, "Wk Zniczomat 1 dzień", None, "szt.", "2600", "1.20", "3120.00"),
        _poz(2, "Wk Zniczomat 2 dni", None, "szt.", "1820", "1.37", "2493.40"),
    )
    return Faktura(
        gid_numer=60, naglowek=_NAGLOWEK,
        podmiot1=_SPRZEDAWCA, podmiot2=nabywca,
        kod_waluty="PLN", data_wystawienia=date(2026, 4, 14),
        data_sprzedazy=None, numer_faktury="FS-60/04/26/SPKR",
        podsumowanie=_vat23("5613.40", "1291.08", "6904.48"),
        adnotacje=_ADNOTACJE_DEFAULT, rodzaj="VAT", wiersze=wiersze,
        platnosc=Platnosc(
            termin_platnosci=date(2026, 5, 14),
            kod_formy_platnosci="6",
            nr_rachunku_bankowego="65109013910000000039004697",
        ),
    )


# ---- FS-73 ----------------------------------------------------------------

def make_fs_73() -> Faktura:
    nabywca = Podmiot(
        nip="7841009718",
        pelna_nazwa="F.H.U. Tomasz Nitecki",
        kod_kraju="PL",
        adres_l1="ul. Borowa 3",
        adres_l2="62-200 Gniezno",
    )
    wiersze = (
        _poz(1, "ZP 279 Solar", "5907508425296", "szt.", "2", "22.00", "35.77"),
        _poz(2, "Cor Anioł LED serce 7cc 1/20 ANG", "5907520029953", "szt.", "1", "33.00", "26.83"),
        _poz(3, "Cor Anioł LED serce 7cc 4/20/ANG", "5907520030973", "szt.", "1", "27.00", "21.95"),
        _poz(4, "Cor Anioł LED serce 7cc 2/20/ANG", "5907520029960", "szt.", "1", "27.00", "21.95"),
        _poz(5, "Cor Wkład Led Anioł efekt płomienia (2xR6)", "5907520046509", "szt.", "5", "10.00", "40.65"),
        _poz(6, "Ass Świetlik S1 - żółty", "5907646175725", "szt.", "12", "3.50", "34.15"),
        _poz(7, "Cor Wkład LED serce (2xR6) Biały", "5907520039310", "szt.", "3", "6.00", "14.63"),
        _poz(8, "Cor Anioł LED serce 7cc 1/15/ANG mały", "5907520040644", "szt.", "2", "15.00", "24.39"),
    )
    return Faktura(
        gid_numer=73, naglowek=_NAGLOWEK,
        podmiot1=_SPRZEDAWCA, podmiot2=nabywca,
        kod_waluty="PLN", data_wystawienia=date(2026, 4, 14),
        data_sprzedazy=None, numer_faktury="FS-73/04/26/FRA",
        podsumowanie=_vat23("220.33", "50.67", "271.00"),
        adnotacje=_ADNOTACJE_DEFAULT, rodzaj="VAT", wiersze=wiersze,
        platnosc=Platnosc(
            termin_platnosci=date(2026, 4, 28),
            kod_formy_platnosci="3",
            nr_rachunku_bankowego=None,
        ),
    )


# ---- FSK-1 ----------------------------------------------------------------

def make_fsk_1() -> Korekta:
    nabywca = Podmiot(
        nip="7822508194",
        pelna_nazwa="SOLEI SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ",
        kod_kraju="PL",
        adres_l1="Aleja Tysiąclecia 34A",
        adres_l2="59-700 Bolesławiec",
    )
    przed = (
        _poz_kor(12, stan_przed=True, data_kor=None,
                 nazwa="Znicz szklany Z 499 LED sr Kerti",
                 indeks="CZNI26167", gtin="5903293726167",
                 ilosc="8", cena_netto="7.92",
                 wartosc_netto="63.36"),
        _poz_kor(25, stan_przed=True, data_kor=None,
                 nazwa="Barok ZŁ", indeks="DAVP42263", gtin="5907702542263",
                 ilosc="8", cena_netto="9.50",
                 wartosc_netto="76.00"),
    )
    po = (
        _poz_kor(12, stan_przed=False, data_kor=date(2026, 4, 14),
                 nazwa="Znicz szklany Z 499 LED sr Kerti",
                 indeks="CZNI26167", gtin="5903293726167",
                 ilosc="3", cena_netto="7.92",
                 wartosc_netto="23.76"),
        _poz_kor(25, stan_przed=False, data_kor=date(2026, 4, 14),
                 nazwa="Barok ZŁ", indeks="DAVP42263", gtin="5907702542263",
                 ilosc="7", cena_netto="9.50",
                 wartosc_netto="66.50"),
    )
    return Korekta(
        gid_numer=1, naglowek=_NAGLOWEK,
        podmiot1=_SPRZEDAWCA, podmiot2=nabywca,
        kod_waluty="PLN", data_wystawienia=date(2026, 4, 14),
        data_sprzedazy=None, numer_faktury="FSK-1/04/26/SPKRK",
        podsumowanie=_vat23("-49.10", "-11.29", "-60.39"),
        adnotacje=_ADNOTACJE_DEFAULT,
        przyczyna_korekty="Uszkodzenie towaru",
        dane_fa_korygowanej=DaneFaKorygowanej(
            data_wystawienia_org=date(2026, 3, 25),
            numer_faktury_org="FS-228/03/26/SPKR",
        ),
        stan_przed=StanPrzed(wiersze=przed),
        stan_po=StanPo(wiersze=po),
        platnosc=Platnosc(
            termin_platnosci=date(2026, 5, 29),
            kod_formy_platnosci="6",
            nr_rachunku_bankowego=None,
        ),
    )
