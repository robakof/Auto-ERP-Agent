"""Markdown renderers for mrowisko.db views."""

from datetime import date
from pathlib import Path


def render_backlog_md(data: list[dict], title: str, output: Path) -> None:
    """Backlog md: summary tables grouped by effort/value, then detailed sections."""
    today = date.today().strftime("%Y-%m-%d")
    lines = [f"# {title} — {today}\n", f"*{len(data)} pozycji*\n", "---\n"]

    def table_rows(items):
        rows = ["| id | tytuł | obszar | wartość | effort |",
                "|----|-------|--------|---------|--------|"]
        for r in items:
            rows.append(f"| {r.get('id','')} | {r.get('title','')} | {r.get('area','')} | {r.get('value','')} | {r.get('effort','')} |")
        return rows

    groups = [
        ("Szybkie strzały (wysoka wartość, mała praca)",
         [r for r in data if r.get("value") == "wysoka" and r.get("effort") == "mala"]),
        ("Wysoka wartość, średnia praca",
         [r for r in data if r.get("value") == "wysoka" and r.get("effort") == "srednia"]),
        ("Wysoka wartość, duża praca",
         [r for r in data if r.get("value") == "wysoka" and r.get("effort") == "duza"]),
        ("Średnia wartość, mała praca",
         [r for r in data if r.get("value") == "srednia" and r.get("effort") == "mala"]),
        ("Średnia wartość, średnia/duża praca",
         [r for r in data if r.get("value") == "srednia" and r.get("effort") in ("srednia", "duza")]),
        ("Pozostałe",
         [r for r in data if r.get("value") not in ("wysoka", "srednia") or r.get("effort") not in ("mala", "srednia", "duza")]),
    ]

    for heading, items in groups:
        if not items:
            continue
        lines.append(f"## {heading}\n")
        lines.extend(table_rows(items))
        lines.append("")

    lines.append("---\n")
    lines.append("## Szczegóły\n")

    for row in data:
        item_id = row.get("id")
        item_title = row.get("title", "")
        lines.append(f"### [{item_id}] {item_title}")
        meta = []
        for col in ["area", "value", "effort", "status", "created_at"]:
            val = row.get(col)
            if val:
                if col == "created_at":
                    val = str(val)[:10]
                meta.append(f"**{col}:** {val}")
        if meta:
            lines.append("  ".join(meta))
        content = (row.get("content") or "").strip()
        if content:
            lines.append(f"\n{content}")
        lines.append("")

    output.write_text("\n".join(lines), encoding="utf-8")


def render_suggestions_md(data: list[dict], title: str, output: Path) -> None:
    """Suggestions md: table at top (grouped by type), full content sections below."""
    today = date.today().strftime("%Y-%m-%d")
    lines = [f"# {title} — {today}\n", f"*{len(data)} sugestii*\n", "---\n"]

    TYPE_ORDER = ["rule", "tool", "discovery", "observation"]
    TYPE_LABELS = {
        "rule": "Zasady (rule)",
        "tool": "Narzędzia (tool)",
        "discovery": "Odkrycia (discovery)",
        "observation": "Obserwacje (observation)",
    }

    def table_rows(items):
        rows = [
            "| id | autor | tytuł | status | data |",
            "|----|-------|-------|--------|------|",
        ]
        for r in items:
            date_val = str(r.get("created_at", ""))[:10]
            rows.append(
                f"| {r.get('id','')} | {r.get('author','')} "
                f"| {r.get('title','')} | {r.get('status','')} | {date_val} |"
            )
        return rows

    grouped = {t: [r for r in data if r.get("type") == t] for t in TYPE_ORDER}
    other = [r for r in data if r.get("type") not in TYPE_ORDER]
    if other:
        grouped["observation"] = grouped.get("observation", []) + other

    for type_key in TYPE_ORDER:
        items = grouped.get(type_key, [])
        if not items:
            continue
        lines.append(f"## {TYPE_LABELS[type_key]}\n")
        lines.extend(table_rows(items))
        lines.append("")

    lines.append("---\n")
    lines.append("## Treści\n")

    for type_key in TYPE_ORDER:
        items = grouped.get(type_key, [])
        if not items:
            continue
        lines.append(f"### {TYPE_LABELS[type_key]}\n")
        for row in items:
            sid = row.get("id")
            stitle = row.get("title") or ""
            author = row.get("author", "")
            status = row.get("status", "")
            date_val = str(row.get("created_at", ""))[:10]
            lines.append(f"#### [{sid}] {stitle}")
            lines.append(f"**autor:** {author}  **status:** {status}  **data:** {date_val}")
            content = (row.get("content") or "").strip()
            if content:
                lines.append(f"\n{content}")
            lines.append("")

    output.write_text("\n".join(lines), encoding="utf-8")


def render_md(data: list[dict], columns: list[str], title: str, output: Path) -> None:
    """Human-readable md: each item as a section with metadata + content (if present)."""
    META_COLS = ["id", "area", "value", "effort", "status", "created_at", "sender", "author", "role"]
    CONTENT_COLS = ["content", "title"]

    lines = [f"# {title} — {len(data)} pozycji\n"]
    for row in data:
        item_title = str(row.get("title") or row.get("id") or "")
        item_id = row.get("id")
        heading = f"## [{item_id}] {item_title}" if item_id and item_title and item_title != str(item_id) else f"## {item_title or item_id}"
        lines.append(heading)

        meta = []
        for col in META_COLS:
            if col in columns and row.get(col) is not None:
                val = str(row[col])
                if col == "created_at":
                    val = val[:10]
                meta.append(f"**{col}:** {val}")
        if meta:
            lines.append("  ".join(meta))

        content = row.get("content") or ""
        if content and "content" not in columns:
            lines.append(f"\n{content.strip()}")
        elif content:
            lines.append(f"\n{content.strip()}")

        lines.append("\n---\n")

    output.write_text("\n".join(lines), encoding="utf-8")
