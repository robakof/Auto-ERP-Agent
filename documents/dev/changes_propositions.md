# Changes Propositions — Agent Bus (Faza 1)

**Źródło:** handoff_db_architecture.md (Metodolog, 2026-03-12)
**Cel:** Komunikacja i stan agentów w SQLite zamiast plików .md

---

## Zakres fazy 1

Weryfikacja wzorca: czy agenty potrafią komunikować się przez DB zamiast appendowania
do plików .md? Minimalna implementacja — bez dyrektyw, bez warstwy myśli, bez widoków.

---

## 1. Baza danych: `mrowisko.db`

Plik SQLite obok istniejącego `docs.db`. WAL mode dla lepszej współbieżności.
Lokalizacja: root projektu (`mrowisko.db`).

### Tabela `messages`

```sql
CREATE TABLE messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    sender      TEXT NOT NULL,           -- rola nadawcy (erp_specialist, analyst, developer, metodolog, human)
    recipient   TEXT NOT NULL,           -- rola odbiorcy
    type        TEXT NOT NULL DEFAULT 'suggestion',  -- suggestion | handoff | flag_human | note
    content     TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'unread',      -- unread | read | archived
    session_id  TEXT,                    -- UUID sesji która utworzyła wiadomość
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    read_at     TEXT
);

CREATE INDEX idx_messages_recipient_status ON messages(recipient, status);
CREATE INDEX idx_messages_session ON messages(session_id);
```

### Tabela `state`

```sql
CREATE TABLE state (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    role        TEXT NOT NULL,           -- rola autora
    type        TEXT NOT NULL,           -- progress | reflection | backlog_item
    content     TEXT NOT NULL,
    session_id  TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    metadata    TEXT                     -- JSON dla dodatkowych pól (priorytet, status backlog itd.)
);

CREATE INDEX idx_state_role_type ON state(role, type);
CREATE INDEX idx_state_session ON state(session_id);
```

---

## 2. Moduł: `tools/lib/agent_bus.py`

Klasa `AgentBus` — importowana przez narzędzia i agenty. Nie CLI, nie subprocess.

### API

```python
class AgentBus:
    def __init__(self, db_path: str = "mrowisko.db"):
        """Otwiera/tworzy bazę, ustawia WAL mode, tworzy tabele jeśli brak."""

    # --- Messages ---
    def send_message(self, sender: str, recipient: str, content: str,
                     type: str = "suggestion", session_id: str = None) -> int:
        """Wysyła wiadomość. Zwraca id."""

    def get_inbox(self, role: str, status: str = "unread") -> list[dict]:
        """Zwraca wiadomości dla roli o danym statusie. Sortowanie: created_at ASC."""

    def mark_read(self, message_id: int) -> None:
        """Oznacza wiadomość jako przeczytaną (status='read', read_at=now)."""

    def archive_message(self, message_id: int) -> None:
        """Oznacza wiadomość jako zarchiwizowaną."""

    # --- State ---
    def write_state(self, role: str, type: str, content: str,
                    session_id: str = None, metadata: dict = None) -> int:
        """Zapisuje wpis stanu. metadata serializowane jako JSON. Zwraca id."""

    def get_state(self, role: str, type: str = None, limit: int = 20) -> list[dict]:
        """Zwraca wpisy stanu dla roli (opcjonalnie filtr type). Najnowsze pierwsze."""

    # --- Human escalation ---
    def flag_for_human(self, sender: str, reason: str,
                       urgency: str = "normal", session_id: str = None) -> int:
        """Skrót: send_message do 'human' z type='flag_human'."""
```

### Szczegóły implementacyjne

- `sqlite3` z stdlib — zero nowych zależności
- `connection.execute("PRAGMA journal_mode=WAL")` na starcie
- `connection.execute("PRAGMA foreign_keys=ON")`
- Tabele tworzone przez `CREATE TABLE IF NOT EXISTS` w `__init__`
- Daty w UTC (`datetime('now')`)
- `metadata` jako JSON string (sqlite3 nie ma natywnego JSON, ale ma json_extract)
- Thread-safe: nowe połączenie per operację lub `check_same_thread=False`

---

## 3. CLI wrapper: `tools/agent_bus_cli.py`

Cienki CLI nad `AgentBus` — do użytku z Bash gdy import nie jest możliwy.

```
python tools/agent_bus_cli.py send --from developer --to erp_specialist --content "..."
python tools/agent_bus_cli.py inbox --role developer
python tools/agent_bus_cli.py inbox --role developer --status all
python tools/agent_bus_cli.py state --role developer --type progress
python tools/agent_bus_cli.py write-state --role developer --type progress --content "..."
python tools/agent_bus_cli.py flag --from analyst --reason "..." --urgency high
```

Output: JSON (parsowalne przez agenty).

