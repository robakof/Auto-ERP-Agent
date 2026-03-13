# Agent Bus — Faza 1.5: Przebudowa schematu DB

## Stan obecny

Dwie tabele w `mrowisko.db`:

```
messages   — komunikacja agent↔agent i eskalacja do human
state      — worek na wszystko: type IN (progress, reflection, backlog_item)
```

Problem: `state` nie ma struktury właściwej dla każdego typu.
Backlog items nie mają statusu, tytułu, priorytetu. Refleksje nie mają odbiorców.
Nie da się zarządzać backlogiem ani przeglądać sugestii bez parsowania `content`.

---

## Nowy schemat

### Zostaje bez zmian

```
messages (id, sender, recipient, type, content, status, session_id, created_at, read_at)
```

### Nowe tabele (zastępują `state`)

```
suggestions
    id               INTEGER PK
    author           TEXT NOT NULL          -- rola autora
    recipients       TEXT                   -- JSON array | null (null = do developera)
    content          TEXT NOT NULL
    status           TEXT DEFAULT 'open'    -- open | in_backlog | rejected | implemented
    backlog_id       INTEGER FK -> backlog
    session_id       TEXT
    created_at       TEXT DEFAULT now

backlog
    id               INTEGER PK
    title            TEXT NOT NULL
    content          TEXT NOT NULL
    area             TEXT                   -- Bot | Arch | Dev | ERP | ...
    value            TEXT                   -- wysoka | srednia | niska
    effort           TEXT                   -- mala | srednia | duza
    status           TEXT DEFAULT 'planned' -- planned | in_progress | done | cancelled
    source_id        INTEGER FK -> suggestions
    created_at       TEXT DEFAULT now
    updated_at       TEXT DEFAULT now

session_log
    id               INTEGER PK
    role             TEXT NOT NULL
    content          TEXT NOT NULL
    session_id       TEXT
    created_at       TEXT DEFAULT now
```

### Migracja obecnych danych z `state`

| Obecny typ | Cel |
|---|---|
| `backlog_item` (27 wpisów) | → `backlog` (status=planned) + `suggestions` (status=in_backlog) |
| `reflection` | → `suggestions` (status=open) |
| `progress` | → `session_log` |

---

## Nowe komendy CLI

```bash
# Sugestie
python tools/agent_bus_cli.py suggest --from erp_specialist --content-file tmp.md
python tools/agent_bus_cli.py suggestions --status open
python tools/agent_bus_cli.py suggest-status --id 5 --status in_backlog

# Backlog
python tools/agent_bus_cli.py backlog-add --title "..." --area Bot --value wysoka --effort mala --content-file tmp.md
python tools/agent_bus_cli.py backlog --status planned
python tools/agent_bus_cli.py backlog-update --id 3 --status done

# Session log
python tools/agent_bus_cli.py log --role developer --content-file tmp.md

# Istniejące (bez zmian)
python tools/agent_bus_cli.py send / inbox / flag
```

---

## Plan implementacji

**Kolejność — TDD:**

1. Nowe tabele w `agent_bus.py` + testy (zachować stare `state` do migracji)
2. Skrypt migracyjny `tools/migrate_state.py` — state → suggestions + backlog + session_log
3. Nowe komendy w `agent_bus_cli.py` + testy CLI
4. Usunięcie `write-state` z CLI (lub deprecated z ostrzeżeniem)
5. Aktualizacja dokumentów ról (CLAUDE.md, ERP_SPECIALIST.md, ANALYST.md, METHODOLOGY.md)

**Zachowanie `state` podczas migracji:** tabela zostaje do czasu potwierdzenia że migracja jest kompletna. Usunięcie w osobnym commicie.

---

## Decyzje

1. `write-state` — usunąć od razu po migracji (brak deprecated)
2. `backlog-add` — `--source-id` jako opcjonalny argument (link sugestii → backlog)
3. `suggestions` — domyślnie wszyscy autorzy, opcjonalny filtr `--from <rola>`
