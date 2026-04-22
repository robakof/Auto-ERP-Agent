"""Ustawienie wartości atrybutu na obiekcie ERP XL via CDN.XLDodajAktualizujAtr (UPDATE)
lub bezpośredni INSERT gdy atrybut nie istnieje dla danego obiektu.

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

# Sprawdź czy atrybut istnieje dla obiektu danego typu
_CHECK_EXISTS_SQL = {
    16: """
        SELECT COUNT(*) FROM CDN.Atrybuty a
        JOIN CDN.TwrKarty t ON t.Twr_GidNumer = a.Atr_ObiNumer
        JOIN CDN.AtrybutyKlasy k ON k.AtK_ID = a.Atr_AtkId
        WHERE t.Twr_Kod = ? AND k.AtK_Nazwa = ? AND a.Atr_ObiTyp = 16 AND a.Atr_ObiLp = 0
    """,
    32: """
        SELECT COUNT(*) FROM CDN.Atrybuty a
        JOIN CDN.KntKarty t ON t.Knt_GidNumer = a.Atr_ObiNumer
        JOIN CDN.AtrybutyKlasy k ON k.AtK_ID = a.Atr_AtkId
        WHERE t.Knt_Akronim = ? AND k.AtK_Nazwa = ? AND a.Atr_ObiTyp = 32 AND a.Atr_ObiSubLp = 0
    """,
    368: """
        SELECT COUNT(*) FROM CDN.Atrybuty a
        JOIN CDN.Srtkarty t ON t.Srt_GidNumer = a.Atr_ObiNumer
        JOIN CDN.AtrybutyKlasy k ON k.AtK_ID = a.Atr_AtkId
        WHERE t.Srt_Akronim = ? AND k.AtK_Nazwa = ? AND a.Atr_ObiTyp = 368
    """,
}

# INSERT nowego przypisania atrybutu do obiektu
_INSERT_SQL = {
    16: """
        INSERT INTO CDN.Atrybuty (
            Atr_ObiTyp, Atr_ObiFirma, Atr_ObiNumer, Atr_ObiLp, Atr_ObiSubLp,
            Atr_AtkId, Atr_Wartosc,
            Atr_AtrTyp, Atr_AtrFirma, Atr_AtrNumer, Atr_AtrLp, Atr_AtrSubLp,
            Atr_Pozycja, Atr_GUID, Atr_LastMod
        )
        SELECT
            t.Twr_GIDTyp, t.Twr_GIDFirma, t.Twr_GidNumer, t.Twr_GIDLp, 0,
            k.AtK_ID, ?,
            0, 0, 0, 0, 0,
            ISNULL((SELECT MAX(a2.Atr_Pozycja)+1 FROM CDN.Atrybuty a2
                    WHERE a2.Atr_ObiNumer=t.Twr_GidNumer AND a2.Atr_ObiTyp=16), 1),
            NEWID(),
            DATEDIFF(S, '19900101', GETDATE())
        FROM CDN.TwrKarty t
        CROSS JOIN CDN.AtrybutyKlasy k
        WHERE t.Twr_Kod = ? AND k.AtK_Nazwa = ?
    """,
    32: """
        INSERT INTO CDN.Atrybuty (
            Atr_ObiTyp, Atr_ObiFirma, Atr_ObiNumer, Atr_ObiLp, Atr_ObiSubLp,
            Atr_AtkId, Atr_Wartosc,
            Atr_AtrTyp, Atr_AtrFirma, Atr_AtrNumer, Atr_AtrLp, Atr_AtrSubLp,
            Atr_Pozycja, Atr_GUID, Atr_LastMod
        )
        SELECT
            t.Knt_GIDTyp, t.Knt_GIDFirma, t.Knt_GidNumer, t.Knt_GIDLp, 0,
            k.AtK_ID, ?,
            0, 0, 0, 0, 0,
            ISNULL((SELECT MAX(a2.Atr_Pozycja)+1 FROM CDN.Atrybuty a2
                    WHERE a2.Atr_ObiNumer=t.Knt_GidNumer AND a2.Atr_ObiTyp=32), 1),
            NEWID(),
            DATEDIFF(S, '19900101', GETDATE())
        FROM CDN.KntKarty t
        CROSS JOIN CDN.AtrybutyKlasy k
        WHERE t.Knt_Akronim = ? AND k.AtK_Nazwa = ?
    """,
    368: """
        INSERT INTO CDN.Atrybuty (
            Atr_ObiTyp, Atr_ObiFirma, Atr_ObiNumer, Atr_ObiLp, Atr_ObiSubLp,
            Atr_AtkId, Atr_Wartosc,
            Atr_AtrTyp, Atr_AtrFirma, Atr_AtrNumer, Atr_AtrLp, Atr_AtrSubLp,
            Atr_Pozycja, Atr_GUID, Atr_LastMod
        )
        SELECT
            t.Srt_GIDTyp, t.Srt_GIDFirma, t.Srt_GidNumer, t.Srt_GIDLp, 0,
            k.AtK_ID, ?,
            0, 0, 0, 0, 0,
            ISNULL((SELECT MAX(a2.Atr_Pozycja)+1 FROM CDN.Atrybuty a2
                    WHERE a2.Atr_ObiNumer=t.Srt_GidNumer AND a2.Atr_ObiTyp=368), 1),
            NEWID(),
            DATEDIFF(S, '19900101', GETDATE())
        FROM CDN.Srtkarty t
        CROSS JOIN CDN.AtrybutyKlasy k
        WHERE t.Srt_Akronim = ? AND k.AtK_Nazwa = ?
    """,
}


def _attribute_exists(cursor, class_name: str, akronim: str, obj_type: int) -> bool:
    check_sql = _CHECK_EXISTS_SQL.get(obj_type)
    if check_sql is None:
        return True  # typy 1617/4800 — nie obsługujemy INSERT, tylko UPDATE
    cursor.execute(check_sql, [akronim, class_name])
    row = cursor.fetchone()
    return bool(row and row[0] > 0)


def _insert_attribute(cursor, class_name: str, value: str, akronim: str, obj_type: int) -> int:
    insert_sql = _INSERT_SQL.get(obj_type)
    if insert_sql is None:
        return -105  # typ nieobsługiwany dla INSERT
    cursor.execute(insert_sql, [value, akronim, class_name])
    return 0 if cursor.rowcount > 0 else -112


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

        exists = _attribute_exists(cursor, class_name, akronim, obj_type)

        if exists:
            cursor.execute(_PROC_SQL, [class_name, value, akronim, obj_type, operator])
            row = cursor.fetchone()
            return_code = row[0] if row else None
            action = "updated"
        else:
            return_code = _insert_attribute(cursor, class_name, value, akronim, obj_type)
            action = "inserted"

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

    if return_code == 0:
        return {
            "ok": True,
            "data": {
                "class": class_name,
                "value": value,
                "akronim": akronim,
                "type": obj_type,
                "action": action,
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
        help="Identyfikator operatora ERP (wymagany dla atrybutów wielowartościowych)",
    )
    args = parser.parse_args()

    result = set_attribute(args.class_name, args.value, args.akronim, args.obj_type, args.operator)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
