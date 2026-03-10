# Wspólne fixtures i dane testowe używane przez wiele plików testowych.

from unittest.mock import MagicMock


def make_mock_conn(columns: list[str], rows: list[list]) -> tuple[MagicMock, MagicMock]:
    """Zwraca (mock_conn, mock_cursor) z zaprogramowanymi kolumnami i wierszami."""
    mock_cursor = MagicMock()
    mock_cursor.description = [(col, None, None, None, None, None, None) for col in columns]
    mock_cursor.fetchall.return_value = [tuple(row) for row in rows]
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    return mock_conn, mock_cursor


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
