# CHANGELOG — KM3 Kanał Telegram

## 2026-03-10

### Nowe pliki

**`bot/channels/__init__.py`**
- Pusty init pakietu

**`bot/channels/telegram_channel.py`**
- `load_allowed_users(path)` — wczytuje whitelist user_id z pliku txt (ignoruje #, puste linie; ValueError gdy brak pliku)
- `TelegramChannel.__init__(token, pipeline, allowed_users)` — buduje Application PTB, rejestruje handler tekstowy
- `TelegramChannel.handle_message(update, context)` — whitelist check (silent reject + log WARNING), ChatAction.TYPING, pipeline.run w executor (async-safe), reply z podziałem
- `TelegramChannel._send_reply(update, text)` — iteruje przez chunki
- `TelegramChannel._split(text)` — dzieli tekst na kawałki <= 4096 znaków
- `TelegramChannel.run()` — app.run_polling() (blokujące)

**`bot/config/allowed_users.txt`**
- Pusty plik z komentarzem instrukcyjnym (whitelist produkcyjna)

**`bot/main.py`**
- Ładuje .env, czyta TELEGRAM_BOT_TOKEN, ładuje allowed_users.txt
- sys.exit(1) gdy brak tokenu lub brak pliku whitelist
- log WARNING gdy whitelist pusta
- Tworzy NlpPipeline + TelegramChannel, uruchamia channel.run()

**`tests/test_bot/test_telegram_channel.py`**
- 6 testów: load_allowed_users (komentarze, brak pliku), silent reject, odpowiedź autoryzowanemu, split długiej odpowiedzi, kolejność TYPING → pipeline

### Zmiany istniejących plików

**`.env.example`**
- Dodano sekcję `# Bot — Telegram` z `TELEGRAM_BOT_TOKEN=`

**`requirements.txt`**
- Dodano `python-telegram-bot>=21.0`
