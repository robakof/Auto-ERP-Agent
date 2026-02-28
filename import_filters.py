"""
import_filters.py — jednorazowy import filtrów z CDN.Filtry do solutions/

Uruchomienie:
    python import_filters.py          # pomija istniejące pliki
    python import_filters.py --force  # nadpisuje istniejące pliki
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from tools.sql_query import get_connection  # reużywa połączenia z .env

SOLUTIONS_ROOT = Path(__file__).parent / "solutions" / "solutions in ERP windows"

# Mapowanie (ProcID, ListaID) → (okno, widok)
WINDOW_MAPPING = {
    (2100, 1):  ("Okno kontrahenci",               "Grupy"),
    (2100, 2):  ("Okno kontrahenci",               "Wg akronimu"),
    (2300, 1):  ("Okno towary",                    "Towary według EAN"),
    (2300, 2):  ("Okno towary",                    "Towary według grup"),
    (2700, 1):  ("Okno rejestr VAT",               "Rejestr VAT"),
    (2715, 1):  ("Okno dokumenty",                 "Handlowe"),
    (2715, 2):  ("Okno dokumenty",                 "Magazynowe"),
    (2715, 81): ("Okno dokumenty",                 "Elementy"),
    (8301, 1):  ("Okno zapisy bankowe",            "Zapisy bankowe"),
    (8501, 1):  ("Okno historia kontrahenta",      "Transakcje - Zbiorczo"),
    (8501, 2):  ("Okno historia kontrahenta",      "Transakcje - Chronologicznie"),
    (8501, 3):  ("Okno historia kontrahenta",      "Transakcje - Dla towaru"),
    (8504, 1):  ("Okno historia towaru",           "Transakcje - Chronologicznie"),
    (8504, 2):  ("Okno historia towaru",           "Transakcje - Dla kontrahenta"),
    (8504, 11): ("Okno historia towaru",           "Magazyn - Chronologicznie"),
    (8504, 13): ("Okno historia towaru",           "Transakcje - Wg kontrahentow"),
    (9010, 3):  ("Okno lista zamówień sprzedaży",  "Zamówienia"),
    (9023, 1):  ("Okno zamówienie",                "Zamówienie"),
    (30499, 1): ("Okno dokument",                  "Dokument"),
}

ILLEGAL_CHARS = re.compile(r'[\\/:*?"<>|]')


def safe_filename(name: str) -> str:
    return ILLEGAL_CHARS.sub("", name).strip()


def load_filters() -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT FIL_ProcID, FIL_ListaID, FIL_Lp, FIL_Nazwa, FIL_FiltrSQL
        FROM CDN.Filtry
        WHERE LEN(ISNULL(FIL_FiltrSQL, '')) > 0
        ORDER BY FIL_ProcID, FIL_ListaID, FIL_Lp
    """)
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "proc_id": r[0],
            "lista_id": r[1],
            "nazwa": r[3],
            "sql": r[4],
        }
        for r in rows
    ]


def import_filters(force: bool = False) -> None:
    filters = load_filters()

    created = 0
    skipped_existing = 0
    skipped_unmapped = 0

    for f in filters:
        key = (f["proc_id"], f["lista_id"])
        if key not in WINDOW_MAPPING:
            skipped_unmapped += 1
            continue

        okno, widok = WINDOW_MAPPING[key]
        filters_dir = SOLUTIONS_ROOT / okno / widok / "filters"
        filters_dir.mkdir(parents=True, exist_ok=True)

        filename = safe_filename(f["nazwa"]) + ".sql"
        target = filters_dir / filename

        if target.exists() and not force:
            skipped_existing += 1
            continue

        target.write_text(f["sql"], encoding="utf-8")
        created += 1
        print(f"  [+] {okno}/{widok}/filters/{filename}")

    print(
        f"\nGotowe: {created} utworzono"
        f", {skipped_existing} pominięto (plik istniał)"
        f", {skipped_unmapped} pominięto (brak mapowania)"
    )


if __name__ == "__main__":
    force = "--force" in sys.argv
    if force:
        print("Tryb --force: nadpisywanie istniejących plików\n")
    import_filters(force=force)
