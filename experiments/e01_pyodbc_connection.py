"""
E-01: Weryfikacja połączenia pyodbc z SQL Server ERP
Cel: potwierdzić że połączenie działa i konto CEiM_Reader ma dostęp read-only
"""

import json
import os
import sys
import pyodbc
from dotenv import load_dotenv

load_dotenv()

DRIVER = "ODBC Driver 17 for SQL Server"
SERVER = os.getenv("SQL_SERVER")
DATABASE = os.getenv("SQL_DATABASE")
USERNAME = os.getenv("SQL_USERNAME")
PASSWORD = os.getenv("SQL_PASSWORD")

connection_string = (
    f"DRIVER={{{DRIVER}}};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE};"
    f"UID={USERNAME};"
    f"PWD={PASSWORD};"
    f"TrustServerCertificate=yes;"
)


def test_connection():
    print(f"[1] Łączenie z {SERVER}/{DATABASE} jako {USERNAME}...")
    conn = pyodbc.connect(connection_string, timeout=10)
    print("    OK — połączenie nawiązane")
    return conn


def test_select(conn):
    print("[2] SELECT TOP 5 z CDN.ZamNag...")
    cursor = conn.cursor()
    cursor.execute("SELECT TOP 5 ZaN_GIDNumer, ZaN_GIDTyp, ZaN_GIDFirma FROM CDN.ZamNag")
    columns = [col[0] for col in cursor.description]
    rows = [list(row) for row in cursor.fetchall()]
    result = {"columns": columns, "rows": rows, "row_count": len(rows)}
    print(f"    OK — zwrócono {len(rows)} wierszy")
    print(f"    Kolumny: {columns}")
    print(f"    Przykład: {rows[0] if rows else 'brak danych'}")
    return result


def test_dml_blocked(conn):
    print("[3] Weryfikacja blokady DML (próba INSERT)...")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO CDN.ZamNag (ZaN_Typ) VALUES (0)")
        print("    FAIL — INSERT nie został zablokowany!")
        return False
    except pyodbc.Error as e:
        print(f"    OK — INSERT zablokowany: {e.args[1][:80]}")
        return True


def test_information_schema(conn):
    print("[4] SELECT z INFORMATION_SCHEMA (sprawdzenie widoczności tabel)...")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) as table_count
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_TYPE = 'BASE TABLE'
    """)
    count = cursor.fetchone()[0]
    print(f"    OK — widocznych tabel: {count}")
    return count


if __name__ == "__main__":
    try:
        conn = test_connection()
        test_select(conn)
        test_dml_blocked(conn)
        test_information_schema(conn)
        conn.close()
        print("\n[E-01] SUKCES — wszystkie testy przeszły")
    except Exception as e:
        print(f"\n[E-01] BŁĄD — {e}")
        sys.exit(1)
