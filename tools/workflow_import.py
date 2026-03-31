#!/usr/bin/env python3
"""Import workflow .md (strict 04R format) into mrowisko.db.

Parses YAML header → workflow_definitions,
       ## Step N: ... → workflow_steps,
       ## Decision Point N: ... → workflow_decisions,
       ### Exit Gate → workflow_exit_gates.

Usage:
    py tools/workflow_import.py workflows/workflow_foo.md
    py tools/workflow_import.py --all                       # import all from workflows/
    py tools/workflow_import.py --all --dir custom/path     # custom directory
    py tools/workflow_import.py --dry-run workflows/foo.md  # parse only, no DB write
"""

import json
import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

DB_PATH = "mrowisko.db"
DEFAULT_WORKFLOWS_DIR = "workflows"


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def parse_yaml_header(text: str) -> dict | None:
    """Extract YAML front-matter between --- delimiters."""
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return None
    raw = m.group(1)
    result = {}
    for line in raw.split("\n"):
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        if ":" in line:
            key, _, val = line.partition(":")
            val = val.strip().strip('"').strip("'")
            if val:
                result[key.strip()] = val
    return result if result.get("workflow_id") else None


def parse_steps(text: str) -> list[dict]:
    """Parse ## Step N: ... or ### Step N: ... blocks into list of step dicts."""
    pattern = re.compile(
        r"^#{2,3}\s+Step\s+\d+:\s+(.+?)$",
        re.MULTILINE,
    )
    positions = [(m.start(), m.group(1).strip()) for m in pattern.finditer(text)]
    steps = []
    for idx, (pos, _title) in enumerate(positions):
        end = positions[idx + 1][0] if idx + 1 < len(positions) else len(text)
        block = text[pos:end]
        step = _parse_step_block(block, sort_order=idx + 1)
        if step:
            steps.append(step)
    return steps


def _parse_step_block(block: str, sort_order: int) -> dict | None:
    """Parse a single step block into a dict."""
    def field(name: str) -> str:
        m = re.search(rf"\*\*{name}:\*\*\s*(.+)", block)
        return m.group(1).strip() if m else ""

    step_id = field("step_id")
    if not step_id:
        return None

    action = field("action")
    tool = field("tool")
    command = field("command").strip("`")
    verification_raw = field("verification")
    next_step_raw = field("next_step")

    # Parse verification into type + value
    v_type, v_value = _parse_verification(verification_raw)

    # Parse on_failure block
    on_fail = _parse_on_failure(block)

    # Parse next_step: "step_x (if PASS), action (if FAIL)"
    next_pass, next_fail = _parse_next_step(next_step_raw)

    # Detect HANDOFF
    is_handoff = 1 if re.search(r"→\s*HANDOFF:", block) else 0
    handoff_to = ""
    if is_handoff:
        hm = re.search(r"→\s*HANDOFF:\s*(\w+)", block)
        handoff_to = hm.group(1) if hm else ""

    # Detect phase from preceding ## Phase header
    phase = ""

    return {
        "step_id": step_id,
        "phase": phase,
        "sort_order": sort_order,
        "action": action,
        "tool": tool,
        "command": command,
        "verification_type": v_type,
        "verification_value": v_value,
        "on_failure_retry": on_fail.get("retry", 0),
        "on_failure_skip": on_fail.get("skip", 0),
        "on_failure_escalate": on_fail.get("escalate", 1),
        "on_failure_reason": on_fail.get("reason", ""),
        "next_step_pass": next_pass,
        "next_step_fail": next_fail,
        "is_handoff": is_handoff,
        "handoff_to": handoff_to,
    }


def _parse_verification(raw: str) -> tuple[str, str]:
    """Map verification string to (type, value)."""
    if not raw:
        return "manual", ""
    known = ["file_exists", "file_not_empty", "test_pass", "commit_exists",
             "message_sent", "git_clean"]
    for t in known:
        if raw.startswith(t):
            value = raw[len(t):].strip()
            return t, value
    return "manual", raw


def _parse_on_failure(block: str) -> dict:
    """Parse on_failure sub-fields from block."""
    result = {"retry": 0, "skip": 0, "escalate": 1, "reason": ""}
    for key in ["retry", "skip", "escalate"]:
        m = re.search(rf"-\s*{key}:\s*(yes|no)", block, re.IGNORECASE)
        if m:
            result[key] = 1 if m.group(1).lower() == "yes" else 0
    m = re.search(r'-\s*reason:\s*"([^"]*)"', block)
    if m:
        result["reason"] = m.group(1)
    return result


def _parse_next_step(raw: str) -> tuple[str, str]:
    """Parse 'step_x (if PASS), action (if FAIL)' into (pass, fail)."""
    if not raw:
        return "", ""
    pass_m = re.search(r"(\S+)\s*\(if PASS\)", raw)
    fail_m = re.search(r"(\S+)\s*\(if FAIL\)", raw)
    return (
        pass_m.group(1).strip(",") if pass_m else raw.split(",")[0].strip(),
        fail_m.group(1).strip(",") if fail_m else "",
    )


