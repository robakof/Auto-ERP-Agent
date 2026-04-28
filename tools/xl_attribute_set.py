"""Ustawienie wartości atrybutu na obiekcie ERP XL.

Zapis przez XLDodajAtrybut (Comarch XL API DLL) — tylko INSERT nowych atrybutów.
Jeśli atrybut już istnieje → zwraca action="skipped" (UPDATE = podprojekt).

Obsługiwane typy obiektów:
  16 = towar (akronim = Twr_Kod)
"""

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.lib.sql_client import SqlClient
from tools.lib.xl_client import XlClient

_GID_SQL = """
    SELECT Twr_GIDNumer, Twr_GIDFirma, Twr_GIDTyp
    FROM CDN.TwrKarty WHERE Twr_Kod = ?
"""

_EXISTS_SQL = """
    SELECT COUNT(*) FROM CDN.Atrybuty a
    JOIN CDN.AtrybutyKlasy k ON a.Atr_AtkId = k.AtK_Id
    WHERE a.Atr_ObiNumer = ? AND a.Atr_ObiTyp = ? AND k.AtK_Nazwa = ?
"""


def _err(err_type: str, msg: str, start: float) -> dict:
    return {
        "ok": False, "data": None,
        "error": {"type": err_type, "message": msg},
        "meta": {"duration_ms": round((time.monotonic() - start) * 1000)},
    }


def set_attribute(
    class_name: str,
    value: str,
    akronim: str,
    obj_type: int = 16,
    operator: str | None = None,
) -> dict:
    start = time.monotonic()

    if obj_type != 16:
        return _err("UNSUPPORTED_TYPE", "Tylko typ 16 (towar) obsługiwany — pozostałe typy: podprojekt", start)

    try:
        conn = SqlClient().get_connection()
        cursor = conn.cursor()

        cursor.execute(_GID_SQL, [akronim])
        row = cursor.fetchone()
        if not row:
            return _err("OBJECT_NOT_FOUND", f"Nie znaleziono towaru: {akronim}", start)
        gid_numer, gid_firma, gid_typ = int(row[0]), int(row[1]), int(row[2])

        cursor.execute(_EXISTS_SQL, [gid_numer, gid_typ, class_name])
        exists = cursor.fetchone()[0] > 0

    except Exception as exc:
        return _err("SQL_ERROR", str(exc), start)

    if exists:
        return {
            "ok": True,
            "data": {"class": class_name, "value": value, "akronim": akronim,
                     "type": obj_type, "action": "skipped"},
            "error": None,
            "meta": {"duration_ms": round((time.monotonic() - start) * 1000)},
        }

    try:
        result = XlClient().dodaj_atrybut(
            gid_typ=gid_typ,
            gid_numer=gid_numer,
            gid_firma=gid_firma,
            klasa=class_name,
            wartosc=value,
        )
    except Exception as exc:
        return _err("XL_API_ERROR", str(exc), start)

    duration_ms = round((time.monotonic() - start) * 1000)

    if not result.get("ok"):
        return {
            "ok": False, "data": None,
            "error": result.get("error", {"type": "XL_API_ERROR", "message": "Nieznany błąd XL API"}),
            "meta": {"duration_ms": duration_ms},
        }

    return {
        "ok": True,
        "data": {"class": class_name, "value": value, "akronim": akronim,
                 "type": obj_type, "action": "inserted"},
        "error": None,
        "meta": {"duration_ms": duration_ms},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Dodaj nowy atrybut na obiekcie ERP XL przez XL API")
    parser.add_argument("--class-name", required=True, help="Nazwa klasy atrybutu")
    parser.add_argument("--value", required=True, help="Wartość atrybutu")
    parser.add_argument("--akronim", required=True, help="Kod towaru")
    parser.add_argument("--type", type=int, default=16, choices=[16],
                        dest="obj_type", help="Typ obiektu (domyślnie: 16 = towar)")
    parser.add_argument("--operator", default=None, help="Identyfikator operatora ERP")
    args = parser.parse_args()

    result = set_attribute(args.class_name, args.value, args.akronim, args.obj_type, args.operator)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
