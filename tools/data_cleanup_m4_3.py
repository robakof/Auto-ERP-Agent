#!/usr/bin/env python3
"""
M4.3 Data Cleanup — Invalid enum values cleanup

Cleans up Unicode variants and compound values in backlog table.
Dry run mode by default — use --execute to apply changes.

Usage:
  python tools/data_cleanup_m4_3.py           # dry run (show changes)
  python tools/data_cleanup_m4_3.py --execute # apply changes
"""

import sqlite3
import sys
import json
from pathlib import Path

DB_PATH = "mrowisko.db"

# Cleanup mappings (production → domain model)
CLEANUP_RULES = [
    # backlog.value: Unicode → ASCII
    {
        "table": "backlog",
        "column": "value",
        "from": "średnia",
        "to": "srednia",
        "reason": "Unicode variant → ASCII"
    },

    # backlog.effort: Unicode → ASCII
    {
        "table": "backlog",
        "column": "effort",
        "from": "mała",
        "to": "mala",
        "reason": "Unicode variant → ASCII"
    },
    {
        "table": "backlog",
        "column": "effort",
        "from": "średnia",
        "to": "srednia",
        "reason": "Unicode variant → ASCII"
    },

    # backlog.effort: Compound → single enum
    {
        "table": "backlog",
        "column": "effort",
        "from": "mała-średnia",
        "to": "srednia",
        "reason": "Compound value → srednia"
    },
    {
        "table": "backlog",
        "column": "effort",
        "from": "mała–średnia",
        "to": "srednia",
        "reason": "Compound value (em-dash) → srednia"
    },

    # backlog.effort: Ambiguous (backlog #7, status=done → mala retrospectively)
    {
        "table": "backlog",
        "column": "effort",
        "from": "mała (opcja 3) / duża (opcja 1)",
        "to": "mala",
        "reason": "Backlog #7 (done) → mala retrospectively"
    },
]


def print_json(obj):
    print(json.dumps(obj, ensure_ascii=True, indent=2))


def get_affected_records(conn, rule):
    """Get records that would be affected by this cleanup rule."""
    query = f"""
        SELECT id, {rule['column']}
        FROM {rule['table']}
        WHERE {rule['column']} = ?
    """
    rows = conn.execute(query, (rule['from'],)).fetchall()
    return [{"id": r[0], "current_value": r[1]} for r in rows]


def apply_cleanup(conn, rule):
    """Apply cleanup rule to database."""
    query = f"""
        UPDATE {rule['table']}
        SET {rule['column']} = ?
        WHERE {rule['column']} = ?
    """
    cursor = conn.execute(query, (rule['to'], rule['from']))
    return cursor.rowcount


def main():
    # Parse args
    execute_mode = "--execute" in sys.argv

    if not Path(DB_PATH).exists():
        print_json({"ok": False, "error": f"Database not found: {DB_PATH}"})
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)

    try:
        # Dry run: show what would be changed
        changes = []
        total_affected = 0

        for rule in CLEANUP_RULES:
            affected = get_affected_records(conn, rule)
            if affected:
                changes.append({
                    "rule": f"{rule['table']}.{rule['column']}: '{rule['from']}' → '{rule['to']}'",
                    "reason": rule['reason'],
                    "affected_count": len(affected),
                    "records": affected
                })
                total_affected += len(affected)

        if not changes:
            print_json({
                "ok": True,
                "mode": "dry_run" if not execute_mode else "execute",
                "message": "No cleanup needed — all enum values are valid",
                "changes": []
            })
            sys.exit(0)

        # Show changes
        print_json({
            "ok": True,
            "mode": "dry_run" if not execute_mode else "execute",
            "total_affected": total_affected,
            "changes": changes
        })

        # Execute if --execute flag
        if execute_mode:
            print("\nApplying changes...", file=sys.stderr)

            for rule in CLEANUP_RULES:
                affected_count = apply_cleanup(conn, rule)
                if affected_count > 0:
                    print(f"  ✓ {rule['table']}.{rule['column']}: {affected_count} records updated", file=sys.stderr)

            conn.commit()
            print("\n✓ Cleanup complete. Run enum_audit.py to verify.", file=sys.stderr)
        else:
            print("\nDry run complete. Use --execute to apply changes.", file=sys.stderr)
            sys.exit(0)

    except Exception as e:
        conn.rollback()
        print_json({"ok": False, "error": str(e)})
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
