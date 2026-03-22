# Suggestions — 2026-03-22

*42 sugestii*

---

## Zasady (rule)

| id | autor | tytuł | status | data |
|----|-------|-------|--------|------|
| 145 | prompt_engineer | Agent bez roli = STOP, wymaga mocnego gate | open | 2026-03-22 |
| 141 | architect | Nowy kod w core/, stary w tools/ przez adaptery | open | 2026-03-22 |
| 134 | prompt_engineer | Research przed promptem nowej roli — standardowy krok PE | open | 2026-03-22 |
| 132 | architect | Audyt Fazy 1-4: findings do wdrożenia | open | 2026-03-22 |
| 125 | prompt_engineer | Funkcje krótkie (≤15 linii) — standard dla Developer, nie tylko Architect | open | 2026-03-21 |
| 124 | prompt_engineer | Nowy prompt roli: minimal viable prompt zamiast pełnych workflow | open | 2026-03-21 |
| 120 | architect | Workflow Architecture Discovery — kroki | open | 2026-03-21 |
| 119 | prompt_engineer | Research przed promptem nowej roli — standardowy krok PE | open | 2026-03-21 |
| 95 | erp_specialist | Nr_Dokumentu_Zrodlowego — złożony JOIN gdy ZrdTyp ma wiele typów | open | 2026-03-20 |
| 83 | prompt_engineer | PE: suggestion z self-reported violation = analiza compliance, nie tool request | open | 2026-03-18 |
| 69 | prompt_engineer | Konwencja numeracji kroków w workflow i listach | open | 2026-03-18 |
| 64 | developer | Jeden błąd tego samego typu = diagnoza zasięgu przed naprawą | open | 2026-03-17 |
| 63 | developer | Przed migracją danych — przedstaw plan człowiekowi | open | 2026-03-17 |
| 52 | developer | session_init załadował doc roli — przy edycji używaj tej treści, nie Read | open | 2026-03-17 |
| 51 | developer | Runner: busy = ochrona budżetu tokenowego, nie "subprocess działa" | open | 2026-03-17 |

## Narzędzia (tool)

| id | autor | tytuł | status | data |
|----|-------|-------|--------|------|
| 123 | architect | Narzędzie do generowania diagramu architektury | open | 2026-03-21 |

## Odkrycia (discovery)

| id | autor | tytuł | status | data |
|----|-------|-------|--------|------|
| 144 | developer | 13 backlogów zamkniętych w jednej sesji - quick wins effective | open | 2026-03-22 |
| 139 | architect | invocation_log śledzi wywołania agent→agent | open | 2026-03-22 |
| 137 | architect | Tabele trace i state są martwe/legacy | open | 2026-03-22 |
| 133 | architect | 75k rekordów tool_calls/token_usage — gotowe do analizy | open | 2026-03-22 |
| 122 | architect | _loom jako seed replikacji | open | 2026-03-21 |

## Obserwacje (observation)

| id | autor | tytuł | status | data |
|----|-------|-------|--------|------|
| 146 | architect | Architect pracuje zbyt krótkowzrocznie | open | 2026-03-22 |
| 143 | developer | Pattern - zrealizowane backlogi nie zamknięte | open | 2026-03-22 |
| 142 | developer | Rename narzędzia wymaga update settings.local.json | open | 2026-03-22 |
| 140 | architect | Moment strategiczny na refaktor | open | 2026-03-22 |
| 138 | architect | Bot wymaga hardeningu przed skalowaniem | open | 2026-03-22 |
| 136 | architect | Dict-based architecture nie skaluje się | open | 2026-03-22 |
| 135 | prompt_engineer | Verification gates — gdzie jeszcze brakuje? | open | 2026-03-22 |
| 131 | architect | Granica Architect vs Developer rozmyta | open | 2026-03-21 |
| 130 | architect | _loom wygląda na porzucony | open | 2026-03-21 |
| 129 | architect | Nazewnictwo narzędzi — brak konwencji | open | 2026-03-21 |
| 128 | architect | tmp/ jako de facto inbox człowieka | open | 2026-03-21 |
| 127 | architect | mrowisko.db — podwójna odpowiedzialność | open | 2026-03-21 |
| 126 | prompt_engineer | Code maturity levels — wzorzec referencyjny dla oceny jakości kodu | open | 2026-03-21 |
| 121 | architect | Istniejący ARCHITECTURE.md w documents/dev/ | open | 2026-03-21 |
| 109 | developer | bot eval (id=84) krytyczny przed kolejną rundą zmian promptu | open | 2026-03-20 |
| 105 | analyst | MagElem — duplikat aliasu Kod_Towaru — planowanie dwóch źródeł dla jednej kolumny | open | 2026-03-20 |
| 104 | analyst | Faza 3 — ERP Specialist domyślnie wysyła self-check, nie pełne bi_verify | open | 2026-03-20 |
| 101 | analyst | ERP Specialist używa Komentarz_Analityka jako listy TODO — nie jako gotowego planu | open | 2026-03-20 |
| 98 | erp_specialist | Inbox i workflow konsumuja nadmiernie kontekst — 3 kierunki optymalizacji | open | 2026-03-20 |
| 62 | analyst | Handoff ERP→Analityk — Analityk nie ładuje doc workflow poprzednika automatycznie | open | 2026-03-17 |
| 53 | developer | Logowanie per etap — brakuje przypomnienia w workflow gates ról | open | 2026-03-17 |

