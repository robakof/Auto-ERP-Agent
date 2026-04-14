"""Testy dla ksef_generate_kor.py — generator korekt KSeF."""

import sys
from pathlib import Path
from lxml import etree

# Dodaj root projektu do sys.path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "tools"))

from tools.ksef_generate_kor import (
    build_xml, build_sql, fmt_decimal, v, E, NS,
)


# ---------------------------------------------------------------------------
# Fixture: minimalny wiersz danych jak z SQL
# ---------------------------------------------------------------------------

def make_row(**overrides):
    """Zwróć słownik imitujący wiersz z ksef_fsk_draft.sql."""
    base = {
        # Podmiot1
        "P1_NIP": "7871003063",
        "P1_PelnaNazwa": "Firma Testowa Sp. z o.o.",
        "P1_KodKraju": "PL",
        "P1_AdresL1": "Testowa 1",
        "P1_AdresL2": "00-001 Warszawa",
        # Podmiot2
        "P2_NIP": "1234567890",
        "P2_PelnaNazwa": "Nabywca Test",
        "P2_KodKraju": "PL",
        "P2_AdresL1": "Kupiecka 5",
        "P2_AdresL2": "00-002 Kraków",
        # Fa nagłówek
        "Fa_KodWaluty": "PLN",
        "Fa_P1_DataWystawienia": "2026-04-10",
        "Fa_P2A_NumerFaktury": "FSK-1/04/26/SPKR",
        "Fa_P2_DataSprzedazy": "2026-04-10",
        "Fa_RodzajFaktury": "KOR",
        # Korekta — dane oryginalnej FS
        "Kor_DataWystFaKorygowanej": "2026-03-15",
        "Kor_NrFaKorygowanej": "FS-100/03/26/SPKR",
        "Kor_PrzyczynaKorekty": "Błędna ilość",
        # VAT
        "Fa_P13_1_Podstawa23": -100.00,
        "Fa_P14_1_VAT23": -23.00,
        "Fa_P13_2_Podstawa8": None,
        "Fa_P14_2_VAT8": None,
        "Fa_P13_3_Podstawa5": None,
        "Fa_P14_3_VAT5": None,
        "Fa_P13_5_Podstawa0": None,
        "Fa_P14_5_VAT0": None,
        "Fa_P13_6_PodstawaZW": None,
        "Fa_P13_7_PodstawaNP": None,
        "Fa_P15_KwotaNaleznosci": -123.00,
        # Adnotacje
        "Fa_P16_MPP": "2",
        # Wiersz — model StanPrzed/StanPo; test fixture = wiersz "przed"
        "Wiersz_NrPozycji": 1,
        "Wiersz_StanPrzed": 1,
        "Wiersz_DataKorekty": None,
        "Wiersz_P7_NazwaTowaru": "Znicz testowy",
        "Wiersz_Indeks": "ZNICZ-001",
        "Wiersz_PKWiU": None,
        "Wiersz_P8A_JM": "szt.",
        "Wiersz_P8B_Ilosc": 5.0,
        "Wiersz_P9B_CenaBrutto": 61.50,
        "Wiersz_P11A_WartoscNetto": 250.00,
        "Wiersz_P11Vat": 57.50,
        "Wiersz_P12_StawkaVAT": "23",
        "Wiersz_GTIN": None,
        # Płatność
        "Plat_TerminPlatnosci": "2026-04-24",
        "Plat_KodFormyPlatnosci": "6",
        "Plat_FormaPlatnosci_Nazwa": "Przelew",
        "Plat_NrRachunkuBankowego": "PL12345678901234567890123456",
        # Klucze techniczne
        "_GIDTyp": 2041,
        "_GIDNumer": 9000001,
        "_GIDFirma": 1,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Testy: helpers
# ---------------------------------------------------------------------------

class TestHelpers:
    def test_v_strips_whitespace(self):
        assert v({"x": "  abc  "}, "x") == "abc"

    def test_v_none_returns_none(self):
        assert v({"x": None}, "x") is None

    def test_v_missing_key_returns_none(self):
        assert v({}, "x") is None

    def test_fmt_decimal_positive(self):
        assert fmt_decimal(123.456) == "123.46"

    def test_fmt_decimal_negative(self):
        assert fmt_decimal(-100.0) == "-100.00"

    def test_fmt_decimal_none(self):
        assert fmt_decimal(None) is None

    def test_fmt_decimal_custom_places(self):
        assert fmt_decimal(1.23456, 4) == "1.2346"


# ---------------------------------------------------------------------------
# Testy: build_sql
# ---------------------------------------------------------------------------

class TestBuildSql:
    def test_base_sql_has_gidtyp_2041(self):
        sql = build_sql()
        assert "TrN_GIDTyp = 2041" in sql

    def test_gid_filter(self):
        sql = build_sql(gids=[9000001, 9000002])
        assert "n.TrN_GIDNumer IN (9000001, 9000002)" in sql

    def test_date_filter(self):
        sql = build_sql(date_from="2026-04-01", date_to="2026-04-14")
        assert "'2026-04-01'" in sql
        assert "'2026-04-14'" in sql

    def test_no_filter_returns_base(self):
        sql = build_sql()
        assert "TrN_GIDTyp = 2041" in sql
        assert "TrN_GIDNumer IN" not in sql

    def test_sql_has_orig_join(self):
        sql = build_sql()
        assert "orig.TrN_GIDNumer = n.TrN_ZwrNumer" in sql


# ---------------------------------------------------------------------------
# Testy: build_xml — struktura XML korekty
# ---------------------------------------------------------------------------

class TestBuildXml:
    def setup_method(self):
        self.rows = [make_row()]
        self.root = build_xml(self.rows)
        self.tree_str = etree.tostring(self.root, encoding="unicode")

    def _find(self, xpath):
        return self.root.findall(xpath, namespaces={"k": NS})

    def test_root_is_faktura(self):
        assert self.root.tag == f"{{{NS}}}Faktura"

    def test_naglowek_wariant_3(self):
        els = self._find(".//k:Naglowek/k:WariantFormularza")
        assert len(els) == 1
        assert els[0].text == "3"

    def test_naglowek_system_info(self):
        els = self._find(".//k:Naglowek/k:SystemInfo")
        assert len(els) == 1
        assert els[0].text == "Comarch ERP XL"

    def test_podmiot1_nip(self):
        els = self._find(".//k:Podmiot1/k:DaneIdentyfikacyjne/k:NIP")
        assert els[0].text == "7871003063"

    def test_podmiot2_nip(self):
        els = self._find(".//k:Podmiot2/k:DaneIdentyfikacyjne/k:NIP")
        assert els[0].text == "1234567890"

    def test_rodzaj_faktury_kor(self):
        els = self._find(".//k:Fa/k:RodzajFaktury")
        assert len(els) == 1
        assert els[0].text == "KOR"

    def test_przyczyna_korekty(self):
        els = self._find(".//k:Fa/k:PrzyczynaKorekty")
        assert len(els) == 1
        assert els[0].text == "Błędna ilość"

    def test_typ_korekty_omitted(self):
        """TypKorekty pomijane — model StanPrzed/StanPo nie wymaga."""
        els = self._find(".//k:Fa/k:TypKorekty")
        assert len(els) == 0

    def test_dane_fa_korygowanej_data(self):
        els = self._find(".//k:Fa/k:DaneFaKorygowanej/k:DataWystFaKorygowanej")
        assert len(els) == 1
        assert els[0].text == "2026-03-15"

    def test_dane_fa_korygowanej_numer(self):
        els = self._find(".//k:Fa/k:DaneFaKorygowanej/k:NrFaKorygowanej")
        assert len(els) == 1
        assert els[0].text == "FS-100/03/26/SPKR"

    def test_dane_fa_korygowanej_nr_ksef_n(self):
        """Oryginały poza KSeF — znacznik NrKSeFN=1."""
        els = self._find(".//k:Fa/k:DaneFaKorygowanej/k:NrKSeFN")
        assert len(els) == 1
        assert els[0].text == "1"

    def test_p15_kwota_ujemna(self):
        els = self._find(".//k:Fa/k:P_15")
        assert els[0].text == "-123.00"

    def test_vat_23_ujemny(self):
        els = self._find(".//k:Fa/k:P_13_1")
        assert els[0].text == "-100.00"
        els = self._find(".//k:Fa/k:P_14_1")
        assert els[0].text == "-23.00"

    def test_wiersz_nazwa(self):
        els = self._find(".//k:Fa/k:FaWiersz/k:P_7")
        assert len(els) == 1
        assert els[0].text == "Znicz testowy"

    def test_wiersz_ilosc(self):
        els = self._find(".//k:Fa/k:FaWiersz/k:P_8B")
        assert els[0].text == "5"

    def test_wiersz_stan_przed(self):
        els = self._find(".//k:Fa/k:FaWiersz/k:StanPrzed")
        assert len(els) == 1
        assert els[0].text == "1"

    def test_wiersz_p11a_p11vat(self):
        els = self._find(".//k:Fa/k:FaWiersz/k:P_11A")
        assert els[0].text == "250.00"
        els = self._find(".//k:Fa/k:FaWiersz/k:P_11Vat")
        assert els[0].text == "57.50"

    def test_wiersz_p9b_brutto(self):
        els = self._find(".//k:Fa/k:FaWiersz/k:P_9B")
        assert els[0].text == "61.50"

    def test_wiersz_indeks(self):
        els = self._find(".//k:Fa/k:FaWiersz/k:Indeks")
        assert len(els) == 1
        assert els[0].text == "ZNICZ-001"

    def test_platnosc_no_rachunek(self):
        """Korekta = zwrot, nie emitujemy numeru rachunku bankowego."""
        els = self._find(".//k:Fa/k:Platnosc/k:RachunekBankowy")
        assert len(els) == 0

    def test_adnotacje_present(self):
        els = self._find(".//k:Fa/k:Adnotacje/k:P_16")
        assert len(els) == 1


class TestBuildXmlMultipleRows:
    """Korekta z wieloma pozycjami."""

    def test_multiple_wiersze(self):
        rows = [
            make_row(Wiersz_NrPozycji=1, Wiersz_P7_NazwaTowaru="Produkt A"),
            make_row(Wiersz_NrPozycji=2, Wiersz_P7_NazwaTowaru="Produkt B"),
        ]
        root = build_xml(rows)
        wiersze = root.findall(f".//{{{NS}}}FaWiersz")
        assert len(wiersze) == 2
        names = [w.find(f"{{{NS}}}P_7").text for w in wiersze]
        assert names == ["Produkt A", "Produkt B"]


class TestStanPrzedStanPo:
    """Para wierszy StanPrzed=1 + StanPrzed=0 (z P_6A) per pozycja."""

    def test_stan_przed_before_stan_po(self):
        rows = [
            make_row(
                Wiersz_NrPozycji=1, Wiersz_StanPrzed=0,
                Wiersz_DataKorekty="2026-04-14",
                Wiersz_P8B_Ilosc=3.0, Wiersz_P11A_WartoscNetto=150.00,
                Wiersz_P11Vat=34.50,
            ),
            make_row(
                Wiersz_NrPozycji=1, Wiersz_StanPrzed=1,
                Wiersz_P8B_Ilosc=5.0, Wiersz_P11A_WartoscNetto=250.00,
                Wiersz_P11Vat=57.50,
            ),
        ]
        root = build_xml(rows)
        wiersze = root.findall(f".//{{{NS}}}FaWiersz")
        assert len(wiersze) == 2

        # Kolejność: StanPrzed=1 najpierw, potem StanPo
        stan1 = wiersze[0].find(f"{{{NS}}}StanPrzed")
        assert stan1 is not None and stan1.text == "1"
        assert wiersze[0].find(f"{{{NS}}}P_6A") is None

        # Drugi: bez StanPrzed, z P_6A
        assert wiersze[1].find(f"{{{NS}}}StanPrzed") is None
        p6a = wiersze[1].find(f"{{{NS}}}P_6A")
        assert p6a is not None and p6a.text == "2026-04-14"


class TestBuildXmlEdgeCases:
    def test_no_przyczyna_korekty(self):
        """Puste TrN_NrKorekty — PrzyczynaKorekty pomijana."""
        rows = [make_row(Kor_PrzyczynaKorekty=None)]
        root = build_xml(rows)
        els = root.findall(f".//{{{NS}}}PrzyczynaKorekty")
        assert len(els) == 0

    def test_data_sprzedazy_same_as_wystawienia(self):
        """P_6 pomijane gdy data sprzedaży = data wystawienia."""
        rows = [make_row(
            Fa_P1_DataWystawienia="2026-04-10",
            Fa_P2_DataSprzedazy="2026-04-10",
        )]
        root = build_xml(rows)
        els = root.findall(f".//{{{NS}}}Fa/{{{NS}}}P_6")
        assert len(els) == 0

    def test_data_sprzedazy_different(self):
        """P_6 obecne gdy data sprzedaży ≠ data wystawienia."""
        rows = [make_row(
            Fa_P1_DataWystawienia="2026-04-10",
            Fa_P2_DataSprzedazy="2026-03-31",
        )]
        root = build_xml(rows)
        els = root.findall(f".//{{{NS}}}Fa/{{{NS}}}P_6")
        assert len(els) == 1
        assert els[0].text == "2026-03-31"

    def test_gtin_included_when_present(self):
        rows = [make_row(Wiersz_GTIN="5901234123457")]
        root = build_xml(rows)
        els = root.findall(f".//{{{NS}}}FaWiersz/{{{NS}}}GTIN")
        assert len(els) == 1
        assert els[0].text == "5901234123457"

    def test_gtin_omitted_when_none(self):
        rows = [make_row(Wiersz_GTIN=None)]
        root = build_xml(rows)
        els = root.findall(f".//{{{NS}}}FaWiersz/{{{NS}}}GTIN")
        assert len(els) == 0

    def test_platnosc_no_rachunek_for_cash(self):
        """Gotówka — brak NrRB."""
        rows = [make_row(
            Plat_KodFormyPlatnosci="1",
            Plat_NrRachunkuBankowego=None,
        )]
        root = build_xml(rows)
        els = root.findall(f".//{{{NS}}}RachunekBankowy")
        assert len(els) == 0
