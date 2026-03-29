# Plan: Poke v2 — redesign mechanizmu poke

## Problem
Poke v1 to fire-and-forget sendText + PreToolUse intercept. Brak śledzenia, adresowanie po roli,
treść inline, przerywa pracującego agenta. Nie odpowiada potrzebom koordynacji.

## Design (zatwierdzony przez użytkownika)
Szczegóły: `documents/human/reports/poke_mechanism.md`

## Zakres zmian

### 1. Nowa tabela `pokes` w DB

```sql
CREATE TABLE IF NOT EXISTS pokes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      TEXT NOT NULL,
    ref_type        TEXT NOT NULL,
    ref_id          INTEGER NOT NULL,
    poke_type       TEXT NOT NULL DEFAULT 'poke',
    status          TEXT NOT NULL DEFAULT 'pending',
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    delivered_at    TEXT,
    CHECK (ref_type IN ('backlog', 'message')),
    CHECK (poke_type IN ('poke', 'poke_stop')),
    CHECK (status IN ('pending', 'delivered', 'acted_on'))
);
```

Migracja w `agent_bus.py` ensure_schema.

### 2. Redesign CLI `poke` w agent_bus_cli.py

```
# Normalny poke — budzi stojącego, czeka na pracującego
py tools/agent_bus_cli.py poke --session-id <id> --ref backlog:205
py tools/agent_bus_cli.py poke --session-id <id> --ref message:461

# Awaryjny stop
py tools/agent_bus_cli.py poke-stop --session-id <id> --reason "powód"
```

Usunięte: `--from`, `--role`, `--message`, `--message-file`.
Dodane: `--session-id`, `--ref`.

Flow `poke`:
1. Sprawdź display_status agenta (z v_agent_status)
2. Jeśli stale/dead → sendText natychmiast (status=delivered)
3. Jeśli working → zapisz jako pending (dostarczenie później)
4. Tekst wstrzyknięty: `[POKE] Sprawdź backlog #205` lub `[POKE] Sprawdź wiadomość #461`

Flow `poke-stop`:
1. PreToolUse intercept (deny z reason) — bez zmian w mechanizmie
2. Zapisz do tabeli pokes z poke_type=poke_stop

### 3. Mechanizm dostarczania pending poke

Opcje:
A) `render_dashboard.py` — odpala się na każdym user prompt. Sprawdza pending pokes,
   jeśli agent stale → dostarcza. Zero nowej infrastruktury.
B) Osobny skrypt wywoływany z `on_user_prompt.py` lub `post_tool_use.py`.

Rekomendacja: opcja A (dashboard render jako side-effect).

### 4. Zmiany w pre_tool_use.py

Obecny `_check_poke()` (PreToolUse intercept type=poke z messages) → zamienić na:
- Sprawdź tabele `pokes` WHERE poke_type='poke_stop' AND status='pending'
- Jeśli jest → deny z reason
- Zwykły poke (poke_type='poke') NIE jest obsługiwany przez PreToolUse — czeka

### 5. Extension — bez zmian
`pokeAgent` URI handler zostaje jak jest. CLI decyduje kiedy wysłać.

### 6. vscode_uri.py — bez zmian
Parametry `--terminal-name`, `--message` zostają.

## Czego NIE robimy
- Instrukcje w promptach (PE, osobny backlog #200)
- Mechanizm acted_on (agent potwierdza realizację — przyszłość)

## Exit gate
- [ ] Tabela pokes w DB
- [ ] CLI poke z --session-id --ref
- [ ] CLI poke-stop z --session-id --reason
- [ ] Pending delivery w render_dashboard
- [ ] pre_tool_use sprawdza poke_stop zamiast messages type=poke
- [ ] Testy PASS
