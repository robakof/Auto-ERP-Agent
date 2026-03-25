# Wspólne fixtures i dane testowe używane przez wiele plików testowych.

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock

# Add project root to sys.path for core module imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def make_mock_conn(columns: list[str], rows: list[list]) -> tuple[MagicMock, MagicMock]:
    """Zwraca (mock_conn, mock_cursor) z zaprogramowanymi kolumnami i wierszami."""
    mock_cursor = MagicMock()
    mock_cursor.description = [(col, None, None, None, None, None, None) for col in columns]
    mock_cursor.fetchall.return_value = [tuple(row) for row in rows]
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    return mock_conn, mock_cursor


# --- Safety hook helpers (shared by test_pre_tool_use.py, test_boundary.py) ---

HOOK_PATH = Path(__file__).parent.parent / "tools" / "hooks" / "pre_tool_use.py"


def run_hook(payload: dict) -> tuple:
    """Run pre_tool_use hook with given payload. Returns (returncode, parsed_output)."""
    result = subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
    )
    output = None
    if result.stdout.strip():
        output = json.loads(result.stdout.strip())
    return result.returncode, output


def make_bash(command: str) -> dict:
    """Create Bash tool payload for hook testing."""
    return {"tool_name": "Bash", "tool_input": {"command": command}}


def make_ws(rows: list[tuple]) -> MagicMock:
    """Tworzy mock arkusza Excel zwracający podane wiersze."""
    ws = MagicMock()
    ws.iter_rows.return_value = rows
    return ws


# Minimalne dane testowe współdzielone między test_build_index i test_search_docs

TABELE_ROWS = [
    (None, None, None, None, None, None),
    (1, "Zamówienia", "CDN.ZamNag", "ZaN", None, "Nagłówki zamówień sprzedaży"),
    (2, "Kontrahenci", "CDN.KntKarty", "Knt", None, "Kartoteka kontrahentów"),
]

KOLUMNY_ROWS = [
    ("some", "other", "stuff", None, None, None, None, None, None, None, None, None),
    ("Numer tabeli", "Nazwa własna tabeli", "Nazwa tabeli", "Nr kol",
     "Nazwa własna kol", "Nazwa kol", "Rola", "Czy użyteczna",
     "Preferowana", "Typ", None, "Opis"),
    (1, "Zamówienia", "CDN.ZamNag", 1, "ID zamówienia", "ZaN_GIDNumer",
     None, "Tak", "Nie", "int", None, "Identyfikator rekordu"),
    (1, "Zamówienia", "CDN.ZamNag", 2, "ID kontrahenta", "ZaN_KntGIDNumer",
     None, "Tak", "Tak", "int", None, "Klucz obcy do kontrahenta"),
    (2, "Kontrahenci", "CDN.KntKarty", 1, "Nazwa kontrahenta", "Knt_Nazwa1",
     None, "Tak", "Tak", "varchar", None, "Pierwsza linia nazwy"),
]

RELACJE_ROWS = [
    (None,) * 12,
    (None, None, "KntKarty", None, "ZaN_KntGIDNumer", "Knt_GIDNumer",
     None, None, None, None, None, "CDN.ZamNag"),
]

SLOWNIK_ROWS = [
    (None,) * 8,
    (1, "Zamówienia", "CDN.ZamNag", 3, "Status", "ZaN_Status", 0, "robocze"),
    (1, "Zamówienia", "CDN.ZamNag", 3, "Status", "ZaN_Status", 1, "zatwierdzone"),
    (1, "Zamówienia", "CDN.ZamNag", 3, "Status", "ZaN_Status", 2, "zrealizowane"),
]

PRZYKLADOWE_ROWS = [
    (None,) * 7,
    (1, None, "CDN.KntKarty", 1, None, "Knt_Nazwa1", "Firma ABC"),
    (1, None, "CDN.KntKarty", 1, None, "Knt_Nazwa1", "Jan Kowalski"),
]
