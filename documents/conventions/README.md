# Convention Registry

**Lokalizacja centralna dla wszystkich konwencji projektu.**

Wszystkie konwencje w jednym miejscu — łatwe odnalezienie, spójna struktura, jasny lifecycle.

---

## Meta-Convention

**META_CONVENTION.md** — konwencja do konwencji (jak pisać conventions)

- Definiuje strukturę każdej convention (obowiązkowe sekcje)
- Definiuje format (YAML header, markdown sections, templates)
- Definiuje enforcement (review checklist)
- Definiuje lifecycle (draft → review → active → deprecated)

**Status:** DRAFT (czeka na research results)

---

## Existing Conventions

Konwencje obecne w projekcie (do migracji):

### WORKFLOW_CONVENTION.md
**Lokalizacja obecnie:** `documents/prompt_engineer/WORKFLOW_CONVENTION.md`
**Scope:** Struktura workflow documents
**Owner:** Prompt Engineer
**Audience:** PE (tworzenie workflows), Developer (implementacja workflow-driven features)
**Status:** Active (wymaga enhancement — DB-readiness sections)
**Migration:** Planned (po zatwierdzeniu META_CONVENTION)

### PROMPT_CONVENTION.md
**Lokalizacja obecnie:** `documents/prompt_engineer/PROMPT_CONVENTION.md`
**Scope:** Formatowanie promptów (tagi XML, struktura, kompresja)
**Owner:** Prompt Engineer
**Audience:** PE (edycja promptów), Architect (review prompt architecture)
**Status:** Active
**Migration:** Planned (po zatwierdzeniu META_CONVENTION)

### CODE_STANDARDS.md → CODE_CONVENTION.md
**Lokalizacja obecnie:** `documents/dev/CODE_STANDARDS.md`
**Scope:** Nazewnictwo, funkcje, modularność, testy
**Owner:** Developer
**Audience:** Developer (implementacja), Architect (code review)
**Status:** Active
**Migration:** Planned (rename CODE_STANDARDS → CODE_CONVENTION + move do conventions/)

### PATTERNS.md
**Lokalizacja:** `documents/architecture/PATTERNS.md`
**Scope:** Katalog wzorców architektonicznych (system design, validation, domain model, migration, testing, security, data quality)
**Owner:** Architect
**Audience:** Architect (projektowanie), Developer (implementacja patterns), Metodolog (review alignment)
**Status:** Active
**Migration:** **NIE** — to pattern catalog, nie convention (pozostaje w documents/architecture/)

---

## Planned Conventions (Priority 1)

Konwencje do utworzenia (po META_CONVENTION):

### COMMIT_CONVENTION.md
**Scope:** Commit messages (feat/fix/refactor prefix, format, co w body)
**Owner:** Developer
**Audience:** Wszyscy (każdy commituje)
**Rationale:** Spójna historia zmian, parseable do DB (future: commit as data)
**Effort:** Mała (research → draft → enforce)
**Status:** Planned

### FILE_NAMING_CONVENTION.md
**Scope:** Nazewnictwo plików i folderów (snake_case.py, UPPER.md, kebab-case folders)
**Owner:** Developer
**Audience:** Wszyscy (każdy tworzy pliki)
**Rationale:** Konsystencja, łatwość wyszukiwania (Glob patterns)
**Effort:** Mała
**Status:** Planned

### DB_SCHEMA_CONVENTION.md
**Scope:** Nazewnictwo tabel, kolumn, FKs, indexes, constraints
**Owner:** Developer
**Audience:** Developer (schema design), ERP Specialist (ERP DB schema reference)
**Rationale:** Spójność między application DB i ERP DB patterns
**Effort:** Średnia (research SQL best practices)
**Status:** Planned

### TEST_CONVENTION.md
**Scope:** Naming testów, fixtures, assertions, file structure
**Owner:** Developer
**Audience:** Developer (pisanie testów)
**Rationale:** Czytelność testów, łatwość debugowania
**Effort:** Mała
**Status:** Planned

### DOCUMENTATION_CONVENTION.md
**Scope:** ADR format, README structure, docstrings style
**Owner:** Architect
**Audience:** Architect (ADR), Developer (README, docstrings)
**Rationale:** Trwała dokumentacja decyzji i kodu
**Effort:** Średnia
**Status:** Planned

---

## Planned Conventions (Priority 2)

Konwencje przydatne, ale nie krytyczne:

### ERROR_HANDLING_CONVENTION.md
**Scope:** Try-catch patterns, propagacja błędów, logging errors
**Owner:** Developer
**Audience:** Developer
**Rationale:** Fail-fast architecture enforcement
**Status:** Deferred (po Priority 1)

### API_CONVENTION.md
**Scope:** REST endpoints naming, response format, error codes
**Owner:** Developer
**Audience:** Developer (API design), Bot (API consumption)
**Rationale:** Przygotowanie pod HTTP API dla external integrations
**Status:** Deferred (gdy budujemy HTTP API)

---

## Convention Lifecycle

**Każda convention przechodzi przez:**

1. **Research** — PE tworzy prompt → research agent → wyniki do pliku
2. **Draft** — Owner (Architect/Developer/PE) pisze convention na podstawie researchu
3. **Review** — Cross-role review (PE checks parseability, Architect checks scalability, Metodolog checks alignment z SPIRIT)
4. **Active** — Convention zatwierdzona, enforcement starts
5. **Enhancement** — Convention update (minor changes, nie breaking structure)
6. **Deprecated** — Convention replaced (superseded by nowa wersja)

**Status w README:** DRAFT | REVIEW | ACTIVE | DEPRECATED

---

## Ownership & Enforcement

| Convention | Owner | Enforcement |
|---|---|---|
| META_CONVENTION | Architect | Architect review (każda nowa convention) |
| WORKFLOW_CONVENTION | Prompt Engineer | PE review (każdy nowy workflow) |
| PROMPT_CONVENTION | Prompt Engineer | PE review (każdy prompt edit) |
| CODE_CONVENTION | Developer | Architect code review, future: linter |
| COMMIT_CONVENTION | Developer | git_commit.py validation (future) |
| DB_SCHEMA_CONVENTION | Developer | Schema migration review |

---

## Migration Timeline

**Phase 1: META_CONVENTION (current)**
- Research (PE + research agent) — **in progress**
- Draft (Architect) — czeka na research results
- Review (PE + Metodolog) — czeka na draft
- Active — czeka na review approval

**Phase 2: Migrate Existing Conventions**
- Move WORKFLOW_CONVENTION → `documents/conventions/`
- Move PROMPT_CONVENTION → `documents/conventions/`
- Rename + move CODE_STANDARDS → `documents/conventions/CODE_CONVENTION.md`
- Update paths (PROMPT_ENGINEER.md, DEVELOPER.md, ARCHITECT.md)
- Verify compliance z META_CONVENTION (każda existing convention)

**Phase 3: Priority 1 Conventions**
- COMMIT_CONVENTION (research → draft → review)
- FILE_NAMING_CONVENTION (research → draft → review)
- DB_SCHEMA_CONVENTION (research → draft → review)
- TEST_CONVENTION (research → draft → review)
- DOCUMENTATION_CONVENTION (research → draft → review)

**Estimated Total Time:** 3-4 tygodnie (PE + Architect + Developer collaboration)

---

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-24 | Convention Registry utworzony (folder + README) | Architect |
| 2026-03-24 | META_CONVENTION research request wysłany (message #238) | Architect |

---

**Next step:** META_CONVENTION research results → draft → review → implement.
