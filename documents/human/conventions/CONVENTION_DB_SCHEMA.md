---
convention_id: db-schema
version: "1.0"
status: draft
created: 2026-03-26
updated: 2026-03-26
author: architect
owner: architect
approver: dawid
audience: [developer, architect]
scope: "Nazewnictwo, struktura i migracje schematu mrowisko.db (SQLite)"
---

# CONVENTION_DB_SCHEMA — Konwencja schematu bazy danych

## TL;DR

- Nazwy tabel: snake_case, liczba mnoga (np. `messages`, `sessions`)
- Nazwy kolumn: snake_case, bez prefiksu tabeli
- PK: `id INTEGER PRIMARY KEY AUTOINCREMENT` (lub `TEXT PRIMARY KEY` dla UUIDów)
- FK: `{tabela_singular}_id` (np. `session_id`, `execution_id`)
- Timestamps: `TEXT NOT NULL DEFAULT (datetime('now'))`
- Migracje: numerowane, osobna pozycja per zmiana, komentarz z numerem backlogu
- CHECK constraints na każdym polu enumowym
- PRAGMAs: WAL, foreign_keys=ON, busy_timeout=3000

---

## Zakres

**Pokrywa:**
- Nazewnictwo tabel i kolumn w mrowisko.db
- Typy danych i wzorce kolumn (PK, FK, timestamps, enums)
- Indeksy
- Migracje (format, kolejność, idempotentność)
- PRAGMAs i ustawienia połączenia

**NIE pokrywa:**
- Logikę domenową encji (ADR-001, PATTERNS.md)
- Repository pattern i mapowanie entity↔row (CONVENTION_PYTHON)
- SQL w narzędziach (queries, raporty ERP)

---

## Reguły

### 01R: Nazwy tabel — snake_case, plural

Nazwy tabel w **snake_case** i **liczbie mnogiej**.

Dobrze: `messages`, `sessions`, `tool_calls`, `known_gaps`
Źle: `message`, `toolCall`, `KnownGaps`, `tbl_sessions`

**Znane wyjątki (legacy):** `backlog`, `state`, `trace`, `conversation` — istniejące tabele w liczbie pojedynczej. Rename wymaga migrację. Nie blokuje — nowe tabele MUSZĄ stosować regułę.

### 02R: Nazwy kolumn — snake_case, bez prefiksu tabeli

Kolumny w **snake_case**. Nie powtarzaj nazwy tabeli w kolumnie.

Dobrze: `messages.sender`, `sessions.started_at`
Źle: `messages.message_sender`, `sessions.session_started_at`

### 03R: Primary Key

Domyślnie: `id INTEGER PRIMARY KEY AUTOINCREMENT`.
UUID jako PK: `id TEXT PRIMARY KEY` — stosuj gdy ID generowany poza bazą (np. session_id z Claude Code).

### 04R: Foreign Key

Nazwa FK: `{tabela_w_liczbie_pojedynczej}_id`.

Dobrze: `session_id`, `execution_id`, `backlog_id`
Źle: `sessions_id`, `exec_id`, `fk_backlog`

Zawsze z explicit `REFERENCES`: `session_id TEXT REFERENCES sessions(id)`.

### 05R: Timestamps

Format: `TEXT NOT NULL DEFAULT (datetime('now'))`.
Nazwy: `created_at` (obowiązkowe), `updated_at` (jeśli tabela mutowalna), `ended_at` / `read_at` / `resolved_at` (specyficzne dla domeny).

SQLite nie ma natywnego typu datetime — TEXT z ISO 8601 (`YYYY-MM-DD HH:MM:SS`) jest standardem projektu.

### 06R: Enums — CHECK constraint

Każde pole z zamkniętym zbiorem wartości MUSI mieć CHECK constraint.

```sql
status TEXT NOT NULL DEFAULT 'planned',
CHECK (status IN ('planned', 'in_progress', 'done', 'cancelled', 'deferred'))
```

Dodanie nowej wartości enum = migracja (nowy CHECK constraint).

Pattern: Proactive Discovery — audit istniejących danych przed dodaniem CHECK (patrz PATTERNS.md).

### 07R: Indeksy

Nazewnictwo: `idx_{tabela}_{kolumny}`.

Dobrze: `idx_messages_recipient_status`, `idx_tool_calls_session`
Źle: `messages_idx1`, `index_on_messages`

Indeksuj: FK kolumny, kolumny filtrowane w WHERE, kolumny sortowane w ORDER BY.
UNIQUE index: gdy potrzebna deduplikacja (np. `idx_tool_calls_dedup`).

### 08R: Migracje — format

Migracje w liście `_MIGRATE_SQL` w `agent_bus.py` (docelowo: `core/database/migrations/`).

