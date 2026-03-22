# Plan implementacji: Domain Model (ADR-001)

**Backlog:** #115
**ADR:** documents/architect/ADR-001-domain-model.md
**Data utworzenia:** 2026-03-22
**Owner:** Developer
**Status:** Planowanie

---

## Cel

Przejście z architektury dict-based na Domain Model oparty o klasy (dataclasses).
Przygotowanie architektury pod wieloagentowość (mrowisko_runner).

---

## Kamienie milowe

### Milestone 1: Fundament (Faza 0)

**Scope:**
- Struktura katalogów `core/`
- Klasy bazowe: `Entity`, `Status`, wyjątki domenowe
- Encje komunikacji: `Suggestion`, `BacklogItem`, `Message` z enumerami
- Testy jednostkowe encji (walidacja, state transitions)

**Deliverables:**
```
core/
├── __init__.py
├── entities/
│   ├── __init__.py
│   ├── base.py            # Entity, Status
│   ├── messaging.py       # Message, Suggestion, BacklogItem
│   └── __init__ exports
├── exceptions.py          # DomainError, InvalidStateError, etc.
└── README.md              # Dokumentacja core/
tests/
└── core/
    └── test_entities.py   # Testy jednostkowe
```

**Definition of Done:**
- [ ] Wszystkie encje z ADR-001 (warstwy 1-2) zaimplementowane
- [ ] `suggestion.implement()`, `backlog_item.start()`, `message.mark_read()` działają
- [ ] Testy pokrywają happy path + edge cases (nieprawidłowe stany)
- [ ] Testy przechodzą 100%
- [ ] Commit + push

**Zależności:** brak

**Estymata:** 1 sesja (4-6h)

---

### Milestone 2: Repozytoria (Faza 1)

**Scope:**
- Abstrakcja `Repository[T]`
- `SuggestionRepository`, `BacklogRepository`, `MessageRepository`
- Mapowanie encji ↔ DB (SQLite)
- Testy integracyjne z DB

**Deliverables:**
```
core/
└── repositories/
    ├── __init__.py
    ├── base.py                  # Repository ABC
    ├── suggestion_repo.py       # CRUD dla Suggestion
    ├── backlog_repo.py          # CRUD dla BacklogItem
    └── message_repo.py          # CRUD dla Message
tests/
└── core/
    └── test_repositories.py     # Testy integracyjne z SQLite
```

**Definition of Done:**
- [ ] `repo.get(id)`, `.save(entity)`, `.delete(id)` działają
- [ ] Query methods: `find_by_status()`, `find_by_author()`, `find_by_area()`
- [ ] Testy używają tymczasowej DB (fixture)
- [ ] Testy pokrywają INSERT + UPDATE + SELECT + DELETE
- [ ] Testy przechodzą 100%
- [ ] Commit + push

**Zależności:** Milestone 1

**Estymata:** 1 sesja (4-6h)

---

### Milestone 3: AgentBus adapter (Faza 2)

**Scope:**
- Nowy `core/services/agent_bus.py` używający repozytoriów
- Adapter w `tools/lib/agent_bus.py` delegujący do `core/`
- Zachowanie kompatybilności wstecznej (dict output dla CLI)
- Testy end-to-end (CLI → adapter → core → DB)

**Deliverables:**
```
core/
└── services/
    ├── __init__.py
    └── agent_bus.py             # Nowy AgentBus z encjami
tools/
└── lib/
    └── agent_bus.py             # Adapter: deleguje do core/services/
tests/
└── integration/
    └── test_agent_bus_e2e.py    # CLI → adapter → core
```

**Definition of Done:**
- [ ] Stary `tools/lib/agent_bus.py` działa bez zmian w wywołaniach
- [ ] CLI (`agent_bus_cli.py`) działa bez zmian
- [ ] Wszystkie operacje (suggest, backlog-add, send) używają encji wewnętrznie
- [ ] Output dla CLI nadal jako dict (kompatybilność)
- [ ] Testy end-to-end przechodzą
- [ ] Istniejące testy (`tests/test_agent_bus.py`) nadal przechodzą
- [ ] Commit + push

**Zależności:** Milestone 2

**Estymata:** 1 sesja (4-6h)

---

### Milestone 4: Agenci i sesje (Faza 3)

**Scope:**
- Encje dla agentów: `Role`, `Session`, `Agent`, `LiveAgent`
- Powiązanie z `mrowisko_runner.py`
- `LiveAgent.spawn_child()` — abstrakcja samowywołania
- Testy multi-agent scenariuszy

**Deliverables:**
```
core/
└── entities/
    └── agents.py                # Role, Session, Agent, LiveAgent
tests/
└── core/
    └── test_agents.py           # Testy dla agentów i sesji
```

**Definition of Done:**
- [ ] `Agent.start_session()`, `.end_session()` działają
- [ ] `LiveAgent.update_heartbeat()`, `.is_alive()` działają
- [ ] `Session.consume_document()`, `.duration_minutes()` działają
- [ ] `LiveAgent.spawn_child()` gotowy do integracji z runnerem
- [ ] Testy scenariuszy: agent startuje sesję, wykonuje task, kończy sesję
- [ ] Commit + push

