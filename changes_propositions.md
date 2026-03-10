# KM3 — Kanał Telegram

*Data: 2026-03-10*

---

## Cel

Podłączyć `NlpPipeline` do Telegrama przez `python-telegram-bot` (async).

Warunek ukończenia: pytanie przez Telegram → odpowiedź PL w < 30s.

---

## Otwarte wątki z poprzednich sesji

Brak wątków zablokowanych dotyczących KM3.

Backlog aktywny (nieblokujące, odkładamy):
- [Workflow] ERP_SCHEMA_PATTERNS + ERP_VIEW_WORKFLOW — obserwacje z Rozrachunki
- [Dev] Komendy agenta blokowane przez hook (docs_search + sql_query)
- [Dev] Informacja o kontekście na końcu wiadomości agenta
- [Arch] Separacja pamięci między agentami
- [Arch] Sygnatury narzędzi powielone
- [Agent] Baza wzorców numeracji

---

## Decyzje techniczne

**Biblioteka:** `python-telegram-bot >= 21` (async, PTB — największa społeczność, Application Builder API)

**Whitelist:** `bot/config/allowed_users.txt` — jeden `user_id` na linię, linie `#` ignorowane.
Dlaczego plik zamiast `.env`: whitelist zmienia się niezależnie od credentiali, łatwiej edytować bez restartowania bota z edycją `.env`.

**BOT_TOKEN:** `.env` → `TELEGRAM_BOT_TOKEN=`

**user_id w pipeline:** Telegram daje unikalny numeryczny `user_id` — przekazujemy go jako string do `NlpPipeline.run(user_id=...)`. ConversationManager już obsługuje dowolny string.

**Timeout odpowiedzi:** status "pisze..." (`ChatAction.TYPING`) wyświetlany podczas oczekiwania na pipeline.

**Długie odpowiedzi:** Telegram limit 4096 znaków — jeśli odpowiedź dłuższa, wysyłamy w częściach.

---

## Nowe pliki

### `bot/channels/telegram_channel.py`

Klasa `TelegramChannel`:
- `__init__(token, pipeline, allowed_users)` — inicjalizacja Application
- `run()` — `app.run_polling()` (blokujące, async event loop)
- Handler `handle_message(update, context)`:
  - sprawdza `user_id` w `allowed_users`
  - wysyła `ChatAction.TYPING`
  - wywołuje `pipeline.run(user_id, question)` w executor (async-safe)
  - wysyła odpowiedź (split jeśli > 4096 znaków)
  - nieautoryzowany → bez odpowiedzi (silent reject, log WARNING)

### `bot/config/allowed_users.txt`

Plik tekstowy — jeden Telegram `user_id` na linię.
Przykład:
```
# Administratorzy
123456789
987654321
```

### `bot/main.py`

Entry point:
- ładuje `.env`
- czyta `TELEGRAM_BOT_TOKEN`
- ładuje `allowed_users.txt`
- tworzy `NlpPipeline()` i `TelegramChannel()`
- uruchamia `channel.run()`

---

## Zmiany w istniejących plikach

### `.env.example`

Dodać:
```
# Bot — Telegram
TELEGRAM_BOT_TOKEN=
```

### `requirements.txt`

Dodać:
```
python-telegram-bot>=21.0
```

---

## Testy

### `tests/bot/test_telegram_channel.py`

Unit testy z mockami (bez prawdziwego Telegrama):

1. **test_unauthorized_user_silent_reject** — wiadomość od user_id spoza whitelist → brak odpowiedzi, log WARNING
2. **test_authorized_user_gets_answer** — wiadomość od user_id z whitelist → `pipeline.run()` wywołany, odpowiedź wysłana
3. **test_long_answer_split** — odpowiedź > 4096 znaków → wysłana w częściach
4. **test_load_allowed_users_ignores_comments** — `#komentarz` i puste linie ignorowane
5. **test_load_allowed_users_missing_file** — brak pliku → ValueError z czytelnym komunikatem

---

## Kolejność pracy

1. Testy (TDD) → `tests/bot/test_telegram_channel.py`
2. `bot/channels/telegram_channel.py`
3. `bot/config/allowed_users.txt` (przykładowy pusty)
4. `bot/main.py`
5. `.env.example` + `requirements.txt`
6. Testy zielone → commit + push

---

## Poza zakresem KM3

- KM4 (biblioteka raportów)
- KM5 (deployment jako serwis Windows)
- KM6 (WhatsApp)
- Backlog developerski (wszystkie pozycje aktywne)
