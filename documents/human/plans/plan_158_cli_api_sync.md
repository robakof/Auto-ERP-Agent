# Plan #158: CLI-API sync guard + single source of truth

## Krok 1: Test-guard (MVP)

Test introspektuje publiczne metody AgentBus i porównuje z dispatch dict w CLI.

### Mapowanie API → CLI

Nie każda metoda AgentBus powinna mieć komendę CLI (np. `transaction()`, `close()`,
`register_instance()` to API wewnętrzne). Potrzebna jest explicit lista wykluczeń.

```python
# Metody AgentBus WYŁĄCZONE z CLI (wewnętrzne API):
INTERNAL_METHODS = {
    "transaction", "close",
    # Instance management (runner-only)
    "register_instance", "heartbeat", "set_instance_busy",
    "set_instance_idle", "terminate_instance",
    "get_free_instances", "get_all_instances",
    "claim_task", "unclaim_task", "get_pending_tasks",
    # Conversation/session (used by session_init, not CLI)
    "upsert_session", "get_session_trace",
    "add_conversation_entry", "get_conversation",
    # Aliases (covered by other commands)
    "mark_message_read",  # alias for mark_read
    "get_session_log",    # covered by get_session_logs
    "get_session_logs_init",  # used by session_init
    "get_messages",       # covered by inbox with filters
}
```

### Test

```python
def test_cli_covers_all_public_api():
    """Every public AgentBus method has a CLI command (or is explicitly excluded)."""
    bus_methods = {
        name for name in dir(AgentBus)
        if not name.startswith("_") and callable(getattr(AgentBus, name))
    }
    cli_dispatch = set(COMMANDS.keys())  # extract from agent_bus_cli
    uncovered = bus_methods - INTERNAL_METHODS - MAPPED_METHODS
    assert uncovered == set(), f"AgentBus methods without CLI coverage: {uncovered}"
```

Wymaga wyeksportowania dispatch dict i mapowania method→command z CLI.

### Lokalizacja

`tests/test_agent_bus_cli.py::TestCliApiSync`

---

## Krok 2: Single source of truth — dekorator CLI

### Architektura

Dekorator `@cli_command` na metodach AgentBus definiuje metadane CLI.
`agent_bus_cli.py` iteruje dekoratory, buduje argparse, dispatchuje automatycznie.

### Dekorator

```python
# core/cli_meta.py

@dataclass
class CliArg:
    name: str                    # --from, --role, --id
    dest: str = None             # Python name (sender, role)
    type: type = str
    required: bool = False
    default: Any = None
    choices: list = None
    help: str = ""
    positional: bool = False

@dataclass
class CliMeta:
    command: str                 # "send", "backlog-add"
    help: str
    args: list[CliArg]
    content_mode: str = None     # "content"|"content_file"|"both"|None
    mutually_exclusive: list[list[str]] = None

def cli_command(meta: CliMeta):
    """Decorator that attaches CLI metadata to an AgentBus method."""
    def decorator(func):
        func._cli_meta = meta
        return func
    return decorator
```

### Przykład użycia

```python
class AgentBus:
    @cli_command(CliMeta(
        command="send",
        help="Send a message to a role",
        args=[
            CliArg("--from", dest="sender", required=True),
            CliArg("--to", required=True),
            CliArg("--type", default="suggestion"),
            CliArg("--session-id", dest="session_id"),
            CliArg("--reply-to", dest="reply_to_id", type=int),
        ],
        content_mode="both",  # --content XOR --content-file
    ))
    def send_message(self, sender, recipient, content, ...):
        ...
```

### Generator CLI

```python
# agent_bus_cli.py (nowa wersja, ~80 linii)

def build_parser(bus_class):
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    dispatch = {}

    for name in dir(bus_class):
        method = getattr(bus_class, name)
        meta = getattr(method, "_cli_meta", None)
        if meta is None:
            continue
        sub = subparsers.add_parser(meta.command, help=meta.help)
        for arg in meta.args:
            # ... add_argument based on CliArg
        dispatch[meta.command] = (name, meta)

    return parser, dispatch

def main():
    bus = AgentBus()
    parser, dispatch = build_parser(AgentBus)
    args = parser.parse_args()
    method_name, meta = dispatch[args.command]
    # Map args → method kwargs, call, print JSON
```

### Komendy wymagające custom logic

Nie wszystkie komendy to proste delegacje. Wyjątki:

| Komenda | Custom logic |
|---|---|
| `send` | `--to all` broadcast |
| `inbox` | M3 auto mark-read, `--sender` post-filter, `--id` shortcut |
| `handoff` | Budowanie content z --phase/--status/--summary |
| `suggest-bulk` | Parsowanie blokowego pliku |
| `backlog-update` | `--depends-on 0` → None, dependency warning |
| `flag` | Budowanie content z --reason/--urgency |

**Podejście:** Dekorator obsługuje proste delegacje automatycznie.
Komendy z custom logic mają `handler` callback w CliMeta:

```python
@dataclass
class CliMeta:
    ...
    handler: Callable = None  # Custom handler, None = auto-delegate
```

### Fazy implementacji

1. **core/cli_meta.py** — CliArg, CliMeta, cli_command decorator
2. **Dekoratory na prostych metodach** — mark_read, mark_unread, delete, gaps, gap_add,
   gap_resolve, workflow_start, step_log, workflow_end, execution_status,
   interrupted_workflows, log, session_logs, backlog, backlog_add, suggestions,
   suggest_status (~16 metod)
3. **Generator w agent_bus_cli.py** — build_parser + auto-dispatch
4. **Migracja custom commands** — send, inbox, handoff, flag, suggest-bulk,
   backlog-update z handler callbacks
5. **Usunięcie starego kodu** — cmd_* functions, ręczny argparse
6. **Test sync guard** — krok 1, ale teraz testuje _cli_meta zamiast dispatch dict

### Szacunek

- Nowy kod: ~150 linii (cli_meta.py ~50, dekoratory ~20 per komenda, generator ~80)
- Usunięty kod: ~550 linii (stary CLI)
- Netto: ~400 linii mniej
- Testy: istniejące 143 testy CLI = regression guard

### Ryzyka

1. **Dekoratory na facade** — AgentBus to facade delegujący do services.
   Dekorator na facade jest OK — to warstwa CLI, nie domena.
2. **Backward compat** — external callers (hooks, CLAUDE.md) używają `py tools/agent_bus_cli.py send ...`.
   Interface nie zmienia się — zmienia się tylko implementacja.
3. **Bulk commands** — suggest-bulk, backlog-add-bulk, backlog-update-bulk
   mają złożoną logikę. Mogą zostać jako explicit handlers.

### Kolejność realizacji

```
Faza 1: cli_meta.py + dekoratory na 5 prostych metod + generator (proof of concept)
   ↓  test: istniejące testy passują
Faza 2: dekoratory na pozostałe proste metody
   ↓  test: istniejące testy passują
Faza 3: migracja custom commands (send, inbox, handoff, flag)
   ↓  test: istniejące testy passują
Faza 4: migracja bulk commands + cleanup
   ↓  test: 143 PASS + sync guard test
Faza 5: usunięcie starego kodu
   ↓  test: 143+ PASS
```

Każda faza = commit + testy. Backward compat gwarantowany przez istniejące 143 testy.
