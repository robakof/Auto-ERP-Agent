# Plan: Konfigurowalny session_init

**Trigger:** User feedback + PE msg #224
**Scope:** Redesign session_init.py — from "doc only" to "full context per-role config"

---

## Problem Statement

**Obecnie:**
- Agent wywołuje `session_init.py --role X` → dostaje tylko `doc_content`
- Potem ręcznie wywołuje 4-6 komend CLI w session_start:
  - `inbox --role X`
  - `backlog --area Y --status planned`
  - `session-logs --role X --limit 3`
  - `session-logs --role X --offset 3 --limit 7 --metadata-only`
  - `session-logs --limit 20 --metadata-only` (tylko dla ról nie-wykonawczych)
  - `inbox --role human` (flagi)

**Ryzyko:**
- Agent może pominąć krok (błąd proceduralny)
- Pomylić parametry
- Session_start różni się między rolami (brak spójności)

**PE pain point:**
- Każda zmiana ilości wiadomości/logów wymaga edycji 6 plików promptów
- Brak centralnej konfiguracji

---

## Solution: Configurable session_init

**Jeden JSON config** (`config/session_init_config.json`) kontroluje CO i ILE każda rola dostaje na starcie.

**PE edytuje config** zamiast 6 promptów — centralna kontrola.

**Agent wywołuje:**
```bash
py tools/session_init.py --role architect
```

**Dostaje pełny kontekst:**
```json
{
  "ok": true,
  "session_id": "abc123",
  "role": "architect",
  "doc_path": "documents/architect/ARCHITECT.md",
  "doc_content": "...",
  "context": {
    "inbox": {
      "messages": [...],
      "count": 5
    },
    "backlog": {
      "items": [...],
      "count": 3
    },
    "session_logs": {
      "own_full": [...],
      "own_metadata": [...],
      "cross_role": [...]
    },
    "flags_human": {
      "items": [...],
      "count": 0
    }
  }
}
```

**Session_start promptu:** 1 komenda zamiast 6.

---

## Config Structure

**File:** `config/session_init_config.json`

**Przykład:**
```json
{
  "architect": {
    "inbox": {
      "enabled": true,
      "limit": 10,
      "status": "unread"
    },
    "backlog": {
      "enabled": true,
      "areas": ["Arch"],
      "status": "planned",
      "limit": 20
    },
    "session_logs": {
      "own_full": {
        "enabled": true,
        "limit": 3
      },
      "own_metadata": {
        "enabled": true,
        "offset": 3,
        "limit": 7
      },
      "cross_role": {
        "enabled": true,
        "limit": 20
      }
    },
    "flags_human": {
      "enabled": true
    }
  },
  "developer": {
    "inbox": {
      "enabled": true,
      "limit": 10,
      "status": "unread"
    },
    "backlog": {
      "enabled": true,
      "areas": ["Dev", "Arch"],
      "status": "planned",
      "limit": 20
    },
    "session_logs": {
      "own_full": {
        "enabled": true,
        "limit": 3
      },
      "own_metadata": {
        "enabled": true,
        "offset": 3,
        "limit": 7
      },
      "cross_role": {
        "enabled": true,
        "limit": 20
      }
    },
    "flags_human": {
      "enabled": true
    }
  },
  "erp_specialist": {
    "inbox": {
      "enabled": true,
      "limit": 5,
      "status": "unread"
    },
    "backlog": {
      "enabled": true,
      "areas": ["ERP"],
      "status": "planned",
      "limit": 10
    },
    "session_logs": {
      "own_full": {
        "enabled": true,
        "limit": 3
      },
      "own_metadata": {
        "enabled": false
      },
      "cross_role": {
        "enabled": false
      }
    },
    "flags_human": {
      "enabled": true
    }
  },
  "analyst": {
    "inbox": {
      "enabled": true,
      "limit": 5,
      "status": "unread"
    },
    "backlog": {
      "enabled": true,
      "areas": ["Analyst"],
      "status": "planned",
      "limit": 10
    },
    "session_logs": {
      "own_full": {
        "enabled": true,
        "limit": 3
      },
      "own_metadata": {
        "enabled": false
      },
      "cross_role": {
        "enabled": false
      }
    },
    "flags_human": {
      "enabled": true
    }
  },
  "prompt_engineer": {
    "inbox": {
      "enabled": true,
      "limit": 10,
      "status": "unread"
    },
    "backlog": {
      "enabled": true,
      "areas": ["Prompts"],
      "status": "planned",
      "limit": 20
    },
    "session_logs": {
      "own_full": {
        "enabled": true,
        "limit": 3
      },
      "own_metadata": {
        "enabled": true,
        "offset": 3,
        "limit": 7
      },
      "cross_role": {
        "enabled": true,
        "limit": 20
      }
    },
    "flags_human": {
      "enabled": true
    }
  },
  "metodolog": {
    "inbox": {
      "enabled": true,
      "limit": 10,
      "status": "unread"
    },
    "backlog": {
      "enabled": true,
      "areas": ["Methodology"],
      "status": "planned",
      "limit": 20
    },
    "session_logs": {
      "own_full": {
        "enabled": true,
        "limit": 3
      },
      "own_metadata": {
        "enabled": true,
        "offset": 3,
        "limit": 7
      },
      "cross_role": {
        "enabled": true,
        "limit": 20
      }
    },
    "flags_human": {
      "enabled": true
    }
  }
}
```

