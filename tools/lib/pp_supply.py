"""pp_supply.py — Stany magazynowe surowców OTOR_SUR (MAG_GIDNumer=4)."""
from pathlib import Path

from tools.lib.sql_client import SqlClient

_PROJECT_ROOT = Path(__file__).parent.parent.parent
_SQL_PATH = _PROJECT_ROOT / "solutions/erp_specialist/planowanie_produkcji_stany_mag_otorowo_surowce.sql"


def _strip_comments(sql: str) -> str:
    lines = [ln for ln in sql.splitlines() if not ln.lstrip().startswith("--")]
    return "\n".join(lines)


def fetch_supply() -> dict[str, float]:
    """Zwraca stany surowców OTOR_SUR jako {surowiec_kod: stan}."""
    sql = _strip_comments(_SQL_PATH.read_text(encoding="utf-8"))
    result = SqlClient().execute(sql, inject_top=None)
    if not result["ok"]:
        raise RuntimeError(result["error"]["message"])
    cols = result["columns"]
    rows = [dict(zip(cols, row)) for row in result["rows"]]
    return {r["Towar_Kod"]: float(r["Stan"]) for r in rows if r.get("Towar_Kod")}
