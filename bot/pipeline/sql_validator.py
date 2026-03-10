"""
SqlValidator — guardrails domenowe dla bota.

Rozszerza SqlClient.validate() o reguły specyficzne dla bota:
- Tylko AIBI.* schema (blokada CDN.* i innych)
- Wymuszenie TOP (domyślnie 50, max 200)
"""

import re
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.lib.sql_client import SqlClient


@dataclass
class ValidationResult:
    ok: bool
    error: str | None
    sql: str


class SqlValidator:
    AIBI_PATTERN = re.compile(r"\bFROM\s+(\w+)\.", re.IGNORECASE)
    AIBI_JOIN_PATTERN = re.compile(r"\bJOIN\s+(\w+)\.", re.IGNORECASE)
    TOP_PATTERN = re.compile(r"\bTOP\s+(\d+)\b", re.IGNORECASE)

    def __init__(self, default_top: int = 50, max_top: int = 200):
        self.default_top = default_top
        self.max_top = max_top
        self._base = SqlClient()

    def validate(self, sql: str) -> ValidationResult:
        # 1. Guardrails bazowe (DML/DDL/multiple statements)
        base_error = self._base.validate(sql)
        if base_error:
            return ValidationResult(ok=False, error=base_error, sql=sql)

        # 2. Tylko AIBI.* schema
        schema_error = self._check_schema(sql)
        if schema_error:
            return ValidationResult(ok=False, error=schema_error, sql=sql)

        # 3. TOP — walidacja istniejącego lub wstrzyknięcie domyślnego
        top_match = self.TOP_PATTERN.search(sql)
        if top_match:
            top_value = int(top_match.group(1))
            if top_value > self.max_top:
                return ValidationResult(
                    ok=False,
                    error=f"TOP {top_value} przekracza limit {self.max_top}",
                    sql=sql,
                )
        else:
            # Wstrzyknięcie domyślnego TOP (tylko dla prostego SELECT, nie CTE)
            if not sql.upper().lstrip().startswith("WITH"):
                sql = sql.replace("SELECT ", f"SELECT TOP {self.default_top} ", 1)

        return ValidationResult(ok=True, error=None, sql=sql)

    def _check_schema(self, sql: str) -> str | None:
        """Zwraca błąd jeśli SQL odwołuje się do tabeli spoza AIBI.*"""
        schemas_used: set[str] = set()

        for match in self.AIBI_PATTERN.finditer(sql):
            schemas_used.add(match.group(1).upper())

        for match in self.AIBI_JOIN_PATTERN.finditer(sql):
            schemas_used.add(match.group(1).upper())

        non_aibi = {s for s in schemas_used if s != "AIBI"}
        if non_aibi:
            blocked = ", ".join(sorted(non_aibi))
            return f"SCHEMA_BLOCKED: niedozwolone schematy: {blocked}. Dozwolone tylko AIBI.*"

        return None
