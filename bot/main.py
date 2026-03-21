"""
Entry point bota ERP — Telegram.

Uruchomienie:
    python bot/main.py
"""

import logging
import os
import sys
from pathlib import Path

PID_FILE = Path(__file__).parent / "bot.pid"

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

from bot.channels.telegram_channel import TelegramChannel, load_allowed_users
from bot.pipeline.nlp_pipeline import NlpPipeline

load_dotenv(override=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

ALLOWED_USERS_PATH = Path(__file__).parent / "config" / "allowed_users.txt"


def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        logger.error("Brak TELEGRAM_BOT_TOKEN w .env")
        sys.exit(1)

    try:
        allowed_users = load_allowed_users(ALLOWED_USERS_PATH)
    except ValueError as e:
        logger.error("%s", e)
        sys.exit(1)

    if not allowed_users:
        logger.warning("Whitelist jest pusta — bot nie odpowie nikomu")

    admin_raw = os.getenv("ADMIN_USER_ID", "").strip().split()[0] if os.getenv("ADMIN_USER_ID", "").strip() else ""
    admin_user_id = int(admin_raw) if admin_raw.isdigit() else None
    if admin_user_id is None:
        logger.warning("ADMIN_USER_ID nie ustawiony — komenda /reload wyłączona")

    PID_FILE.write_text(str(os.getpid()), encoding="utf-8")
    logger.info("PID %d zapisany do %s", os.getpid(), PID_FILE)

    pipeline = NlpPipeline()
    channel = TelegramChannel(
        token=token,
        pipeline=pipeline,
        allowed_users=allowed_users,
        allowed_users_path=ALLOWED_USERS_PATH,
        admin_user_id=admin_user_id,
    )
    channel.run()


if __name__ == "__main__":
    main()
