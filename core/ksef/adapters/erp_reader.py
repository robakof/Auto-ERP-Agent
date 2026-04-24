"""Reader ERP XL — SQL → Faktura | Korekta.

run_query wstrzykiwane (DI) — adapter nie importuje tools/sql_query bezposrednio.
Kontrakt callable: (sql: str) -> {'ok': bool, 'data': {'columns', 'rows'}, 'error': ...}

Row mapping w jednym miejscu (_row_to_*) — boundary validation.
Decimal z SQL → Decimal w domain (nie float).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from itertools import groupby
from operator import itemgetter
from pathlib import Path
from typing import Callable

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
from core.ksef.exceptions import KSefError

_BASE = Path(__file__).resolve().parents[3]
SQL_PATH_FS = _BASE / "solutions" / "ksef" / "ksef_fs_draft.sql"
SQL_PATH_FSK = _BASE / "solutions" / "ksef" / "ksef_fsk_draft.sql"
SQL_PATH_FSK_SKONTO = _BASE / "solutions" / "ksef" / "ksef_fsk_skonto_draft.sql"

_WHERE_FS = "WHERE n.TrN_GIDTyp = 2033"
_WHERE_FSK = "WHERE n.TrN_GIDTyp = 2041"


def build_sql_fs(
    *, gids: list[int] | None = None,
    date_from: date | str | None = None,
    date_to: date | str | None = None,
) -> str:
    """Publiczny helper dla --dry-run (bez run_query)."""
    return ErpReader._build_sql(SQL_PATH_FS, _WHERE_FS, _Filters(gids, date_from, date_to))


def build_sql_fsk(
    *, gids: list[int] | None = None,
    date_from: date | str | None = None,
    date_to: date | str | None = None,
) -> str:
    return ErpReader._build_sql(SQL_PATH_FSK, _WHERE_FSK, _Filters(gids, date_from, date_to))

RunQuery = Callable[[str], dict]


class ErpReaderError(KSefError):
    """SQL zwrocil blad lub struktura odpowiedzi jest niezgodna z kontraktem."""


@dataclass(frozen=True)
class _Filters:
    gids: list[int] | None = None
    date_from: date | str | None = None
    date_to: date | str | None = None


class ErpReader:
    """SQL views -> domain. Jedyne miejsce row→domain mapowania."""

    def __init__(self, run_query: RunQuery) -> None:
        self._run_query = run_query

    # ---- public ----------------------------------------------------------

    def fetch_faktury(
        self, *, gids: list[int] | None = None,
        date_from: date | str | None = None,
        date_to: date | str | None = None,
    ) -> list[Faktura]:
        rows = self._execute(SQL_PATH_FS, _WHERE_FS, _Filters(gids, date_from, date_to))
        if not rows:
            return []
        rows.sort(key=itemgetter("_GIDNumer"))
        return [self._rows_to_faktura(list(g)) for _, g in groupby(rows, key=itemgetter("_GIDNumer"))]

    def fetch_korekty(
        self, *, gids: list[int] | None = None,
        date_from: date | str | None = None,
        date_to: date | str | None = None,
    ) -> list[Korekta]:
        rows = self._execute(SQL_PATH_FSK, _WHERE_FSK, _Filters(gids, date_from, date_to))
        if not rows:
            return []
        rows.sort(key=itemgetter("_GIDNumer"))
        return [self._rows_to_korekta(list(g)) for _, g in groupby(rows, key=itemgetter("_GIDNumer"))]

    def fetch_korekty_skonto(
        self, *, gids: list[int] | None = None,
        date_from: date | str | None = None,
        date_to: date | str | None = None,
    ) -> list[Korekta]:
        """Korekty skontowe (rabat wartosciowy, brak TraElem, ZwrNumer=0).

        Pozycje pobierane z bufora 2009, oryginalna FS przez lancuch bufor->FS.
        Reuse _rows_to_korekta — SQL zwraca identyczna strukture kolumn.
        """
        rows = self._execute(SQL_PATH_FSK_SKONTO, _WHERE_FSK, _Filters(gids, date_from, date_to))
        if not rows:
            return []
        rows.sort(key=itemgetter("_GIDNumer"))
        return [self._rows_to_korekta(list(g)) for _, g in groupby(rows, key=itemgetter("_GIDNumer"))]

    # ---- SQL execution ---------------------------------------------------

    def _execute(self, sql_path: Path, where_marker: str, f: _Filters) -> list[dict]:
        sql = self._build_sql(sql_path, where_marker, f)
        res = self._run_query(sql)
        if not res.get("ok"):
            err = res.get("error", {})
            raise ErpReaderError(f"SQL error: {err.get('message', err)}")
        data = res["data"]
        cols = data["columns"]
        return [dict(zip(cols, row, strict=True)) for row in data["rows"]]

    @staticmethod
    def _build_sql(sql_path: Path, where_marker: str, f: _Filters) -> str:
        base = sql_path.read_text(encoding="utf-8")
        conditions: list[str] = []
        if f.gids:
            id_list = ", ".join(str(int(g)) for g in f.gids)
            conditions.append(f"n.TrN_GIDNumer IN ({id_list})")
        if f.date_from:
            conditions.append(
                f"DATEADD(day, n.TrN_Data2, '1800-12-28') >= '{f.date_from}'"
            )
        if f.date_to:
            conditions.append(
                f"DATEADD(day, n.TrN_Data2, '1800-12-28') <= '{f.date_to}'"
            )
        if not conditions:
            return base
        extra = " AND " + " AND ".join(conditions)
        return base.replace(where_marker, where_marker + extra)

    # ---- FS mapping ------------------------------------------------------

    def _rows_to_faktura(self, rows: list[dict]) -> Faktura:
        r = rows[0]
        wiersze = tuple(self._row_to_pozycja(row) for row in rows)
        data_wyst = _as_date(r["Fa_P1_DataWystawienia"])
        data_spr = _as_date(r.get("Fa_P2_DataSprzedazy"))
        return Faktura(
            gid_numer=int(r["_GIDNumer"]),
            naglowek=Naglowek(),
            podmiot1=self._row_to_podmiot1(r),
            podmiot2=self._row_to_podmiot2(r),
            kod_waluty=str(r["Fa_KodWaluty"]).strip(),
            data_wystawienia=data_wyst,
            data_sprzedazy=data_spr if data_spr != data_wyst else None,
            numer_faktury=str(r["Fa_P2A_NumerFaktury"]).strip(),
            podsumowanie=self._rows_to_podsumowanie(r),
            adnotacje=Adnotacje(mpp=_as_str(r.get("Fa_P16_MPP")) or "2"),
            rodzaj=_as_str(r.get("Fa_RodzajFaktury")) or "VAT",
            wiersze=wiersze,
            platnosc=self._row_to_platnosc(r),
        )

    def _row_to_pozycja(self, row: dict) -> Pozycja:
        return Pozycja(
            nr_pozycji=int(row["Wiersz_NrPozycji"]),
            nazwa_towaru=_as_str(row["Wiersz_P7_NazwaTowaru"]) or "",
            gtin=_as_str(row.get("Wiersz_GTIN")),
            jednostka_miary=_as_str(row["Wiersz_P8A_JM"]) or "",
            ilosc=_as_decimal(row["Wiersz_P8B_Ilosc"]),
            cena_netto_jedn=_as_decimal(row["Wiersz_P9A_CenaNettoJedn"]),
            wartosc_netto=_as_decimal(row["Wiersz_P10_WartoscNetto"]),
            stawka_vat=_as_str(row["Wiersz_P11_StawkaVAT"]) or "",
        )

    # ---- FSK mapping -----------------------------------------------------

    def _rows_to_korekta(self, rows: list[dict]) -> Korekta:
        r = rows[0]
        przed = tuple(self._row_to_pozycja_kor(row) for row in rows
                      if int(row.get("Wiersz_StanPrzed") or 0) == 1)
        po = tuple(self._row_to_pozycja_kor(row) for row in rows
                   if int(row.get("Wiersz_StanPrzed") or 0) == 0)
        data_wyst = _as_date(r["Fa_P1_DataWystawienia"])
        data_spr = _as_date(r.get("Fa_P2_DataSprzedazy"))
        return Korekta(
            gid_numer=int(r["_GIDNumer"]),
            naglowek=Naglowek(),
            podmiot1=self._row_to_podmiot1(r),
            podmiot2=self._row_to_podmiot2(r),
            kod_waluty=str(r["Fa_KodWaluty"]).strip(),
            data_wystawienia=data_wyst,
            data_sprzedazy=data_spr if data_spr != data_wyst else None,
            numer_faktury=str(r["Fa_P2A_NumerFaktury"]).strip(),
            podsumowanie=self._rows_to_podsumowanie(r),
            adnotacje=Adnotacje(mpp=_as_str(r.get("Fa_P16_MPP")) or "2"),
            przyczyna_korekty=_as_str(r.get("Kor_PrzyczynaKorekty")) or "",
            dane_fa_korygowanej=DaneFaKorygowanej(
                data_wystawienia_org=_as_date(r["Kor_DataWystFaKorygowanej"]),
                numer_faktury_org=_as_str(r["Kor_NrFaKorygowanej"]) or "",
            ),
            stan_przed=StanPrzed(wiersze=przed),
            stan_po=StanPo(wiersze=po),
            platnosc=self._row_to_platnosc(r),
        )

    def _row_to_pozycja_kor(self, row: dict) -> PozycjaKorekta:
        stan_przed = int(row.get("Wiersz_StanPrzed") or 0) == 1
        data_kor_raw = row.get("Wiersz_DataKorekty")
        data_kor = _as_date(data_kor_raw) if data_kor_raw else None
        return PozycjaKorekta(
            nr_pozycji=int(row["Wiersz_NrPozycji"]),
            nazwa_towaru=_as_str(row["Wiersz_P7_NazwaTowaru"]) or "",
            indeks=_as_str(row.get("Wiersz_Indeks")),
            gtin=_as_str(row.get("Wiersz_GTIN")),
            pkwiu=_as_str(row.get("Wiersz_PKWiU")),
            jednostka_miary=_as_str(row["Wiersz_P8A_JM"]) or "",
            ilosc=_as_decimal(row["Wiersz_P8B_Ilosc"]),
            cena_brutto_jedn=_as_decimal(row["Wiersz_P9B_CenaBrutto"]),
            wartosc_netto=_as_decimal(row["Wiersz_P11A_WartoscNetto"]),
            kwota_vat=_as_decimal(row["Wiersz_P11Vat"]),
            stawka_vat=_as_str(row["Wiersz_P12_StawkaVAT"]) or "",
            stan_przed=stan_przed,
            data_korekty=data_kor if not stan_przed else None,
        )

    # ---- shared mapping --------------------------------------------------

    def _row_to_podmiot1(self, row: dict) -> Podmiot:
        return Podmiot(
            nip=_as_str(row.get("P1_NIP")),
            pelna_nazwa=_as_str(row["P1_PelnaNazwa"]) or "",
            kod_kraju=_as_str(row["P1_KodKraju"]) or "PL",
            adres_l1=_as_str(row["P1_AdresL1"]) or "",
            adres_l2=_as_str(row.get("P1_AdresL2")),
        )

    def _row_to_podmiot2(self, row: dict) -> Podmiot:
        return Podmiot(
            nip=_as_str(row.get("P2_NIP")),
            pelna_nazwa=_as_str(row["P2_PelnaNazwa"]) or "",
            kod_kraju=_as_str(row["P2_KodKraju"]) or "PL",
            adres_l1=_as_str(row["P2_AdresL1"]) or "",
            adres_l2=_as_str(row.get("P2_AdresL2")),
        )

    def _rows_to_podsumowanie(self, row: dict) -> PodsumowanieVat:
        return PodsumowanieVat(
            vat_23_podstawa=_as_decimal_opt(row.get("Fa_P13_1_Podstawa23")),
            vat_23_kwota=_as_decimal_opt(row.get("Fa_P14_1_VAT23")),
            vat_8_podstawa=_as_decimal_opt(row.get("Fa_P13_2_Podstawa8")),
            vat_8_kwota=_as_decimal_opt(row.get("Fa_P14_2_VAT8")),
            vat_5_podstawa=_as_decimal_opt(row.get("Fa_P13_3_Podstawa5")),
            vat_5_kwota=_as_decimal_opt(row.get("Fa_P14_3_VAT5")),
            vat_0_podstawa=_as_decimal_opt(row.get("Fa_P13_5_Podstawa0")),
            vat_0_kwota=_as_decimal_opt(row.get("Fa_P14_5_VAT0")),
            zw_podstawa=_as_decimal_opt(row.get("Fa_P13_6_PodstawaZW")),
            np_podstawa=_as_decimal_opt(row.get("Fa_P13_7_PodstawaNP")),
            kwota_naleznosci=_as_decimal(row["Fa_P15_KwotaNaleznosci"]),
        )

    def _row_to_platnosc(self, row: dict) -> Platnosc:
        termin_raw = row.get("Plat_TerminPlatnosci")
        termin = _as_date(termin_raw) if termin_raw else None
        rozliczona = int(row.get("Plat_Rozliczona") or 0)
        data_rozl_raw = row.get("Plat_DataRozliczenia")
        return Platnosc(
            termin_platnosci=termin,
            kod_formy_platnosci=_as_str(row.get("Plat_KodFormyPlatnosci")),
            nr_rachunku_bankowego=_as_str(row.get("Plat_NrRachunkuBankowego")),
            zaplacono=rozliczona == 1,
            data_zaplaty=_as_date(data_rozl_raw) if rozliczona == 1 and data_rozl_raw else None,
        )


# ---- module-level value coercions ----------------------------------------

def _as_str(v) -> str | None:
    if v is None:
        return None
    s = str(v).strip()
    return s or None


def _as_decimal(v) -> Decimal:
    if isinstance(v, Decimal):
        return v
    return Decimal(str(v))


def _as_decimal_opt(v) -> Decimal | None:
    if v is None:
        return None
    return _as_decimal(v)


def _as_date(v) -> date:
    if isinstance(v, date):
        return v
    return date.fromisoformat(str(v)[:10])
