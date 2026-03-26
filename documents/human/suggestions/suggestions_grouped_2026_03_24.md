# Sugestie Otwarte — Pogrupowane

**Data:** 2026-03-24
**Total:** 136 otwartych sugestii

---

## M1-M4 Migration (to close: realized) (19)

### #263 [architect] ## Transferable Wisdom
**Type:** observation
**Preview:** ## Transferable Wisdom  **Dla przyszłych refactorów:**  1. **Recognize golden windows** — act fast when complexity low 2. **Document decisions** — ADR...

### #262 [architect] ## Końcowa Refleksja
**Type:** observation
**Preview:** ## Końcowa Refleksja  **M1-M4 to nie był "refactor" — był "project save".**  Bez tego: - Za 6 miesięcy: unmaintainable system - Technical debt compoun...

### #260 [architect] ## 10. Context Preservation — Memory Fades, Artifacts Endure
**Type:** observation
**Preview:** ## 10. Context Preservation — Memory Fades, Artifacts Endure  **Obserwacja:**  Session context usage: 56% peak (wysoki) → Większość kontekstu to artif...

### #258 [architect] ## 8. Migration Pattern — Incremental > Big Bang
**Type:** observation
**Preview:** ## 8. Migration Pattern — Incremental > Big Bang  **Obserwacja:**  M1-M4 było 4 fazy, nie 1 big refactor: - M1: Domain entities (foundation) - M2: Rep...

### #252 [architect] ## 2. ADR-001 Quality — Architecture as Communication
**Type:** observation
**Preview:** ## 2. ADR-001 Quality — Architecture as Communication  **Obserwacja:**  ADR-001 (448 linii) to nie "dokumentacja dla dokumentacji" — to **preservation...

### #250 [architect] # Refleksje Architektoniczne: M1-M4 Domain Model Migration
**Type:** observation
**Preview:** # Refleksje Architektoniczne: M1-M4 Domain Model Migration

### #248 [developer] M1-M4 journey — dict hell → production-grade
**Type:** observation
**Preview:** ## Transformation  Before: dict hell, no type safety, scattered mappings, 24 invalid values After: typed entities, fail-fast 4 layers, CHECK constrain...

### #247 [developer] ADR timing — document when context is fresh
**Type:** rule
**Preview:** ## Observation  Architect required ADR-001 BEFORE merge. Why timing matters: context fresh, decisions clear, lessons observable.  ## Rule  ADR = part ...

### #245 [developer] Communication loop closure — critical pattern
**Type:** observation
**Preview:** ## Pattern violation (caught by user)  **Scenario:** - Architect msg #228: GREEN LIGHT conditional (wymagane ADR-001) - Developer: zrealizował (ADR-00...

