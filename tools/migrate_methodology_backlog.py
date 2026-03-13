"""One-time migration: methodology_backlog.md active items → mrowisko.db."""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from tools.lib.agent_bus import AgentBus

BACKLOG_PATH = Path("documents/methodology/methodology_backlog.md")
DB_PATH = "mrowisko.db"


def extract_active(text: str) -> list[str]:
    match = re.search(r"## Aktywne\n(.*?)## Archiwum", text, re.DOTALL)
    if not match:
        return []
    section = match.group(1).strip()
    items = re.split(r"\n(?=### )", section)
    return [i.strip() for i in items if i.strip().startswith("###")]


text = BACKLOG_PATH.read_text(encoding="utf-8")
items = extract_active(text)
bus = AgentBus(db_path=DB_PATH)

for item in items:
    title = item.splitlines()[0]
    state_id = bus.write_state(
        role="metodolog",
        type="backlog_item",
        content=item,
        metadata={"migrated_from": str(BACKLOG_PATH)},
    )
    print(f"  [{state_id}] {title}")

print(f"\nMigrated {len(items)} items.")
