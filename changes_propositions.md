# KM2 — Bot core (bez kanałów)

*Data: 2026-03-10*

---

## Zakres

Zbudowanie pipeline bota od pytania do odpowiedzi, bez warstwy kanałów (Telegram/WhatsApp).
Weryfikacja przez CLI: `python bot/pipeline/nlp_pipeline.py --question "..."`.

---

## Otwarte wątki z poprzednich sesji

Brak otwartych wątków blokujących KM2.
Backlog (bi_catalog_add.py, obserwacje workflow, arch) — odkładamy na po KM2.

---

## Struktura plików

```
bot/
├── __init__.py
├── pipeline/
│   ├── __init__.py
│   ├── nlp_pipeline.py       ← orkiestrator: pytanie → SQL → odpowiedź
│   ├── sql_validator.py      ← guardrails domenowe (AIBI.* only, TOP)
│   └── conversation.py       ← kontekst 3 tury per user, TTL 15 min
├── sql_executor.py            ← pyodbc przez SqlClient, konto CEIM_AIBI
└── answer_formatter.py        ← Claude API call 2: dane → odpowiedź PL

tools/lib/
└── sql_client.py              ← REFAKTOR: SqlCredentials + fabryki + SqlClient(credentials)

tests/
└── test_bot/
    ├── test_sql_validator.py
    ├── test_conversation.py
    ├── test_sql_executor.py
    ├── test_answer_formatter.py
    └── test_nlp_pipeline.py
```

---

## Pliki do stworzenia / zmiany — szczegóły

### tools/lib/sql_client.py — refaktor (KROK 0)

Dodajemy `SqlCredentials` i fabryki. `SqlClient.__init__` przyjmuje opcjonalne credentials
— domyślnie `SqlCredentials.from_env("SQL_")` więc istniejące narzędzia działają bez zmian.

```python
@dataclass(frozen=True)
class SqlCredentials:
    server: str
    database: str
    username: str
    password: str

    @classmethod
    def from_env(cls, prefix: str = "SQL_") -> "SqlCredentials":
        return cls(
            server=os.environ[f"{prefix}SERVER"],
            database=os.environ[f"{prefix}DATABASE"],
            username=os.environ[f"{prefix}USERNAME"],
            password=os.environ[f"{prefix}PASSWORD"],
        )

class SqlClient:
    def __init__(self, credentials: SqlCredentials | None = None):
        self.credentials = credentials or SqlCredentials.from_env("SQL_")

def create_erp_sql_client() -> SqlClient:
    return SqlClient(SqlCredentials.from_env("SQL_"))

def create_bot_sql_client() -> SqlClient:
    return SqlClient(SqlCredentials.from_env("BOT_SQL_"))
```

Istniejące narzędzia (`sql_query.py`, `excel_export.py` itd.) — bez zmian w kodzie.
Nowe zmienne `.env`:
```
BOT_SQL_SERVER=
BOT_SQL_DATABASE=
BOT_SQL_USERNAME=CEIM_AIBI
BOT_SQL_PASSWORD=
```

### bot/pipeline/sql_validator.py

Rozszerza guardrails z `SqlClient.validate()` o reguły domenowe bota:
- Blokada dostępu do CDN.* (tylko AIBI.* dozwolone)
- Wymuszenie TOP max 200, domyślnie 50
- Zwraca `ValidationResult(ok: bool, error: str | None, sql: str)`

### bot/pipeline/conversation.py

- `ConversationManager` — dict per `user_id`, lista `Turn(question, answer, ts)`
- Ostatnie 3 tury per user
- TTL 15 min od ostatniej aktywności — reset przy dostępie po TTL
- Formatuje historię do stringa dla Claude API call 1
- Stan w pamięci (akceptowalne — utracony przy restarcie)

### bot/sql_executor.py

- Używa `create_bot_sql_client()` (konto CEIM_AIBI)
- Max 200 wierszy (inject_top=200)
- Zwraca `ExecutionResult(ok, columns, rows, row_count, error, duration_ms)`

### bot/answer_formatter.py

- Claude API call 2: pytanie + historia + dane SQL → odpowiedź PL
- Obsługuje: brak wyników, błąd SQL, pytanie poza zakresem
- Model konfigurowalny przez `.env`: `BOT_MODEL_FORMAT`

### bot/pipeline/nlp_pipeline.py

Orkiestrator:
```
pytanie
  → ConversationManager.get_context()
  → Claude API call 1 (BOT_MODEL_GENERATE): pytanie + kontekst + catalog.json → SQL
  → SqlValidator.validate(sql)
  → SqlExecutor.execute(sql)
  → AnswerFormatter.format(pytanie, dane, kontekst)
  → ConversationManager.save_turn(pytanie, odpowiedź)
  → zapis do logs/bot/YYYY-MM-DD.jsonl
  → odpowiedź
```

Claude API call 1:
- System prompt: schemat BI z catalog.json (nazwy, opisy, kolumny, example_questions)
- Oczekiwany output: czysty SQL bez markdown
- Pytanie poza zakresem → Claude zwraca marker `NO_SQL`

CLI:
```
python bot/pipeline/nlp_pipeline.py --question "jakie rezerwacje ma Bolsius"
python bot/pipeline/nlp_pipeline.py --question "..." --verbose
```

---

## Zmienne .env do dodania

```
# Bot — SQL Server (konto CEIM_AIBI, dostęp tylko AIBI.*)
BOT_SQL_SERVER=
BOT_SQL_DATABASE=
BOT_SQL_USERNAME=CEIM_AIBI
BOT_SQL_PASSWORD=

# Bot — modele Claude (konfigurowalne bez zmiany kodu)
BOT_MODEL_GENERATE=claude-sonnet-4-6
BOT_MODEL_FORMAT=claude-haiku-4-5-20251001

# Bot — Anthropic API
ANTHROPIC_API_KEY=
```

---

## Logowanie interakcji

Każda interakcja zapisywana do `logs/bot/YYYY-MM-DD.jsonl` (lokalne, nie w repo):
```json
{
  "ts": "2026-03-10T10:15:00",
  "user_id": "cli",
  "question": "jakie rezerwacje ma Bolsius",
  "generated_sql": "SELECT TOP 50 ...",
  "row_count": 3,
  "answer": "Bolsius ma 3 aktywne rezerwacje...",
  "duration_ms": 8200
}
```

`logs/` w `.gitignore`.

---

## Zależności

Do `requirements.txt`:
- `anthropic`

---

## Kolejność implementacji (TDD)

0. Refaktor `tools/lib/sql_client.py` + testy (backwards compatible)
1. `bot/pipeline/sql_validator.py` + `test_sql_validator.py`
2. `bot/pipeline/conversation.py` + `test_conversation.py`
3. `bot/sql_executor.py` + `test_sql_executor.py` (mock pyodbc)
4. `bot/answer_formatter.py` + `test_answer_formatter.py` (mock Claude API)
5. `bot/pipeline/nlp_pipeline.py` + `test_nlp_pipeline.py` (mock wszystko)

---

## Warunek ukończenia KM2

```
python bot/pipeline/nlp_pipeline.py --question "jakie rezerwacje ma Bolsius"
```
Zwraca odpowiedź w języku polskim z danymi z bazy.

---

## Poza zakresem KM2

- Telegram/WhatsApp channel (KM3)
- Biblioteka raportów / search_reports.py (KM4)
- health.py / watchdog (KM5)
