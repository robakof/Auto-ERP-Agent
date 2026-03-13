"""One-time migration: backlog.md active items → mrowisko.db (state table).

Usage:
    python tools/migrate_backlog.py [--dry-run]

Reads backlog.md, extracts active items (between ## Aktywne and ## Archiwum),
writes each as state(role=developer, type=backlog_item).
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.lib.agent_bus import AgentBus

BACKLOG_PATH = Path("documents/dev/backlog.md")
DB_PATH = "mrowisko.db"


def extract_active_items(text: str) -> list[dict]:
    """Extract active backlog items between ## Aktywne and ## Archiwum."""
    # Get section between ## Aktywne and ## Archiwum
    match = re.search(r"## Aktywne\n(.*?)## Archiwum", text, re.DOTALL)
    if not match:
        print("ERROR: Could not find ## Aktywne section", file=sys.stderr)
        return []

    section = match.group(1).strip()

    # Split on ### headers
    raw_items = re.split(r"\n(?=### )", section)
    items = []
    for raw in raw_items:
        raw = raw.strip()
        if not raw or not raw.startswith("###"):
            continue

        # Extract title from ### [Obszar] Tytuł
        title_match = re.match(r"### (.+)", raw)
        title = title_match.group(1).strip() if title_match else "?"

        # Extract metadata fields
        area_match = re.search(r"\*\*Obszar.*?\*\*.*?(\w+)", raw)
        value_match = re.search(r"\*\*Wartość:\*\*\s*(\w+)", raw)
        effort_match = re.search(r"\*\*Pracochłonność:\*\*\s*(.+)", raw)
        source_match = re.search(r"\*\*Źródło:\*\*\s*(.+)", raw)
        session_match = re.search(r"\*\*Sesja:\*\*\s*(.+)", raw)

        metadata = {
            "value": value_match.group(1).strip() if value_match else None,
            "effort": effort_match.group(1).strip() if effort_match else None,
            "source": source_match.group(1).strip() if source_match else None,
            "session": session_match.group(1).strip() if session_match else None,
            "migrated_from": "backlog.md",
        }

        items.append({"title": title, "content": raw, "metadata": metadata})

    return items


def main():
    parser = argparse.ArgumentParser(description="Migrate backlog.md to mrowisko.db")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print items without writing to DB")
    args = parser.parse_args()

    text = BACKLOG_PATH.read_text(encoding="utf-8")
    items = extract_active_items(text)

    if not items:
        print("No active items found.")
        return

    print(f"Found {len(items)} active backlog items.")

    if args.dry_run:
        for i, item in enumerate(items, 1):
            print(f"\n[{i}] {item['title']}")
        return

    bus = AgentBus(db_path=DB_PATH)
    for item in items:
        state_id = bus.write_state(
            role="developer",
            type="backlog_item",
            content=item["content"],
            metadata=item["metadata"],
        )
        print(f"  [{state_id}] {item['title']}")

    print(f"\nMigrated {len(items)} items to {DB_PATH}.")


if __name__ == "__main__":
    main()
