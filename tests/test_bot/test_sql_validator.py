"""Testy jednostkowe dla bot/pipeline/sql_validator.py."""

import pytest

from bot.pipeline.sql_validator import SqlValidator, ValidationResult


class TestValidationResult:
    def test_ok_result(self):
        r = ValidationResult(ok=True, error=None, sql="SELECT 1")
        assert r.ok is True
        assert r.error is None
        assert r.sql == "SELECT 1"

    def test_error_result(self):
        r = ValidationResult(ok=False, error="BLOCKED", sql="SELECT 1")
        assert r.ok is False
        assert r.error == "BLOCKED"


class TestSqlValidatorDml:
    """Guardrails odziedziczone z SqlClient — DML/DDL zablokowane."""

    def setup_method(self):
        self.v = SqlValidator()

    def test_blocks_insert(self):
        r = self.v.validate("INSERT INTO t VALUES (1)")
        assert r.ok is False
        assert "INSERT" in r.error

    def test_blocks_update(self):
        r = self.v.validate("UPDATE t SET col=1")
        assert r.ok is False

    def test_blocks_delete(self):
        r = self.v.validate("DELETE FROM t")
        assert r.ok is False

    def test_blocks_exec(self):
        r = self.v.validate("EXEC sp_who")
        assert r.ok is False

    def test_blocks_multiple_statements(self):
        r = self.v.validate("SELECT 1; SELECT 2")
        assert r.ok is False


class TestSqlValidatorAibiOnly:
    """Blokada dostępu do tabel spoza AIBI.*"""

    def setup_method(self):
        self.v = SqlValidator()

    def test_blocks_cdn_table(self):
        r = self.v.validate("SELECT * FROM CDN.ZamNag")
        assert r.ok is False
        assert "CDN" in r.error

    def test_blocks_dbo_table(self):
        r = self.v.validate("SELECT * FROM dbo.Users")
        assert r.ok is False

    def test_allows_aibi_table(self):
        r = self.v.validate("SELECT TOP 10 * FROM AIBI.Zamowienia")
        assert r.ok is True

    def test_allows_aibi_lowercase(self):
        r = self.v.validate("SELECT TOP 10 * FROM aibi.Zamowienia")
        assert r.ok is True

    def test_allows_aibi_mixed_case(self):
        r = self.v.validate("SELECT TOP 10 * FROM Aibi.Zamowienia")
        assert r.ok is True

    def test_blocks_cdn_in_subquery(self):
        r = self.v.validate("SELECT * FROM AIBI.Zamowienia WHERE ID IN (SELECT ID FROM CDN.KntKarty)")
        assert r.ok is False

    def test_blocks_cdn_in_join(self):
        r = self.v.validate("SELECT * FROM AIBI.Zamowienia JOIN CDN.KntKarty ON 1=1")
        assert r.ok is False


class TestSqlValidatorTop:
    """Wymuszenie TOP — brak TOP w zapytaniu → wstrzyknięcie domyślnego."""

    def setup_method(self):
        self.v = SqlValidator()

    def test_injects_default_top_when_missing(self):
        r = self.v.validate("SELECT * FROM AIBI.Zamowienia")
        assert r.ok is True
        assert "TOP 50" in r.sql.upper()

    def test_does_not_inject_when_top_present(self):
        r = self.v.validate("SELECT TOP 10 * FROM AIBI.Zamowienia")
        assert r.ok is True
        assert r.sql.upper().count("TOP") == 1

    def test_custom_default_top(self):
        v = SqlValidator(default_top=100)
        r = v.validate("SELECT * FROM AIBI.Zamowienia")
        assert "TOP 100" in r.sql.upper()

    def test_blocks_top_exceeding_max(self):
        r = self.v.validate("SELECT TOP 500 * FROM AIBI.Zamowienia")
        assert r.ok is False
        assert "TOP" in r.error

    def test_max_top_configurable(self):
        v = SqlValidator(max_top=500)
        r = v.validate("SELECT TOP 500 * FROM AIBI.Zamowienia")
        assert r.ok is True

    def test_top_at_max_boundary_allowed(self):
        r = self.v.validate("SELECT TOP 200 * FROM AIBI.Zamowienia")
        assert r.ok is True


class TestSqlValidatorValidSql:
    """Happy path — poprawne zapytania przechodzą."""

    def setup_method(self):
        self.v = SqlValidator()

    def test_valid_select_with_where(self):
        r = self.v.validate("SELECT TOP 10 Nazwa FROM AIBI.Zamowienia WHERE ID = 1")
        assert r.ok is True

    def test_valid_with_cte(self):
        sql = "WITH cte AS (SELECT TOP 10 ID FROM AIBI.Zamowienia) SELECT * FROM cte"
        r = self.v.validate(sql)
        assert r.ok is True

    def test_sql_returned_unchanged_when_top_present(self):
        sql = "SELECT TOP 10 * FROM AIBI.Zamowienia"
        r = self.v.validate(sql)
        assert r.sql == sql
