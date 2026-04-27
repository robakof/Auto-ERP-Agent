"""Ustawienie wartości atrybutu na obiekcie ERP XL via XL API (XLDodajAtrybut).

Obsługiwane typy obiektów:
  16   = towar       (lookup po Twr_Kod)
  32   = kontrahent  (lookup po Knt_Akronim)
  368  = srodek_trwaly (lookup po Srt_Akronim)
  1617 = dokument    (lookup po numerycznym TrN_GIDNumer)
  4800 = umowa       (lookup po numerycznym UmN_Id)

GID lookup: nadal przez SQL (odczyt) — migracja na XLWykonajZapytanie w M4.
Zapis: XLDodajAtrybut przez XlClient (oficjalne API, warstwa biznesowa XL).
"""

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.lib.sql_client import SqlClient
from tools.lib.xl_client import XlClient

_SUPPORTED_TYPES = {16, 32, 368, 1617, 4800}

_GID_SQL = {
    16:  "SELECT Twr_GIDTyp, Twr_GidNumer, Twr_GIDFirma FROM CDN.TwrKarty WHERE Twr_Kod = ?",
    32:  "SELECT Knt_GIDTyp, Knt_GidNumer, Knt_GIDFirma FROM CDN.KntKarty WHERE Knt_Akronim = ?",
    368: "SELECT Srt_GIDTyp, Srt_GidNumer, Srt_GIDFirma FROM CDN.Srtkarty WHERE Srt_Akronim = ?",
}


def _lookup_gid(cursor, akronim: str, obj_type: int) -> tuple | None:
    """Zwraca (gid_typ, gid_numer, gid_firma) lub None gdy nie znaleziono."""
    sql = _GID_SQL.get(obj_type)
    if sql is None:
        try:
            numer = int(akronim)
        except ValueError:
            return None
        return (obj_type, numer, 0)
    cursor.execute(sql, [akronim])
    row = cursor.fetchone()
    return (int(row[0]), int(row[1]), int(row[2])) if row else None


def _err(err_type: str, msg: str, start: float) -> dict:
    return {
        "ok": False,
        "data": None,
        "error": {"type": err_type, "message": msg},
        "meta": {"duration_ms": round((time.monotonic() - start) * 1000)},
    }


def set_attribute(
    class_name: str,
    value: str,
    akronim: str,
    obj_type: int = 16,
    operator: str | None = None,  # zachowane dla backward compatibility; operator z sesji XL
) -> dict:
    start = time.monotonic()

    if obj_type not in _SUPPORTED_TYPES:
        return _err("UNSUPPORTED_TYPE", "Nieobsługiwany typ obiektu", start)

    try:
        conn = SqlClient().get_connection()
        gid = _lookup_gid(conn.cursor(), akronim, obj_type)
    except Exception as exc:
        return _err("SQL_ERROR", str(exc), start)

    if gid is None:
        return _err("OBJECT_NOT_FOUND", "Nie znaleziono obiektu", start)

    gid_typ, gid_numer, gid_firma = gid

    try:
        result = XlClient().dodaj_atrybut(gid_typ, gid_numer, gid_firma, class_name, value)
    except Exception as exc:
        return _err("API_ERROR", str(exc), start)

    duration_ms = round((time.monotonic() - start) * 1000)

    if not result.get("ok"):
        msg = result.get("error", {}).get("message", "")
        return {
            "ok": False,
            "data": None,
            "error": {"type": "ATRYBUT_FAIL", "message": msg},
            "meta": {"duration_ms": duration_ms},
        }

    return {
        "ok": True,
        "data": {
            "class": class_name,
            "value": value,
            "akronim": akronim,
            "type": obj_type,
            "action": "set",
        },
        "error": None,
        "meta": {"duration_ms": duration_ms},
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ustaw atrybut na obiekcie ERP XL"
    )
    parser.add_argument("--class-name", required=True, help="Nazwa klasy atrybutu")
    parser.add_argument("--value", required=True, help="Wartość atrybutu")
    parser.add_argument(
        "--akronim", required=True,
        help="Kod towaru / akronim kontrahenta / numeryczny ID dokumentu",
    )
    parser.add_argument(
        "--type", type=int, default=16,
        choices=[16, 32, 368, 1617, 4800],
        dest="obj_type",
        help="Typ obiektu (domyślnie: 16 = towar)",
    )
    parser.add_argument(
        "--operator", default=None,
        help="Identyfikator operatora (deprecated — operator pochodzi z sesji XL)",
    )
    args = parser.parse_args()

    result = set_attribute(args.class_name, args.value, args.akronim, args.obj_type, args.operator)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
