# Backlog — 2026-03-22

*81 pozycji*

---

## Szybkie strzały (wysoka wartość, mała praca)

| id | tytuł | obszar | wartość | effort |
|----|-------|--------|---------|--------|
| 86 | inbox — komenda mark-read --all / --unread-since | Dev | wysoka | mala |
| 79 | [Dev] Sugestie atomowe — jedna obserwacja = jeden wpis | Dev | wysoka | mala |
| 78 | [Dev] Hook post_tool_use — live widocznosc tool calls w DB | Dev | wysoka | mala |
| 76 | [Dev] Usuń referencje do progress_log.md ze wszystkich wytycznych | Dev | wysoka | mala |
| 75 | [Dev] Zarządzanie kontekstem — limity narzędzi + reguły ERP Specialist | Dev | wysoka | mala |
| 74 | [Dev] CLAUDE.md — regula log sesji dla wszystkich rol | Dev | wysoka | mala |
| 67 | [Dev] Plan widoku: Komentarz_Usera → Komentarz_Analityka — usunąć angażowanie usera z Fazy 1 | Dev | wysoka | mala |
| 66 | [Dev] Refleksja agent — memory vs agent_bus: rozróżnienie w promptach ról | Dev | wysoka | mala |
| 57 | [Arch 5.2] Render widoku sesji dla człowieka — co agent dostał i co zwrócił | Arch | wysoka | mala |
| 50 | [Arch 1.3] session_init — ładowanie promptu roli z pliku/DB przez jeden tool call | Arch | wysoka | mala |
| 49 | [Arch 1.2] Zapis sesji — on_stop do conversation + render sesji | Arch | wysoka | mala |
| 47 | Zapis konwersacji agentow do bazy (trace) | Arch | wysoka | mala |
| 43 | Usuń referencje do developer_notes.md z ERP_SPECIALIST.md i ANALYST.md | Dev | wysoka | mala |
| 27 | Zasada: narzędzie od razu w tools/ z testami, nie łatka w root | Dev | wysoka | mala |
| 20 | Zasada projektowania DB — przykładowe rekordy przed schematem | Dev | wysoka | mala |

## Wysoka wartość, średnia praca

| id | tytuł | obszar | wartość | effort |
|----|-------|--------|---------|--------|
| 114 | Plan eksperymentow: Runner wieloagentowy | Arch | wysoka | srednia |
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

## Wysoka wartość, duża praca

| id | tytuł | obszar | wartość | effort |
|----|-------|--------|---------|--------|
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
| 100 | Cleanup policy dla tool_calls/token_usage | Dev | srednia | mala |
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
| 45 | Dodaj typ 'task' do agent_bus send — rozróżnienie task vs suggestion | Arch | srednia | mala |
| 44 | Zaktualizuj MEMORY.md — developer_notes.md i status projektu | Dev | srednia | mala |
| 42 | Zasada: odpowiedź proporcjonalna do zadania w komunikacji agent-agent | Arch | srednia | mala |
| 41 | agent_bus_cli: backlog-add-bulk — bulk dodawanie pozycji z pliku JSON | Dev | srednia | mala |
| 30 | Zasada: ręczna operacja na pliku = sygnał dla narzędzia | Dev | srednia | mala |
| 28 | Zastąpić changes_propositions.md dokumentem architektonicznym per feature | Dev | srednia | mala |
| 24 | Hook blokuje komendy z newline mimo Bash(python:*) w settings | Dev | srednia | mala |
| 22 | Rewizja reguł Bash w DEVELOPER.md po uporządkowaniu settings.local.json | Dev | srednia | mala |
| 21 | settings.local.json — uporzadkowanie uprawnien + agent_bus | Dev | srednia | mala |

## Średnia wartość, średnia/duża praca

| id | tytuł | obszar | wartość | effort |
|----|-------|--------|---------|--------|
| 113 | Folder documents/exports/ — ujednolicenie lokalizacji eksportów | Dev | srednia | srednia |
| 105 | Refactor render.py | Dev | srednia | srednia |
| 56 | [Arch 5.1] Dokumentacja w bazie — tabela docs + render dla agentów | Arch | srednia | duza |
| 55 | [Arch 4.1] Project Manager — rola orkiestracji zadań między agentami | Arch | srednia | duza |
| 53 | [Arch 3.1] Prompty w bazie — tabela prompts + migracja dokumentów ról | Arch | srednia | srednia |

