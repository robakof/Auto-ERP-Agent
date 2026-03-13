"""Migrate existing progress log .md files into session_log table."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from tools.lib.agent_bus import AgentBus

LOGS = [
    ("developer",     "documents/dev/progress_log.md"),
    ("metodolog",     "documents/methodology/progress_log.md"),
    ("metodolog",     "documents/methodology/methodology_progress.md"),
    ("erp_specialist","solutions/bi/Rezerwacje/Rezerwacje_progress.md"),
    ("erp_specialist","solutions/bi/KntKarty/KntKarty_progress.md"),
    ("erp_specialist","solutions/bi/ZamNag/ZamNag_progress.md"),
    ("erp_specialist","solutions/bi/Rozrachunki/Rozrachunki_progress.md"),
]

bus = AgentBus()

for role, path in LOGS:
    p = Path(path)
    if not p.exists():
        print(f"  SKIP  {path}")
        continue
    content = p.read_text(encoding="utf-8")
    lid = bus.add_session_log(role=role, content=content)
    print(f"  [{lid}] {role}: {path}")

print("\nGotowe")
