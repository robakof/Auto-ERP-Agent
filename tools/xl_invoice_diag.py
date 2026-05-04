"""Diagnostyka mapowania TwrKody — sprawdza co jest w CDN.TwrKody dla danego NIP dostawcy.

Użycie:
  python tools/xl_invoice_diag.py --nip 5742080310
  python tools/xl_invoice_diag.py --nip 5742080310 --nazwa "Karton narozniki 1500X200"
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.lib.sql_client import SqlClient

_NIP_SQL = "SELECT Knt_GIDNumer, Knt_GIDFirma, Knt_Nazwa1 FROM CDN.KntKarty WHERE Knt_NIP = ?"

_LIST_SQL = """
    SELECT tw.Twr_Kod, tw.Twr_Nazwa, t.TwK_Kod AS dodatkowy_kod, tk.TKK_KntNumer
    FROM CDN.TwrKody t
    JOIN CDN.TwrKodyKnt tk ON t.TwK_Id = tk.TKK_TwKId
    JOIN CDN.TwrKarty tw ON t.TwK_TwrNumer = tw.Twr_GIDNumer
    WHERE tk.TKK_KntNumer = ?
    ORDER BY tw.Twr_Kod
"""

_MATCH_SQL = """
    SELECT TOP 1 tw.Twr_Kod
    FROM CDN.TwrKody t
    JOIN CDN.TwrKodyKnt tk ON t.TwK_Id = tk.TKK_TwKId
    JOIN CDN.TwrKarty tw ON t.TwK_TwrNumer = tw.Twr_GIDNumer
    WHERE tk.TKK_KntNumer = ?
      AND UPPER(LTRIM(RTRIM(t.TwK_Kod))) = UPPER(LTRIM(RTRIM(?)))
"""

_FIND_CODE_SQL = """
    SELECT tw.Twr_Kod, tw.Twr_Nazwa, t.TwK_Kod, tk.TKK_KntNumer,
           k.Knt_NIP, k.Knt_Nazwa1
    FROM CDN.TwrKody t
    JOIN CDN.TwrKodyKnt tk ON t.TwK_Id = tk.TKK_TwKId
    JOIN CDN.TwrKarty tw ON t.TwK_TwrNumer = tw.Twr_GIDNumer
    LEFT JOIN CDN.KntKarty k ON tk.TKK_KntNumer = k.Knt_GIDNumer
    WHERE UPPER(LTRIM(RTRIM(t.TwK_Kod))) LIKE UPPER(LTRIM(RTRIM(?)))
"""


def diag(nip: str, nazwa: str | None = None) -> None:
    conn = SqlClient().get_connection()
    cur = conn.cursor()

    cur.execute(_NIP_SQL, [nip])
    row = cur.fetchone()
    if not row:
        print(f"[BRAK] Kontrahent NIP={nip} nie istnieje w CDN.KntKarty")
        return

    knt_numer, knt_firma, knt_nazwa = int(row[0]), int(row[1]), row[2]
    print(f"Kontrahent: {knt_nazwa.strip()}")
    print(f"  Knt_GIDNumer={knt_numer}  Knt_GIDFirma={knt_firma}")
    print()

    cur.execute(_LIST_SQL, [knt_numer])
    rows = cur.fetchall()
    if not rows:
        print(f"[BRAK] Brak wpisów w CDN.TwrKody dla TKK_KntNumer={knt_numer}")
    else:
        print(f"Wpisy w CDN.TwrKody (TKK_KntNumer={knt_numer}) — {len(rows)} szt.:")
        print(f"  {'Twr_Kod':<12} {'Twr_Nazwa':<30} {'dodatkowy_kod (TwK_Kod)'}")
        print("  " + "-" * 75)
        for r in rows:
            twr_kod = r[0].strip() if r[0] else ""
            twr_nazwa = (r[1] or "").strip()[:28]
            twk_kod = (r[2] or "").strip()
            print(f"  {twr_kod:<12} {twr_nazwa:<30} {repr(twk_kod)}")

    if nazwa:
        print()
        print(f"Szukam (exact, case-insensitive): {repr(nazwa)}")
        cur.execute(_MATCH_SQL, [knt_numer, nazwa])
        match = cur.fetchone()
        if match:
            print(f"  [OK] Znaleziono Twr_Kod = {match[0]}")
        else:
            print(f"  [BRAK] Brak dopasowania dla TKK_KntNumer={knt_numer}.")

        # Szukaj tego kodu u wszystkich kontrahentów (LIKE %)
        like_pattern = f"%{nazwa[:30]}%"
        print()
        print(f"Szukam globalnie (LIKE): {repr(like_pattern)}")
        cur.execute(_FIND_CODE_SQL, [like_pattern])
        found = cur.fetchall()
        if found:
            print(f"  Znaleziono {len(found)} wpis(ów) u innych kontrahentów:")
            for r in found:
                twr_kod = (r[0] or "").strip()
                twk_kod = (r[2] or "").strip()
                tkk_knt = r[3]
                knt_nip = (r[4] or "").strip()
                knt_n = (r[5] or "").strip()
                print(f"    Twr_Kod={twr_kod}  TwK_Kod={repr(twk_kod)}")
                print(f"      → kontrahent: TKK_KntNumer={tkk_knt}  NIP={knt_nip}  {knt_n}")
        else:
            print(f"  [BRAK] Nie znaleziono nigdzie.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Diagnostyka CDN.TwrKody dla NIP dostawcy")
    parser.add_argument("--nip", required=True, help="NIP dostawcy")
    parser.add_argument("--nazwa", nargs="+", help="Nazwa z faktury (P_7) do przetestowania dopasowania")
    args = parser.parse_args()
    nazwa = " ".join(args.nazwa) if args.nazwa else None
    diag(args.nip, nazwa)


if __name__ == "__main__":
    main()