### #213 [architect] Developer learning curve M3 pokazuje że Senior-level to proces, nie binary state
**Type:** observation
**Preview:** **Evidence:** - **Start Phase 1:** Mid-level (transaction support pominięty, potrzebował detailed fix) - **M3.1 patch:** Senior-level (transaction fix...

### #211 [architect] M3 complete to ~75% ADR-001, ale remaining 25% to mostly optional work
**Type:** observation
**Preview:** **Metrics:** - M1-M2 (Foundation): 40% effort → DONE ✓ - M3 (AgentBus adapters): 30% effort → DONE ✓ - M4 (Cleanup): 10% effort → TODO (~1 sesja) - M5...

### #206 [architect] Test checkpoint jako early warning system — 9 bugs caught across M3, nie w code review
**Type:** discovery
**Preview:** **Evidence across M3:** - Phase 1: 0 bugs caught by test checkpoint (transaction nie był checkpointem — bug w code review) - Phase 2: 1 bug caught (up...

### #204 [architect] M3 core messaging complete — 10 adapters, 3 repositories, 29/29 tests, ~75% refaktoru done
**Type:** observation
**Preview:** **Milestone achieved:** M3 core messaging complete (Suggestions + Backlog + Messages).  **Metrics:** - 10 adapter methods implemented (3 + 4 + 3) - 3 ...

### #199 [architect] Test coverage transaction edge cases nie była w scope M3
**Type:** observation
**Preview:** **Observation:** M3 Phase 1 success criteria z planu: - ✓ add_suggestion() + get_suggestions() + update_suggestion_status() używają repositories - ✓ B...

### #190 [architect] Interim solution OK jeśli clear path do final solution — wtyczka (interim) + CLI (final) validated
**Type:** discovery
**Preview:** **Pattern observed:** Wtyczka VS Code to **interim solution** (działa dla dev use case, nie dla wszystkich use cases). Architect zaakceptował to z war...

### #188 [architect] STRATEGIC_PLAN Wariant C delivered — równoległe ścieżki works at scale
**Type:** observation
**Preview:** **Evidence:** Wariant C (równoległe ścieżki): ``` Ścieżka 1: Eksperymenty (E1-E4) → Decyzja → Runner v2 Ścieżka 2: Porządki (ADR-001 M1-M2) → M3 Agent...

### #174 [developer] Repository pattern — separacja działa zgodnie z ADR-001
**Type:** observation
**Preview:** **Obserwacja:** Repository pattern (encja ↔ DB) daje czystą separację. Architect miał rację.  **Zyski zaobserwowane:** - Łatwe testowanie (mockowanie ...

### #168 [architect] Moment strategiczny na refaktor
**Type:** observation
**Preview:** Projekt po stabilizacji promptów, przed skokiem złożoności (multi-agent). Budżet tokenów wykorzystany w 10%. Lepiej przebudować teraz niż po implement...

### #164 [architect] Dict-based architecture nie skaluje się
**Type:** observation
**Preview:** Przy rosnącej liczbie agentów i sesji równoległych, podejście proceduralne z dictami staje się nieczytelne i trudne do utrzymania. Logika rozproszona ...

## Session Init (to close: realized) (15)

### #264 [prompt_engineer] Config as source of truth — prompty referencują, nie duplikują
**Type:** rule
**Preview:** Gdy wprowadzasz nowy mechanizm z zewnętrznym configiem (np. session_init_config.json), nie powielaj struktury configu w promptach. Prompt powinien ref...

### #244 [developer] Test-after wykrył błędy API, ale TDD byłoby lepsze
**Type:** observation
**Preview:** Session_init implementation: - Napisałem kod (session_init.py + get_context) - Potem napisałem testy (5 nowych) - Testy failowały: `message_type` vs `...

### #243 [developer] User feedback loop real-time > strict adherence to spec
**Type:** observation
**Preview:** PE wysłał request #224: "session-logs --init" (Opcja 1 vs Opcja 2).  **Proces:** 1. PE zaproponował 2 opcje (--init flag vs session_init integration) ...

### #242 [developer] Session-aware CLI — security hole w obecnym designie
**Type:** discovery
**Preview:** User zauważył problem podczas review sesji:  **Obecnie:** ```bash py tools/session_init.py --role developer  # Sesja określa rolę py tools/agent_bus_c...

### #241 [developer] Config-driven architecture > hardcoded prompts
**Type:** rule
**Preview:** Przed implementacją session_init config: - 6 promptów z hardcoded limitami (`--limit 3`, `--limit 7`, etc.) - Każda zmiana limitu logów = edycja 6 pli...

### #240 [developer] Handoff pattern skuteczny dla context overflow
**Type:** observation
**Preview:** Poprzednia sesja developera (1def6c7d5759) urwała się z powodu context overflow (33k tokens). Developer zostawił handoff file w `documents/human/plans...

### #239 [prompt_engineer] ## Recommendations (summary)
**Type:** observation
**Preview:** ## Recommendations (summary)  **Immediate (do wdrożenia w następnej sesji PE):** 1. ✓ #228 wdrożyć — drafty do documents/human/ 2. Dodać `--title` do ...

### #236 [prompt_engineer] ## 8. session_init.py jako centralizacja (suggestion #223 revisited)
**Type:** observation
**Preview:** ## 8. session_init.py jako centralizacja (suggestion #223 revisited)  **Developer wybrał:** Option 1 (`session-logs --init`) zamiast Option 2 (`sessio...

### #234 [prompt_engineer] ## 6. PE ↔ wszystkie role notification gap
**Type:** observation
**Preview:** ## 6. PE ↔ wszystkie role notification gap  **Problem:** Developer notyfikuje PE o nowych toolach (msg #214, #221, #227).  Ale **PE nie notyfikuje wsz...

### #231 [prompt_engineer] ## 3. Context window jako architectural constraint
**Type:** observation
**Preview:** ## 3. Context window jako architectural constraint  **Discovery:** 87% savings (7.5k vs 60k) to nie optymalizacja — to **requirement**.  Gdyby agent m...

### #224 [prompt_engineer] Przegląd workflow/ról pod kątem automatyzacji
**Type:** observation
**Preview:** type: observation title: Przegląd workflow/ról/promptów pod kątem automatyzacji — "agent nie musi robić" → wdrażaj  ## Observation  Wiele kroków w wor...

### #223 [prompt_engineer] Zautomatyzować kroki session_start — session_init zwraca dane
**Type:** tool
**Preview:** type: tool title: Zautomatyzować kroki session_start — session_init zwraca dane zamiast instrukcji  ## Observation  `<session_start>` w promptach ról ...

### #221 [architect] type: rule
**Type:** observation
**Preview:** type: rule title: Session start brakuje check logów roli — duplikacja pracy  ## Problem  `<session_start>` nie zawiera instrukcji sprawdzenia logów sw...

### #220 [developer] Auto-mark-read przy odpowiedzi (context window optimization)
**Type:** observation
**Preview:** # Sugestia: Auto-mark-read przy odpowiedzi na wiadomość  ## Observation  Agenci nie odczytują (`mark-read`) wiadomości nawet gdy na nie odpowiadają. T...

### #171 [developer] Context management przy długich sesjach (5h, 88% kontekstu)
**Type:** observation
**Preview:** Sesja była długa — 2 milestones (M1 + M2 part 1), 5h pracy, kontekst urósł do 88%.  **Obserwacja:** Lepiej dzielić duże zadania na mniejsze sesje (1 m...

## Obserwacje bez akcji (to close: noted) (10)

### #166 [architect] Bot wymaga hardeningu przed skalowaniem
**Type:** observation
**Preview:** Krytyczny brak: error handling dla Anthropic API. Bot crashuje przy rate limit lub API error. Dodatkowo: God Object w nlp_pipeline.py (218 linii, 7 od...

### #138 [architect] Bot wymaga hardeningu przed skalowaniem
**Type:** observation
**Preview:** Krytyczny brak: error handling dla Anthropic API. Bot crashuje przy rate limit lub API error. Dodatkowo: God Object w nlp_pipeline.py (218 linii, 7 od...

### #130 [architect] _loom wygląda na porzucony
**Type:** observation
**Preview:** Katalog _loom/ ma minimalną zawartość, ostatnia aktualizacja dawno. W obecnej formie to raczej obietnica niż produkt. Propozycja: albo rozwijamy (doda...

### #129 [architect] Nazewnictwo narzędzi — brak konwencji
**Type:** observation
**Preview:** Widzę: `docs_search` vs `search_bi`, `solutions_save` vs `save_solution`. Prefix (docs_) vs suffix (_search). Przy ~50 skryptach utrudnia nawigację i ...

### #128 [architect] tmp/ jako de facto inbox człowieka
**Type:** observation
**Preview:** W tmp/ jest ~40 plików: handoffy, logi, sugestie, eksporty. To tam ląduje wszystko co człowiek powinien przejrzeć. Ale nazwa "tmp" sugeruje "tymczasow...

### #121 [architect] Istniejący ARCHITECTURE.md w documents/dev/
**Type:** observation
**Preview:** documents/dev/ARCHITECTURE.md opisuje szczegółowo Agent ERP i Bot (Faza 1-2). Brakuje opisu systemu wieloagentowego na wyższym poziomie. Utworzono doc...

### #109 [developer] bot eval (id=84) krytyczny przed kolejną rundą zmian promptu
**Type:** observation
**Preview:** Bez automatycznych testów każda zmiana PE to loteria — widać to po Typ_Dok i akronimach. Eval powinien być zrobiony przed następną sesją zmian promptu...

### #105 [analyst] MagElem — duplikat aliasu Kod_Towaru — planowanie dwóch źródeł dla jednej kolumny
**Type:** observation
**Preview:** ERP Specialist umieścił dwa wiersze Uwzglednic=Tak z aliasem Kod_Towaru: jeden z JOINu TwrKarty, drugi z MaE_TwrKod inline. Symptom niejednoznacznej d...

### #104 [analyst] Faza 3 — ERP Specialist domyślnie wysyła self-check, nie pełne bi_verify
**Type:** observation
**Preview:** W MagNag Faza 3 ERP Specialist wysłał self-check bez pełnych statystyk bi_verify (distinct/null per kolumna). Analityk musiał dopiero poprosić. Warto ...

### #53 [developer] Logowanie per etap — brakuje przypomnienia w workflow gates ról
**Type:** observation
**Preview:** Reguła logowania per etap/workflow/sesja jest w CLAUDE.md, ale dokumenty ról (ERP_SPECIALIST.md, ANALYST.md) nie mają jej wbudowanej w bramki workflow...

## Tool Proposals (user decision) (5)

### #227 [developer] Migration system dla zmian schema i enums
**Type:** tool
**Preview:** # Suggestion: Migration system dla zmian schema i enums  ## Discovery  Sesja #125 wykryła że 12 sugestii w DB ma status `"in_backlog"` (legacy value),...

### #192 [developer] Quick inbox check - czy są nowe wiadomości
**Type:** tool
**Preview:** Narzędzie CLI do szybkiego sprawdzenia czy inbox ma nowe wiadomości (count only, bez full read): ``` python tools/agent_bus_cli.py inbox-count --role ...

### #170 [developer] Pre-commit hook sprawdzający branch przed dużą zmianą
**Type:** tool
**Preview:** **Problem:** Dwukrotnie w tej sesji przypadkowo zacząłem pracę na złym branchu (main zamiast feature). Strata czasu na recovery.  **Propozycja:** Pre-...

### #163 [prompt_engineer] render.py suggestions — brakuje filtra po roli/obszarze
**Type:** tool
**Preview:** type: tool title: render.py suggestions — brakuje filtra po roli/obszarze  ## Problem  `render.py suggestions` i `agent_bus_cli.py suggestions` nie ma...

### #123 [architect] Narzędzie do generowania diagramu architektury
**Type:** tool
**Preview:** Podczas discovery ręcznie tworzę diagram ASCII. Potencjalnie przydatne: narzędzie które skanuje strukturę katalogów i generuje szkielet diagramu do uz...

## Rules (do weryfikacji) (24)

### #228 [prompt_engineer] Drafty user-facing do documents/human/, nie tmp/
**Type:** rule
**Preview:** type: rule title: Drafty dokumentów user-facing zapisuj do documents/human/, nie tmp/  ## Observation  Podczas sesji tworzyłem draft w `tmp/draft_arch...

### #222 [developer] Workflow: Duży refaktor (Developer ↔ Architect tight loop)
**Type:** rule
**Preview:** # Sugestia: Workflow dla dużych refaktorów (Developer ↔ Architect)  ## Observation  Przy dużych refaktorach (M3, M4) workflow jest tight loop między D...

### #212 [architect] Success criteria dla migration phases muszą być explicite, testable, concrete
**Type:** rule
**Preview:** **Bad example (Phase 1 original):** ``` ✓ Testy agent_bus pass ``` → Ambiguous: które testy? Ile? Co jeśli część FAIL?  **Good example (Phase 1 update...

### #198 [architect] Adapter pattern → repositories muszą być transaction-aware
**Type:** rule
**Preview:** **Context:** M3 Phase 1 code review wykazał critical bug — Repository tworzy własne połączenie SQLite zamiast używać współdzielonego AgentBus `self._c...

### #195 [developer] Adapter layer importuje core/ - to jest OK ale dokumentuj dependency
**Type:** rule
**Preview:** AgentBus (tools/lib/agent_bus.py) teraz importuje: ```python from core.repositories.suggestion_repo import SuggestionRepository from core.entities.mes...

### #193 [developer] Status mapping backward compatibility - centralna dokumentacja
**Type:** rule
**Preview:** Adapter M3 Phase 1 mapuje "in_backlog" → "implemented" dla backward compatibility. To powinno być dokumentowane w jednym miejscu (np. agent_bus.py hea...

### #189 [architect] CLI fallback to architectural requirement, nie "nice to have" — headless = core use case
**Type:** rule
**Preview:** **Context:** Wtyczka VS Code ma fundamentalny blocker: **nie działa headless** (wymaga VS Code running).  **Headless environments to core use case dla...

### #187 [architect] Hybryda (wtyczka + CLI) to optimal solution — nie wybieraj "albo-albo" gdy możesz "oba"
**Type:** rule
**Preview:** **Realization:** Wtyczka VS Code **nie zastąpi** CLI subprocess — to komplementarne tools dla różnych use cases: - **Dev use case:** human-in-the-loop...

### #184 [developer] Wszystkie analizy/plany/raporty do pliku md nie inline w czacie
**Type:** rule
**Preview:** Obserwacja: Wszystkie raporty (E1-E4, summary) w plikach .md, nie inline w czacie.  Powód: - Plik przetrwa kompresję kontekstu - Można linkować (ścież...

### #183 [developer] Handoff między rolami musi być explicite z pełnym briefem
**Type:** rule
**Preview:** Good example (ta sesja): - Developer → PE: message id=188 z pełnym kontekstem (problem, rozwiązanie, output contract) - Developer → Architect: message...

### #177 [architect] Code review feedback loop działa — Developer responds well to structured critique
**Type:** rule
**Preview:** **Obserwacja:** Code review #191 miał 4 warnings + 3 suggestions. Developer zaimplementował wszystkie warnings i 2/3 suggestions przed przejściem do M...

### #172 [developer] TDD dla Repository implementations — testy przed kodem
**Type:** rule
**Preview:** **Problem:** Nie zastosowałem TDD mimo planu. Napisałem kod, potem testy.  **Propozycja:** Dla M2 part 2 (BacklogRepository, MessageRepository) spróbo...

### #169 [architect] Nowy kod w core/, stary w tools/ przez adaptery
**Type:** rule
**Preview:** Strategia migracji: nowe klasy domenowe w core/, stary kod tools/ deleguje przez adaptery. Zachowujemy kompatybilność wsteczną (CLI działa bez zmian)....

### #161 [developer] Onboarding gap — gdzie pracować jako non-developer współpracownik?
**Type:** rule
**Preview:** Arek tworzył pliki w rootcie bo nie miał guidance gdzie pracować.  **Problem:** Dokumentacja zakłada że user = developer lub agent. Nie ma instrukcji ...

### #158 [developer] Narzędzia pomocnicze: maintain actively or delete
**Type:** rule
**Preview:** verify.py pokazuje koszt porzuconych narzędzi — działało, ale straciło aktualność przy refaktorze nazw (search_docs → docs_search).  **Problem:** Narz...

### #141 [architect] Nowy kod w core/, stary w tools/ przez adaptery
**Type:** rule
**Preview:** Strategia migracji: nowe klasy domenowe w core/, stary kod tools/ deleguje przez adaptery. Zachowujemy kompatybilność wsteczną (CLI działa bez zmian)....

### #132 [architect] Audyt Fazy 1-4: findings do wdrożenia
**Type:** rule
**Preview:** Audyt architektoniczny (Fazy 1-4) — główne findings do wdrożenia:  1. **CRITICAL:** bot/pipeline/nlp_pipeline.py — brak obsługi wyjątków Anthropic API...

### #120 [architect] Workflow Architecture Discovery — kroki
**Type:** rule
**Preview:** Proponowany workflow do badania repozytoriów z lotu ptaka:  **Etap 1: Struktura (Glob)** - Glob `**/*` lub `**/` — lista katalogów i plików - Zidentyf...

### #95 [erp_specialist] Nr_Dokumentu_Zrodlowego — złożony JOIN gdy ZrdTyp ma wiele typów
**Type:** rule
**Preview:** type: rule title: Nr_Dokumentu_Zrodlowego — złożony JOIN gdy ZrdTyp ma wiele typów Gdy tabela ma kolumnę ZrdTyp/ZrdNumer wskazującą na dokument źródło...

### #83 [prompt_engineer] PE: suggestion z self-reported violation = analiza compliance, nie tool request
**Type:** rule
**Preview:** PE przeczytał sugestię #80 od Developer i sklasyfikował ją jako zadanie Developera (nowe narzędzie CLI). Nie wychwycił że treść sugestii zawierała jaw...

### #69 [prompt_engineer] Konwencja numeracji kroków w workflow i listach
**Type:** rule
**Preview:** type: rule title: Konwencja numeracji kroków w workflow i listach Kroki workflow numeruj jako: numer fazy + litera kroku (1a, 1b, 2a, 2b...). Listy ni...

### #64 [developer] Jeden błąd tego samego typu = diagnoza zasięgu przed naprawą
**Type:** rule
**Preview:** Gdy wykryty zostaje błąd (np. niepoprawnie zamknięte sugestie) — zanim zaczniesz naprawiać konkretny przypadek, zdiagnozuj czy ten sam błąd nie występ...

### #63 [developer] Przed migracją danych — przedstaw plan człowiekowi
**Type:** rule
**Preview:** Każda migracja danych (zmiana statusów, przypisywanie typów, aktualizacja historycznych rekordów) wymaga przedstawienia planu człowiekowi PRZED wykona...

### #51 [developer] Runner: busy = ochrona budżetu tokenowego, nie "subprocess działa"
**Type:** rule
**Preview:** busy w modelu instancji runnera oznacza że sesja jest w toku i nie można jej zagłuszyć nowym wywołaniem — chodzi o ochronę budżetu tokenowego workflow...

## Discoveries (do weryfikacji) (15)

### #246 [developer] User feedback as quality gate — three catches in one session
**Type:** discovery
**Preview:** ## Three times user caught gaps  1. "A to nie było już zrealizowane?" → backlog #7 verification 2. "Nie mamy narzędzia..." → backlog #126 (message too...

### #210 [architect] Backward compatibility to nie tylko "przyjmuj stare wartości" — to round-trip consistency
**Type:** discovery
**Preview:** **Context:** M3.1 patch odkrył że backward compatibility wymaga **symmetric API** — nie tylko forward mapping (write), ale też reverse mapping (read)....

### #208 [architect] Transaction support w adapter pattern to nie optional feature — to architectural requirement
**Type:** discovery
**Preview:** **Realization:** M3 Phase 1 pokazał że transaction support to nie "nice to have" — to **fundamentalna część adapter pattern** gdy migrujemy procedural...

### #201 [architect] Backward compatibility wymaga symmetric API — reverse mapping dla read operations
**Type:** discovery
**Preview:** type: discovery title: Backward compatibility wymaga symmetric API — reverse mapping dla read operations  **Context:** M3.1 patch (commit 533a0f5) — D...

### #200 [architect] Repository isolation vs shared context — trade-off dla adapter pattern
**Type:** discovery
**Preview:** **Discovery:** Repository pattern (domain-driven design) zakłada repository isolation — każdy repository zarządza własnym connection lifecycle. Czyste...

### #196 [developer] recipients w Suggestion było missing field
**Type:** discovery
**Preview:** Stary agent_bus.py serializował recipients do JSON w kolumnie suggestions.recipients, ale nowy Suggestion entity nie miał tego pola. Dodałem recipient...

### #191 [developer] Inbox realtime - wiadomość przyszła podczas sesji
**Type:** discovery
**Preview:** Na początku sesji inbox był pusty. Architekt wysłał msg #191 o 17:23:47 PODCZAS mojej sesji. Nie sprawdziłem inbox ponownie - zakładałem że jest pusty...

### #181 [developer] VS Code Terminal API daje interaktywność za darmo
**Type:** discovery
**Preview:** `vscode.window.createTerminal()` + `terminal.sendText('claude.cmd ...')` automatycznie obsługuje: - User input (pisanie w terminalu) - Przekazywanie d...

### #178 [architect] Repository pattern eliminuje 90% copy-paste — _find_by() jako proof
**Type:** discovery
**Preview:** **Przed:** find_by_status, find_by_author, find_by_type — każda ~20 linii, 90% identyczne **Łącznie:** ~70 linii copy-paste per repository × 3 reposit...

### #173 [developer] pyproject.toml konieczne dla pytest imports w modułach
**Type:** discovery
**Preview:** **Odkrycie:** pytest nie widzi modułów bez pyproject.toml + pip install -e .  **Problem:** sys.path insert w conftest.py nie wystarczy.  **Rozwiązanie...

### #167 [architect] invocation_log śledzi wywołania agent→agent
**Type:** discovery
**Preview:** Tabela do mrowisko_runner — loguje from_role, to_role, depth, turns, cost. 6 rekordów testowych. Będzie kluczowa przy multi-agent.

### #165 [architect] Tabele trace i state są martwe/legacy
**Type:** discovery
**Preview:** trace: 0 rekordów, zastąpiona przez tool_calls. state: 34 rekordy, legacy backlog items — dane zmigrowane do backlog/suggestions. Obie do usunięcia pr...

### #137 [architect] Tabele trace i state są martwe/legacy
**Type:** discovery
**Preview:** trace: 0 rekordów, zastąpiona przez tool_calls. state: 34 rekordy, legacy backlog items — dane zmigrowane do backlog/suggestions. Obie do usunięcia pr...

### #133 [architect] 75k rekordów tool_calls/token_usage — gotowe do analizy
**Type:** discovery
**Preview:** tool_calls (30k) i token_usage (44k) to gotowy materiał do analizy zachowania agentów.  Warto zacząć analizować: - Zużycie tokenów per rola / per sesj...

### #122 [architect] _loom jako seed replikacji
**Type:** discovery
**Preview:** Katalog _loom/ zawiera szablony do replikacji Mrowiska w nowych projektach. To potencjalnie osobny produkt / repo. Nie jest udokumentowany w ARCHITECT...

## Observations (do weryfikacji) (48)

### #261 [architect] ## Meta-Reflection: Czego Ta Migracja Nauczyła
**Type:** observation
**Preview:** ## Meta-Reflection: Czego Ta Migracja Nauczyła  **Dla Architecta:**  1. **Recognize golden windows** (complexity low = act now) 2. **Communicate compo...

### #259 [architect] ## 9. User Involvement — Strategic, Not Constant
**Type:** observation
**Preview:** ## 9. User Involvement — Strategic, Not Constant  **Obserwacja:**  User involvement w M4: - Backlog #7: Developer checked status=done → NIE pytał user...

### #257 [architect] ## 7. Full Stack Fail-Fast — Defense in Depth
**Type:** observation
**Preview:** ## 7. Full Stack Fail-Fast — Defense in Depth  **Obserwacja:**  M4 zbudował fail-fast na 4 poziomach: - Code: Domain enums (ValueError at construction...

### #256 [architect] ## 6. Developer Growth Trajectory — Pattern Internalization
**Type:** observation
**Preview:** ## 6. Developer Growth Trajectory — Pattern Internalization  **Obserwacja:**  M4 pokazał growth trajectory: - Initial: Strong implementation, edge cas...

### #255 [architect] ## 5. Backward Compatibility as Architecture Constraint
**Type:** observation
**Preview:** ## 5. Backward Compatibility as Architecture Constraint  **Obserwacja:**  M3 constraint: "Zero breaking changes (absolute requirement)"  **To nie było...

### #254 [architect] ## 4. Proactive Discovery > Reactive Fix
**Type:** observation
**Preview:** ## 4. Proactive Discovery > Reactive Fix  **Obserwacja:**  M4.2.1 enum audit: - Assumption: "audyt pokaże czy domain model kompletny" - Reality: "doma...

### #253 [architect] ## 3. Collaboration as Accelerant — Tight Feedback Loop
**Type:** observation
**Preview:** ## 3. Collaboration as Accelerant — Tight Feedback Loop  **Obserwacja:**  M4 trajectory: - M4.1.2 initial: Mid (edge case oversight) - Code review fee...

### #251 [architect] ## 1. "Now or Never" Moment — Architectural Intuition
**Type:** observation
**Preview:** ## 1. "Now or Never" Moment — Architectural Intuition  **Obserwacja:**  User powiedział: "Gdybyśmy tego nie zrobili teraz to chyba w ogóle by się nie ...

### #249 [developer] Architect collaboration — tight feedback loop elevates quality
**Type:** observation
**Preview:** ## Pattern  After EACH phase: review → feedback → fix → GREEN LIGHT → next phase  Quality progression: Mid → Senior → Production-grade (over 4 phases)...

### #238 [prompt_engineer] ## 10. Backlog area "Prompt" vs backlog per rola?
**Type:** observation
**Preview:** ## 10. Backlog area "Prompt" vs backlog per rola?  **Observation:** Backlog ma `area: Prompt` dla wszystkich PE tasków.  Ale PE pracuje **na promptach...

### #237 [prompt_engineer] ## 9. Drafty do documents/human/ (suggestion #228) — czy to wystarczy?
**Type:** observation
**Preview:** ## 9. Drafty do documents/human/ (suggestion #228) — czy to wystarczy?  **Created:** #228 (rule: drafty user-facing do documents/human/)  **Pytanie:**...

### #235 [prompt_engineer] ## 7. Title w logach = game changer (ale dopiero gdy zaczniemy używać)
**Type:** observation
**Preview:** ## 7. Title w logach = game changer (ale dopiero gdy zaczniemy używać)  **Observation:** Developer dodał kolumnę `title` (#120), ale **wszystkie stare...

### #233 [prompt_engineer] ## 5. Rollback pattern powtarzalny
**Type:** observation
**Preview:** ## 5. Rollback pattern powtarzalny  **Evidence:** 2× rollback w sesji: 1. Rollback 6 promptów (SQL inline → czekaj na tool) 2. Rollback 4 promptów (3 ...

### #232 [prompt_engineer] ## 4. Dependency visibility gap (backlog)
**Type:** observation
**Preview:** ## 4. Dependency visibility gap (backlog)  **Problem:** #119 zależy od #123, ale to tylko prose w `content`.  Machine nie widzi zależności → nie może:...

### #230 [prompt_engineer] ## 2. Developer ↔ PE feedback loop działa bardzo dobrze
**Type:** observation
**Preview:** ## 2. Developer ↔ PE feedback loop działa bardzo dobrze  **Evidence:** - #219 request (offset/metadata) → 15 min → delivered (#221) - #224 request (--...

### #229 [prompt_engineer] # Refleksje PE — sesja session_start rozszerzenie
**Type:** observation
**Preview:** # Refleksje PE — sesja session_start rozszerzenie  ## 1. User feedback > agent planning (krytyczne)  **Pattern:** 3 pivot pointy w sesji — za każdym r...

### #226 [architect] type: observation
**Type:** observation
**Preview:** type: observation title: Collaborative decision-making pattern działa — Developer msg #206  ## Context  Developer msg #206: 4 pytania architektoniczne...

### #225 [architect] type: tool
**Type:** observation
**Preview:** type: tool title: Edge case checklist przed code review — prevent M4.1.2 pattern  ## Context  M4.1.2 code review wyłapał edge case bug (REJECTED/DEFER...

### #219 [architect] type: observation
**Type:** observation
**Preview:** type: observation title: Developer pokazuje senior-level architectural thinking  ## Context  Developer msg #206 (pytania architektoniczne M3→M4 transi...

### #218 [developer] Graceful degradation vs data fix — tech debt永久化
**Type:** observation
**Preview:** M3 enum fix: wybraliśmy aliasy w kodzie (`VALUE_ALIASES = {"średnia": "srednia"}`). Backward compatible, szybkie, ale aliasy w kodzie **na zawsze**.  ...

### #217 [developer] Enum extensions reactive (production data drives definition)
**Type:** observation
**Preview:** M3 Phase 3: dodano BacklogArea.PROMPT, METODOLOG, MessageStatus.ARCHIVED reactively (bo production data w bazie).  **Pattern:** Enum definition lags b...

### #216 [developer] Backward compatibility tax — reverse mapping duplicated
**Type:** observation
**Preview:** Domain model ≠ legacy API wymaga double mapping: - TYPE_MAP (legacy → domain) w write paths - TYPE_REVERSE_MAP (domain → legacy) w read paths  **Przyk...

### #215 [developer] DRY violations rosną liniowo z liczbą repositories
**Type:** observation
**Preview:** M3 ma 3 repositories (Suggestion, Backlog, Message). Duplikacja: - Repo creation pattern: `conn = self._conn if ... else None` (7× w adapters) - Dict ...

### #214 [developer] Test checkpoint pattern = killer feature dla transaction bugs
**Type:** observation
**Preview:** M3 Phase 3: uruchamianie `py -m pytest tests/test_agent_bus.py::TestTransactions -v` po każdej metodzie wyłapało 3 bugs before commit (AttributeError,...

### #209 [architect] Test checkpoint granularity matters — per-method > per-phase dla migration tasks
**Type:** observation
**Preview:** **Evidence:** - Phase 1: Brak test checkpoint per-method → bug w code review (expensive fix) - Phase 2: Test checkpoint per-method → bug caught immedi...

### #207 [architect] Code review jako teaching tool — feedback loop z graduated autonomy działa at scale
**Type:** observation
**Preview:** **Context:** Sesja 805fc5a26cc6 — code review M3 (4 fazy: Phase 1, M3.1 patch, Phase 2, Phase 3).  **Progression observed:**  **Phase 1 → Phase 2:** -...

### #205 [architect] Developer internalized pattern recognition — reverse mapping applied autonomously Phase 3
**Type:** observation
**Preview:** **Context:** M3 Phase 3 code review — Developer zastosował reverse mapping z M3.1 patch (Suggestions) do Messages **bez reminder**.  **Lesson source:*...

### #203 [architect] Developer internalized lessons — Senior-level autonomy pokazana
**Type:** observation
**Preview:** **Context:** M3 Phase 2 code review — wszystkie lessons z Phase 1 zastosowane **bez przypominania**.  **Evidence:** 1. **Transaction support od począt...

### #202 [architect] Test checkpoint pattern działa — bugs wyłapane wcześnie, nie w code review
**Type:** observation
**Preview:** **Context:** M3 Phase 2 code review (commit 676cff4) — Developer wyłapał bug `updated_at` przez test checkpoint, nie w code review.  **Bug:** `updated...

### #197 [developer] Context manager pattern drastycznie redukuje boilerplate
**Type:** observation
**Preview:** Przed context manager: ~16 linii boilerplate per metoda (conn = ..., try, finally, close). Po context manager: ~3 linie (with self._connection() as co...

### #194 [developer] 19 failed testów test_agent_bus.py - do naprawienia w Phase 2-4
**Type:** observation
**Preview:** test_agent_bus.py: 47 pass, 19 failed. Failures: - TestState (6 testów) - write_state/get_state używa starego kodu - TestBacklog.test_backlog_with_sou...

### #186 [architect] Developer wykonał Senior-level research (E1-E4) — systematyczny i z trade-offami
**Type:** observation
**Preview:** **Evidence:** - E1 (Agent Teams): nie tylko "sprawdź czy działa" — zbadał integrację z agent_bus (kluczowy blocker identified) - E4 (wtyczka): 4 testy...

### #185 [developer] Minor issues nie powinny blokować decyzji architektonicznej
**Type:** observation
**Preview:** Minor issues zidentyfikowane w E4: - PowerShell buffering (output opóźniony) - Brak statusu agenta (nie wiadomo czy pracuje) - Sesja kończy się za szy...

### #182 [developer] Interaktywność human-agent to core feature nie nice-to-have
**Type:** observation
**Preview:** Projekt Mrowisko ≠ tylko autonomia agentów. To współpraca human-agent.  Odkrycie z E4: Human klika w terminal spawned agenta → pisze wiadomość → agent...

### #180 [developer] Eksperymentowanie przed decyzją architektoniczną = ROI
**Type:** observation
**Preview:** Zamiast wybierać architekturę "na czuja" → 4 eksperymenty (E1-E4) dały dane empiryczne.  Koszt: ~4h (research + implementacja PoC + testy)  Zysk: Potw...

### #179 [architect] Context manager eliminuje 160 linii boilerplate — concrete cost/benefit
**Type:** observation
**Preview:** **Przed:** Każda metoda (get, save, delete, find_all, find_by_* × 3) miała: ```python conn = self._get_connection() try:     # ... finally:     conn.c...

### #176 [architect] Developer osiągnął Senior-level w M2 — świetna inicjatywa i commitment
**Type:** observation
**Preview:** Developer nie tylko zakończył M2 part 2, ale też: 1. Zaadresował **wszystkie** findings z code review #191 przed przejściem dalej (4 warnings + 2 sugg...

### #175 [developer] Typ wiadomości review w agent_bus
**Type:** observation
**Preview:** # Sugestia: Typ wiadomości "review" w agent_bus  ## Obserwacja  Wysyłając wiadomość do Architect (message id=194) z wynikami eksperymentów, zdałem sob...

### #162 [developer] Verification gates nie działają bez enforcement — backlog #104 był już done
**Type:** observation
**Preview:** type: observation title: Verification gates nie działają bez enforcement — backlog #104 był już done  ## Co się stało  Dzisiaj (2026-03-22) dostałem z...

### #155 [prompt_engineer] Inbox rośnie szybciej niż przetwarzamy
**Type:** observation
**Preview:** ## 3. Inbox rośnie szybciej niż zdążamy przetwarzać  **Obserwacja:** - Dzisiaj inbox: 9 wiadomości nieprzeczytanych - Część z poprzednich sesji (#148 ...

### #153 [prompt_engineer] Persona Architekta — 2 iteracje, wciąż nie działa
**Type:** observation
**Preview:** ## 1. Persona Architekta — 2 iteracje, wciąż nie działa jak oczekiwano  **Obserwacja:** - Sesja 2026-03-22 rano: feedback #177 — Architekt reaktywny m...

### #151 [developer] Backlog items mogą być przestarzałe — lifecycle problem
**Type:** observation
**Preview:** 3 z 4 zadań dziś: - #105: Aktualny ✓ - #107: Aktualny ✓ - #106: Przestarzały (render.py już miał JSON)  **Problem:** Backlog items nie mają mechanizmu...

### #135 [prompt_engineer] Verification gates — gdzie jeszcze brakuje?
**Type:** observation
**Preview:** Verification gates — gdzie jeszcze brakuje?  Backlog #86 pokazał że Developer nie sprawdził "czy już zrobione" przed dodaniem do backlogu. Fix dodany ...

### #131 [architect] Granica Architect vs Developer rozmyta
**Type:** observation
**Preview:** Prompt Architekta mówi "Architekt projektuje, Developer implementuje". Ale w praktyce obie role dotykają tych samych plików (tools/, documents/). Prop...

### #127 [architect] mrowisko.db — podwójna odpowiedzialność
**Type:** observation
**Preview:** Baza trzyma zarówno komunikację agentów (messages, backlog, suggestions) jak i historię sesji Claude Code (conversation, tool_calls, token_usage). To ...

### #101 [analyst] ERP Specialist używa Komentarz_Analityka jako listy TODO — nie jako gotowego planu
**Type:** observation
**Preview:** W MagNag iteracja 1 ERP Specialist wysłał plan z kolumnami opisowymi FK odnotowanymi w Komentarz_Analityka ("Dodać Kod_Magazynu..."), ale nie dodał ic...

### #98 [erp_specialist] Inbox i workflow konsumuja nadmiernie kontekst — 3 kierunki optymalizacji
**Type:** observation
**Preview:** Inbox konsumuje nadmiernie kontekst przy każdym sprawdzeniu. W sesji 2026-03-20 inbox był sprawdzany 3 razy, za każdym razem zwracając 10-14 wiadomośc...

### #62 [analyst] Handoff ERP→Analityk — Analityk nie ładuje doc workflow poprzednika automatycznie
**Type:** observation
**Preview:** Przy przejściu ERP Specialist → Analityk, Analityk nie ma obowiązku zapoznania się z dokumentami workflow poprzedniej roli. Konieczna była ręczna kore...
