"""pp_demand.py — Pobieranie zamówień CZNI z ERP (ZaN_Stan=2)."""
from pathlib import Path

from tools.lib.sql_client import SqlClient

_PROJECT_ROOT = Path(__file__).parent.parent.parent
_SQL_PATH = _PROJECT_ROOT / "solutions/erp_specialist/planowanie_produkcji_zamowienia_niepotwierdzone.sql"


def _strip_comments(sql: str) -> str:
    lines = [ln for ln in sql.splitlines() if not ln.lstrip().startswith("--")]
    return "\n".join(lines)


def _year_of(d) -> int:
    if hasattr(d, "year"):
        return d.year
    raise TypeError(f"Nieoczekiwany typ daty: {type(d)}")


def fetch_demand(year: int) -> list[dict]:
    """Pobiera zamówienia CZNI dla danego roku z ERP. Zwraca listę dict."""
    sql = _strip_comments(_SQL_PATH.read_text(encoding="utf-8"))
    result = SqlClient().execute(sql, inject_top=None)
    if not result["ok"]:
        raise RuntimeError(result["error"]["message"])
    cols = result["columns"]
    rows = [dict(zip(cols, row)) for row in result["rows"]]
    return [
        r for r in rows
        if r.get("Data_Realizacji") is not None
        and _year_of(r["Data_Realizacji"]) == year
    ]