**Zasady config:**
- `enabled: false` → sekcja pomijana (nie wywołuj API)
- `limit`, `offset`, `status`, `areas` → przekazywane do AgentBus
- Role wykonawcze (ERP, Analyst) → `cross_role: disabled` (oszczędność context window)
- Role meta (Architect, Dev, PE, Metodolog) → `cross_role: enabled` (szerszy obraz)

---

## Implementation

### 1. File structure

**Nowy plik:**
```
config/
  session_init_config.json  ← nowy
```

### 2. session_init.py changes

**Przed:**
```python
def session_init(role: str, db_path: str = "mrowisko.db"):
    doc_path = get_doc_path(role)
    doc_content = read_doc(doc_path)
    session_id = generate_session_id()

    return {
        "ok": True,
        "session_id": session_id,
        "role": role,
        "doc_path": doc_path,
        "doc_content": doc_content,
    }
```

**Po:**
```python
import json
from tools.lib.agent_bus import AgentBus

def load_config(role: str) -> dict:
    """Load session_init config for given role."""
    with open("config/session_init_config.json", "r", encoding="utf-8") as f:
        config = json.load(f)

    if role not in config:
        raise ValueError(f"Role '{role}' not found in session_init_config.json")

    return config[role]

def get_context(role: str, config: dict, db_path: str) -> dict:
    """Gather all context per config."""
    bus = AgentBus(db_path)
    context = {}

    # Inbox
    if config.get("inbox", {}).get("enabled", False):
        inbox_config = config["inbox"]
        messages = bus.get_messages(
            recipient=role,
            status=inbox_config.get("status", "unread"),
            limit=inbox_config.get("limit", 10)
        )
        context["inbox"] = {
            "messages": messages,
            "count": len(messages)
        }

    # Backlog
    if config.get("backlog", {}).get("enabled", False):
        backlog_config = config["backlog"]
        items = []
        for area in backlog_config.get("areas", []):
            area_items = bus.get_backlog(
                area=area,
                status=backlog_config.get("status", "planned"),
                limit=backlog_config.get("limit", 20)
            )
            items.extend(area_items)

        context["backlog"] = {
            "items": items,
            "count": len(items)
        }

    # Session logs
    if config.get("session_logs", {}).get("own_full", {}).get("enabled", False):
        logs_config = config["session_logs"]

        # Own full
        own_full_config = logs_config.get("own_full", {})
        own_full = bus.get_session_logs(
            role=role,
            limit=own_full_config.get("limit", 3),
            metadata_only=False
        )

        # Own metadata (optional)
        own_metadata = []
        if logs_config.get("own_metadata", {}).get("enabled", False):
            own_meta_config = logs_config["own_metadata"]
            own_metadata = bus.get_session_logs(
                role=role,
                offset=own_meta_config.get("offset", 3),
                limit=own_meta_config.get("limit", 7),
                metadata_only=True
            )

        # Cross-role (optional)
        cross_role = []
        if logs_config.get("cross_role", {}).get("enabled", False):
            cross_config = logs_config["cross_role"]
            cross_role = bus.get_session_logs(
                limit=cross_config.get("limit", 20),
                metadata_only=True
            )

        context["session_logs"] = {
            "own_full": own_full,
            "own_metadata": own_metadata,
            "cross_role": cross_role
        }

    # Flags human
    if config.get("flags_human", {}).get("enabled", False):
        flags = bus.get_messages(recipient="human", status="unread")
        context["flags_human"] = {
            "items": flags,
            "count": len(flags)
        }

    return context

def session_init(role: str, db_path: str = "mrowisko.db"):
    # Load config
    config = load_config(role)

    # Get doc
    doc_path = get_doc_path(role)
    doc_content = read_doc(doc_path)

    # Generate session ID
    session_id = generate_session_id()

    # Get context
    context = get_context(role, config, db_path)

    return {
        "ok": True,
        "session_id": session_id,
        "role": role,
        "doc_path": doc_path,
        "doc_content": doc_content,
        "context": context,
    }
```

