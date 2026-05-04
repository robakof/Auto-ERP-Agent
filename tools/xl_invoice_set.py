"""Import faktury zakupowej FZ do Comarch XL przez XL API.

Wejście: FzInvoice (z xl_invoice_parser.py)
Wyjście: dict {ok, data: {doc_id, nr_obcy, action, avista}, error, meta}

Obsługiwane: FZ kosztowa surowcowa (seria ZSKR), waluta PLN.
action: "inserted" | "skipped" (duplikat po nr_obcy).
avista: lista nazw pozycji niezmapowanych na kartotekę towaru.
"""

from __future__ import annotations

import csv
import sys
import time
from datetime import date
from os import environ
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.lib.sql_client import SqlClient
from tools.lib.xl_client import XlClient
from tools.xl_invoice_parser import FzInvoice

_EPOCH_OFFSET = 657433  # date(1800, 12, 28).toordinal()
_KNT_TYP      = 32
_DOC_TYP      = 1       # FZ
_SERIA        = "ZSKR"  # kosztowa surowcowa
_RODZAJ_ZAKUPU = 1

_MAGAZYN_CSV = Path(__file__).parent.parent / "config" / "fz_magazyn.csv"

# Mapowanie stawki VAT z KSeF P_12 na symbol grupy VAT w Comarch XL
_VAT_GROUP: dict[str, str] = {
    "23": "A",
    "8":  "B",
    "5":  "C",
    "0":  "D",
    "zw": "E",
    "ZW": "E",
    "np": "F",
    "NP": "F",
}


def _vat_group(stawka: str) -> str:
    return _VAT_GROUP.get(stawka.strip(), stawka)


def _resolve_magazyn(nip: str) -> str:
    """Zwraca magazyn dla danego NIP dostawcy.

    Szuka NIP w config/fz_magazyn.csv. Fallback: FZ_MAGAZYN_DEFAULT z .env.
    """
    default = environ.get("FZ_MAGAZYN_DEFAULT", "OTO_SUR")
    if _MAGAZYN_CSV.exists():
        with _MAGAZYN_CSV.open(newline="", encoding="utf-8-sig", errors="replace") as f:
            for row in csv.DictReader(f, delimiter=";"):
                if row.get("nip", "").strip() == nip:
                    return row.get("magazyn", "").strip() or default
    return default


_NIP_SQL = """
    SELECT Knt_GIDNumer, Knt_GIDFirma
    FROM CDN.KntKarty
    WHERE Knt_NIP = ?
"""

_EXISTS_SQL = """
    SELECT COUNT(*)
    FROM CDN.TraNag
    WHERE TrN_DokumentObcy = ? AND RTRIM(TrN_TrNSeria) = ?
"""

# GUI Comarch XL zapisuje "Dodatkowy kod" dostawcy w CDN.TwrDost.TWD_KodDodatkowyKnt
_TOWAR_SQL = """
    SELECT TOP 1 tw.Twr_Kod
    FROM CDN.TwrDost d
    JOIN CDN.TwrKarty tw ON d.TWD_TwrNumer = tw.Twr_GIDNumer
                        AND d.TWD_TwrFirma = tw.Twr_GIDFirma
    WHERE d.TWD_KntNumer = ?
      AND UPPER(LTRIM(RTRIM(d.TWD_KodDodatkowyKnt))) = UPPER(LTRIM(RTRIM(?)))
      AND d.TWD_KodDodatkowyKnt <> ''
"""

# fallback bez filtra kontrahenta (gdy wpis jest przypisany do innego Knt)
_TOWAR_SQL_FALLBACK = """
    SELECT TOP 1 tw.Twr_Kod
    FROM CDN.TwrDost d
    JOIN CDN.TwrKarty tw ON d.TWD_TwrNumer = tw.Twr_GIDNumer
                        AND d.TWD_TwrFirma = tw.Twr_GIDFirma
    WHERE UPPER(LTRIM(RTRIM(d.TWD_KodDodatkowyKnt))) = UPPER(LTRIM(RTRIM(?)))
      AND d.TWD_KodDodatkowyKnt <> ''
"""


def _to_epoch(d: date) -> int:
    return d.toordinal() - _EPOCH_OFFSET


def _err(err_type: str, msg: str, start: float) -> dict:
    return {
        "ok": False, "data": None,
        "error": {"type": err_type, "message": msg},
        "meta": {"duration_ms": round((time.monotonic() - start) * 1000)},
    }