---

## Treści

### Zasady (rule)

#### [145] Agent bez roli = STOP, wymaga mocnego gate
**autor:** prompt_engineer  **status:** open  **data:** 2026-03-22

## Brak inicjalizacji roli - agent działał bez session_init

### Co się stało

Sesja 2026-03-22 ~11:05 - user napisał "Masz wiadomość od Architekta".

Agent:
1. Przeczytał wiadomość z inbox
2. Analizował treść
3. Rozmawiał z userem o problemie
4. Dopiero gdy user zapytał "A w jakiej roli jesteś?" zainicjował `session_init.py --role prompt_engineer`

### Problem

Agent nie wykonał `session_init.py` na początku sesji. Działał bez określonej roli przez ~10 wiadomości.

**Dlaczego to się stało:**
- User pisał "PE" w kontekście (skrót od Prompt Engineer)
- Agent założył rolę po kontekście zamiast wymagać jawnej inicjalizacji
- Brak mocnego gate'a "STOP jeśli nie masz roli"

### Ryzyko

Gdy agent działa bez roli:
- Nie ma loaded instrukcji operacyjnych
- Nie wie jakie ma narzędzia allowed/disallowed
- Może wykonywać zadania poza swoim scope
- Nie loguje do właściwej roli
- Narusza podstawową konwencję systemu

### Rekomendacja

**CLAUDE.md - dodać na początku sekcji "Twoja rola":**

```markdown
## UWAGA: Agent bez roli = STOP

Jeśli NIE wykonałeś `python tools/session_init.py --role <parametr>` na początku tej sesji:

**WYŚWIETL ALERT:**
```
⚠️ UWAGA: NIE MAM OKREŚLONEJ ROLI

Nie wykonałem session_init.py na początku sesji.
Bez roli nie wiem:
- Jakie są moje instrukcje operacyjne
- Jakie narzędzia mogę używać
- Do kogo eskalowaćć

Którą rolę powinienem przyjąć dla tego zadania?
(Tabela ról poniżej)
```

**NIE wykonuj żadnych poleceń (poza odczytem inbox informacyjnym) dopóki user nie potwierdzi roli.**

**Wyjątek:** User napisał jawnie nazwę roli w pierwszej wiadomości (np. "ERP Specialist, zbuduj widok X")
- wtedy możesz od razu wywołać session_init.

Skróty typu "PE" NIE są jawną nazwą roli - pytaj o potwierdzenie.
```

### Typ

rule (zasada do wdrożenia w CLAUDE.md)

#### [141] Nowy kod w core/, stary w tools/ przez adaptery
**autor:** architect  **status:** open  **data:** 2026-03-22

Strategia migracji: nowe klasy domenowe w core/, stary kod tools/ deleguje przez adaptery. Zachowujemy kompatybilność wsteczną (CLI działa bez zmian). Stopniowa migracja, nie big bang.

#### [134] Research przed promptem nowej roli — standardowy krok PE
**autor:** prompt_engineer  **status:** open  **data:** 2026-03-22

Research przed promptem nowej roli — standardowy krok PE

Pattern użyty przy Architect i Researcher:
1. Napisz research prompt
2. Uruchom research (zewnętrzny agent)
3. Przeczytaj wyniki
4. Projektuj prompt roli na podstawie wyników

To działa — prompt Architect był minimal viable (171 linii) dzięki researchu (487 linii wyników, 27 źródeł).

Ale:
- Pattern nie jest sformalizowany w PROMPT_ENGINEER.md workflow
- Jest jako suggestion #119 (status: open), nie wdrożony

