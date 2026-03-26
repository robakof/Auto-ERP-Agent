"""
M5.1: Add Message.title column and extract from markdown headers.

Migration steps:
1. ADD COLUMN title TEXT NOT NULL DEFAULT ''
2. Extract title from existing messages (parse markdown header)
3. Clean content (remove header line if extracted)

Usage:
    python tools/migration_m5_1_message_title.py --dry-run
    python tools/migration_m5_1_message_title.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import sqlite3
import argparse


def extract_title_from_markdown(content: str) -> tuple[str, str]:
    """
    Extract title from markdown header.

    Returns:
        (title, cleaned_content)
    """
    if not content:
        return "", content

    lines = content.split('\n', 1)
    first_line = lines[0].strip()

    # Check for markdown header (# or ##)
    if first_line.startswith('#'):
        title = first_line.lstrip('#').strip()
        # Content without header (skip first line + potential empty line)
        if len(lines) > 1:
            cleaned = lines[1].lstrip('\n')
        else:
            cleaned = ""
        return title, cleaned

    # No header found
    return "", content


def migrate_schema(conn: sqlite3.Connection, dry_run: bool = False):
    """Add title column to messages table."""
    print("=" * 80)
    print("M5.1 Schema Migration: ADD COLUMN messages.title")
    print("=" * 80)

    # Check if column already exists
    cursor = conn.execute("PRAGMA table_info(messages)")
    columns = [row[1] for row in cursor.fetchall()]

    if 'title' in columns:
        print("[OK] Column 'title' already exists. Skipping schema migration.")
        return

    sql = "ALTER TABLE messages ADD COLUMN title TEXT NOT NULL DEFAULT ''"

    if dry_run:
        print(f"[DRY RUN] Would execute: {sql}")
    else:
        print(f"Executing: {sql}")
        conn.execute(sql)
        conn.commit()
        print("[OK] Column 'title' added successfully.")


def migrate_data(conn: sqlite3.Connection, dry_run: bool = False):
    """Extract titles from existing messages."""
    print("\n" + "=" * 80)
    print("M5.1 Data Migration: Extract titles from content")
    print("=" * 80)

    # Check if title column exists
    cursor = conn.execute("PRAGMA table_info(messages)")
    columns = [row[1] for row in cursor.fetchall()]
    has_title = 'title' in columns

    if not has_title:
        if dry_run:
            print("Note: Column 'title' does not exist yet (dry run mode).")
            print("      Simulating data migration based on current content...")
            cursor = conn.execute("SELECT id, sender, recipient, content FROM messages")
            messages = [(row[0], row[1], row[2], row[3], "") for row in cursor.fetchall()]
        else:
            print("ERROR: Column 'title' does not exist. Run schema migration first.")
            return
    else:
        # Get all messages
        cursor = conn.execute("SELECT id, sender, recipient, content, title FROM messages")
        messages = cursor.fetchall()

    updates = []

    for msg_id, sender, recipient, content, current_title in messages:
        # Skip if title already set
        if current_title and current_title.strip():
            continue

        # Extract title
        title, cleaned_content = extract_title_from_markdown(content)

        # Fallback if no header found
        if not title:
            title = f"{sender} → {recipient}"
            cleaned_content = content  # Don't modify content if no header

        updates.append((title, cleaned_content, msg_id))

    print(f"\nMessages to update: {len(updates)}/{len(messages)}")

    if not updates:
        print("[OK] No updates needed.")
        return

    # Show sample (write to file to avoid unicode issues in console)
    sample_file = Path("tmp/migration_m5_1_sample.txt")
    sample_file.parent.mkdir(exist_ok=True)

    with open(sample_file, 'w', encoding='utf-8') as f:
        f.write("Sample updates (first 10):\n")
        for title, content, msg_id in updates[:10]:
            f.write(f"  ID {msg_id}: title='{title[:80]}'\n")

    print(f"\nSample updates written to: {sample_file}")

    if dry_run:
        print(f"\n[DRY RUN] Would update {len(updates)} messages.")
        return

    # Execute updates
    print(f"\nUpdating {len(updates)} messages...")
    for title, cleaned_content, msg_id in updates:
        conn.execute(
            "UPDATE messages SET title = ?, content = ? WHERE id = ?",
            (title, cleaned_content, msg_id)
        )

    conn.commit()
    print(f"[OK] Updated {len(updates)} messages successfully.")


def verify_migration(conn: sqlite3.Connection):
    """Verify migration results."""
    print("\n" + "=" * 80)
    print("M5.1 Verification")
    print("=" * 80)

    # Count messages with/without title
    cursor = conn.execute("SELECT COUNT(*) FROM messages WHERE title = ''")
    empty_titles = cursor.fetchone()[0]

    cursor = conn.execute("SELECT COUNT(*) FROM messages WHERE title != ''")
    with_titles = cursor.fetchone()[0]

    print(f"\nMessages with title: {with_titles}")
    print(f"Messages without title: {empty_titles}")

    if empty_titles == 0:
        print("\n[OK] All messages have titles.")
    else:
        print(f"\n[WARNING] {empty_titles} messages still have empty titles.")

    # Sample titles (write to file to avoid unicode issues)
    cursor = conn.execute("SELECT id, title FROM messages WHERE title != '' LIMIT 5")
    sample_file = Path("tmp/migration_m5_1_verification.txt")
    with open(sample_file, 'w', encoding='utf-8') as f:
        f.write("Sample titles:\n")
        for msg_id, title in cursor.fetchall():
            f.write(f"  ID {msg_id}: {title[:70]}\n")
    print(f"\nSample titles written to: {sample_file}")


def main():
    parser = argparse.ArgumentParser(description="M5.1 Message.title migration")
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without executing')
    parser.add_argument('--db', default='mrowisko.db', help='Database path')
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)

    try:
        migrate_schema(conn, dry_run=args.dry_run)
        migrate_data(conn, dry_run=args.dry_run)

        if not args.dry_run:
            verify_migration(conn)

        print("\n" + "=" * 80)
        if args.dry_run:
            print("M5.1 Migration: DRY RUN COMPLETE")
        else:
            print("M5.1 Migration: COMPLETE [OK]")
        print("=" * 80)

    finally:
        conn.close()


if __name__ == '__main__':
    main()
