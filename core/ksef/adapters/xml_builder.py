"""Builder XML KSeF FA(3) — domain → XML bytes.

Helpery wspoldzielone FS/FSK (_build_podmiot, _build_adnotacje, _build_fa_header).
Rozne pozycje (FS: Pozycja, FSK: PozycjaKorekta) — dedykowane metody wierszy.

Clock injection dla DataWytworzeniaFa — testy deterministyczne.
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Callable

from lxml import etree

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

NS = "http://crd.gov.pl/wzor/2025/06/25/13775/"
_NSMAP = {None: NS}
_Q2 = Decimal("0.01")


class XmlBuilder:
    """Domain → UTF-8 XML bytes. `clock` injection dla DataWytworzeniaFa."""

    def __init__(self, clock: Callable[[], datetime] | None = None) -> None:
        self._clock = clock or datetime.now

    # ---- public ----------------------------------------------------------

    def build_faktura(self, faktura: Faktura) -> bytes:
        root = self._root()
        self._build_naglowek(root, faktura.naglowek)
        self._build_podmiot(root, faktura.podmiot1, tag="Podmiot1", with_jst_gv=False)
        self._build_podmiot(root, faktura.podmiot2, tag="Podmiot2", with_jst_gv=True)

        fa = _sub(root, "Fa")
        self._build_fa_header(
            fa, faktura.kod_waluty, faktura.data_wystawienia,
            faktura.numer_faktury, faktura.data_sprzedazy,
        )
        self._build_podsumowanie(fa, faktura.podsumowanie)
        self._build_adnotacje(fa, faktura.adnotacje)
        _sub(fa, "RodzajFaktury", text=faktura.rodzaj)
        for pozycja in faktura.wiersze:
            self._build_wiersz_fs(fa, pozycja)
        self._build_platnosc(fa, faktura.platnosc, with_rachunek=True)

        return _serialize(root)

    def build_korekta(self, korekta: Korekta) -> bytes:
        root = self._root()
        self._build_naglowek(root, korekta.naglowek)
        self._build_podmiot(root, korekta.podmiot1, tag="Podmiot1", with_jst_gv=False)
        self._build_podmiot(root, korekta.podmiot2, tag="Podmiot2", with_jst_gv=True)

        fa = _sub(root, "Fa")
        self._build_fa_header(
            fa, korekta.kod_waluty, korekta.data_wystawienia,
            korekta.numer_faktury, korekta.data_sprzedazy,
        )
        self._build_podsumowanie(fa, korekta.podsumowanie)
        self._build_adnotacje(fa, korekta.adnotacje)
        _sub(fa, "RodzajFaktury", text="KOR")
        if korekta.przyczyna_korekty:
            _sub(fa, "PrzyczynaKorekty", text=korekta.przyczyna_korekty)
        self._build_dane_fa_korygowanej(fa, korekta.dane_fa_korygowanej)
        self._build_wiersze_fsk(fa, korekta.stan_przed, korekta.stan_po)
        self._build_platnosc(fa, korekta.platnosc, with_rachunek=False)

        return _serialize(root)

    # ---- shared helpers --------------------------------------------------

    def _root(self) -> etree._Element:
        return etree.Element(f"{{{NS}}}Faktura", nsmap=_NSMAP)

    def _build_naglowek(self, parent: etree._Element, nag: Naglowek) -> None:
        el = _sub(parent, "Naglowek")
        _sub(el, "KodFormularza", text=nag.kod_formularza,
             attrib={"kodSystemowy": nag.kod_systemowy, "wersjaSchemy": nag.wersja_schemy})
        _sub(el, "WariantFormularza", text=nag.wariant_formularza)
        _sub(el, "DataWytworzeniaFa", text=self._clock().strftime("%Y-%m-%dT%H:%M:%S") + "Z")
        _sub(el, "SystemInfo", text=nag.system_info)

    def _build_podmiot(
        self, parent: etree._Element, p: Podmiot, *,
        tag: str, with_jst_gv: bool,
    ) -> None:
        el = _sub(parent, tag)
        di = _sub(el, "DaneIdentyfikacyjne")
        if p.nip is not None:
            _sub(di, "NIP", text=p.nip)
        _sub(di, "Nazwa", text=p.pelna_nazwa)
        adr = _sub(el, "Adres")
        _sub(adr, "KodKraju", text=p.kod_kraju)
        _sub(adr, "AdresL1", text=p.adres_l1)
        if p.adres_l2 is not None:
            _sub(adr, "AdresL2", text=p.adres_l2)
        if with_jst_gv:
            _sub(el, "JST", text="2")
            _sub(el, "GV", text="2")

    def _build_fa_header(
        self, fa: etree._Element, kod_waluty: str, data_wyst: date,
        numer: str, data_spr: date | None,
    ) -> None:
        _sub(fa, "KodWaluty", text=kod_waluty)
        _sub(fa, "P_1", text=_iso(data_wyst))
        _sub(fa, "P_2", text=numer)
        if data_spr is not None and data_spr != data_wyst:
            _sub(fa, "P_6", text=_iso(data_spr))

    def _build_podsumowanie(self, fa: etree._Element, p: PodsumowanieVat) -> None:
        pairs = [
            (p.vat_23_podstawa, p.vat_23_kwota, "P_13_1", "P_14_1"),
            (p.vat_8_podstawa, p.vat_8_kwota, "P_13_2", "P_14_2"),
            (p.vat_5_podstawa, p.vat_5_kwota, "P_13_3", "P_14_3"),
            (p.vat_0_podstawa, p.vat_0_kwota, "P_13_5", "P_14_5"),
        ]
        for netto, vat, netto_tag, vat_tag in pairs:
            if netto is not None:
                _sub(fa, netto_tag, text=self._format_decimal(netto))
                _sub(fa, vat_tag, text=self._format_decimal(vat))
        if p.zw_podstawa is not None:
            _sub(fa, "P_13_6", text=self._format_decimal(p.zw_podstawa))
        if p.np_podstawa is not None:
            _sub(fa, "P_13_7", text=self._format_decimal(p.np_podstawa))
        _sub(fa, "P_15", text=self._format_decimal(p.kwota_naleznosci))

    def _build_adnotacje(self, fa: etree._Element, a: Adnotacje) -> None:
        el = _sub(fa, "Adnotacje")
        _sub(el, "P_16", text=a.mpp)
        _sub(el, "P_17", text=a.p_17)
        _sub(el, "P_18", text=a.p_18)
        _sub(el, "P_18A", text=a.p_18a)
        zw = _sub(el, "Zwolnienie")
        _sub(zw, "P_19N", text=a.zwolnienie_p19n)
        nst = _sub(el, "NoweSrodkiTransportu")
        _sub(nst, "P_22N", text=a.nst_p22n)
        _sub(el, "P_23", text=a.p_23)
        pm = _sub(el, "PMarzy")
        _sub(pm, "P_PMarzyN", text=a.p_marzy_n)

    def _build_platnosc(
        self, fa: etree._Element, plat: Platnosc, *, with_rachunek: bool,
    ) -> None:
        el = _sub(fa, "Platnosc")
        if plat.zaplacono:
            _sub(el, "Zaplacono", text="1")
            if plat.data_zaplaty is not None:
                _sub(el, "DataZaplaty", text=_iso(plat.data_zaplaty))
        if plat.termin_platnosci is not None:
            termin_el = _sub(el, "TerminPlatnosci")
            _sub(termin_el, "Termin", text=_iso(plat.termin_platnosci))
        if plat.kod_formy_platnosci:
            _sub(el, "FormaPlatnosci", text=plat.kod_formy_platnosci)
        if with_rachunek and plat.nr_rachunku_bankowego:
            rb = _sub(el, "RachunekBankowy")
            _sub(rb, "NrRB", text=plat.nr_rachunku_bankowego)

    # ---- FS wiersze ------------------------------------------------------

    def _build_wiersz_fs(self, fa: etree._Element, pozycja: Pozycja) -> None:
        fw = _sub(fa, "FaWiersz")
        _sub(fw, "NrWierszaFa", text=str(pozycja.nr_pozycji))
        _sub(fw, "P_7", text=pozycja.nazwa_towaru)
        if pozycja.gtin:
            _sub(fw, "GTIN", text=pozycja.gtin)
        _sub(fw, "P_8A", text=pozycja.jednostka_miary)
        _sub(fw, "P_8B", text=self._format_ilosc(pozycja.ilosc))
        _sub(fw, "P_9A", text=self._format_decimal(pozycja.cena_netto_jedn))
        _sub(fw, "P_11", text=self._format_decimal(pozycja.wartosc_netto))
        _sub(fw, "P_12", text=pozycja.stawka_vat)

    # ---- FSK wiersze -----------------------------------------------------

    def _build_dane_fa_korygowanej(
        self, fa: etree._Element, d: DaneFaKorygowanej,
    ) -> None:
        el = _sub(fa, "DaneFaKorygowanej")
        _sub(el, "DataWystFaKorygowanej", text=_iso(d.data_wystawienia_org))
        _sub(el, "NrFaKorygowanej", text=d.numer_faktury_org)
        _sub(el, "NrKSeFN", text="1")

    def _build_wiersze_fsk(
        self, fa: etree._Element, stan_przed: StanPrzed, stan_po: StanPo,
    ) -> None:
        przed_by_pos = {w.nr_pozycji: w for w in stan_przed.wiersze}
        po_by_pos = {w.nr_pozycji: w for w in stan_po.wiersze}
        all_pos = sorted(set(przed_by_pos) | set(po_by_pos))
        for pos in all_pos:
            if pos in przed_by_pos:
                self._build_wiersz_fsk(fa, przed_by_pos[pos])
            if pos in po_by_pos:
                self._build_wiersz_fsk(fa, po_by_pos[pos])

    def _build_wiersz_fsk(self, fa: etree._Element, w: PozycjaKorekta) -> None:
        fw = _sub(fa, "FaWiersz")
        _sub(fw, "NrWierszaFa", text=str(w.nr_pozycji))
        if not w.stan_przed and w.data_korekty is not None:
            _sub(fw, "P_6A", text=_iso(w.data_korekty))
        _sub(fw, "P_7", text=w.nazwa_towaru)
        if w.indeks:
            _sub(fw, "Indeks", text=w.indeks)
        if w.gtin:
            _sub(fw, "GTIN", text=w.gtin)
        if w.pkwiu:
            _sub(fw, "PKWiU", text=w.pkwiu)
        _sub(fw, "P_8A", text=w.jednostka_miary)
        _sub(fw, "P_8B", text=self._format_ilosc(w.ilosc))
        _sub(fw, "P_9B", text=self._format_decimal(w.cena_brutto_jedn))
        _sub(fw, "P_11A", text=self._format_decimal(w.wartosc_netto))
        _sub(fw, "P_11Vat", text=self._format_decimal(w.kwota_vat))
        _sub(fw, "P_12", text=w.stawka_vat)
        if w.stan_przed:
            _sub(fw, "StanPrzed", text="1")

    # ---- formatters ------------------------------------------------------

    def _format_decimal(self, v: Decimal | None, places: int = 2) -> str | None:
        if v is None:
            return None
        q = Decimal(10) ** -places
        return str(v.quantize(q, rounding=ROUND_HALF_UP))

    def _format_ilosc(self, v: Decimal) -> str:
        s = str(v.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP))
        s = s.rstrip("0").rstrip(".")
        return s or "0"


# ---- module-level helpers ------------------------------------------------

def _sub(parent: etree._Element, tag: str, *, text: str | None = None,
         attrib: dict | None = None) -> etree._Element:
    el = etree.SubElement(parent, f"{{{NS}}}{tag}", attrib=attrib or {})
    if text is not None:
        el.text = text
    return el


def _iso(d) -> str:
    return d.isoformat() if hasattr(d, "isoformat") else str(d)


def _serialize(root: etree._Element) -> bytes:
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", pretty_print=True)