def parse_decisions(text: str) -> list[dict]:
    """Parse ## Decision Point N: ... or ### Decision Point N: ... blocks."""
    pattern = re.compile(
        r"^##?#?\s+Decision\s+Point\s+\d+:\s+(.+?)$",
        re.MULTILINE,
    )
    positions = [(m.start(), m.group(1).strip()) for m in pattern.finditer(text)]
    decisions = []
    for idx, (pos, _title) in enumerate(positions):
        end = positions[idx + 1][0] if idx + 1 < len(positions) else len(text)
        block = text[pos:end]
        dec = _parse_decision_block(block)
        if dec:
            decisions.append(dec)
    return decisions


def _parse_decision_block(block: str) -> dict | None:
    """Parse a single decision block."""
    def field(name: str) -> str:
        m = re.search(rf"\*\*{name}:\*\*\s*(.+)", block)
        return m.group(1).strip() if m else ""

    decision_id = field("decision_id")
    if not decision_id:
        return None
    return {
        "decision_id": decision_id,
        "condition": field("condition"),
        "path_true": field("path_true"),
        "path_false": field("path_false"),
        "default_action": field("default"),
    }


def parse_exit_gates(text: str) -> list[dict]:
    """Parse ### Exit Gate sections with - **item_id:** condition items."""
    gates = []
    # Find phase context for each exit gate
    phase_pattern = re.compile(r"^##\s+Phase\s+\d+:\s+(.+?)$", re.MULTILINE)
    gate_pattern = re.compile(r"^###\s+Exit\s+Gate", re.MULTILINE)

    phases = [(m.start(), m.group(1).strip()) for m in phase_pattern.finditer(text)]
    gate_positions = [m.start() for m in gate_pattern.finditer(text)]

    for gate_pos in gate_positions:
        # Determine which phase this gate belongs to
        phase = ""
        for p_pos, p_name in reversed(phases):
            if p_pos < gate_pos:
                phase = p_name
                break

        # Extract gate block (until next ## or end)
        next_section = re.search(r"\n##\s", text[gate_pos + 1:])
        end = gate_pos + 1 + next_section.start() if next_section else len(text)
        block = text[gate_pos:end]

        # Parse items: - **item_id:** condition
        for m in re.finditer(r"-\s+\*\*(\w+):\*\*\s+(.+)", block):
            gates.append({
                "phase": phase,
                "item_id": m.group(1),
                "condition": m.group(2).strip(),
            })
    return gates


def assign_phases(steps: list[dict], text: str) -> list[dict]:
    """Assign phase names to steps based on ## Phase headers in text."""
    phase_pattern = re.compile(r"^##\s+Phase\s+\d+:\s+(.+?)$", re.MULTILINE)
    step_pattern = re.compile(r"^#{2,3}\s+Step\s+\d+:", re.MULTILINE)

    phases = [(m.start(), m.group(1).strip()) for m in phase_pattern.finditer(text)]
    step_positions = [m.start() for m in step_pattern.finditer(text)]

    for i, pos in enumerate(step_positions):
        phase = ""
        for p_pos, p_name in reversed(phases):
            if p_pos < pos:
                phase = p_name
                break
        if i < len(steps):
            steps[i]["phase"] = phase
    return steps


# ---------------------------------------------------------------------------
# Full parse
# ---------------------------------------------------------------------------

def parse_workflow(filepath: Path) -> dict:
    """Parse a strict-format workflow .md file. Returns structured dict or error."""
    text = filepath.read_text(encoding="utf-8")
    header = parse_yaml_header(text)
    if not header:
        return {"ok": False, "error": "Missing or invalid YAML header (no workflow_id)"}

    workflow_id = header["workflow_id"]
    version = header.get("version", "1.0")

    steps = parse_steps(text)
    if not steps:
        return {
            "ok": False,
            "warning": f"No strict steps found in {filepath.name} — skipping (human-readable?)",
            "workflow_id": workflow_id,
        }

    steps = assign_phases(steps, text)
    decisions = parse_decisions(text)
    exit_gates = parse_exit_gates(text)

    return {
        "ok": True,
        "workflow_id": workflow_id,
        "version": version,
        "owner_role": header.get("owner_role", ""),
        "trigger_desc": header.get("trigger", ""),
        "steps": steps,
        "decisions": decisions,
        "exit_gates": exit_gates,
    }


# ---------------------------------------------------------------------------
# DB upsert
# ---------------------------------------------------------------------------

