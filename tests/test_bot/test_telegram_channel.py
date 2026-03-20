"""Testy jednostkowe dla bot/channels/telegram_channel.py."""

import asyncio
import logging
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.channels.telegram_channel import TelegramChannel, load_allowed_users

TELEGRAM_MAX_LENGTH = 4096


# ---------------------------------------------------------------------------
# load_allowed_users
# ---------------------------------------------------------------------------


def test_load_allowed_users_ignores_comments_and_blanks(tmp_path):
    f = tmp_path / "allowed_users.txt"
    f.write_text("# Admin\n123456789\n\n987654321\n# Koniec\n", encoding="utf-8")
    result = load_allowed_users(f)
    assert result == {123456789, 987654321}


def test_load_allowed_users_missing_file(tmp_path):
    with pytest.raises(ValueError, match="allowed_users"):
        load_allowed_users(tmp_path / "nieistniejacy.txt")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_update(user_id: int, text: str = "test") -> MagicMock:
    update = MagicMock()
    update.effective_user.id = user_id
    update.message.text = text
    update.message.reply_text = AsyncMock()
    update.message.chat_id = user_id
    return update


def make_context() -> MagicMock:
    ctx = MagicMock()
    ctx.bot.send_chat_action = AsyncMock()
    return ctx


def make_channel(allowed_ids=None, answer="Odpowiedź.", allowed_users_path=None, admin_user_id=None):
    pipeline = MagicMock()
    pipeline.run.return_value = MagicMock(answer=answer, sql=None, error=None)

    allowed = {111} if allowed_ids is None else allowed_ids

    with patch("bot.channels.telegram_channel.Application"):
        channel = TelegramChannel(
            token="fake-token",
            pipeline=pipeline,
            allowed_users=allowed,
            allowed_users_path=allowed_users_path,
            admin_user_id=admin_user_id,
        )
    channel._pipeline = pipeline
    return channel


# ---------------------------------------------------------------------------
# Testy handlera
# ---------------------------------------------------------------------------


def test_unauthorized_user_silent_reject(caplog):
    channel = make_channel(allowed_ids={111})
    update = make_update(user_id=999, text="Ile zamówień?")
    ctx = make_context()

    with caplog.at_level(logging.WARNING):
        asyncio.get_event_loop().run_until_complete(
            channel.handle_message(update, ctx)
        )

    update.message.reply_text.assert_not_called()
    channel._pipeline.run.assert_not_called()
    assert any("999" in r.message for r in caplog.records)


def test_authorized_user_gets_answer():
    answer = "Masz 42 zamówienia."
    channel = make_channel(allowed_ids={111}, answer=answer)
    update = make_update(user_id=111, text="Ile zamówień?")
    ctx = make_context()

    asyncio.get_event_loop().run_until_complete(
        channel.handle_message(update, ctx)
    )

    channel._pipeline.run.assert_called_once_with(user_id="111", question="Ile zamówień?")
    update.message.reply_text.assert_called_once_with(answer, parse_mode="HTML")


def test_long_answer_split():
    long_answer = "A" * (TELEGRAM_MAX_LENGTH + 100)
    channel = make_channel(allowed_ids={111}, answer=long_answer)
    update = make_update(user_id=111, text="Długie pytanie")
    ctx = make_context()

    asyncio.get_event_loop().run_until_complete(
        channel.handle_message(update, ctx)
    )

    assert update.message.reply_text.call_count >= 2
    sent = "".join(
        call.args[0] for call in update.message.reply_text.call_args_list
    )
    assert sent == long_answer


# ---------------------------------------------------------------------------
# /reload
# ---------------------------------------------------------------------------


def make_reload_update(user_id: int) -> MagicMock:
    update = MagicMock()
    update.effective_user.id = user_id
    update.message.reply_text = AsyncMock()
    return update


def test_reload_admin_reloads_whitelist(tmp_path):
    users_file = tmp_path / "allowed_users.txt"
    users_file.write_text("111\n222\n", encoding="utf-8")

    channel = make_channel(
        allowed_ids={111},
        allowed_users_path=users_file,
        admin_user_id=111,
    )
    update = make_reload_update(user_id=111)

    asyncio.get_event_loop().run_until_complete(
        channel.handle_reload(update, MagicMock())
    )

    assert channel._allowed_users == {111, 222}
    update.message.reply_text.assert_called_once()
    assert "2" in update.message.reply_text.call_args.args[0]


def test_reload_non_admin_silent_reject(caplog):
    channel = make_channel(admin_user_id=111)
    update = make_reload_update(user_id=999)

    with caplog.at_level(logging.WARNING):
        asyncio.get_event_loop().run_until_complete(
            channel.handle_reload(update, MagicMock())
        )

    update.message.reply_text.assert_not_called()
    assert any("999" in r.message for r in caplog.records)


def test_reload_no_admin_configured_silent_reject():
    channel = make_channel(admin_user_id=None)
    update = make_reload_update(user_id=111)

    asyncio.get_event_loop().run_until_complete(
        channel.handle_reload(update, MagicMock())
    )

    update.message.reply_text.assert_not_called()


def test_reload_missing_file_returns_error(tmp_path):
    channel = make_channel(
        allowed_users_path=tmp_path / "nieistniejacy.txt",
        admin_user_id=111,
    )
    update = make_reload_update(user_id=111)

    asyncio.get_event_loop().run_until_complete(
        channel.handle_reload(update, MagicMock())
    )

    update.message.reply_text.assert_called_once()
    assert "Błąd" in update.message.reply_text.call_args.args[0]


def test_typing_action_sent_before_pipeline():
    channel = make_channel(allowed_ids={111})
    update = make_update(user_id=111, text="Pytanie")
    ctx = make_context()

    call_order = []
    ctx.bot.send_chat_action = AsyncMock(
        side_effect=lambda **_: call_order.append("typing")
    )
    channel._pipeline.run = MagicMock(
        side_effect=lambda **_: call_order.append("pipeline") or MagicMock(answer="ok", sql=None, error=None)
    )

    asyncio.get_event_loop().run_until_complete(
        channel.handle_message(update, ctx)
    )

    assert call_order[0] == "typing"
    assert "pipeline" in call_order
