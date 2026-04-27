"""Ustawienie wartości atrybutu na obiekcie ERP XL.

Zapis przez CDN.XLDodajAktualizujAtr — Comarch SP obsługuje INSERT i UPDATE.
XLDodajAtrybut (XL API) nie działa w trybie wsadowym — pominięte.

Wymagane: GRANT EXECUTE ON CDN.XLDodajAktualizujAtr TO Arek_Demo

Obsługiwane typy obiektów:
  16   = towar         (akronim = Twr_Kod)
  32   = kontrahent    (akronim = Knt_Akronim)
  368  = srodek_trwaly (akronim = Srt_Akronim)
  1617 = dokument      (akronim = numeryczny TrN_GIDNumer jako string)
  4800 = umowa         (akronim = numeryczny UmN_Id jako string)
"""

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.lib.sql_client import SqlClient

_SUPPORTED_TYPES = {16, 32, 368, 1617, 4800}

_SP_SQL = """
DECLARE @ret INT
EXEC @ret = CDN.XLDodajAktualizujAtr
    @AtK_Nazwa    = ?,
    @Atr_Wartosc  = ?,
    @Akronim      = ?,
    @Typ          = ?,
    @OpeIden      = ?,
    @IgnorujBledy = 1
SELECT @ret AS return_code
"""

_SP_ERRORS = {
    -101: ("MISSING_CLASS_NAME",    "Nie podano nazwy klasy atrybutu"),
    -102: ("MISSING_VALUE",         "Nie podano wartości atrybutu"),
    -103: ("MISSING_AKRONIM",       "Nie podano akronimu obiektu"),
    -104: ("MISSING_TYPE",          "Nie podano typu obiektu"),
    -105: ("UNSUPPORTED_TYPE",      "Nieobsługiwany typ obiektu"),
    -106: ("UNSUPPORTED_ATTRIBUTE", "Atrybut nieobsługiwany przez procedurę"),
    -107: ("PRODUCT_NOT_FOUND",     "Nie znaleziono towaru o podanym kodzie"),
    -108: ("CONTRACTOR_NOT_FOUND",  "Nie znaleziono kontrahenta o podanym akronimie"),
    -109: ("VALUE_ALREADY_EXISTS",  "Wartość już istnieje (atrybut wielowartościowy)"),
    -110: ("VALUE_NOT_ON_LIST",     "Wartość nie jest na liście dozwolonych"),
    -111: ("AKRONIM_NOT_NUMERIC",   "Identyfikator dokumentu musi być liczbą"),
    -112: ("OBJECT_NOT_FOUND",      "Nie znaleziono obiektu"),
    -113: ("CLASS_NOT_FOUND",       "Nie znaleziono klasy atrybutu o podanej nazwie"),
    -1100: ("DB_HIST_ERROR",        "Błąd zapisu historii atrybutu"),
    -1101: ("DB_WARTOSC_ERROR",     "Błąd zapisu do AtrybutyWartosci"),
    -1102: ("DB_UPDATE_ERROR",      "Błąd aktualizacji tabeli Atrybuty"),
}


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

    if obj_type not in _SUPPORTED_TYPES:
        return _err("UNSUPPORTED_TYPE", "Nieobsługiwany typ obiektu", start)

    if obj_type in {1617, 4800}:
        try:
            int(akronim)
        except ValueError:
            return _err("OBJECT_NOT_FOUND", "Identyfikator dokumentu musi być liczbą", start)

    try:
        conn = SqlClient().get_connection()
        cursor = conn.cursor()
        cursor.execute(_SP_SQL, [class_name, value, akronim, obj_type, operator])
        row = cursor.fetchone()
        return_code = row[0] if row else None
        conn.commit()
    except Exception as exc:
        return _err("SQL_ERROR", str(exc), start)

    duration_ms = round((time.monotonic() - start) * 1000)

    if return_code != 0:
        err_type, err_msg = _SP_ERRORS.get(
            return_code,
            ("UNKNOWN_ERROR", f"Nieznany kod błędu procedury: {return_code}"),
        )
        return {"ok": False, "data": None,
                "error": {"type": err_type, "message": err_msg, "code": return_code},
                "meta": {"duration_ms": duration_ms}}

    return {
        "ok": True,
        "data": {"class": class_name, "value": value, "akronim": akronim,
                 "type": obj_type, "action": "upserted"},
        "error": None,
        "meta": {"duration_ms": duration_ms},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Ustaw lub zaktualizuj atrybut na obiekcie ERP XL")
    parser.add_argument("--class-name", required=True, help="Nazwa klasy atrybutu")
    parser.add_argument("--value", required=True, help="Wartość atrybutu")
    parser.add_argument("--akronim", required=True,
                        help="Kod towaru / akronim kontrahenta / numeryczny ID dokumentu")
    parser.add_argument("--type", type=int, default=16, choices=[16, 32, 368, 1617, 4800],
                        dest="obj_type", help="Typ obiektu (domyślnie: 16 = towar)")
    parser.add_argument("--operator", default=None,
                        help="Identyfikator operatora ERP")
    args = parser.parse_args()

    result = set_attribute(args.class_name, args.value, args.akronim, args.obj_type, args.operator)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