### 3. CLI support

**Optional flag:**
```bash
# Full context (default)
py tools/session_init.py --role architect

# Doc only (legacy mode, dla backward compatibility)
py tools/session_init.py --role architect --doc-only
```

**Implementation:**
```python
parser.add_argument("--doc-only", action="store_true",
                    help="Return only doc_content (legacy mode)")

if args.doc_only:
    # Skip context gathering
    return session_init_legacy(role=args.role, db_path=args.db)
else:
    return session_init(role=args.role, db_path=args.db)
```

---

## Backward Compatibility

**Existing calls:**
```bash
py tools/session_init.py --role architect
```

**Behavior:**
- **Przed:** Zwraca tylko `{doc_content, doc_path, session_id, role}`
- **Po:** Zwraca rozszerzony JSON z `context`

**Impact na agenta:**
- Agent ignoruje `context` jeśli prompt nie został zaktualizowany (graceful degradation)
- Stare prompty dalej działają (dostają `doc_content`)

**Migration path (PE):**
1. Developer wdraża konfigurowalny session_init
2. PE aktualizuje 1 rolę (np. Architect) — testuje
3. Jeśli działa → PE aktualizuje pozostałe 5 ról
4. Stare wywołania CLI w session_start można usunąć

---

## Benefits

### Dla PE:
- **Centralna kontrola** — 1 plik config zamiast 6 promptów
- **Eksperymentowanie** — zmiana limitu logów dla 1 roli → edit JSON, nie edit prompt
- **Spójność** — wszystkie role używają tej samej struktury session_init

### Dla Agenta:
- **Mniej błędów** — 1 wywołanie zamiast 6 (eliminuje ryzyko pomyłki)
- **Szybszy start** — wszystko w jednym response
- **Czytelniejszy kod** — session_start uproszczony do 1 linii

### Dla projektu:
- **Maintainability** — config JSON łatwiejszy do edycji niż prompty
- **Testability** — session_init można testować z różnymi configami
- **Scalability** — dodanie nowej roli = dodanie bloku do JSON

---

## Tests

**Unit tests (test_session_init.py):**

1. `test_load_config_valid_role` — verify config loads correctly
2. `test_load_config_invalid_role` — ValueError when role not in config
3. `test_get_context_inbox_enabled` — verify inbox returned when enabled
4. `test_get_context_inbox_disabled` — verify inbox skipped when disabled
5. `test_get_context_session_logs_full` — all 3 sections (own_full, own_metadata, cross_role)
6. `test_get_context_session_logs_partial` — only own_full (erp_specialist case)
7. `test_session_init_full_context` — full integration (doc + context)
8. `test_session_init_doc_only_flag` — legacy mode (--doc-only)

**Integration test:**
```python
def test_architect_session_init_full():
    """Architect gets: inbox, backlog (Arch area), session logs (all 3), flags."""
    result = session_init(role="architect", db_path="mrowisko.db")

    assert result["ok"] is True
    assert result["role"] == "architect"
    assert "doc_content" in result
    assert "context" in result

    context = result["context"]
    assert "inbox" in context
    assert "backlog" in context
    assert "session_logs" in context
    assert "flags_human" in context

    # Session logs structure
    assert "own_full" in context["session_logs"]
    assert "own_metadata" in context["session_logs"]
    assert "cross_role" in context["session_logs"]
```

---

## Deliverables

1. **Config file:** `config/session_init_config.json` (6 ról)
2. **Code:** `tools/session_init.py` rozszerzony o `get_context()`
3. **Tests:** `tests/test_session_init.py` (8 testów)
4. **Documentation:** Ten plan (handoff dla PE)
5. **Message do PE:** Notyfikacja że tool gotowy + instrukcja jak zaktualizować prompty

---

## Open Questions

1. **Czy backlog powinien filtrować po `status` też?**
   - Obecnie: `status="planned"` hardcoded w config
   - Alternatywa: `"status": ["planned", "in_progress"]` (lista)

2. **Czy dodać support dla suggestions w session_init?**
   - Use case: PE może chcieć widzieć open suggestions na starcie
   - Trade-off: więcej danych = większy context window

3. **Czy `--doc-only` jest potrzebne?**
   - Backward compatibility — ale agent ignoruje nieznane pola w JSON
   - Można pominąć jeśli nie potrzebne

---

## Next Steps

1. **User approval** tego planu
2. Utworzyć `config/session_init_config.json`
3. Rozszerzyć `tools/session_init.py`
4. Napisać testy
5. Commit + message do PE

---

**Estimated effort:** Średnia (2-3h implementation + 1h tests + 1h PE message/docs)

**Impact:** Wysoka — eliminuje 5 wywołań CLI w session_start dla każdej roli
