"""
Weryfikacja instalacji środowiska Auto-ERP-Agent.
Uruchom: python verify.py
"""

import json
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str]) -> dict:
    result = subprocess.run(cmd, capture_output=True)
    stdout = (result.stdout or b"").decode("utf-8", errors="replace")
    stderr = (result.stderr or b"").decode("utf-8", errors="replace")
    try:
        return json.loads(stdout)
    except (json.JSONDecodeError, ValueError):
        return {"ok": False, "error": {"message": stderr or stdout}}


def check(label: str, passed: bool, detail: str = "") -> bool:
    status = "OK" if passed else "FAIL"
    line = f"  [{status}] {label}"
    if detail:
        line += f": {detail}"
    print(line)
    return passed


def main() -> int:
    print("Auto-ERP-Agent: weryfikacja instalacji")
    print("=" * 40)
    all_ok = True

    # 1. docs.db
    print("\n1. Baza dokumentacji (docs.db)")
    db_path = Path("erp_docs/index/docs.db")
    all_ok &= check("plik istnieje", db_path.exists(), str(db_path))
    if db_path.exists():
        resp = run([sys.executable, "tools/docs_search.py", "towar*", "--useful-only", "--limit", "1"])
        all_ok &= check("docs_search.py", resp.get("ok") is True)

    # 2. Baza rozwiązań
    print("\n2. Baza rozwiazan (solutions/)")
    resp = run([sys.executable, "tools/windows_search.py", "towary"])
    found = resp.get("ok") is True and len(resp.get("data", {}).get("results", [])) > 0
    all_ok &= check("windows_search.py", resp.get("ok") is True)
    all_ok &= check("Okno towary znalezione", found)

    # 3. SQL Server
    print("\n3. Polaczenie z SQL Server")
    resp = run([sys.executable, "tools/sql_query.py", "SELECT TOP 1 Twr_GIDNumer FROM CDN.TwrKarty"])
    ok = resp.get("ok") is True
    all_ok &= check("sql_query.py", ok)
    if ok:
        row_count = resp.get("data", {}).get("row_count", 0)
        all_ok &= check("zwraca dane", row_count > 0, f"{row_count} row(s)")
    else:
        err = resp.get("error", {}).get("message", "unknown error")
        check("blad polaczenia", False, err)

    # Podsumowanie
    print("\n" + "=" * 40)
    if all_ok:
        print("OK: srodowisko gotowe do pracy.")
    else:
        print("FAIL: sprawdz .env i polaczenie z SQL Serverem.")
        print("Szczegoly: INSTALL.md")

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
