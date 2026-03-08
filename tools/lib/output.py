"""
output.py — Wspólna logika drukowania JSON na stdout z wymuszonym UTF-8.

Na Windows domyślne kodowanie stdout to cp1250. ensure_ascii=False powoduje
zastąpienie znaków spoza cp1250 znakiem '?'. Wymuszenie UTF-8 rozwiązuje problem.
"""

import json
import sys


def print_json(result: dict) -> None:
    """Drukuje słownik jako JSON na stdout z wymuszonym UTF-8."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, default=str))
