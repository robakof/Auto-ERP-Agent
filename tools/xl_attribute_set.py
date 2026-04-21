"""Ustawienie wartości atrybutu na obiekcie ERP XL via CDN.XLDodajAktualizujAtr.

Obsługiwane typy obiektów:
  16   = towar       (lookup po Twr_Kod)
  32   = kontrahent  (lookup po Knt_Akronim)
  368  = srodek_trwaly (lookup po Srt_Akronim)
  1617 = dokument    (lookup po numerycznym TrN_GIDNumer)
  4800 = umowa       (lookup po numerycznym UmN_Id)
"""

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.lib.sql_client import SqlClient

_ERROR_MAP = {
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

_PROC_SQL = """
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


def set_attribute(
    class_name: str,
    value: str,
    akronim: str,
    obj_type: int = 16,
    operator: str | None = None,
) -> dict:
    start = time.monotonic()
    try:
        client = SqlClient()
        conn = client.get_connection()
        cursor = conn.cursor()
        cursor.execute(_PROC_SQL, [class_name, value, akronim, obj_type, operator])
        row = cursor.fetchone()
        conn.commit()
        duration_ms = round((time.monotonic() - start) * 1000)
    except Exception as exc:
        duration_ms = round((time.monotonic() - start) * 1000)
        return {
            "ok": False,
            "data": None,
            "error": {"type": "SQL_ERROR", "message": str(exc)},
            "meta": {"duration_ms": duration_ms},
        }

    return_code = row[0] if row else None

    if return_code == 0:
        return {
            "ok": True,
            "data": {
                "class": class_name,
                "value": value,
                "akronim": akronim,
                "type": obj_type,
            },
            "error": None,
            "meta": {"duration_ms": duration_ms},
        }

    err_type, err_msg = _ERROR_MAP.get(
        return_code,
        ("UNKNOWN_ERROR", f"Nieznany kod błędu procedury: {return_code}"),
    )
    return {
        "ok": False,
        "data": None,
        "error": {"type": err_type, "message": err_msg, "code": return_code},
        "meta": {"duration_ms": duration_ms},
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ustaw lub zaktualizuj atrybut na obiekcie ERP XL"
    )
    parser.add_argument(
        "--class-name", required=True,
        help="Nazwa klasy atrybutu, np. 'WAGA PRODUKTU'",
    )
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
        help="Identyfikator operatora ERP (opcjonalny, wymagany dla atrybutów wielowartościowych)",
    )
    args = parser.parse_args()

    result = set_attribute(args.class_name, args.value, args.akronim, args.obj_type, args.operator)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
