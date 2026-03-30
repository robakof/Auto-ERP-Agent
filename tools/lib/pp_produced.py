"""pp_produced.py — Pobieranie przyjętej produkcji PW Otorowo z ERP.

Query: CDN.TraNag JOIN CDN.TraElem
  GIDTyp=1617 (PW), Seria=OTO, TwrKod LIKE 'CZNI%', rok z TrN_DataMag.

Output: dict[czni_kod, suma_qty] — gotowe do odjęcia od popytu w pp_schedule.
"""
from pathlib import Path

from tools.lib.sql_client import SqlClient

_PROJECT_ROOT = Path(__file__).parent.parent.parent
_SQL_PATH = _PROJECT_ROOT / "solutions/erp_specialist/planowanie_produkcji_pw_otorowo_produkcja.sql"


def _strip_comments(sql: str) -> str:
    lines = [ln for ln in sql.splitlines() if not ln.lstrip().startswith("--")]
    return "\n".join(lines)


def fetch_produced(year: int) -> dict[str, float]:
    """Pobiera przyjętą produkcję PW Otorowo dla danego roku.

    Zwraca dict[czni_kod, suma_qty].
    Rzuca RuntimeError jeśli zapytanie do ERP nie powiedzie się.
    """
    sql_template = _strip_comments(_SQL_PATH.read_text(encoding="utf-8"))
    sql = sql_template.replace("= 2025", f"= {int(year)}")
    result = SqlClient().execute(sql, inject_top=None)
    if not result["ok"]:
        raise RuntimeError(result["error"]["message"])
    cols = result["columns"]
    rows = result["rows"]
    return {
        str(row[cols.index("Czni_Kod")]): float(row[cols.index("Suma_Qty")] or 0)
        for row in rows
        if row[cols.index("Czni_Kod")]
    }