## Pozostałe

| id | tytuł | obszar | wartość | effort |
|----|-------|--------|---------|--------|
| 109 | Rename conversation_search.py | Dev | niska | mala |
| 108 | Rename search_bi.py → bi_search.py | Dev | niska | mala |
| 107 | Helper _bulk_json_processor w agent_bus_cli | Dev | niska | mala |
| 106 | JSON output dla generatorów | Dev | niska | mala |
| 104 | Transakcje atomowe w agent_bus | Dev | niska | srednia |
| 103 | Dodać indeks do invocation_log | Dev | niska | mala |
| 102 | Deprecate tabelę state | Dev | niska | mala |
| 101 | Usunąć tabelę trace | Dev | niska | mala |
| 29 | Posprzątać tmp_* z rootu projektu | Dev | niska | mala |
| 23 | settings.local.json posprzatany — usunieto 5 jednorazowych hardcoded komend, artefakty __NEW_LINE__, WebFetch(domain:), | Dev | None | None |
| 18 | Komunikacja w roju — wzorzec dla warstwy myśli | Arch | None | None |
| 15 | generate_view — pliki podgladowe .md z mrowisko.db dla czlowieka | Arch | None | None |
| 14 | Model abstraction layer -- multi-model + fallback | Arch | średnia | średnia |
| 13 | Audit trail / trace -- logowanie decyzji agentów | Arch | wysoka | średnia |
| 12 | Eval harness -- golden tasks dla widoków BI i bota | Arch | wysoka | średnia |
| 10 | Research prompts -- plik odpowiedzi + rola Researcher | Arch | średnia | mała-średnia |
| 9 | Brak backlogu per-rola — eskalacja do Metodologa | Arch | średnia | mała–średnia |
| 8 | arch_check.py — walidator ścieżek w dokumentach | Arch | średnia | mała |
| 7 | Sygnatury narzędzi powielone w wielu miejscach | Arch | średnia | mała (opcja 3) / duża (opcja 1) |
| 1 | LOOM — publikacja na GitHub | Dev | średnia | mała |

---

## Szczegóły

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
**area:** Arch  **value:** wysoka  **effort:** srednia  **status:** in_progress  **created_at:** 2026-03-22

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
**area:** Arch  **value:** wysoka  **effort:** duza  **status:** planned  **created_at:** 2026-03-21

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
**area:** Arch  **value:** średnia  **effort:** średnia  **status:** deferred  **created_at:** 2026-03-13

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
**area:** Arch  **value:** wysoka  **effort:** średnia  **status:** cancelled  **created_at:** 2026-03-13

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
**area:** Arch  **value:** wysoka  **effort:** średnia  **status:** deferred  **created_at:** 2026-03-13

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

### [10] Research prompts -- plik odpowiedzi + rola Researcher
**area:** Arch  **value:** średnia  **effort:** mała-średnia  **status:** deferred  **created_at:** 2026-03-13

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
**area:** Arch  **value:** średnia  **effort:** mała–średnia  **status:** done  **created_at:** 2026-03-13

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
**area:** Arch  **value:** średnia  **effort:** mała  **status:** done  **created_at:** 2026-03-13

### [Arch] arch_check.py — walidator ścieżek w dokumentach

**Źródło:** obserwacja sesji 2026-03-11
**Sesja:** 2026-03-11
**Wartość:** średnia
**Pracochłonność:** mała

Skanuje pliki `.md` w poszukiwaniu wzorców `` `documents/...` `` i sprawdza czy ścieżki istnieją.
Do wdrożenia przy kolejnym dużym refaktorze.

---

### [7] Sygnatury narzędzi powielone w wielu miejscach
**area:** Arch  **value:** średnia  **effort:** mała (opcja 3) / duża (opcja 1)  **status:** done  **created_at:** 2026-03-13

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

### [1] LOOM — publikacja na GitHub
**area:** Dev  **value:** średnia  **effort:** mała  **status:** deferred  **created_at:** 2026-03-13

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
