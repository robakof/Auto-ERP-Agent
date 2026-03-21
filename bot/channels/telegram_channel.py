"""
TelegramChannel — kanał Telegram dla bota ERP.

Architektura:
  long polling (Application.run_polling)
  → handle_message
    → whitelist check (silent reject)
    → ChatAction.TYPING
    → NlpPipeline.run (w asyncio executor — pipeline jest synchroniczny)
    → reply (split jeśli > 4096 znaków)
"""

import asyncio
import logging
from pathlib import Path

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, MessageHandler, filters

logger = logging.getLogger(__name__)

TELEGRAM_MAX_LENGTH = 4096


def load_allowed_users(path: Path) -> set[int]:
    """Wczytuje whitelist user_id z pliku tekstowego.

    Ignoruje linie puste i zaczynające się od '#'.
    Rzuca ValueError gdy plik nie istnieje.
    """
    if not path.exists():
        raise ValueError(f"Plik allowed_users nie istnieje: {path}")
    ids = set()
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            ids.add(int(line))
        except ValueError:
            raise ValueError(
                f"allowed_users.txt linia {lineno}: nieprawidłowy format '{line}' "
                f"— oczekiwano liczby całkowitej (komentarze inline '#' są niedozwolone)"
            )
    return ids


class TelegramChannel:
    def __init__(
        self,
        token: str,
        pipeline,
        allowed_users: set[int],
        allowed_users_path: Path | None = None,
        admin_user_id: int | None = None,
    ) -> None:
        self._pipeline = pipeline
        self._allowed_users = allowed_users
        self._allowed_users_path = allowed_users_path
        self._admin_user_id = admin_user_id
        self._app = (
            Application.builder()
            .token(token)
            .build()
        )
        self._app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )
        self._app.add_handler(
            CommandHandler("reload", self.handle_reload)
        )

    async def handle_reload(self, update: Update, context) -> None:
        user_id = update.effective_user.id

        if self._admin_user_id is None or user_id != self._admin_user_id:
            logger.warning("Nieautoryzowana proba /reload: user_id=%s", user_id)
            return

        if self._allowed_users_path is None:
            await update.message.reply_text("Reload niedostępny — brak ścieżki konfiguracji.")
            return

        try:
            self._allowed_users = load_allowed_users(self._allowed_users_path)
            logger.info("/reload — whitelist przeładowana, %d użytkowników", len(self._allowed_users))
            await update.message.reply_text(
                f"Whitelist przeładowana. Aktywnych użytkowników: {len(self._allowed_users)}."
            )
        except (ValueError, OSError) as e:
            logger.error("/reload — błąd odczytu pliku: %s", e)
            await update.message.reply_text("Błąd odczytu pliku whitelist — sprawdź logi.")

    async def handle_message(self, update: Update, context) -> None:
        user_id = update.effective_user.id

        if user_id not in self._allowed_users:
            logger.warning("Nieautoryzowany dostep: user_id=%s", user_id)
            return

        await context.bot.send_chat_action(
            chat_id=update.message.chat_id,
            action=ChatAction.TYPING,
        )

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self._pipeline.run(
                user_id=str(user_id),
                question=update.message.text,
            ),
        )

        await self._send_reply(update, result.answer)

    async def _send_reply(self, update: Update, text: str) -> None:
        for chunk in self._split(text):
            await update.message.reply_text(chunk, parse_mode="HTML")

    @staticmethod
    def _split(text: str) -> list[str]:
        if len(text) <= TELEGRAM_MAX_LENGTH:
            return [text]
        chunks = []
        while text:
            chunks.append(text[:TELEGRAM_MAX_LENGTH])
            text = text[TELEGRAM_MAX_LENGTH:]
        return chunks

    def run(self) -> None:
        """Uruchamia bota (blokujące)."""
        logger.info("Uruchamianie bota Telegram (long polling)...")
        self._app.run_polling()
