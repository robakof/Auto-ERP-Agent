"""Testy jednostkowe dla bot/answer_formatter.py."""

from unittest.mock import MagicMock, patch

import pytest

from bot.answer_formatter import AnswerFormatter
from bot.sql_executor import ExecutionResult


def make_execution_result(ok=True, rows=None, columns=None, error=None, row_count=None):
    rows = rows or []
    columns = columns or []
    return ExecutionResult(
        ok=ok,
        columns=columns,
        rows=rows,
        row_count=row_count if row_count is not None else len(rows),
        error=error,
        duration_ms=100,
    )


def make_mock_claude(response_text: str):
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=response_text)]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_message
    return mock_client


class TestAnswerFormatterHappyPath:
    def setup_method(self):
        self.formatter = AnswerFormatter()

    def test_returns_string(self):
        mock_client = make_mock_claude("Bolsius ma 3 rezerwacje.")
        with patch.object(self.formatter, "_client", mock_client):
            result = self.formatter.format(
                question="jakie rezerwacje ma Bolsius",
                execution_result=make_execution_result(rows=[["Bolsius", 5]], columns=["Nazwa", "Ilosc"]),
                history="",
            )
        assert isinstance(result, str)
        assert len(result) > 0

    def test_calls_claude_api(self):
        mock_client = make_mock_claude("odpowiedź")
        with patch.object(self.formatter, "_client", mock_client):
            self.formatter.format(
                question="q",
                execution_result=make_execution_result(rows=[["x"]], columns=["col"]),
                history="",
            )
        assert mock_client.messages.create.called

    def test_uses_configured_model(self):
        formatter = AnswerFormatter(model="claude-haiku-4-5-20251001")
        mock_client = make_mock_claude("ok")
        with patch.object(formatter, "_client", mock_client):
            formatter.format(
                question="q",
                execution_result=make_execution_result(rows=[["x"]], columns=["col"]),
                history="",
            )
        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["model"] == "claude-haiku-4-5-20251001"


class TestAnswerFormatterEdgeCases:
    def setup_method(self):
        self.formatter = AnswerFormatter()

    def test_empty_result_no_api_call(self):
        mock_client = make_mock_claude("")
        with patch.object(self.formatter, "_client", mock_client):
            result = self.formatter.format(
                question="jakie zamówienia?",
                execution_result=make_execution_result(rows=[], columns=["ID"]),
                history="",
            )
        assert not mock_client.messages.create.called
        assert isinstance(result, str)
        assert len(result) > 0

    def test_sql_error_no_api_call(self):
        mock_client = make_mock_claude("")
        with patch.object(self.formatter, "_client", mock_client):
            result = self.formatter.format(
                question="q",
                execution_result=make_execution_result(ok=False, error="SQL_ERROR: invalid"),
                history="",
            )
        assert not mock_client.messages.create.called
        assert isinstance(result, str)

    def test_history_included_in_prompt(self):
        mock_client = make_mock_claude("ok")
        with patch.object(self.formatter, "_client", mock_client):
            self.formatter.format(
                question="q",
                execution_result=make_execution_result(rows=[["x"]], columns=["col"]),
                history="Użytkownik: poprzednie pytanie\nBot: poprzednia odpowiedź",
            )
        call_kwargs = mock_client.messages.create.call_args[1]
        messages_content = str(call_kwargs["messages"])
        assert "poprzednie pytanie" in messages_content
