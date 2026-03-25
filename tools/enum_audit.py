"""Enum audit tool — proactive enum verification

Per architectural decision #207 (M4.2):
- SELECT DISTINCT all enum columns
- Document findings
- Identify missing values in domain model enums

Usage:
    python tools/enum_audit.py [--db PATH]

Output:
    - Audit report (JSON + human-readable)
    - Missing values per enum type
    - Recommendations for enum updates
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path


def audit_enum_column(conn: sqlite3.Connection, table: str, column: str) -> list[str]:
    """Get distinct values for an enum column."""
    query = f"SELECT DISTINCT {column} FROM {table} WHERE {column} IS NOT NULL ORDER BY {column}"
    cursor = conn.execute(query)
    return [row[0] for row in cursor.fetchall()]


def audit_all_enums(db_path: str) -> dict:
    """Audit all enum columns in database.

    Returns:
        dict with audit results per table/column
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    results = {}

    # messages table
    results["messages"] = {
        "type": audit_enum_column(conn, "messages", "type"),
        "status": audit_enum_column(conn, "messages", "status"),
    }

    # suggestions table
    results["suggestions"] = {
        "type": audit_enum_column(conn, "suggestions", "type"),
        "status": audit_enum_column(conn, "suggestions", "status"),
    }

    # backlog table
    results["backlog"] = {
        "area": audit_enum_column(conn, "backlog", "area"),
        "value": audit_enum_column(conn, "backlog", "value"),
        "effort": audit_enum_column(conn, "backlog", "effort"),
        "status": audit_enum_column(conn, "backlog", "status"),
    }

    conn.close()
    return results


def get_domain_model_enums() -> dict:
    """Get expected values from domain model enums.

    Returns:
        dict with expected enum values per type
    """
    # Import domain model enums
    from core.entities.messaging import (
        BacklogArea,
        BacklogEffort,
        BacklogStatus,
        BacklogValue,
        MessageStatus,
        MessageType,
        SuggestionStatus,
        SuggestionType,
    )

    return {
        "MessageType": [e.value for e in MessageType],
        "MessageStatus": [e.value for e in MessageStatus],
        "SuggestionType": [e.value for e in SuggestionType],
        "SuggestionStatus": [e.value for e in SuggestionStatus],
        "BacklogArea": [e.value for e in BacklogArea],
        "BacklogValue": [e.value for e in BacklogValue],
        "BacklogEffort": [e.value for e in BacklogEffort],
        "BacklogStatus": [e.value for e in BacklogStatus],
    }


