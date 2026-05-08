"""Import faktury kosztowej FKo do Comarch XL przez XL API.

Wejście: FzInvoice (z xl_invoice_parser.py)
Wyjście: dict {ok, data: {doc_id, nr_obcy, action, avista}, error, meta}

Obsługiwane: FKo kosztowa krajowa (seria ZKKR), waluta PLN.
action: "inserted" | "skipped" (duplikat po nr_obcy).
avista: lista nazw pozycji niezmapowanych na kartotekę towaru.
"""

from __future__ import annotations

import sys
import time
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.lib.sql_client import SqlClient
from tools.lib.xl_client import XlClient
from tools.xl_invoice_parser import FzInvoice

_EPOCH_OFFSET  = 657433  # date(1800, 12, 28).toordinal()
_KNT_TYP       = 32
_DOC_TYP       = 1       # FZ (TraNag GIDTyp=1521)
_SERIA         = "ZKKR"  # Zakup Kosztowy Kraj
_RODZAJ_ZAKUPU = 2       # koszty (1=towary, 2=koszty, 3=środki trwałe)

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

_VAT_KEYS: dict[str, tuple[int, int]] = {
    "23": (23, 1),
    "8":  (8,  1),
    "5":  (5,  1),
    "0":  (0,  1),
    "zw": (0,  0),
    "ZW": (0,  0),
    "np": (0,  2),
    "NP": (0,  2),
}


def _vat_group(stawka: str) -> str:
    return _VAT_GROUP.get(stawka.strip(), stawka)


def _vat_key(stawka: str) -> tuple[int, int]:
    return _VAT_KEYS.get(stawka.strip(), (0, 1))


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

_TOWAR_SQL = """
    SELECT TOP 1 tw.Twr_Kod
    FROM CDN.TwrDost d
    JOIN CDN.TwrKarty tw ON d.TWD_TwrNumer = tw.Twr_GIDNumer
                        AND d.TWD_TwrFirma = tw.Twr_GIDFirma
    WHERE d.TWD_KntNumer = ?
      AND UPPER(LTRIM(RTRIM(d.TWD_KodDodatkowyKnt))) = UPPER(LTRIM(RTRIM(?)))
      AND d.TWD_KodDodatkowyKnt <> ''
"""

_TOWAR_SQL_FALLBACK_KOD = """
    SELECT TOP 1 tw.Twr_Kod
    FROM CDN.TwrDost d
    JOIN CDN.TwrKarty tw ON d.TWD_TwrNumer = tw.Twr_GIDNumer
                        AND d.TWD_TwrFirma = tw.Twr_GIDFirma
    WHERE UPPER(LTRIM(RTRIM(d.TWD_KodDodatkowyKnt))) = UPPER(LTRIM(RTRIM(?)))
      AND d.TWD_KodDodatkowyKnt <> ''
"""

_TOWAR_SQL_NAZWA = """
    SELECT TOP 1 tw.Twr_Kod
    FROM CDN.TwrDost d
    JOIN CDN.TwrKarty tw ON d.TWD_TwrNumer = tw.Twr_GIDNumer
                        AND d.TWD_TwrFirma = tw.Twr_GIDFirma
    WHERE d.TWD_KntNumer = ?
      AND UPPER(LTRIM(RTRIM(d.TWD_NazwaKnt))) = UPPER(LTRIM(RTRIM(?)))
      AND d.TWD_NazwaKnt <> ''
"""

_TOWAR_SQL_NAZWA_FALLBACK = """
    SELECT TOP 1 tw.Twr_Kod
    FROM CDN.TwrDost d
    JOIN CDN.TwrKarty tw ON d.TWD_TwrNumer = tw.Twr_GIDNumer
                        AND d.TWD_TwrFirma = tw.Twr_GIDFirma
    WHERE UPPER(LTRIM(RTRIM(d.TWD_NazwaKnt))) = UPPER(LTRIM(RTRIM(?)))
      AND d.TWD_NazwaKnt <> ''
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
    for sql, params in [
        (_TOWAR_SQL,                [knt_numer, nazwa]),
        (_TOWAR_SQL_FALLBACK_KOD,   [nazwa]),
        (_TOWAR_SQL_NAZWA,          [knt_numer, nazwa]),
        (_TOWAR_SQL_NAZWA_FALLBACK, [nazwa]),
    ]:
        cursor.execute(sql, params)
        row = cursor.fetchone()
        if row:
            return str(row[0])
    return None


def set_invoice(invoice: FzInvoice) -> dict:
    """Importuje fakturę kosztową FKo do Comarch XL przez XL API."""
    start = time.monotonic()

    if invoice.waluta != "PLN":
        return _err("UNSUPPORTED_CURRENCY",
                    f"Tylko PLN obsługiwane: {invoice.waluta}", start)

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

        avista = []
        for poz in invoice.pozycje:
            towar_kod = _resolve_towar_kod(cursor, knt_numer, poz.nazwa)
            stawka_int, flaga_int = _vat_key(poz.stawka_vat)
            poz_params = {
                "_lDokumentID": doc_id,
                "Ilosc":        str(poz.ilosc).replace(".", ","),
                "Cena":         str(poz.cena_netto).replace(".", ","),
                "NiePrzeliczaj": 1,
                "Vat":          _vat_group(poz.stawka_vat),
                "StawkaPod":    stawka_int * 100,
                "FlagaVAT":     flaga_int,
                "JmZ":          poz.jm,
            }
            if towar_kod:
                poz_params["TowarKod"] = towar_kod
            else:
                poz_params["TowarNazwa"] = poz.nazwa
                avista.append(poz.nazwa)

            resp = client.invoke("XLDodajPozycje", **poz_params)
            if not resp.get("ok"):
                client.zamknij_dokument(lDokumentID=doc_id, Tryb=0)
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