Każda migracja:
- Komentarz z numerem backlogu/ticketu: `# #147: Telemetry deduplication`
- Idempotentna gdzie możliwe (`IF NOT EXISTS`, `ADD COLUMN` z try/except)
- Jedno działanie per wpis (nie łącz schema change z data fix w jednym stringu)

```python
_MIGRATE_SQL = [
    # #147: Telemetry deduplication - unique constraint
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_tool_calls_dedup ON tool_calls(session_id, tool_name, timestamp)",
    # #146: Fix claimed status leak
    "UPDATE messages SET claimed_by = 'legacy-runner', status = 'unread' WHERE status = 'claimed'",
]
```

### 09R: Nowa tabela — checklist

Przed dodaniem nowej tabeli sprawdź:
1. Czy tabela nie duplikuje istniejącej (szukaj overlap)
2. Czy nazwa w plural snake_case (01R)
3. Czy PK zgodny z 03R
4. Czy FK z REFERENCES (04R)
5. Czy `created_at` timestamp (05R)
6. Czy enums mają CHECK (06R)
7. Czy indeksy na FK i filtrowanych kolumnach (07R)

### 10R: PRAGMAs — standard projektu

Każde połączenie do mrowisko.db MUSI ustawić:

```sql
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;
PRAGMA busy_timeout=3000;
```

WAL = współbieżność read+write. foreign_keys = integralność referencyjna. busy_timeout = odporność na lock contention przy wielu agentach.

### 11R: BEGIN IMMEDIATE dla write paths

Operacje zapisu w kontekście multi-agent POWINNY używać `BEGIN IMMEDIATE`:

```python
conn.execute("BEGIN IMMEDIATE")
conn.execute("UPDATE live_agents SET status = 'active' WHERE session_id = ?", (sid,))
conn.commit()
```

Dlaczego: `BEGIN IMMEDIATE` rezerwuje write lock na starcie transakcji. Bez tego SQLite może zwrócić `SQLITE_BUSY` w środku transakcji (po partial work). Z `BEGIN IMMEDIATE` — albo lock dostaniesz od razu, albo dostaniesz busy od razu (bez zmarnowanej pracy).

Dla pojedynczych statementów (jeden INSERT/UPDATE) — opcjonalne (statement sam jest transakcją).

---

## Przykłady

### Przykład 1: Nowa tabela per konwencję

```sql
CREATE TABLE IF NOT EXISTS invocations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    invoker_type    TEXT NOT NULL,
    invoker_id      TEXT NOT NULL,
    target_role     TEXT NOT NULL,
    task            TEXT NOT NULL,
    session_id      TEXT REFERENCES sessions(id),
    status          TEXT NOT NULL DEFAULT 'pending',
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    ended_at        TEXT,
    CHECK (invoker_type IN ('human', 'agent', 'orchestrator')),
    CHECK (status IN ('pending', 'approved', 'running', 'completed', 'failed', 'rejected'))
);

CREATE INDEX IF NOT EXISTS idx_invocations_status ON invocations(status);
CREATE INDEX IF NOT EXISTS idx_invocations_session ON invocations(session_id);
```

### Przykład 2: Migracja — dodanie kolumny

```python
# #192: Agent Launcher — invocation tracking
"ALTER TABLE sessions ADD COLUMN parent_invocation_id INTEGER REFERENCES invocations(id)",
```

---

## Antywzorce

### 01AP: Tabela w singular

Nowa tabela `invocation` zamiast `invocations`. Niespójne z większością schematu.

### 02AP: Enum bez CHECK

```sql
status TEXT NOT NULL DEFAULT 'open'
-- brak CHECK → dowolna wartość, brak fail-fast
```

### 03AP: Migracja bez komentarza

```python
"ALTER TABLE messages ADD COLUMN reply_to_id INTEGER"
-- Kto? Kiedy? Dlaczego? Brak kontekstu.
```

### 04AP: Mix schema + data fix w jednym stringu

```python
"ALTER TABLE messages ADD COLUMN claimed_by TEXT; UPDATE messages SET claimed_by='legacy' WHERE status='claimed'"
-- Dwa działania w jednym → trudne do debug, idempotentność zagubiona
```

---

## Changelog

| Wersja | Data | Zmiany |
|---|---|---|
| 1.1 | 2026-03-26 | +11R BEGIN IMMEDIATE dla write paths. Research potwierdził: snake_case, CHECK na enumach, idx_ naming OK. Plural vs singular — spójność ważniejsza niż wybór. |
| 1.0 | 2026-03-26 | Początkowa wersja — 10 reguł, 2 przykłady, 4 antywzorce. Baseline: 14 tabel w mrowisko.db. |
