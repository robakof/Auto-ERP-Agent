"""
import_columns.py — jednorazowy import kolumn z CDN.DefinicjeKolumn do solutions/

Uruchomienie:
    python import_columns.py          # pomija istniejące pliki
    python import_columns.py --force  # nadpisuje istniejące pliki
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from tools.sql_query import get_connection

SOLUTIONS_ROOT = Path(__file__).parent / "solutions" / "solutions in ERP windows"

# Mapowanie (IDFormatki, IDListy) → (okno, widok)
# IDFormatki = ten sam identyfikator okna co FIL_ProcID w CDN.Filtry
# IDListy = wewnętrzny ID listy/zakładki (inna numeracja niż w CDN.Filtry)
WINDOW_MAPPING = {
    (2100, 1):    ("Okno kontrahenci",               "Grupy"),
    (2100, 2):    ("Okno kontrahenci",               "Wg akronimu"),
    (2300, 30):   ("Okno towary",                    "Towary według grup"),
    (2300, 31):   ("Okno towary",                    "Towary według EAN"),
    (2715, 4):    ("Okno dokumenty",                 "Handlowe"),
    (2715, 5):    ("Okno dokumenty",                 "Magazynowe"),
    (2715, 1008): ("Okno dokumenty",                 "Elementy"),
    (8504, 16):   ("Okno historia towaru",           "Transakcje - Chronologicznie"),
    (9010, 8):    ("Okno lista zamówień sprzedaży",  "Zamówienia"),
    (9023, 13):   ("Okno zamówienie",                "Zamówienie"),
}

# Nazwy kolumn testowych/debugowych — pomijamy
DEBUG_NAMES = {
    "filtrsql", "filtr sql", "filtr_sql", "filtrsql", "filtr sql dawid",
    "filtr_sql_dawid", "n/b",
}

ILLEGAL_CHARS = re.compile(r'[\\/:*?"<>|]')


def safe_filename(name: str) -> str:
    return ILLEGAL_CHARS.sub("", name).strip()


def normalize_sql(sql: str) -> str:
    """Normalizuje SQL do porównania duplikatów (spacje, wielkość liter)."""
    return re.sub(r'\s+', ' ', sql).strip().lower()


def load_columns() -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DFK_IDFormatki, DFK_IDListy, DFK_Nazwa, DFK_SQL
        FROM CDN.DefinicjeKolumn
        WHERE DFK_Aktywny = 1
          AND LEN(ISNULL(DFK_SQL, '')) > 0
        ORDER BY DFK_IDFormatki, DFK_IDListy, DFK_ID
    """)
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "formatka_id": r[0],
            "lista_id":    r[1],
            "nazwa":       r[2],
            "sql":         r[3],
        }
        for r in rows
    ]


def deduplicate(columns: list[dict]) -> list[dict]:
    """
    Per (formatka, lista): zachowuje jedną kolumnę per unikalny SQL.
    Przy wielu rekordach z tym samym SQL bierze pierwszy (najstarszy DFK_ID).
    Kolumny debugowe (nazwa w DEBUG_NAMES) są pomijane.
    """
    seen: dict[tuple, set] = {}  # (formatka_id, lista_id) → {normalized_sql, ...}
    result = []

    for col in columns:
        if col["nazwa"].strip().lower() in DEBUG_NAMES:
            continue

        key = (col["formatka_id"], col["lista_id"])
        if key not in WINDOW_MAPPING:
            continue

        norm = normalize_sql(col["sql"])
        if key not in seen:
            seen[key] = set()

        if norm in seen[key]:
            continue  # duplikat SQL u innego operatora

        seen[key].add(norm)
        result.append(col)

    return result


def import_columns(force: bool = False) -> None:
    all_columns = load_columns()
    columns = deduplicate(all_columns)

    created = 0
    skipped_existing = 0

    for col in columns:
        key = (col["formatka_id"], col["lista_id"])
        okno, widok = WINDOW_MAPPING[key]
        columns_dir = SOLUTIONS_ROOT / okno / widok / "columns"
        columns_dir.mkdir(parents=True, exist_ok=True)

        filename = safe_filename(col["nazwa"]) + ".sql"
        target = columns_dir / filename

        if target.exists() and not force:
            skipped_existing += 1
            continue

        target.write_text(col["sql"], encoding="utf-8")
        created += 1
        print(f"  [+] {okno}/{widok}/columns/{filename}")

    skipped_unmapped = len(all_columns) - len(
        [c for c in all_columns if (c["formatka_id"], c["lista_id"]) in WINDOW_MAPPING]
    )

    print(
        f"\nGotowe: {created} utworzono"
        f", {skipped_existing} pominięto (plik istniał)"
        f", {skipped_unmapped} pominięto (brak mapowania lub debug)"
    )


if __name__ == "__main__":
    force = "--force" in sys.argv
    if force:
        print("Tryb --force: nadpisywanie istniejących plików\n")
    import_columns(force=force)