---

## 4. Testy

### Unit testy: `tests/test_agent_bus.py`

- `test_send_and_receive_message` — send → inbox zwraca wiadomość
- `test_inbox_filters_by_role` — wiadomości do innej roli nie widoczne
- `test_inbox_filters_by_status` — unread vs read vs archived
- `test_mark_read` — status zmienia się, read_at ustawiony
- `test_archive_message` — status=archived
- `test_write_and_get_state` — zapis i odczyt
- `test_state_filters_by_type` — progress vs reflection vs backlog_item
- `test_state_metadata_json` — metadata dict → JSON → dict roundtrip
- `test_flag_for_human` — tworzy message do 'human' z type='flag_human'
- `test_get_state_limit` — domyślnie 20, respektuje parametr
- `test_get_state_ordering` — najnowsze pierwsze
- `test_empty_inbox` — pusta lista, nie error
- `test_db_created_if_not_exists` — nowa baza z tabelami
- `test_wal_mode` — PRAGMA journal_mode zwraca 'wal'

### Integration testy: `tests/test_agent_bus_cli.py`

- `test_cli_send_and_inbox` — pełny roundtrip przez CLI
- `test_cli_write_state` — zapis i odczyt stanu przez CLI
- `test_cli_flag` — flag_for_human przez CLI

Łącznie: ~17 testów. Baza tymczasowa (tmp_path fixture).

---

## 5. Migracja

**Podejście: opcja C (stopniowe)**

Faza 1 NIE migruje istniejących danych. Zmiana:
- Agenty od teraz piszą suggestions/progress/refleksje do DB przez agent_bus
- Stare pliki .md zostają jako archiwum read-only (nie usuwamy, nie edytujemy)
- Developer na starcie sesji czyta inbox z DB zamiast plików suggestions

**Pliki które przestają być aktywnie aktualizowane:**
- `documents/erp_specialist/erp_specialist_suggestions.md` → nowe wpisy do DB
- `documents/analyst/analyst_suggestions.md` → nowe wpisy do DB
- `documents/dev/progress_log.md` → nowe wpisy do DB (type=progress)
- `documents/dev/backlog.md` → nowe wpisy do DB (type=backlog_item)

**Pliki które zostają bez zmian:**
- Wszystkie pliki .md z wytycznymi i workflow (CLAUDE.md, DEVELOPER.md, itd.)
- `documents/dev/handoff_db_architecture.md` — archiwum decyzji

---

## 6. Zmiany w istniejących dokumentach

Minimalne — dodanie informacji o agent_bus do workflow startowego.

### CLAUDE.md
- Dodanie `mrowisko.db` do sekcji Projekt (1 linia)

### DEVELOPER.md
- Krok startowy: "Sprawdź inbox z DB" zamiast "Przeczytaj pliki suggestions"

### ERP_SPECIALIST.md
- Krok refleksji: "Dopisz do DB przez agent_bus" zamiast "Dopisz do erp_specialist_suggestions.md"

### ANALYST.md
- Analogiczna zmiana jak ERP_SPECIALIST.md

Każda z tych zmian to 2-3 linie. Dokumenty chronione — zatwierdzenie przed edycją.

---

## 7. Kolejność implementacji

1. `tools/lib/agent_bus.py` — klasa AgentBus
2. `tests/test_agent_bus.py` — unit testy (TDD: testy pierwsze)
3. `tools/agent_bus_cli.py` — CLI wrapper
4. `tests/test_agent_bus_cli.py` — integration testy CLI
5. Zmiany w dokumentach ról (po zatwierdzeniu)
6. Commit + push

---

## 8. Otwarte wątki z kontekstu

Poniższe NIE wchodzą w zakres tej implementacji, ale są aktywne w backlogu:

- **Backlog #1** LOOM publikacja GitHub — niezależne, bez blokad
- **Backlog #2–6** Bot (NO_SQL, kontekst firmowy, reload, routing, fallback) — niezależne
- **Backlog #7** Sygnatury narzędzi — agent_bus_cli.py to nowe narzędzie, więc dodajemy je do ewentualnej listy
- **Backlog #9** Brak backlogu per-rola — agent_bus rozwiązuje to strukturalnie (filtr role+type w DB)
- **Backlog #12** Eval harness — niezależne, ale agent_bus ułatwi trace
- **Backlog #13** Audit trail — agent_bus.messages + state to fundament pod przyszły audit
- **Niezacommitowane zmiany** z sesji Metodologa (CLAUDE.md, backlog.md, SPIRIT.md, methodology_progress.md, research_results_agi_horizon.md) — do scommitowania przed rozpoczęciem

---

## .gitignore

Dodać `mrowisko.db` do .gitignore — baza jest lokalna, nie wersjonowana (jak docs.db).
