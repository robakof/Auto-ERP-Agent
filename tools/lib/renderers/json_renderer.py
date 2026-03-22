"""JSON renderer for mrowisko.db views."""

import json
from pathlib import Path


def render_json(data: list[dict], title: str, output: Path) -> None:
    """Render data as JSON with metadata envelope."""
    payload = {"title": title, "data": data, "count": len(data)}
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