Rekomendacja:
Dodać do PE workflow jako Faza 0 przed projektowaniem nowej roli:
```
Faza 0 — Research (przed projektem promptu)
1. Napisz research prompt (research_prompt_<rola>.md)
2. Uruchom research przez zewnętrzne narzędzie
3. Zapisz wyniki (research_results_<rola>.md)
4. Przeczytaj wyniki i zidentyfikuj kluczowe wzorce
5. Dopiero teraz projektuj prompt roli
```

Wzorzec z Architect pokazał że research (487 linii) + minimal prompt (171 linii) > duży prompt bez researchu (643 linie draftu).

Source: sesja PE 2026-03-22, Architect + Researcher

#### [132] Audyt Fazy 1-4: findings do wdrożenia
**autor:** architect  **status:** open  **data:** 2026-03-22

Audyt architektoniczny (Fazy 1-4) — główne findings do wdrożenia:

1. **CRITICAL:** bot/pipeline/nlp_pipeline.py — brak obsługi wyjątków Anthropic API (RateLimitError, APIError)
2. **HIGH:** mrowisko.db — cleanup policy dla tool_calls (30k) i token_usage (44k)
3. **MEDIUM:** Usunąć martwą tabelę `trace`, deprecate `state`
4. **MEDIUM:** Rozbić nlp_pipeline.py (218 linii) na mniejsze komponenty
5. **LOW:** Rename search_bi.py → bi_search.py dla spójności nazewnictwa

#### [125] Funkcje krótkie (≤15 linii) — standard dla Developer, nie tylko Architect
**autor:** prompt_engineer  **status:** open  **data:** 2026-03-21

Funkcje krótkie — standard jakości kodu dla całego projektu.

Wymaganie użytkownika (sesja PE 2026-03-21, projektowanie Architect):
- Optymalna funkcja: ≤15 linii
- Powyżej 40 linii → wymaga refaktoru (jeśli możliwy)
- Logika dzielona między funkcjami → wyciągnij do podfunkcji (DRY)

Obecnie:
- Zasada jest w ARCHITECT.md critical_rules #6 (code review)
- Brak w DEVELOPER.md (Developer pisze kod, ale nie ma tej zasady w swoich instrukcjach)

Propozycja:
Dodać do DEVELOPER.md critical_rules lub end_of_turn_checklist:
"Funkcje krótkie i focused: optymalna ≤15 linii, >40 wymaga refaktoru. Logika dzielona między funkcjami → podfunkcja (DRY)."

Albo:
Dodać do CLAUDE.md jako zasada wspólna dla wszystkich ról piszących kod (Developer, Architect w PoC).

Uzasadnienie: jeśli to standard projektu, powinien być w instrukcjach tego kto pisze kod, nie tylko kto go ocenia.

#### [124] Nowy prompt roli: minimal viable prompt zamiast pełnych workflow
**autor:** prompt_engineer  **status:** open  **data:** 2026-03-21

Nowy prompt roli: minimal viable prompt (MVP) zamiast pełnych workflow na starcie.

Obserwacja z sesji Architect:
- Pierwsza wersja: 643 linie (pełne workflow per typ zadania)
- Feedback użytkownika: "długi, wolę coś krótkiego na początek"
- Wersja finalna: 171 linii (minimal, rozszerzalny)

Uzasadnienie:
1. Pełne workflow na starcie = sztywność, trudne do modyfikacji
2. Minimal prompt = elastyczność, nabudowa w praktyce na podstawie rzeczywistych sesji
3. Agent uczy się w praktyce, nie z góry zaprojektowanych wszystkich scenariuszy
4. Łatwiejsze utrzymanie i iteracja

Zasada dla PE przy projektowaniu nowej roli:
- Minimum: mission, scope, critical rules (5-8), output contract, minimal workflow routing
- Nie pisać szczegółowych kroków workflow zanim nie zobaczymy jak rola działa w praktyce
- Workflow nabudowywać iteracyjnie na podstawie rzeczywistych sesji i failure modes

Wzorzec: ARCHITECT.md (171 linii) vs pierwotny draft (643 linie).

#### [120] Workflow Architecture Discovery — kroki
**autor:** architect  **status:** open  **data:** 2026-03-21

Proponowany workflow do badania repozytoriów z lotu ptaka:

**Etap 1: Struktura (Glob)**
- Glob `**/*` lub `**/` — lista katalogów i plików
- Zidentyfikuj główne katalogi: src/, tools/, docs/, tests/

**Etap 2: Kluczowe pliki (Read równolegle)**
- README.md — cel projektu, instalacja
- CLAUDE.md lub podobne — instrukcje dla agenta
- Plik manifestu (package.json, pyproject.toml, requirements.txt)
- Główny plik architektury jeśli istnieje

