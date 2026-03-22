# ADR-001: Domain Model dla Mrowiska

**Data:** 2026-03-22
**Status:** Proposed
**Autor:** Architect
**Decydent:** Dawid Cyprowski

---

## Context

### Obecny stan

Projekt Mrowisko używa podejścia proceduralnego z danymi jako słownikami (dict):

```python
# Obecny kod
suggestion = {"id": 1, "author": "dev", "status": "open", "content": "..."}
bus.update_suggestion_status(suggestion["id"], "implemented")
```

**Problemy:**
1. Brak walidacji typów — błędy wykrywane runtime
2. Logika rozproszona — `update_suggestion_status` w AgentBus, walidacja statusów w CLI, formatowanie w render.py
3. Brak enkapsulacji — każdy może zmodyfikować dowolne pole
4. Trudne testowanie — trzeba mockować DB zamiast obiektów
5. Brak dokumentacji w kodzie — co to jest Suggestion? Trzeba czytać schemat DB

### Nadchodząca złożoność

Projekt stoi przed skokiem złożoności:

| Teraz | Za chwilę |
|-------|-----------|
| 1 agent na raz | N agentów równolegle (mrowisko_runner) |
| Sesje w głowie użytkownika | Sesje jako obiekty z kontekstem |
| Proste workflow | Auto-wywołania agent→agent |
| 6 ról | Role + instancje + stany |

Proceduralny kod z dictami nie udźwignie tej złożoności.

### Dlaczego teraz

1. Projekt właśnie przeszedł refaktor promptów — jest stabilny
2. Stoimy przed implementacją multi-agent (mrowisko_runner)
3. Budżet tokenów wykorzystany w 10% — jest przestrzeń na rozwój
4. Lepiej przebudować teraz niż po implementacji kolejnej warstwy

---

## Decision

**Przechodzimy z architektury dict-based na Domain Model oparty o klasy.**

### Zasady

1. **Encje domenowe jako dataclasses** — Suggestion, BacklogItem, Message, etc.
2. **Zachowania w metodach** — `suggestion.implement()` zamiast `bus.update_suggestion_status()`
3. **Walidacja przy tworzeniu** — nieprawidłowy status = TypeError, nie błąd SQL
4. **Repozytoria do persystencji** — `SuggestionRepository.save(suggestion)`
5. **Nowy kod w `core/`** — nie modyfikujemy istniejącego tools/ od razu

---

## Hierarchia klas

### Warstwa 1: Bazowe

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Optional
from enum import Enum

class Status(Enum):
    """Bazowy enum dla statusów"""
    pass

@dataclass
class Entity:
    """Bazowa klasa dla wszystkich encji z ID"""
    id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)

    def is_persisted(self) -> bool:
        return self.id is not None
```

### Warstwa 2: Komunikacja (agent_bus)

```python
class MessageStatus(Enum):
    UNREAD = "unread"
    READ = "read"

class MessageType(Enum):
    DIRECT = "direct"
    SUGGESTION = "suggestion"
    ESCALATION = "escalation"

@dataclass
class Message(Entity):
    sender: str
    recipient: str
    content: str
    type: MessageType = MessageType.DIRECT
    status: MessageStatus = MessageStatus.UNREAD
    session_id: Optional[str] = None
    read_at: Optional[datetime] = None

    def mark_read(self) -> None:
        if self.status == MessageStatus.UNREAD:
            self.status = MessageStatus.READ
            self.read_at = datetime.now()

    def reply(self, content: str) -> "Message":
        """Tworzy wiadomość zwrotną"""
        return Message(
            sender=self.recipient,
            recipient=self.sender,
            content=content,
            type=self.type
        )


class SuggestionStatus(Enum):
    OPEN = "open"
    IMPLEMENTED = "implemented"
    REJECTED = "rejected"
    DEFERRED = "deferred"

class SuggestionType(Enum):
    RULE = "rule"
    TOOL = "tool"
    DISCOVERY = "discovery"
    OBSERVATION = "observation"