def upsert_workflow(conn: sqlite3.Connection, data: dict) -> dict:
    """Insert or replace workflow definition + steps + decisions + exit gates."""
    wf_id = data["workflow_id"]
    version = data["version"]

    # Delete existing data for this workflow+version (upsert = delete + insert)
    conn.execute("DELETE FROM workflow_exit_gates WHERE workflow_id=? AND workflow_version=?",
                 (wf_id, version))
    conn.execute("DELETE FROM workflow_decisions WHERE workflow_id=? AND workflow_version=?",
                 (wf_id, version))
    conn.execute("DELETE FROM workflow_steps WHERE workflow_id=? AND workflow_version=?",
                 (wf_id, version))
    conn.execute("DELETE FROM workflow_definitions WHERE workflow_id=? AND version=?",
                 (wf_id, version))

    # Insert definition
    conn.execute(
        "INSERT INTO workflow_definitions (workflow_id, version, owner_role, trigger_desc) VALUES (?,?,?,?)",
        (wf_id, version, data.get("owner_role", ""), data.get("trigger_desc", "")),
    )

    # Insert steps
    for s in data["steps"]:
        conn.execute(
            """INSERT INTO workflow_steps
               (workflow_id, workflow_version, step_id, phase, sort_order, action,
                tool, command, verification_type, verification_value,
                on_failure_retry, on_failure_skip, on_failure_escalate, on_failure_reason,
                next_step_pass, next_step_fail, is_handoff, handoff_to)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (wf_id, version, s["step_id"], s["phase"], s["sort_order"], s["action"],
             s["tool"], s["command"], s["verification_type"], s["verification_value"],
             s["on_failure_retry"], s["on_failure_skip"], s["on_failure_escalate"],
             s["on_failure_reason"], s["next_step_pass"], s["next_step_fail"],
             s["is_handoff"], s["handoff_to"]),
        )

    # Insert decisions
    for d in data["decisions"]:
        conn.execute(
            """INSERT INTO workflow_decisions
               (workflow_id, workflow_version, decision_id, condition, path_true, path_false, default_action)
               VALUES (?,?,?,?,?,?,?)""",
            (wf_id, version, d["decision_id"], d["condition"],
             d["path_true"], d["path_false"], d.get("default_action", "")),
        )

    # Insert exit gates
    for g in data["exit_gates"]:
        conn.execute(
            """INSERT INTO workflow_exit_gates
               (workflow_id, workflow_version, phase, item_id, condition)
               VALUES (?,?,?,?,?)""",
            (wf_id, version, g["phase"], g["item_id"], g["condition"]),
        )

    conn.commit()
    return {
        "ok": True,
        "workflow_id": wf_id,
        "version": version,
        "steps": len(data["steps"]),
        "decisions": len(data["decisions"]),
        "exit_gates": len(data["exit_gates"]),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def import_file(filepath: Path, db_path: str = DB_PATH, dry_run: bool = False) -> dict:
    """Parse and import a single workflow file."""
    parsed = parse_workflow(filepath)
    if not parsed["ok"]:
        return parsed

    if dry_run:
        return {
            "ok": True,
            "mode": "dry_run",
            "workflow_id": parsed["workflow_id"],
            "version": parsed["version"],
            "steps": len(parsed["steps"]),
            "decisions": len(parsed["decisions"]),
            "exit_gates": len(parsed["exit_gates"]),
        }

    conn = sqlite3.connect(db_path)
    try:
        result = upsert_workflow(conn, parsed)
        return result
    finally:
        conn.close()


def import_all(workflows_dir: str = DEFAULT_WORKFLOWS_DIR,
               db_path: str = DB_PATH,
               dry_run: bool = False) -> dict:
    """Import all workflow_*.md from directory."""
    wf_dir = Path(workflows_dir)
    if not wf_dir.is_dir():
        return {"ok": False, "error": f"Directory not found: {workflows_dir}"}

    files = sorted(wf_dir.glob("workflow_*.md"))
    results = {"imported": [], "skipped": [], "errors": []}

    for f in files:
        r = import_file(f, db_path=db_path, dry_run=dry_run)
        if r.get("ok") and "warning" not in r:
            results["imported"].append(r)
        elif r.get("warning"):
            results["skipped"].append({"file": f.name, "reason": r["warning"]})
        else:
            results["errors"].append({"file": f.name, "error": r.get("error", "unknown")})

    return {
        "ok": True,
        "imported": len(results["imported"]),
        "skipped": len(results["skipped"]),
        "errors": len(results["errors"]),
        "details": results,
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Import strict workflow .md into mrowisko.db")
    parser.add_argument("file", nargs="?", help="Path to workflow .md file")
    parser.add_argument("--all", action="store_true", help="Import all from workflows/")
    parser.add_argument("--dir", default=DEFAULT_WORKFLOWS_DIR, help="Workflows directory")
    parser.add_argument("--db", default=DB_PATH, help="Database path")
    parser.add_argument("--dry-run", action="store_true", help="Parse only, no DB write")
    args = parser.parse_args()

    if args.all:
        result = import_all(workflows_dir=args.dir, db_path=args.db, dry_run=args.dry_run)
    elif args.file:
        result = import_file(Path(args.file), db_path=args.db, dry_run=args.dry_run)
    else:
        parser.print_help()
        sys.exit(1)

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
