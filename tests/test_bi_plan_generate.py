"""Testy dla tools/bi_plan_generate.py."""

import pytest
from pathlib import Path

import tools.bi_plan_generate as bpg


SAMPLE_SQL = """\
SELECT 1 AS Kolejnosc, 'ZaN_GIDNumer' AS CDN_Pole, 'Identyfikator' AS Opis, 'TAK' AS Uwzglednic
UNION ALL SELECT 2, 'ZaN_KntNumer', 'Kontrahent', 'TAK'
UNION ALL SELECT 3, 'ZaN_Stan', 'Status z polskimi: żółć', 'NIE'
"""

SAMPLE_SQL_POLISH = """\
SELECT 1 AS Kolejnosc, 'ZaN_Url' AS CDN_Pole, 'Uwagi — myślnik i żółć' AS Opis, 'TAK' AS Uwzglednic
UNION ALL SELECT 2, 'ZaN_Rabat', 'Upust (%)','NIE'
"""


class TestGeneratePlan:
    def test_happy_path(self, tmp_path):
        src = tmp_path / "Widok_plan_src.sql"
        src.write_text(SAMPLE_SQL, encoding="utf-8")
        output = tmp_path / "out.xlsx"

        result = bpg.generate_plan(src, output)

        assert result["ok"] is True
        assert result["data"]["row_count"] == 3
        assert result["data"]["columns"] == ["Kolejnosc", "CDN_Pole", "Opis", "Uwzglednic"]
        assert result["data"]["path"] == str(output.resolve())
        assert output.exists()

    def test_polish_characters(self, tmp_path):
        src = tmp_path / "plan_src.sql"
        src.write_text(SAMPLE_SQL_POLISH, encoding="utf-8")
        output = tmp_path / "out.xlsx"

        result = bpg.generate_plan(src, output)

        assert result["ok"] is True
        assert result["data"]["row_count"] == 2

    def test_file_not_found(self, tmp_path):
        result = bpg.generate_plan(tmp_path / "nieistniejacy.sql", tmp_path / "out.xlsx")

        assert result["ok"] is False
        assert result["error"]["type"] == "FILE_NOT_FOUND"

    def test_invalid_sql(self, tmp_path):
        src = tmp_path / "plan_src.sql"
        src.write_text("TO NIE JEST SQL", encoding="utf-8")
        output = tmp_path / "out.xlsx"

        result = bpg.generate_plan(src, output)

        assert result["ok"] is False
        assert result["error"]["type"] == "SQL_ERROR"

    def test_default_output_path(self, tmp_path):
        src = tmp_path / "Zamowienia_plan_src.sql"
        src.write_text(SAMPLE_SQL, encoding="utf-8")

        result = bpg.generate_plan(src, output_path=None)

        assert result["ok"] is True
        assert result["data"]["path"].endswith("Zamowienia_plan.xlsx")

    def test_default_output_path_no_suffix(self, tmp_path):
        """Gdy nazwa pliku nie pasuje do wzorca *_plan_src.sql — fallback z timestampem."""
        src = tmp_path / "dowolna_nazwa.sql"
        src.write_text(SAMPLE_SQL, encoding="utf-8")

        result = bpg.generate_plan(src, output_path=None)

        assert result["ok"] is True
        assert result["data"]["path"].endswith(".xlsx")