**Zależności:** Milestone 3

**Estymata:** 1 sesja (4-6h)

**Uwaga:** Integracja z `mrowisko_runner.py` to osobny task — ten milestone daje tylko encje.

---

### Milestone 5: Bot entities (Faza 4)

**Scope:**
- Encje dla bota: `User`, `Query`, `QueryResult`, `Conversation`
- Refaktor `bot/nlp_pipeline.py` używający nowych klas
- Przeniesienie walidacji SQL do `Query.validate()`
- Testy

**Deliverables:**
```
core/
└── entities/
    └── bot.py                   # User, Query, QueryResult, Conversation
bot/
└── nlp_pipeline.py              # Refaktor: używa core/entities/bot
tests/
└── bot/
    └── test_bot_entities.py     # Testy dla encji bota
```

**Definition of Done:**
- [ ] `Query.validate()`, `.execute()` działają
- [ ] `QueryResult.to_markdown()`, `.is_empty()` działają
- [ ] `Conversation.add_user_message()`, `.get_context()` działają
- [ ] `bot/nlp_pipeline.py` używa encji zamiast dictów
- [ ] Istniejące testy bota nadal przechodzą
- [ ] Commit + push

**Zależności:** Milestone 3 (nie zależy od Milestone 4)

**Estymata:** 1 sesja (4-6h)

---

### Milestone 6: Cleanup i dokumentacja (Faza 5)

**Scope:**
- Usunięcie martwego kodu
- Aktualizacja `documents/dev/ARCHITECTURE.md`
- Dokumentacja w `core/README.md`
- Code review całości

**Deliverables:**
- Zaktualizowana dokumentacja architektury
- Usunięte nieużywane metody/klasy
- README w `core/` z przykładami użycia

**Definition of Done:**
- [ ] Brak martwego kodu (grep po starych metodach)
- [ ] `ARCHITECTURE.md` opisuje Domain Model
- [ ] `core/README.md` z przykładami: jak tworzyć encje, jak używać repozytoriów
- [ ] Code review przez Architekta (opcjonalnie)
- [ ] Commit + push

**Zależności:** Milestone 4 + 5

**Estymata:** 1 sesja (2-4h)

---

## Harmonogram

| Milestone | Estymata | Zależności | Priorytet |
|-----------|----------|------------|-----------|
| M1: Fundament | 1 sesja | brak | **Krytyczny** |
| M2: Repozytoria | 1 sesja | M1 | **Krytyczny** |
| M3: AgentBus adapter | 1 sesja | M2 | **Krytyczny** |
| M4: Agenci i sesje | 1 sesja | M3 | Wysoki |
| M5: Bot entities | 1 sesja | M3 | Średni |
| M6: Cleanup | 1 sesja | M4+M5 | Niski |

**Ścieżka krytyczna:** M1 → M2 → M3 → M4 → M6

**Równoległość:** M5 (Bot) może iść równolegle z M4 (Agenci) — oba zależą tylko od M3.

**Łączny wysiłek:** 6 sesji (~24-30h)

---

## Strategia migracji

### Kompatybilność wsteczna (M1-M3)

Adapter w `tools/lib/agent_bus.py` zapewnia że:
- Istniejące wywołania CLI działają bez zmian
- Output nadal jako dict (dla backward compatibility)
- Wewnętrznie używamy encji

### Cut-over (M4-M5)

Po M3 system działa w trybie hybrydowym:
- Nowy kod (`core/`) używa encji
- Stary kod (`tools/`, `bot/`) używa dictów przez adapter

M4-M5 usuwa adapter stopniowo — migruje kolejne moduły.

### Rollback

Każdy milestone jest niezależny i commitowany osobno.
Jeśli M4 wprowadzi regresję — możemy wrócić do M3 (system działa).

---

## Ryzyka i mitygacje

| Ryzyko | Prawdopodobieństwo | Wpływ | Mitygacja |
|--------|-------------------|-------|-----------|
| Regresje w istniejącym kodzie | Średnie | Wysoki | Testy end-to-end per milestone, adapter zachowuje API |
| Refaktor się przeciągnie | Niskie | Średni | Fazy niezależne, można wdrażać po jednej |
| Over-engineering | Niskie | Niski | Zaczynamy od 3 encji (M1), rośniemy organicznie |
| Konflikt z równoległym runnerem | Średnie | Wysoki | M3 (adapter) kończy się przed integracją z runnerem |

---

## Checkpoints

Po każdym milestone:
1. **Testy przechodzą 100%**
2. **Commit + push**
3. **Prezentacja użytkownikowi** — co zrobione, co dalej
4. **Decyzja:** kontynuować / pivot / pauza

---

## Otwarty wątek: integracja z runnerem

M4 daje `LiveAgent.spawn_child()` jako abstrakcję.
Faktyczna integracja z `mrowisko_runner.py` to **osobny task** (poza tym planem).

Zależność: M4 musi być gotowe przed refaktorem runnera.

---

**Status:** Czeka na zatwierdzenie użytkownika

**Następny krok:** Po zatwierdzeniu → Milestone 1 (Fundament)
