"""arch_check.py — walidator ścieżek w dokumentach .md.

Skanuje pliki .md w poszukiwaniu wzorców `documents/...` i `tools/...`
i sprawdza czy ścieżki faktycznie istnieją w projekcie.

Użycie:
    python tools/arch_check.py
    python tools/arch_check.py --path documents/dev/
"""

import argparse
import io
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
PATH_PATTERN = re.compile(r'`((?:documents|tools|solutions)/[^`\s]+)`')


def check_file(md_file: Path) -> list[dict]:
    issues = []
    text = md_file.read_text(encoding="utf-8", errors="ignore")
    for match in PATH_PATTERN.finditer(text):
        ref = match.group(1)
        if "*" in ref or "{" in ref:  # skip wildcards and placeholders
            continue
        target = PROJECT_ROOT / ref
        if not target.exists():
            line = text[:match.start()].count("\n") + 1
            issues.append({"file": str(md_file.relative_to(PROJECT_ROOT)), "line": line, "ref": ref})
    return issues


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    parser = argparse.ArgumentParser(description="Walidator ścieżek w dokumentach .md")
    parser.add_argument("--path", default=".", help="Katalog do przeszukania")
    args = parser.parse_args()

    search_root = PROJECT_ROOT / args.path
    all_issues = []
    for md_file in sorted(search_root.rglob("*.md")):
        if ".git" in md_file.parts or "archive" in md_file.parts or "_loom" in md_file.parts:
            continue
        if "progress_log" in md_file.name or "methodology_progress" in md_file.name:
            continue
        all_issues.extend(check_file(md_file))

    if all_issues:
        print(f"Znalezione nieistniejące ścieżki: {len(all_issues)}")
        for issue in all_issues:
            print(f"  {issue['file']}:{issue['line']}  →  {issue['ref']}")
        sys.exit(1)
    else:
        print("OK — wszystkie ścieżki istnieją")


if __name__ == "__main__":
    main()
