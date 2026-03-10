"""Testy jednostkowe dla bot/pipeline/conversation.py."""

import time

import pytest

from bot.pipeline.conversation import ConversationManager, Turn


class TestTurn:
    def test_turn_stores_fields(self):
        t = Turn(question="q", answer="a", ts=1000.0)
        assert t.question == "q"
        assert t.answer == "a"
        assert t.ts == 1000.0


class TestConversationManagerSaveTurn:
    def setup_method(self):
        self.mgr = ConversationManager(ttl_seconds=900, max_turns=3)

    def test_save_and_retrieve(self):
        self.mgr.save_turn("u1", "pytanie 1", "odpowiedź 1")
        turns = self.mgr.get_turns("u1")
        assert len(turns) == 1
        assert turns[0].question == "pytanie 1"
        assert turns[0].answer == "odpowiedź 1"

    def test_multiple_turns_stored(self):
        self.mgr.save_turn("u1", "q1", "a1")
        self.mgr.save_turn("u1", "q2", "a2")
        turns = self.mgr.get_turns("u1")
        assert len(turns) == 2

    def test_max_turns_respected(self):
        for i in range(5):
            self.mgr.save_turn("u1", f"q{i}", f"a{i}")
        turns = self.mgr.get_turns("u1")
        assert len(turns) == 3
        assert turns[0].question == "q2"  # najstarsze z ostatnich 3

    def test_different_users_isolated(self):
        self.mgr.save_turn("u1", "q1", "a1")
        self.mgr.save_turn("u2", "q2", "a2")
        assert len(self.mgr.get_turns("u1")) == 1
        assert len(self.mgr.get_turns("u2")) == 1
        assert self.mgr.get_turns("u1")[0].question == "q1"

    def test_unknown_user_returns_empty(self):
        assert self.mgr.get_turns("nieznany") == []


class TestConversationManagerTTL:
    def test_turns_reset_after_ttl(self):
        mgr = ConversationManager(ttl_seconds=1, max_turns=3)
        mgr.save_turn("u1", "q1", "a1")
        time.sleep(1.1)
        turns = mgr.get_turns("u1")
        assert turns == []

    def test_turns_alive_within_ttl(self):
        mgr = ConversationManager(ttl_seconds=60, max_turns=3)
        mgr.save_turn("u1", "q1", "a1")
        turns = mgr.get_turns("u1")
        assert len(turns) == 1

    def test_save_after_ttl_starts_fresh(self):
        mgr = ConversationManager(ttl_seconds=1, max_turns=3)
        mgr.save_turn("u1", "q1", "a1")
        time.sleep(1.1)
        mgr.save_turn("u1", "q2", "a2")
        turns = mgr.get_turns("u1")
        assert len(turns) == 1
        assert turns[0].question == "q2"


class TestConversationManagerFormatHistory:
    def setup_method(self):
        self.mgr = ConversationManager()

    def test_empty_history_returns_empty_string(self):
        assert self.mgr.format_history("u1") == ""

    def test_single_turn_formatted(self):
        self.mgr.save_turn("u1", "Co to jest?", "To jest X.")
        history = self.mgr.format_history("u1")
        assert "Co to jest?" in history
        assert "To jest X." in history

    def test_multiple_turns_in_order(self):
        self.mgr.save_turn("u1", "pierwsze", "odp1")
        self.mgr.save_turn("u1", "drugie", "odp2")
        history = self.mgr.format_history("u1")
        assert history.index("pierwsze") < history.index("drugie")
