# Plan: Warstwa samoobserwacji mrowiska — moduł trace

**Duch projektu:** "Wiedza musi przetrwać sesję, model i firmę." (SPIRIT.md zasada 3)
Mrowisko nie może analizować swojej pracy jeśli ta praca znika po każdej sesji.
Ten moduł to pierwsza warstwa samooptymalizacji — rój zaczyna widzieć sam siebie.

---

## Cel

Parser transkryptów sesji (.jsonl) → strukturyzowane dane w mrowisko.db.
Fundamentem są relacje: sesja → rola → wywołania narzędzi → tokeny → błędy.
W przyszłości: połączenie z backlogiem, workflow, widokami BI — analiza co zajmuje
czas, gdzie agenci się blokują, co kosztuje kontekst.

---

## Odkrycia z inspekcji

### Struktura progress events
`progress` zawiera wyłącznie hook_progress (które narzędzie wywołało hook) i bash_progress
(output Basha w trakcie). **Brak info o blokadach** — blokady są w `tool_result` z
`is_error=true` w wiadomościach user.

### Problem session_id
Dwa różne identyfikatory sesji:

| ID | Format | Źródło | Przykład |
|----|--------|--------|---------|
| `our_session_id` | 12 hex | `session_init.py` | `d5cb7d1c234d` |
| `claude_session_id` | UUID | Claude Code | `ee7a6456-7ecd-...` |

`/clear` w Claude Code tworzy nową sesję (nowe UUID, nowy .jsonl).
Nasze `session_init` też tworzy nowe ID — są już zsynchronizowane z /clear.

**Łącznik:** `on_stop.py` otrzymuje `transcript_path` zawierający `claude_session_id`
w nazwie pliku. Musimy zapisywać to mapowanie do DB.

### Dostęp do .jsonl
Pliki w `~/.claude/projects/<hash>/` — poza projektem, niedostępne dla agentów.
Jedyna trwała ścieżka: sparsować do mrowisko.db przy zamknięciu sesji (on_stop.py).

### Zmiana narzędzia = utrata danych?
Bez parsowania: tak. Po sparsowaniu do DB: dane nasze niezależnie od narzędzia.

---

## Schemat bazy — nowe tabele

```
sessions
├── id (our_session_id, TEXT PK)        ← z session_init
├── claude_session_id (TEXT)            ← z transcript_path w on_stop
├── role (TEXT)                         ← z session_init
├── transcript_path (TEXT)             ← pełna ścieżka .jsonl
├── started_at (TEXT)
└── ended_at (TEXT)

tool_calls
├── id (INTEGER PK AUTOINCREMENT)
├── session_id (FK → sessions.id)
├── tool_name (TEXT)                    ← Read/Write/Edit/Bash/Glob/Grep...
├── input_summary (TEXT)               ← file_path / command (skrócone do 200 znaków)
├── is_error (INTEGER 0/1)
├── tokens_out (INTEGER)               ← z message.usage.output_tokens tury
└── timestamp (TEXT)

token_usage
├── id (INTEGER PK AUTOINCREMENT)
├── session_id (FK → sessions.id)
├── turn_index (INTEGER)
├── input_tokens (INTEGER)
├── output_tokens (INTEGER)
├── cache_read_tokens (INTEGER)
├── cache_create_tokens (INTEGER)
├── duration_ms (INTEGER)              ← z system turn_duration
└── timestamp (TEXT)
```

**Relacje z istniejącymi tabelami:**
- `sessions.id` = `conversation.session_id` — wiadomości sesji
- `sessions.id` = `session_log.session_id` — logi ról
- `sessions.role` — filtry per rola w przyszłych raportach

---

## Przykładowe wartości (dla Excela)

### sessions

| id | claude_session_id | role | started_at |
|----|------------------|------|------------|
| d5cb7d1c234d | ee7a6456-7ecd-49fd... | developer | 2026-03-15 12:00:00 |
| a6476f8f9e66 | ccb915c1d19b... | erp_specialist | 2026-03-15 11:00:00 |

### tool_calls

| id | session_id | tool_name | input_summary | is_error |
|----|-----------|-----------|---------------|---------|
| 1 | d5cb7d1c234d | Read | documents/erp_specialist/ERP_SPECIALIST.md | 0 |
| 2 | d5cb7d1c234d | Bash | python tools/agent_bus_cli.py backlog | 0 |
| 3 | d5cb7d1c234d | Edit | CLAUDE.md (stara treść → nowa) | 0 |
| 4 | a6476f8f9e66 | Read | solutions/bi/TraNag/TraNag_draft.sql | 0 |
| 5 | a6476f8f9e66 | Bash | python tools/sql_query.py ... | 1 |

### token_usage

| session_id | turn_index | input_tokens | output_tokens | cache_read | duration_ms |
|-----------|-----------|-------------|--------------|-----------|------------|
| d5cb7d1c234d | 1 | 12500 | 340 | 8200 | 4200 |
| d5cb7d1c234d | 2 | 13100 | 180 | 9100 | 2800 |

---

## Komponenty

### 1. `on_stop.py` — rozszerzenie (istniejące)
Dodać: po zapisaniu last_assistant_message → wywołaj parser na `transcript_path`.

### 2. `tools/jsonl_parser.py` — nowe
Wejście: ścieżka do .jsonl
Wyjście: wypełnienie tabel `sessions`, `tool_calls`, `token_usage` w mrowisko.db

Parsuje:
- `assistant` z `tool_use` → `tool_calls`
- `user` z `tool_result.is_error=true` → `tool_calls.is_error=1`
- `assistant.message.usage` + `system.durationMs` → `token_usage`
- metadane sesji → `sessions`

### 3. `tools/render.py` — rozszerzenie
Dodać: `render.py session-trace --session <id>` → XLSX z zakładkami:
- Summary (sesja, rola, łączne tokeny, czas)
- ToolCalls (lista wywołań z błędami)
- TokenUsage (per tura)

---

## Poza zakresem (teraz)

- Pattern detection (PASS vs BLOCKED) — gdy mamy 20+ sesji
- Korelacja z backlogiem (które zadanie = która sesja) — wymaga tagowania sesji
- Analiza zużycia kontekstu per plik — następny krok po zebraniu danych

---

## Kolejność

1. Schemat DB (migracja w `agent_bus.py`) + testy
2. `jsonl_parser.py` + testy
3. Rozszerzenie `on_stop.py` — automatyczny parse po sesji
4. Połączenie `our_session_id` ↔ `claude_session_id` przez `on_stop` hook
5. `render.py session-trace` — widok dla człowieka
6. Commit + Excel ze schematem dla usera