@dataclass
class Suggestion(Entity):
    author: str
    content: str
    title: str = ""
    type: SuggestionType = SuggestionType.OBSERVATION
    status: SuggestionStatus = SuggestionStatus.OPEN
    backlog_id: Optional[int] = None
    session_id: Optional[str] = None

    def implement(self, backlog_id: Optional[int] = None) -> None:
        if self.status != SuggestionStatus.OPEN:
            raise InvalidStateError(f"Cannot implement suggestion in status {self.status}")
        self.status = SuggestionStatus.IMPLEMENTED
        self.backlog_id = backlog_id

    def reject(self, reason: str = None) -> None:
        if self.status != SuggestionStatus.OPEN:
            raise InvalidStateError(f"Cannot reject suggestion in status {self.status}")
        self.status = SuggestionStatus.REJECTED

    def defer(self) -> None:
        self.status = SuggestionStatus.DEFERRED


class BacklogArea(Enum):
    BOT = "Bot"
    DEV = "Dev"
    ARCH = "Arch"
    ERP = "ERP"

class BacklogStatus(Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    DEFERRED = "deferred"

class BacklogValue(Enum):
    HIGH = "wysoka"
    MEDIUM = "srednia"
    LOW = "niska"

class BacklogEffort(Enum):
    SMALL = "mala"
    MEDIUM = "srednia"
    LARGE = "duza"

@dataclass
class BacklogItem(Entity):
    title: str
    content: str = ""
    area: Optional[BacklogArea] = None
    status: BacklogStatus = BacklogStatus.PLANNED
    value: Optional[BacklogValue] = None
    effort: Optional[BacklogEffort] = None
    source_id: Optional[int] = None  # FK do Suggestion
    updated_at: Optional[datetime] = None

    def start(self) -> None:
        if self.status not in (BacklogStatus.PLANNED, BacklogStatus.DEFERRED):
            raise InvalidStateError(f"Cannot start item in status {self.status}")
        self.status = BacklogStatus.IN_PROGRESS
        self.updated_at = datetime.now()

    def complete(self) -> None:
        if self.status != BacklogStatus.IN_PROGRESS:
            raise InvalidStateError(f"Cannot complete item not in progress")
        self.status = BacklogStatus.DONE
        self.updated_at = datetime.now()

    def defer(self) -> None:
        self.status = BacklogStatus.DEFERRED
        self.updated_at = datetime.now()
```

### Warstwa 3: Agenci i Sesje

```python
@dataclass
class Role:
    """Definicja roli agenta"""
    name: str
    doc_path: str
    allowed_tools: list[str] = field(default_factory=list)
    escalates_to: Optional[str] = None

    def can_use_tool(self, tool_name: str) -> bool:
        return tool_name in self.allowed_tools or not self.allowed_tools

    def get_escalation_target(self) -> Optional[str]:
        return self.escalates_to


@dataclass
class ConsumedDocument:
    """Dokument przeczytany przez agenta w sesji"""
    path: str
    content_hash: str
    consumed_at: datetime = field(default_factory=datetime.now)
    tokens: Optional[int] = None


@dataclass
class Session(Entity):
    """Sesja pracy agenta (jedna rozmowa CLI)"""
    session_id: str  # Claude session ID
    role: Role
    started_at: datetime = field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None
    messages: list[Message] = field(default_factory=list)
    consumed_docs: list[ConsumedDocument] = field(default_factory=list)
    tool_calls: list["ToolCall"] = field(default_factory=list)

    def end(self) -> None:
        self.ended_at = datetime.now()

    def duration_minutes(self) -> Optional[float]:
        if not self.ended_at:
            return None
        return (self.ended_at - self.started_at).total_seconds() / 60

    def add_message(self, msg: Message) -> None:
        self.messages.append(msg)

    def consume_document(self, path: str, content: str) -> None:
        import hashlib
        content_hash = hashlib.md5(content.encode()).hexdigest()
        self.consumed_docs.append(ConsumedDocument(path=path, content_hash=content_hash))


@dataclass
class Agent:
    """Agent — instancja roli z kontekstem"""
    role: Role
    session: Optional[Session] = None
    inbox: list[Message] = field(default_factory=list)

    def is_active(self) -> bool:
        return self.session is not None and self.session.ended_at is None

    def start_session(self, session_id: str) -> Session:
        self.session = Session(session_id=session_id, role=self.role)
        return self.session

    def end_session(self) -> None:
        if self.session:
            self.session.end()


@dataclass
class LiveAgent(Agent):
    """Agent z aktywną sesją CLI (mrowisko_runner)"""
    process_id: Optional[int] = None
    heartbeat: Optional[datetime] = None
    parent_agent: Optional["LiveAgent"] = None  # Agent który go wywołał

    def update_heartbeat(self) -> None:
        self.heartbeat = datetime.now()

    def is_alive(self, timeout_seconds: int = 60) -> bool:
        if not self.heartbeat:
            return False
        return (datetime.now() - self.heartbeat).total_seconds() < timeout_seconds

    def spawn_child(self, role: Role, task: str) -> "LiveAgent":
        """Wywołuje podagenta"""
        child = LiveAgent(role=role, parent_agent=self)
        # ... logika spawnu
        return child
```

### Warstwa 4: Bot (Telegram)

```python
@dataclass
class User:
    """Użytkownik Telegram"""
    telegram_id: int
    is_allowed: bool = False
    query_count: int = 0
    last_query_at: Optional[datetime] = None

    def can_query(self, rate_limit: int = 10, window_seconds: int = 60) -> bool:
        if not self.is_allowed:
            return False
        if not self.last_query_at:
            return True
        # Rate limiting logic
        return True  # simplified

    def record_query(self) -> None:
        self.query_count += 1
        self.last_query_at = datetime.now()


@dataclass
class Query:
    """Zapytanie użytkownika do bota"""
    user: User
    raw_text: str
    generated_sql: Optional[str] = None
    is_valid: bool = False
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

    def validate(self) -> bool:
        # SQL validation logic
        pass

    def execute(self) -> "QueryResult":
        # Execution logic
        pass


@dataclass
class QueryResult:
    """Wynik zapytania SQL"""
    query: Query
    rows: list[tuple] = field(default_factory=list)
    columns: list[str] = field(default_factory=list)
    row_count: int = 0
    error: Optional[str] = None
    execution_time_ms: Optional[float] = None

    def to_markdown(self, max_rows: int = 50) -> str:
        # Formatting logic
        pass

    def is_empty(self) -> bool:
        return self.row_count == 0

    def is_error(self) -> bool:
        return self.error is not None


@dataclass
class Conversation:
    """Rozmowa z użytkownikiem (historia)"""
    user: User
    messages: list[dict] = field(default_factory=list)  # Claude format
    created_at: datetime = field(default_factory=datetime.now)

    def add_user_message(self, content: str) -> None:
        self.messages.append({"role": "user", "content": content})

    def add_assistant_message(self, content: str) -> None:
        self.messages.append({"role": "assistant", "content": content})

    def get_context(self, max_messages: int = 10) -> list[dict]:
        return self.messages[-max_messages:]

    def clear(self) -> None:
        self.messages.clear()
```

### Warstwa 5: Repozytoria (persystencja)

```python
from abc import ABC, abstractmethod

class Repository(ABC, Generic[T]):
    """Bazowy interfejs repozytorium"""

    @abstractmethod
    def get(self, id: int) -> Optional[T]:
        pass

    @abstractmethod
    def save(self, entity: T) -> T:
        pass

    @abstractmethod
    def delete(self, id: int) -> bool:
        pass


class SuggestionRepository(Repository[Suggestion]):
    def __init__(self, db_path: str = "mrowisko.db"):
        self.db_path = db_path

    def get(self, id: int) -> Optional[Suggestion]:
        # SELECT FROM suggestions WHERE id = ?
        # return Suggestion(**row)
        pass

    def save(self, suggestion: Suggestion) -> Suggestion:
        if suggestion.is_persisted():
            # UPDATE
            pass
        else:
            # INSERT, set suggestion.id
            pass
        return suggestion

    def find_by_status(self, status: SuggestionStatus) -> list[Suggestion]:
        pass

    def find_by_author(self, author: str) -> list[Suggestion]:
        pass


class BacklogRepository(Repository[BacklogItem]):
    # Analogicznie
    pass


class MessageRepository(Repository[Message]):
    # Analogicznie
    pass
```

### Wyjątki domenowe

```python
class DomainError(Exception):
    """Bazowy wyjątek domenowy"""
    pass

class InvalidStateError(DomainError):
    """Próba niedozwolonej zmiany stanu"""
    pass

class NotFoundError(DomainError):
    """Encja nie znaleziona"""
    pass

class ValidationError(DomainError):
    """Błąd walidacji danych"""
    pass
```

---

## Struktura katalogów

```
mrowisko/
├── core/                      # NOWY — Domain Model
│   ├── __init__.py
│   ├── entities/
│   │   ├── __init__.py
│   │   ├── base.py            # Entity, Status
│   │   ├── messaging.py       # Message, Suggestion
│   │   ├── backlog.py         # BacklogItem
│   │   ├── agents.py          # Role, Agent, LiveAgent, Session
│   │   └── bot.py             # User, Query, QueryResult, Conversation
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── base.py            # Repository ABC
│   │   ├── suggestion_repo.py
│   │   ├── backlog_repo.py
│   │   └── message_repo.py
│   ├── services/              # Logika biznesowa
│   │   ├── __init__.py
│   │   ├── agent_bus.py       # Nowy AgentBus używający entities
│   │   └── workflow.py        # Workflow engine
│   └── exceptions.py
├── tools/                     # STARE — stopniowa migracja
│   ├── lib/
│   │   └── agent_bus.py       # Stary, adapter do core/
│   └── ...
├── bot/                       # STARE — stopniowa migracja
└── ...
```

---

## Plan migracji

### Faza 0: Fundament (Effort: 4h)
- [ ] Utworzyć `core/` z pustą strukturą
- [ ] Zaimplementować `Entity`, `Status`, wyjątki
- [ ] Zaimplementować `Suggestion`, `BacklogItem`, `Message`
- [ ] Testy jednostkowe dla encji

### Faza 1: Repozytoria (Effort: 4h)
- [ ] Zaimplementować `SuggestionRepository`
- [ ] Zaimplementować `BacklogRepository`
- [ ] Zaimplementować `MessageRepository`
- [ ] Testy integracyjne z SQLite

### Faza 2: Adapter AgentBus (Effort: 4h)
- [ ] Nowy `core/services/agent_bus.py` używający repozytoriów
- [ ] Adapter w `tools/lib/agent_bus.py` delegujący do core/
- [ ] Zachować kompatybilność wsteczną (dict output dla CLI)
- [ ] Testy end-to-end

### Faza 3: Agenci i Sesje (Effort: 6h)
- [ ] Zaimplementować `Role`, `Session`, `Agent`, `LiveAgent`
- [ ] Zintegrować z mrowisko_runner
- [ ] Testy dla multi-agent scenariuszy

### Faza 4: Bot (Effort: 6h)
- [ ] Zaimplementować `User`, `Query`, `QueryResult`, `Conversation`
- [ ] Zrefaktorować `nlp_pipeline.py` używając nowych klas
- [ ] Przenieść walidację do `Query.validate()`
- [ ] Testy

### Faza 5: Cleanup (Effort: 4h)
- [ ] Usunąć martwy kod
- [ ] Zaktualizować dokumentację
- [ ] Code review całości

**Łączny effort: ~28h**

---

## Consequences

### Zyskujemy

1. **Czytelność** — `suggestion.implement()` zamiast `bus.update_suggestion_status(id, "implemented")`
2. **Walidacja** — błędy przy tworzeniu obiektu, nie przy zapisie do DB
3. **Testowalność** — mockujemy repozytoria, testujemy logikę biznesową w izolacji
4. **Enkapsulacja** — reguły biznesowe w jednym miejscu
5. **IDE support** — autocomplete, refactoring, go to definition
6. **Dokumentacja** — klasa = dokumentacja
7. **Skalowalność** — dziedziczenie, kompozycja, wzorce

### Tracimy

1. **Czas na refaktor** — ~28h rozłożone na fazy
2. **Prostota dict** — więcej kodu (ale lepszego)
3. **Krzywa uczenia** — nowe osoby muszą znać strukturę

### Ryzyka

| Ryzyko | Mitygacja |
|--------|-----------|
| Refaktor się przeciągnie | Fazy są niezależne, można wdrażać po jednej |
| Regresje w istniejącym kodzie | Adaptery zachowują kompatybilność |
| Over-engineering | Zaczynamy od 3 encji, rośniemy organicznie |

---

## Decyzja

**Do zatwierdzenia przez:** Dawid Cyprowski

- [ ] Zatwierdzam ADR-001
- [ ] Zatwierdzam plan migracji
- [ ] Priorytet: Faza 0 + 1 w najbliższym sprincie

---

*Dokument przygotowany przez: Architect*
*Lokalizacja: documents/architect/ADR-001-domain-model.md*