**Etap 3: Głębsze nurkowanie (Read równolegle)**
- Entry points (main.py, index.js)
- Kluczowe moduły biblioteczne (lib/, core/)
- Konfiguracja (config/, .env.example)

**Etap 4: Synteza**
- Zidentyfikuj warstwy systemu
- Narysuj diagram przepływu
- Wypisz komponenty i ich relacje

**Etap 5: Dokument**
- Utwórz SYSTEM_ARCHITECTURE.md lub podobny
- Sekcje: Wizja, Diagram, Warstwy, Komponenty, Słownik

Obserwacja: równoległe Read (do 5 plików naraz) znacząco przyspiesza discovery.

#### [119] Research przed promptem nowej roli — standardowy krok PE
**autor:** prompt_engineer  **status:** open  **data:** 2026-03-21

Przy projektowaniu nowej roli agenta — najpierw research, potem prompt.

Research przed promptem pozwala:
1. Znaleźć sprawdzone wzorce i terminologię z publicznych źródeł
2. Uniknąć wymyślania konwencji od zera (skorzystać z praktyk OpenAI, Anthropic, LangChain, CrewAI)
3. Zidentyfikować anti-patterns przed ich wdrożeniem
4. Mieć bazę źródłową do uzasadnienia decyzji projektowych

Wzorzec użyty w projekcie Architect (2026-03-21):
1. Research prompt → research_prompt_architect_role.md (pytania badawcze, output contract)
2. Uruchomienie researchu (WebSearch)
3. Wyniki → research_results_architect_role.md (487 linii, 27 źródeł)
4. Projektowanie promptu ARCHITECT.md na podstawie wyników researchu

Konwencja do wdrożenia w workflow PE: research przed promptem nowej roli jako standardowy krok.

#### [95] Nr_Dokumentu_Zrodlowego — złożony JOIN gdy ZrdTyp ma wiele typów
**autor:** erp_specialist  **status:** open  **data:** 2026-03-20

type: rule
title: Nr_Dokumentu_Zrodlowego — złożony JOIN gdy ZrdTyp ma wiele typów
Gdy tabela ma kolumnę ZrdTyp/ZrdNumer wskazującą na dokument źródłowy wielu różnych typów
(np. MagNag: 21 typów = TraNag + ZamNag), budowa Nr_Dokumentu_Zrodlowego wymaga:
1. LEFT JOIN CDN.TraNag zrd_tra ON TrN_GIDNumer = ZrdNumer AND TrN_GIDTyp = ZrdTyp AND ZrdNumer > 0 AND ZrdTyp <> 960
2. LEFT JOIN CDN.ZamNag zrd_zan ON ZaN_GIDNumer = ZrdNumer AND ZrdTyp = 960 AND ZrdNumer > 0
3. CASE WHEN ZrdNumer = 0 THEN NULL WHEN ZrdTyp = 960 THEN [format ZS] ELSE [format TraNag ze skrótem z obiekty.tsv] END
Nie buduj osobnego JOIN per typ — wystarczą dwa (TraNag pokrywa ~20/21 typów, ZamNag pokrywa 960).

#### [83] PE: suggestion z self-reported violation = analiza compliance, nie tool request
**autor:** prompt_engineer  **status:** open  **data:** 2026-03-18

PE przeczytał sugestię #80 od Developer i sklasyfikował ją jako zadanie Developera (nowe narzędzie CLI).
Nie wychwycił że treść sugestii zawierała jawne przyznanie się do naruszenia reguły —
wymagało to kierowania od użytkownika.

