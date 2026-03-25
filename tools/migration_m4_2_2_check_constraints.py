#!/usr/bin/env python3
"""
M4.2.2 CHECK Constraints Migration

Adds CHECK constraints to enforce valid enum values at database level.
Fail fast on write — prevent invalid enum values from being inserted.

Usage:
  python tools/migration_m4_2_2_check_constraints.py           # dry run
  python tools/migration_m4_2_2_check_constraints.py --execute # apply migration
"""

import json
import sqlite3
import sys
from pathlib import Path

DB_PATH = "mrowisko.db"

# CHECK constraint definitions (table, column, valid values)
CHECK_CONSTRAINTS = [
    {
        "table": "messages",
        "column": "type",
        "values": ["direct", "suggestion", "task", "escalation", "flag_human", "info", "handoff"],
        "comment": "Legacy aliases (flag_human, info) included for backward compatibility"
    },
    {
        "table": "suggestions",
        "column": "status",
        "values": ["open", "implemented", "rejected", "deferred", "in_backlog"],
        "comment": "Legacy alias (in_backlog) included for backward compatibility"
    },
    {
        "table": "backlog",
        "column": "value",
        "values": ["wysoka", "srednia", "niska"],
        "comment": "Business value priority"
    },
    {
        "table": "backlog",
        "column": "effort",
        "values": ["mala", "srednia", "duza"],
        "comment": "Estimated effort"
    },
    {
        "table": "backlog",
        "column": "status",
        "values": ["planned", "in_progress", "done", "cancelled", "deferred"],
        "comment": "Task status"
    },
]


def print_json(obj):
    print(json.dumps(obj, ensure_ascii=True, indent=2))


def check_constraint_exists(conn, table, column):
    """Check if table already has CHECK constraint on column."""
    # SQLite doesn't have easy way to query constraints, so we check schema
    schema = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone()
    if schema:
        sql = schema[0]
        # Simple heuristic: look for CHECK in column definition
        return "CHECK" in sql and f"{column}" in sql
    return False


def create_temp_table_sql(conn, table, constraint_defs):
    """Generate CREATE TABLE statement for temp table with CHECK constraints.

    Args:
        constraint_defs: List of constraint definitions for this table
    """
    # Get current schema
    schema = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone()
    if not schema:
        raise ValueError(f"Table {table} not found")

    original_sql = schema[0]

    # Generate CHECK constraint clauses for all constraints
    check_clauses = []
    for constraint_def in constraint_defs:
        values_str = ", ".join(f"'{v}'" for v in constraint_def['values'])
        check_clause = f"CHECK ({constraint_def['column']} IN ({values_str}))"
        check_clauses.append(check_clause)

    # Insert all CHECK constraints before closing parenthesis
    # Find last closing paren (end of column definitions)
    last_paren_idx = original_sql.rfind(")")
    if last_paren_idx == -1:
        raise ValueError(f"Invalid table schema for {table}")

    # Insert all check constraints
    constraints_str = ",\n  ".join(check_clauses)
    new_sql = original_sql[:last_paren_idx].rstrip() + f",\n  {constraints_str}\n)"

    # Replace table name with temp table name
    new_sql = new_sql.replace(f"CREATE TABLE {table}", f"CREATE TABLE {table}_new", 1)

    return new_sql


def apply_constraints(conn, table, constraint_defs):
    """Apply CHECK constraints to table using SQLite's table recreation method.

    Args:
        constraint_defs: List of constraint definitions for this table
    """

    # 0. Cleanup temp table if exists (from previous failed migration)
    conn.execute(f"DROP TABLE IF EXISTS {table}_new")

    # 1. Create new table with CHECK constraints
    new_table_sql = create_temp_table_sql(conn, table, constraint_defs)
    conn.execute(new_table_sql)

    # 2. Copy data from old table to new table
    columns_query = f"PRAGMA table_info({table})"
    columns = [row[1] for row in conn.execute(columns_query).fetchall()]
    columns_str = ", ".join(columns)

    copy_sql = f"INSERT INTO {table}_new ({columns_str}) SELECT {columns_str} FROM {table}"
    conn.execute(copy_sql)

    # 3. Drop old table
    conn.execute(f"DROP TABLE {table}")

    # 4. Rename new table to original name
    conn.execute(f"ALTER TABLE {table}_new RENAME TO {table}")


def main():
    execute_mode = "--execute" in sys.argv

    if not Path(DB_PATH).exists():
        print_json({"ok": False, "error": f"Database not found: {DB_PATH}"})
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)

    try:
        # Group constraints by table
        constraints_by_table = {}
        for constraint in CHECK_CONSTRAINTS:
            table = constraint['table']
            if table not in constraints_by_table:
                constraints_by_table[table] = []
            constraints_by_table[table].append(constraint)

        # Validate constraints per table
        migrations = []

        for table, table_constraints in constraints_by_table.items():
            table_migration = {
                "table": table,
                "constraints": [],
                "status": "ready"
            }

            for constraint in table_constraints:
                column = constraint['column']

                # Check if constraint already exists
                if check_constraint_exists(conn, table, column):
                    table_migration['constraints'].append({
                        "column": column,
                        "status": "skip",
                        "reason": "CHECK constraint already exists"
                    })
                    continue

                # Verify data is valid before adding constraint
                values_str = ", ".join(f"'{v}'" for v in constraint['values'])
                invalid_check = f"""
                    SELECT COUNT(*) FROM {table}
                    WHERE {column} IS NOT NULL AND {column} NOT IN ({values_str})
                """
                invalid_count = conn.execute(invalid_check).fetchone()[0]

                if invalid_count > 0:
                    table_migration['constraints'].append({
                        "column": column,
                        "status": "error",
                        "reason": f"Found {invalid_count} invalid values",
                        "invalid_count": invalid_count
                    })
                    table_migration['status'] = "error"
                    continue

                table_migration['constraints'].append({
                    "column": column,
                    "values": constraint['values'],
                    "comment": constraint['comment'],
                    "status": "ready"
                })

            migrations.append(table_migration)

        # Show migrations
        print_json({
            "ok": True,
            "mode": "dry_run" if not execute_mode else "execute",
            "migrations": migrations
        })

        # Execute if --execute flag
        if execute_mode:
            print("\nApplying migrations...", file=sys.stderr)

            for table, table_constraints in constraints_by_table.items():
                # Find migration status for this table
                table_migration = next(m for m in migrations if m['table'] == table)

                if table_migration['status'] == "error":
                    print(f"  X {table}: SKIPPED (validation errors)", file=sys.stderr)
                    continue

                # Get ready constraints for this table
                ready_constraints = [
                    c for c in table_constraints
                    if not check_constraint_exists(conn, table, c['column'])
                ]

                if not ready_constraints:
                    print(f"  - {table}: skipped (all constraints exist)", file=sys.stderr)
                    continue

                # Apply all constraints for this table in one operation
                apply_constraints(conn, table, ready_constraints)
                constraint_names = ", ".join(c['column'] for c in ready_constraints)
                print(f"  ✓ {table}: CHECK constraints added ({constraint_names})", file=sys.stderr)

            conn.commit()
            print("\n✓ Migration complete. Run enum_audit.py to verify.", file=sys.stderr)
        else:
            print("\nDry run complete. Use --execute to apply migration.", file=sys.stderr)

    except Exception as e:
        conn.rollback()
        print_json({"ok": False, "error": str(e)})
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