def _resolve_towar_kod(cursor, knt_numer: int, nazwa: str) -> str | None:
    """Zwraca Twr_Kod z CDN.TwrDost (TWD_KodDodatkowyKnt).

    Najpierw z filtrem kontrahenta, fallback bez filtra gdy wpis przypisany do innego Knt.
    """
    cursor.execute(_TOWAR_SQL, [knt_numer, nazwa])
    row = cursor.fetchone()
    if row:
        return str(row[0])
    cursor.execute(_TOWAR_SQL_FALLBACK, [nazwa])
    row = cursor.fetchone()
    return str(row[0]) if row else None


def set_invoice(invoice: FzInvoice) -> dict:
    """Importuje fakturę zakupową FZ do Comarch XL przez XL API."""
    start = time.monotonic()

    if invoice.waluta != "PLN":
        return _err("UNSUPPORTED_CURRENCY",
                    f"Tylko PLN obsługiwane — faza 2: {invoice.waluta}", start)

    try:
        conn = SqlClient().get_connection()
        cursor = conn.cursor()

        cursor.execute(_NIP_SQL, [invoice.nip_sprzedawcy])
        row = cursor.fetchone()
        if not row:
            return _err("CONTRACTOR_NOT_FOUND",
                        f"Kontrahent NIP={invoice.nip_sprzedawcy} nie istnieje w kartotece",
                        start)
        knt_numer, knt_firma = int(row[0]), int(row[1])
        magazyn = _resolve_magazyn(invoice.nip_sprzedawcy)

        cursor.execute(_EXISTS_SQL, [invoice.nr_obcy, _SERIA])
        if cursor.fetchone()[0] > 0:
            return {
                "ok": True,
                "data": {"nr_obcy": invoice.nr_obcy, "action": "skipped", "avista": []},
                "error": None,
                "meta": {"duration_ms": round((time.monotonic() - start) * 1000)},
            }

    except Exception as exc:
        return _err("SQL_ERROR", str(exc), start)

    client = XlClient()
    try:
        data_epoch = _to_epoch(invoice.data_wystawienia)
        resp = client.invoke(
            "XLNowyDokument",
            Typ=_DOC_TYP,
            Seria=_SERIA,
            RodzajZakupu=_RODZAJ_ZAKUPU,
            Data=data_epoch,
            DataSpr=data_epoch,
            DataVat=data_epoch,
            DataMag=data_epoch,
            Termin=_to_epoch(invoice.termin_platnosci),
            KntTyp=_KNT_TYP,
            KntFirma=knt_firma,
            KntNumer=knt_numer,
            DokumentObcy=invoice.nr_obcy,
        )
        if not resp.get("ok"):
            return _err("XL_API_ERROR",
                        f"XLNowyDokument: {resp.get('error', {}).get('message', resp)}", start)
        doc_id = int(resp.get("data", {}).get("_lDokumentID", 0))

        resp = client.invoke(
            "XLModyfikujNaglowek",
            _lDokumentID=doc_id,
            MagazynD=magazyn,
            DataMag=data_epoch,
        )
        if not resp.get("ok"):
            return _err("XL_API_ERROR",
                        f"XLModyfikujNaglowek: {resp.get('error', {}).get('message', resp)}", start)

        avista = []
        for poz in invoice.pozycje:
            towar_kod = _resolve_towar_kod(cursor, knt_numer, poz.nazwa)
            poz_params = {
                "_lDokumentID": doc_id,
                "Ilosc":        str(poz.ilosc),
                "Cena":         str(poz.cena_netto),
                "Vat":          _vat_group(poz.stawka_vat),
                "JmZ":          poz.jm,
                "Magazyn":      magazyn,
            }
            if towar_kod:
                poz_params["TowarKod"] = towar_kod
            else:
                poz_params["TowarNazwa"] = poz.nazwa
                avista.append(poz.nazwa)

            resp = client.invoke("XLDodajPozycje", **poz_params)
            if not resp.get("ok"):
                return _err("XL_API_ERROR",
                            f"XLDodajPozycje [{poz.nr}]: {resp.get('error', {}).get('message', resp)}",
                            start)

        resp = client.zamknij_dokument(lDokumentID=doc_id, Tryb=1)
        if not resp.get("ok"):
            api_msg = resp.get("error", {}).get("message", str(resp))
            blad = client.opis_bledu()
            opis = blad.get("opis", "")
            detail = f" | ERP: {opis}" if opis else ""
            return _err("XL_API_ERROR",
                        f"XLZamknijDokument: {api_msg}{detail}", start)

    except Exception as exc:
        return _err("XL_API_ERROR", str(exc), start)

    return {
        "ok": True,
        "data": {"doc_id": doc_id, "nr_obcy": invoice.nr_obcy, "action": "inserted",
                 "avista": avista},
        "error": None,
        "meta": {"duration_ms": round((time.monotonic() - start) * 1000)},
    }