def compare_with_domain_model(audit_results: dict, domain_enums: dict) -> dict:
    """Compare audit results with domain model enums.

    Returns:
        dict with missing values and extra values per enum
    """
    findings = {}

    # messages.type
    findings["messages.type"] = {
        "production": audit_results["messages"]["type"],
        "domain_model": domain_enums["MessageType"],
        "missing_in_domain": [
            v for v in audit_results["messages"]["type"] if v not in domain_enums["MessageType"]
        ],
        "unused_in_production": [
            v for v in domain_enums["MessageType"] if v not in audit_results["messages"]["type"]
        ],
    }

    # messages.status
    findings["messages.status"] = {
        "production": audit_results["messages"]["status"],
        "domain_model": domain_enums["MessageStatus"],
        "missing_in_domain": [
            v for v in audit_results["messages"]["status"] if v not in domain_enums["MessageStatus"]
        ],
        "unused_in_production": [
            v for v in domain_enums["MessageStatus"] if v not in audit_results["messages"]["status"]
        ],
    }

    # suggestions.type
    findings["suggestions.type"] = {
        "production": audit_results["suggestions"]["type"],
        "domain_model": domain_enums["SuggestionType"],
        "missing_in_domain": [
            v for v in audit_results["suggestions"]["type"]
            if v not in domain_enums["SuggestionType"]
        ],
        "unused_in_production": [
            v for v in domain_enums["SuggestionType"]
            if v not in audit_results["suggestions"]["type"]
        ],
    }

    # suggestions.status
    findings["suggestions.status"] = {
        "production": audit_results["suggestions"]["status"],
        "domain_model": domain_enums["SuggestionStatus"],
        "missing_in_domain": [
            v for v in audit_results["suggestions"]["status"]
            if v not in domain_enums["SuggestionStatus"]
        ],
        "unused_in_production": [
            v for v in domain_enums["SuggestionStatus"]
            if v not in audit_results["suggestions"]["status"]
        ],
    }

    # backlog.area
    findings["backlog.area"] = {
        "production": audit_results["backlog"]["area"],
        "domain_model": domain_enums["BacklogArea"],
        "missing_in_domain": [
            v for v in audit_results["backlog"]["area"] if v not in domain_enums["BacklogArea"]
        ],
        "unused_in_production": [
            v for v in domain_enums["BacklogArea"] if v not in audit_results["backlog"]["area"]
        ],
    }

    # backlog.value
    findings["backlog.value"] = {
        "production": audit_results["backlog"]["value"],
        "domain_model": domain_enums["BacklogValue"],
        "missing_in_domain": [
            v for v in audit_results["backlog"]["value"] if v not in domain_enums["BacklogValue"]
        ],
        "unused_in_production": [
            v for v in domain_enums["BacklogValue"] if v not in audit_results["backlog"]["value"]
        ],
    }

    # backlog.effort
    findings["backlog.effort"] = {
        "production": audit_results["backlog"]["effort"],
        "domain_model": domain_enums["BacklogEffort"],
        "missing_in_domain": [
            v for v in audit_results["backlog"]["effort"] if v not in domain_enums["BacklogEffort"]
        ],
        "unused_in_production": [
            v for v in domain_enums["BacklogEffort"] if v not in audit_results["backlog"]["effort"]
        ],
    }

    # backlog.status
    findings["backlog.status"] = {
        "production": audit_results["backlog"]["status"],
        "domain_model": domain_enums["BacklogStatus"],
        "missing_in_domain": [
            v for v in audit_results["backlog"]["status"] if v not in domain_enums["BacklogStatus"]
        ],
        "unused_in_production": [
            v for v in domain_enums["BacklogStatus"] if v not in audit_results["backlog"]["status"]
        ],
    }

    return findings


def print_report(findings: dict):
    """Print human-readable audit report."""
    print("\n" + "=" * 80)
    print("ENUM AUDIT REPORT — Production vs Domain Model")
    print("=" * 80 + "\n")

    issues_found = False

    for enum_name, data in findings.items():
        missing = data["missing_in_domain"]
        unused = data["unused_in_production"]

        if missing or unused:
            issues_found = True
            print(f"\n{enum_name}:")
            print(f"  Production values: {data['production']}")
            print(f"  Domain model values: {data['domain_model']}")

            if missing:
                print(f"  [!] MISSING in domain model: {missing}")
                print("      Action: Add to domain model enum")

            if unused:
                print(f"  [i] UNUSED in production: {unused}")
                print("      Info: Defined but not used (OK)")

    if not issues_found:
        print("\n✓ All production values present in domain model enums")
        print("✓ No action needed")

    print("\n" + "=" * 80 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Audit enum columns in database")
    parser.add_argument("--db", default="mrowisko.db", help="Path to database (default: mrowisko.db)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    # Check if database exists
    if not Path(args.db).exists():
        print(f"Error: Database not found: {args.db}", file=sys.stderr)
        sys.exit(1)

    # Run audit
    audit_results = audit_all_enums(args.db)
    domain_enums = get_domain_model_enums()
    findings = compare_with_domain_model(audit_results, domain_enums)

    # Output
    if args.json:
        print(json.dumps(findings, indent=2, ensure_ascii=False))
    else:
        print_report(findings)

    # Exit code: 0 if no issues, 1 if missing values found
    has_missing = any(data["missing_in_domain"] for data in findings.values())
    sys.exit(1 if has_missing else 0)


if __name__ == "__main__":
    main()