Sygnały które były w tekście i powinny były uruchomić analizę compliance:
- "naruszenie reguły Bash" — agent sam to nazwał
- "obejście jednorazowe" — agent przyznał że zrobił źle
- cytat własnej reguły z DEVELOPER.md (#6) z poprawną diagnozą — agent wiedział co powinien był zrobić

Failure mode PE: klasyfikacja po tytule i typie sugestii (tool), pominięcie analizy
zachowania osadzonego w treści. Krok 2 workflow ("Zidentyfikuj typ problemu") nie
był zastosowany do treści sugestii — tylko do jej tematu.

Reguła do wdrożenia w PE workflow: gdy suggestion zawiera self-reported violation
("naruszyłem", "obejście", "błąd") — najpierw zidentyfikuj typ problemu zachowania,
potem oceń czy to zadanie developerskie czy compliance/prompt failure.

#### [69] Konwencja numeracji kroków w workflow i listach
**autor:** prompt_engineer  **status:** open  **data:** 2026-03-18

type: rule
title: Konwencja numeracji kroków w workflow i listach
Kroki workflow numeruj jako: numer fazy + litera kroku (1a, 1b, 2a, 2b...).
Listy niezależne od faz: numeracja prosta (1, 2, 3...).
Dotyczy wszystkich dokumentów workflow i promptów ról.
Wzorzec: bi_view_creation_workflow.md (Faza 0, Faza 1a, Faza 1b...).

#### [64] Jeden błąd tego samego typu = diagnoza zasięgu przed naprawą
**autor:** developer  **status:** open  **data:** 2026-03-17

Gdy wykryty zostaje błąd (np. niepoprawnie zamknięte sugestie) — zanim zaczniesz naprawiać konkretny przypadek, zdiagnozuj czy ten sam błąd nie występuje szerzej (blind spot query: "czy są inne sugestie z tym samym problemem?"). Naprawianie jednej instancji gdy jest ich 10 to strata czasu i ryzyko że problem wróci przez pominięte przypadki.

#### [63] Przed migracją danych — przedstaw plan człowiekowi
**autor:** developer  **status:** open  **data:** 2026-03-17

Każda migracja danych (zmiana statusów, przypisywanie typów, aktualizacja historycznych rekordów) wymaga przedstawienia planu człowiekowi PRZED wykonaniem. Dotyczy zwłaszcza operacji bulk na istniejących danych. Błąd w migracji jest trudniejszy do wykrycia niż błąd w kodzie — i może siedzieć w DB tygodniami.

#### [52] session_init załadował doc roli — przy edycji używaj tej treści, nie Read
**autor:** developer  **status:** open  **data:** 2026-03-17

session_init zwraca pełną treść dokumentu roli w polu doc_content. Gdy w tej samej sesji edytujesz ten plik, masz go już w kontekście — nie czytaj go ponownie przez Read. Podwójne załadowanie = ~300 linii tokenów zmarnowanych.

#### [51] Runner: busy = ochrona budżetu tokenowego, nie "subprocess działa"
**autor:** developer  **status:** open  **data:** 2026-03-17

busy w modelu instancji runnera oznacza że sesja jest w toku i nie można jej zagłuszyć nowym wywołaniem — chodzi o ochronę budżetu tokenowego workflow, nie o to że subprocess "żyje". Ta różnica musi być explicite w dokumentacji roli przy projektowaniu runnerów — agenci budujący kolejne runnery muszą to rozumieć żeby nie mylić stanu procesu ze stanem sesji LLM.

### Narzędzia (tool)

#### [123] Narzędzie do generowania diagramu architektury
**autor:** architect  **status:** open  **data:** 2026-03-21

Podczas discovery ręcznie tworzę diagram ASCII.
Potencjalnie przydatne: narzędzie które skanuje strukturę katalogów
i generuje szkielet diagramu do uzupełnienia.

### Odkrycia (discovery)

#### [144] 13 backlogów zamkniętych w jednej sesji - quick wins effective
**autor:** developer  **status:** open  **data:** 2026-03-22

Sesja 2026-03-22: 13 zadań (niska/średnia wartość, mała praca) zamkniętych w ~3h. Format "małe szybkie cleanup" działa - wysokie tempo, niski context cost, widoczny progress.

#### [139] invocation_log śledzi wywołania agent→agent
**autor:** architect  **status:** open  **data:** 2026-03-22

Tabela do mrowisko_runner — loguje from_role, to_role, depth, turns, cost. 6 rekordów testowych. Będzie kluczowa przy multi-agent.

#### [137] Tabele trace i state są martwe/legacy
**autor:** architect  **status:** open  **data:** 2026-03-22

trace: 0 rekordów, zastąpiona przez tool_calls. state: 34 rekordy, legacy backlog items — dane zmigrowane do backlog/suggestions. Obie do usunięcia przy cleanup.

#### [133] 75k rekordów tool_calls/token_usage — gotowe do analizy
**autor:** architect  **status:** open  **data:** 2026-03-22

tool_calls (30k) i token_usage (44k) to gotowy materiał do analizy zachowania agentów.

Warto zacząć analizować:
- Zużycie tokenów per rola / per sesja
- Wzorce używania narzędzi
- Efektywność cache
- Sesje "drogie" vs "tanie"

Dane są — brakuje dashboardu/raportów.

#### [122] _loom jako seed replikacji
**autor:** architect  **status:** open  **data:** 2026-03-21

Katalog _loom/ zawiera szablony do replikacji Mrowiska w nowych projektach.
To potencjalnie osobny produkt / repo. Nie jest udokumentowany w ARCHITECTURE.md.
Warto rozważyć: wydzielenie _loom do osobnego repo lub lepsze udokumentowanie.

### Obserwacje (observation)

#### [146] Architect pracuje zbyt krótkowzrocznie
**autor:** architect  **status:** open  **data:** 2026-03-22

type: observation
title: Architect pracuje zbyt krótkowzrocznie — proponuje rozwiązania zamiast strategii

Sesja 2026-03-22: Przy analizie gotowości na wieloagentowość Architect:
1. Zaczął proponować konkretne rozwiązania techniczne (pivot na Agent Teams, draft promptu autonomicznego)
2. Wchodził w domenę Prompt Engineera (projektowanie promptu)
3. Nie przedstawił strategicznego planu z priorytetami i trade-offami
4. Nie odniósł się do całości roadmapy (ADR-001, Faza 3, runner) jako systemu zależności

Oczekiwanie użytkownika: plan strategiczny z kolejnością działań, nie implementacja.
Architekt powinien myśleć w horyzoncie miesięcy, nie pojedynczych tasków.

#### [143] Pattern - zrealizowane backlogi nie zamknięte
**autor:** developer  **status:** open  **data:** 2026-03-22

Dwa backlogi (#86 mark-read, #89 conversation_search auto-approve) były już zrealizowane ale pozostały planned. Developer nie zamknął po implementacji. PE może sprawdzić czy workflow Developer ma checkpoint "zweryfikuj czy już done".

#### [142] Rename narzędzia wymaga update settings.local.json
**autor:** developer  **status:** open  **data:** 2026-03-22

Rename conversation_search.py → search_conversation.py wymaga ręcznego update auto-approve w `.claude/settings.local.json`. Można dodać krok w workflow rename: grep settings.local.json dla starej nazwy, przypomnieć o update.

#### [140] Moment strategiczny na refaktor
**autor:** architect  **status:** open  **data:** 2026-03-22

Projekt po stabilizacji promptów, przed skokiem złożoności (multi-agent). Budżet tokenów wykorzystany w 10%. Lepiej przebudować teraz niż po implementacji kolejnej warstwy. ADR-001 to fundament.

#### [138] Bot wymaga hardeningu przed skalowaniem
**autor:** architect  **status:** open  **data:** 2026-03-22

Krytyczny brak: error handling dla Anthropic API. Bot crashuje przy rate limit lub API error. Dodatkowo: God Object w nlp_pipeline.py (218 linii, 7 odpowiedzialności), brak rate limiting per user.

#### [136] Dict-based architecture nie skaluje się
**autor:** architect  **status:** open  **data:** 2026-03-22

Przy rosnącej liczbie agentów i sesji równoległych, podejście proceduralne z dictami staje się nieczytelne i trudne do utrzymania. Logika rozproszona po wielu plikach, brak walidacji typów, brak enkapsulacji. ADR-001 adresuje ten problem.

#### [135] Verification gates — gdzie jeszcze brakuje?
**autor:** prompt_engineer  **status:** open  **data:** 2026-03-22

Verification gates — gdzie jeszcze brakuje?

Backlog #86 pokazał że Developer nie sprawdził "czy już zrobione" przed dodaniem do backlogu.
Fix dodany do developer_workflow.md krok 2a.

Ale to może być szerszy pattern — gdzie jeszcze agent powinien weryfikować przed działaniem?

**Gdzie mamy verification:**
- ✓ Przed edycją pliku chronionego — pytaj użytkownika (CLAUDE.md)
- ✓ Przed commitem — sprawdź git status (developer_workflow.md)
- ✓ Przed dodaniem do backlogu — sprawdź czy istnieje (dodane dziś, 2026-03-22)

**Gdzie brakuje verification:**
- ✗ Przed napisaniem narzędzia — sprawdź czy nie ma podobnego w tools/
- ✗ Przed eskalacją — sprawdź czy to na pewno poza zakresem (może są instrukcje w CLAUDE.md?)
- ✗ Przed wysłaniem wiadomości agent_bus — sprawdź czy odbiorca istnieje
- ✗ Przed uruchomieniem długiego procesu — sprawdź czy są wolne zasoby/kontekst

**Pytanie dla wszystkich ról:**
Przejrzeć workflow i zidentyfikować miejsca gdzie:
1. Agent może zrobić coś co już istnieje (duplikacja)
2. Agent może zrobić coś nieodwracalne (destrukcja)
3. Agent może zmarnować dużo czasu (inefficiency)

→ Dodać verification gate przed tymi akcjami.

**Rekomendacja:**
Może warto systematyczny przegląd wszystkich workflow pod kątem brakujących verification gates?
Albo meta-reguła w CLAUDE.md: "Przed nieodwracalną/kosztowną akcją — sprawdź alternatywy i stan"?

Source: analiza backlog #86, sesja PE 2026-03-22

#### [131] Granica Architect vs Developer rozmyta
**autor:** architect  **status:** open  **data:** 2026-03-21

Prompt Architekta mówi "Architekt projektuje, Developer implementuje". Ale w praktyce obie role dotykają tych samych plików (tools/, documents/). Propozycja doprecyzowania: Architect = cross-cutting concerns (architektura, NFR, wzorce systemowe), Developer = pojedyncze moduły (implementacja feature, fix, narzędzie).

#### [130] _loom wygląda na porzucony
**autor:** architect  **status:** open  **data:** 2026-03-21

Katalog _loom/ ma minimalną zawartość, ostatnia aktualizacja dawno. W obecnej formie to raczej obietnica niż produkt. Propozycja: albo rozwijamy (dodajemy brakujące szablony, testujemy bootstrap), albo usuwamy/archiwizujemy do czasu gdy będzie priorytetem.

#### [129] Nazewnictwo narzędzi — brak konwencji
**autor:** architect  **status:** open  **data:** 2026-03-21

Widzę: `docs_search` vs `search_bi`, `solutions_save` vs `save_solution`. Prefix (docs_) vs suffix (_search). Przy ~50 skryptach utrudnia nawigację i zapamiętywanie. Propozycja: ustalić konwencję (np. zawsze `<domena>_<akcja>.py`) i zrefaktorować nazwy.

#### [128] tmp/ jako de facto inbox człowieka
**autor:** architect  **status:** open  **data:** 2026-03-21

W tmp/ jest ~40 plików: handoffy, logi, sugestie, eksporty. To tam ląduje wszystko co człowiek powinien przejrzeć. Ale nazwa "tmp" sugeruje "tymczasowe, do usunięcia". Propozycja: przenieść do `inbox/` lub `human/` z lepszą strukturą (podkatalogi per typ: reviews/, exports/, handoffs/).

#### [127] mrowisko.db — podwójna odpowiedzialność
**autor:** architect  **status:** open  **data:** 2026-03-21

Baza trzyma zarówno komunikację agentów (messages, backlog, suggestions) jak i historię sesji Claude Code (conversation, tool_calls, token_usage). To dwa różne concerns w jednym pliku. Przy synchronizacji (#90) może to komplikować — historia sesji jest per-maszyna, komunikacja powinna być shared. Rozważyć podział na dwie bazy lub wyraźną separację tabel.

#### [126] Code maturity levels — wzorzec referencyjny dla oceny jakości kodu
**autor:** prompt_engineer  **status:** open  **data:** 2026-03-21

Code maturity levels (junior/mid/senior) — wzorzec dla code review w systemie.

Wprowadzone w ARCHITECT.md:
- Tabela 8 wymiarów: Funkcje, Naming, Abstrakcja, Error handling, Edge cases, Tests, Dependencies, Structure
- Konkretne kryteria per poziom (junior/mid/senior)
- Wymóg w code review: ogólny poziom + uzasadnienie (2-3 zdania z przykładami)

Potencjalne zastosowania:
1. Code review przez Architekta (główne)
2. Self-assessment Developera przed przekazaniem kodu do review (opcjonalne)
3. Onboarding nowych agentów / ról które piszą kod (benchmark jakości)
4. Ocena postępu projektu (ile kodu na poziomie senior vs mid vs junior)

Obserwacja:
Ten wzorzec może być użyteczny nie tylko dla Architekta — może być referencją dla wszystkich ról które oceniają jakość kodu (PE przy ocenie narzędzi, Metodolog przy ocenie metody pracy).

Nie wymaga akcji teraz — obserwacja do rozważenia w przyszłości jeśli role zaczną potrzebować wspólnego języka do oceny dojrzałości kodu.

#### [121] Istniejący ARCHITECTURE.md w documents/dev/
**autor:** architect  **status:** open  **data:** 2026-03-21

documents/dev/ARCHITECTURE.md opisuje szczegółowo Agent ERP i Bot (Faza 1-2).
Brakuje opisu systemu wieloagentowego na wyższym poziomie.
Utworzono documents/architect/SYSTEM_ARCHITECTURE.md jako dokument nadrzędny.
Rozważyć: czy documents/dev/ARCHITECTURE.md powinien być podzbiorem lub linkowany?

#### [109] bot eval (id=84) krytyczny przed kolejną rundą zmian promptu
**autor:** developer  **status:** open  **data:** 2026-03-20

Bez automatycznych testów każda zmiana PE to loteria — widać to po Typ_Dok i akronimach.
Eval powinien być zrobiony przed następną sesją zmian promptu, nie po.

#### [105] MagElem — duplikat aliasu Kod_Towaru — planowanie dwóch źródeł dla jednej kolumny
**autor:** analyst  **status:** open  **data:** 2026-03-20

ERP Specialist umieścił dwa wiersze Uwzglednic=Tak z aliasem Kod_Towaru: jeden z JOINu TwrKarty, drugi z MaE_TwrKod inline. Symptom niejednoznacznej decyzji projektowej (historyczny vs aktualny kod). Wzorzec z TraElem (inline, historyczny) powinien być domyślną zasadą dla tabel pozycji dokumentów.

#### [104] Faza 3 — ERP Specialist domyślnie wysyła self-check, nie pełne bi_verify
**autor:** analyst  **status:** open  **data:** 2026-03-20

W MagNag Faza 3 ERP Specialist wysłał self-check bez pełnych statystyk bi_verify (distinct/null per kolumna). Analityk musiał dopiero poprosić. Warto ustandaryzować: Faza 3 = bi_verify output obowiązkowy w wiadomości do Analityka, nie opcjonalny.

#### [101] ERP Specialist używa Komentarz_Analityka jako listy TODO — nie jako gotowego planu
**autor:** analyst  **status:** open  **data:** 2026-03-20

W MagNag iteracja 1 ERP Specialist wysłał plan z kolumnami opisowymi FK odnotowanymi w Komentarz_Analityka ("Dodać Kod_Magazynu..."), ale nie dodał ich do planu jako wierszy Tak. Spowodowało to 10 BLOCKINGów i 3 iteracje. Wzorzec powtarza się. Checklist Fazy 1a powinna jawnie mówić: "Każde ID_XXX musi mieć wiersz z kolumną opisową w planie przed wysłaniem do Analityka — nie notatkę w komentarzu."

#### [98] Inbox i workflow konsumuja nadmiernie kontekst — 3 kierunki optymalizacji
**autor:** erp_specialist  **status:** open  **data:** 2026-03-20

Inbox konsumuje nadmiernie kontekst przy każdym sprawdzeniu. W sesji 2026-03-20 inbox był sprawdzany 3 razy, za każdym razem zwracając 10-14 wiadomości (w tym historyczne z TraElem/ZamElem sprzed tygodnia) — łącznie ~45k znaków na historię której agent nie potrzebuje.

Trzy kierunki do rozważenia:

1. agent_bus_cli.py inbox — dodaj flagę --unread (tylko nieprzeczytane) lub --since <data>. Agent markuje wiadomości jako przeczytane po starcie sesji.

2. Workflow bi_view_creation_workflow.md mówi "agent dostaje tylko sekcję swojej bieżącej fazy" — w praktyce agenci wczytują cały dokument (~520 linii). Warto albo podzielić plik na osobne pliki per faza, albo dodać anchor do ładowania fragmentu.

3. Read zamiast Grep przy szukaniu jednego wiersza w dużym pliku — drobna ale powtarzalna strata.

#### [62] Handoff ERP→Analityk — Analityk nie ładuje doc workflow poprzednika automatycznie
**autor:** analyst  **status:** open  **data:** 2026-03-17

Przy przejściu ERP Specialist → Analityk, Analityk nie ma obowiązku zapoznania się z dokumentami workflow poprzedniej roli. Konieczna była ręczna korekta (dodanie kroku 2c do ANALYST.md).
Opcje: (1) Prompt Engineer zarządzający zestawem doc per rola i zadanie, (2) dynamiczne prompty z bazy per kontekst, (3) konwencja handoff — wiadomość agent_bus zawiera listę plików workflow do załadowania.
Decyzja należy do Metodologa.

#### [53] Logowanie per etap — brakuje przypomnienia w workflow gates ról
**autor:** developer  **status:** open  **data:** 2026-03-17

Reguła logowania per etap/workflow/sesja jest w CLAUDE.md, ale dokumenty ról (ERP_SPECIALIST.md, ANALYST.md) nie mają jej wbudowanej w bramki workflow. Agenci pomijają logowanie bo workflow gate nie przypomina o nim jawnie. Decyzja należy do Developera czy wdrożyć per-rola.
