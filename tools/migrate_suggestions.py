"""One-time migration: *_suggestions.md files → mrowisko.db (state table).

Usage:
    python tools/migrate_suggestions.py [--dry-run]
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.lib.agent_bus import AgentBus

DB_PATH = "mrowisko.db"

FILES = [
    {
        "path": Path("documents/methodology/methodology_suggestions.md"),
        "role": "metodolog",
    },
]


def extract_entries(text: str) -> list[str]:
    """Split suggestions file into individual entries by ## [date] heading."""
    # Split on ## [date] or ## heading (skip ## Archiwum and header sections)
    entries = re.split(r"\n(?=## \[)", text)
    result = []
    for entry in entries:
        entry = entry.strip()
        if not entry or entry.startswith("#") and not entry.startswith("## ["):
            continue
        if entry.startswith("## ["):
            result.append(entry)
    return result


def main():
    parser = argparse.ArgumentParser(description="Migrate suggestions .md to mrowisko.db")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    bus = None if args.dry_run else AgentBus(db_path=DB_PATH)
    total = 0

    for spec in FILES:
        path = spec["path"]
        role = spec["role"]

        if not path.exists():
            print(f"SKIP (not found): {path}")
            continue

        text = path.read_text(encoding="utf-8")
        entries = extract_entries(text)

        print(f"\n{path} ({role}): {len(entries)} entries")
        for i, entry in enumerate(entries, 1):
            title = entry.splitlines()[0][:80]
            print(f"  [{i}] {title}")
            if not args.dry_run:
                bus.write_state(
                    role=role,
                    type="reflection",
                    content=entry,
                    metadata={"migrated_from": str(path)},
                )
            total += 1

    print(f"\nTotal: {total} entries {'(dry-run)' if args.dry_run else 'migrated'}.")


if __name__ == "__main__":
    main()
