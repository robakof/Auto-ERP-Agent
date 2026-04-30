"""Testy parsera KSeF XML → FzInvoice."""

import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.xl_invoice_parser import FzInvoice, FzPozycja, parse_ksef_xml

_SAMPLE_VAT = Path(__file__).parent / "fixtures" / "sample_vat.xml"
_SAMPLE_KOR = Path(__file__).parent / "fixtures" / "sample_kor.xml"
_FIXTURES = Path(__file__).parent / "fixtures"


def _make_vat_xml(
    nr="FV/1/2026",
    nip="1234567890",
    nazwa="Dostawca Sp. z o.o.",
    data="2026-04-01",
    termin="2026-04-15",
    waluta="PLN",
    p13_1="100.00",
    p14_1="23.00",
    p15="123.00",
    wiersze=None,
) -> str:
    if wiersze is None:
        wiersze = """<FaWiersz>
          <NrWierszaFa>1</NrWierszaFa>
          <P_7>Surowiec A</P_7>
          <P_8A>szt</P_8A>
          <P_8B>10</P_8B>
          <P_9B>10.00</P_9B>
          <P_11A>100.00</P_11A>
          <P_11Vat>23.00</P_11Vat>
          <P_12>23</P_12>
        </FaWiersz>"""
    ns = "http://crd.gov.pl/wzor/2025/06/25/13775/"
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Faktura xmlns="{ns}">
  <Podmiot1>
    <DaneIdentyfikacyjne>
      <NIP>{nip}</NIP>
      <Nazwa>{nazwa}</Nazwa>
    </DaneIdentyfikacyjne>
  </Podmiot1>
  <Podmiot2>
    <DaneIdentyfikacyjne>
      <NIP>7871003063</NIP>
      <Nazwa>CEIM</Nazwa>
    </DaneIdentyfikacyjne>
  </Podmiot2>
  <Fa>
    <KodWaluty>{waluta}</KodWaluty>
    <P_1>{data}</P_1>
    <P_2>{nr}</P_2>
    <P_13_1>{p13_1}</P_13_1>
    <P_14_1>{p14_1}</P_14_1>
    <P_15>{p15}</P_15>
    <RodzajFaktury>VAT</RodzajFaktury>
    {wiersze}
    <Platnosc>
      <TerminPlatnosci>
        <Termin>{termin}</Termin>
      </TerminPlatnosci>
    </Platnosc>
  </Fa>
</Faktura>"""


def _write_fixture(name: str, content: str) -> Path:
    _FIXTURES.mkdir(parents=True, exist_ok=True)
    p = _FIXTURES / name
    p.write_text(content, encoding="utf-8")
    return p


def test_parse_vat_basic():
    path = _write_fixture("vat_basic.xml", _make_vat_xml())
    result = parse_ksef_xml(path)
    assert result["ok"], result["error"]
    inv: FzInvoice = result["data"]
    assert inv.nr_obcy == "FV/1/2026"
    assert inv.nip_sprzedawcy == "1234567890"
    assert inv.nazwa_sprzedawcy == "Dostawca Sp. z o.o."
    assert inv.data_wystawienia == date(2026, 4, 1)
    assert inv.termin_platnosci == date(2026, 4, 15)
    assert inv.waluta == "PLN"
    assert inv.suma_netto == Decimal("100.00")
    assert inv.suma_vat == Decimal("23.00")
    assert inv.suma_brutto == Decimal("123.00")


def test_parse_vat_pozycje():
    path = _write_fixture("vat_basic.xml", _make_vat_xml())
    result = parse_ksef_xml(path)
    inv: FzInvoice = result["data"]
    assert len(inv.pozycje) == 1
    poz: FzPozycja = inv.pozycje[0]
    assert poz.nr == 1
    assert poz.nazwa == "Surowiec A"
    assert poz.ilosc == Decimal("10")
    assert poz.jm == "szt"
    assert poz.cena_netto == Decimal("10.00")
    assert poz.wartosc_netto == Decimal("100.00")
    assert poz.stawka_vat == "23"
    assert poz.wartosc_vat == Decimal("23.00")


def test_parse_kor_rejected():
    ns = "http://crd.gov.pl/wzor/2025/06/25/13775/"
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Faktura xmlns="{ns}">
  <Podmiot1><DaneIdentyfikacyjne><NIP>123</NIP><Nazwa>X</Nazwa></DaneIdentyfikacyjne></Podmiot1>
  <Fa><KodWaluty>PLN</KodWaluty><P_1>2026-04-01</P_1><P_2>KOR/1</P_2>
  <P_15>0</P_15><RodzajFaktury>KOR</RodzajFaktury></Fa>
</Faktura>"""
    path = _write_fixture("kor.xml", xml)
    result = parse_ksef_xml(path)
    assert not result["ok"]
    assert "KOR" in result["error"]


def test_parse_stanprzed_skipped():
    wiersze = """
    <FaWiersz>
      <NrWierszaFa>1</NrWierszaFa>
      <P_7>Towar stary</P_7><P_8A>szt</P_8A><P_8B>5</P_8B>
      <P_9B>10.00</P_9B><P_11A>50.00</P_11A><P_11Vat>11.50</P_11Vat>
      <P_12>23</P_12><StanPrzed>1</StanPrzed>
    </FaWiersz>
    <FaWiersz>
      <NrWierszaFa>1</NrWierszaFa>
      <P_7>Towar nowy</P_7><P_8A>szt</P_8A><P_8B>3</P_8B>
      <P_9B>10.00</P_9B><P_11A>30.00</P_11A><P_11Vat>6.90</P_11Vat>
      <P_12>23</P_12>
    </FaWiersz>"""
    path = _write_fixture("stanprzed.xml", _make_vat_xml(wiersze=wiersze, p13_1="30.00", p14_1="6.90", p15="36.90"))
    result = parse_ksef_xml(path)
    assert result["ok"]
    assert len(result["data"].pozycje) == 1
    assert result["data"].pozycje[0].nazwa == "Towar nowy"


def test_parse_missing_fa():
    ns = "http://crd.gov.pl/wzor/2025/06/25/13775/"
    xml = f'<?xml version="1.0"?><Faktura xmlns="{ns}"><Podmiot1/></Faktura>'
    path = _write_fixture("no_fa.xml", xml)
    result = parse_ksef_xml(path)
    assert not result["ok"]
    assert "Fa" in result["error"]


def test_parse_invalid_xml():
    path = _write_fixture("broken.xml", "<<NOT XML>>")
    result = parse_ksef_xml(path)
    assert not result["ok"]
    assert "parse error" in result["error"].lower()


if __name__ == "__main__":
    tests = [
        test_parse_vat_basic,
        test_parse_vat_pozycje,
        test_parse_kor_rejected,
        test_parse_stanprzed_skipped,
        test_parse_missing_fa,
        test_parse_invalid_xml,
    ]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"  FAIL  {t.__name__}: {e}")
    print(f"\n{passed}/{len(tests)} passed")
