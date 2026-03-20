"""Testy jednostkowe dla bot/pipeline/nlp_pipeline.py."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from bot.pipeline.nlp_pipeline import NlpPipeline, PipelineResult
from bot.sql_executor import ExecutionResult


def make_execution_result(ok=True, rows=None, columns=None, error=None):
    rows = rows or [["wynik"]]
    columns = columns or ["Kolumna"]
    return ExecutionResult(
        ok=ok, columns=columns, rows=rows,
        row_count=len(rows), error=error, duration_ms=50,
    )


def make_pipeline(sql="SELECT TOP 50 * FROM AIBI.Zamowienia", answer="Odpowiedź bota."):
    pipeline = NlpPipeline()

    mock_claude = MagicMock()
    sql_message = MagicMock()
    sql_message.content = [MagicMock(text=sql)]
    mock_claude.messages.create.return_value = sql_message

    pipeline._client = mock_claude
    pipeline.executor = MagicMock()
    pipeline.executor.execute.return_value = make_execution_result()
    pipeline.formatter = MagicMock()
    pipeline.formatter.format.return_value = answer

    return pipeline


class TestPipelineResult:
    def test_fields(self):
        r = PipelineResult(answer="ok", sql="SELECT 1", row_count=1, error=None)
        assert r.answer == "ok"
        assert r.error is None


class TestNlpPipelineHappyPath:
    def test_returns_pipeline_result(self):
        pipeline = make_pipeline()
        result = pipeline.run(user_id="u1", question="jakie zamówienia?")
        assert isinstance(result, PipelineResult)
        assert result.answer == "Odpowiedź bota."
        assert result.error is None

    def test_sql_generated_and_executed(self):
        pipeline = make_pipeline(sql="SELECT TOP 50 * FROM AIBI.Zamowienia")
        pipeline.run(user_id="u1", question="jakie zamówienia?")
        assert pipeline.executor.execute.called

    def test_answer_formatter_called(self):
        pipeline = make_pipeline()
        pipeline.run(user_id="u1", question="jakie zamówienia?")
        assert pipeline.formatter.format.called

    def test_conversation_saved(self):
        pipeline = make_pipeline()
        pipeline.run(user_id="u1", question="pytanie 1")
        turns = pipeline.conversation.get_turns("u1")
        assert len(turns) == 1
        assert turns[0].question == "pytanie 1"

    def test_history_passed_on_second_turn(self):
        pipeline = make_pipeline()
        pipeline.run(user_id="u1", question="pierwsze")
        pipeline.run(user_id="u1", question="drugie")
        # formatter wywołany dwukrotnie — drugie wywołanie ma historię
        second_call_kwargs = pipeline.formatter.format.call_args_list[1][1]
        assert "pierwsze" in second_call_kwargs["history"]


class TestNlpPipelineNoSql:
    def test_no_sql_marker_returns_out_of_scope(self):
        pipeline = make_pipeline(sql="NO_SQL")
        result = pipeline.run(user_id="u1", question="jaka jest pogoda?")
        assert result.error == "OUT_OF_SCOPE"
        assert not pipeline.executor.execute.called

    def test_no_sql_answer_is_string(self):
        pipeline = make_pipeline(sql="NO_SQL")
        result = pipeline.run(user_id="u1", question="jaka jest pogoda?")
        assert isinstance(result.answer, str)
        assert len(result.answer) > 0


class TestNlpPipelineValidationError:
    def test_invalid_sql_returns_error(self):
        pipeline = make_pipeline(sql="SELECT * FROM CDN.ZamNag")  # niedozwolone schema
        result = pipeline.run(user_id="u1", question="q")
        assert result.error == "VALIDATION_ERROR"
        assert not pipeline.executor.execute.called


class TestNlpPipelineRetry:
    def test_retry_on_execution_error_succeeds(self):
        """Pierwszy execute() failuje, drugi po retry przechodzi."""
        pipeline = make_pipeline(sql="SELECT TOP 50 * FROM AIBI.Zamowienia")
        pipeline.executor.execute.side_effect = [
            make_execution_result(ok=False, error="invalid column"),
            make_execution_result(ok=True),
        ]
        result = pipeline.run(user_id="u1", question="ile zamówień?")
        assert result.error is None
        assert pipeline._client.messages.create.call_count == 2

    def test_hint_included_in_retry_prompt(self):
        """Retry prompt zawiera wskazówkę z błędem."""
        pipeline = make_pipeline(sql="SELECT TOP 50 * FROM AIBI.Zamowienia")
        pipeline.executor.execute.side_effect = [
            make_execution_result(ok=False, error="syntax error"),
            make_execution_result(ok=True),
        ]
        pipeline.run(user_id="u1", question="ile zamówień?")
        retry_call = pipeline._client.messages.create.call_args_list[1]
        user_msg = retry_call.kwargs["messages"][0]["content"]
        assert "syntax error" in user_msg

    def test_two_retries_exhausted_returns_error(self):
        """Po 2 retry nadal błąd → EXECUTION_ERROR."""
        pipeline = make_pipeline(sql="SELECT TOP 50 * FROM AIBI.Zamowienia")
        pipeline.executor.execute.return_value = make_execution_result(ok=False, error="err")
        result = pipeline.run(user_id="u1", question="ile zamówień?")
        assert result.error == "EXECUTION_ERROR"
        assert pipeline._client.messages.create.call_count == 3  # original + 2 retries

    def test_no_retry_when_execution_ok(self):
        """Gdy execute() od razu OK — brak retry."""
        pipeline = make_pipeline()
        pipeline.run(user_id="u1", question="ile zamówień?")
        assert pipeline._client.messages.create.call_count == 1


class TestNlpPipelineLogging:
    def test_logs_written(self, tmp_path):
        pipeline = make_pipeline()
        pipeline.log_dir = tmp_path
        pipeline.run(user_id="u1", question="test pytanie")

        log_files = list(tmp_path.glob("*.jsonl"))
        assert len(log_files) == 1
        line = json.loads(log_files[0].read_text(encoding="utf-8").strip())
        assert line["question"] == "test pytanie"
        assert line["user_id"] == "u1"
        assert "answer" in line
        assert "duration_ms" in line

    def test_log_contains_sql(self, tmp_path):
        pipeline = make_pipeline(sql="SELECT TOP 50 * FROM AIBI.Zamowienia")
        pipeline.log_dir = tmp_path
        pipeline.run(user_id="u1", question="q")

        log_files = list(tmp_path.glob("*.jsonl"))
        line = json.loads(log_files[0].read_text(encoding="utf-8").strip())
        assert "generated_sql" in line
