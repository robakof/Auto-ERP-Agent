# Suggestions — 2026-03-22

*69 sugestii*

---

## Zasady (rule)

| id  | autor           | tytuł                                                                                    | status | data       |
| --- | --------------- | ---------------------------------------------------------------------------------------- | ------ | ---------- |
| 195 | developer       | Adapter layer importuje core/ - to jest OK ale dokumentuj dependency                     | open   | 2026-03-22 |
| 193 | developer       | Status mapping backward compatibility - centralna dokumentacja                           | open   | 2026-03-22 |
| 189 | architect       | CLI fallback to architectural requirement, nie "nice to have" — headless = core use case | open   | 2026-03-22 |
| 187 | architect       | Hybryda (wtyczka + CLI) to optimal solution — nie wybieraj "albo-albo" gdy możesz "oba"  | open   | 2026-03-22 |
| 184 | developer       | Wszystkie analizy/plany/raporty do pliku md nie inline w czacie                          | open   | 2026-03-22 |
| 183 | developer       | Handoff między rolami musi być explicite z pełnym briefem                                | open   | 2026-03-22 |
| 177 | architect       | Code review feedback loop działa — Developer responds well to structured critique        | open   | 2026-03-22 |
| 172 | developer       | TDD dla Repository implementations — testy przed kodem                                   | open   | 2026-03-22 |
| 169 | architect       | Nowy kod w core/, stary w tools/ przez adaptery                                          | open   | 2026-03-22 |
| 161 | developer       | Onboarding gap — gdzie pracować jako non-developer współpracownik?                       | open   | 2026-03-22 |
| 158 | developer       | Narzędzia pomocnicze: maintain actively or delete                                        | open   | 2026-03-22 |
| 141 | architect       | Nowy kod w core/, stary w tools/ przez adaptery                                          | open   | 2026-03-22 |
| 132 | architect       | Audyt Fazy 1-4: findings do wdrożenia                                                    | open   | 2026-03-22 |
| 120 | architect       | Workflow Architecture Discovery — kroki                                                  | open   | 2026-03-21 |
| 95  | erp_specialist  | Nr_Dokumentu_Zrodlowego — złożony JOIN gdy ZrdTyp ma wiele typów                         | open   | 2026-03-20 |
| 83  | prompt_engineer | PE: suggestion z self-reported violation = analiza compliance, nie tool request          | open   | 2026-03-18 |
| 69  | prompt_engineer | Konwencja numeracji kroków w workflow i listach                                          | open   | 2026-03-18 |
| 64  | developer       | Jeden błąd tego samego typu = diagnoza zasięgu przed naprawą                             | open   | 2026-03-17 |
| 63  | developer       | Przed migracją danych — przedstaw plan człowiekowi                                       | open   | 2026-03-17 |
| 51  | developer       | Runner: busy = ochrona budżetu tokenowego, nie "subprocess działa"                       | open   | 2026-03-17 |

## Narzędzia (tool)

| id  | autor           | tytuł                                                   | status | data       |
| --- | --------------- | ------------------------------------------------------- | ------ | ---------- |
| 192 | developer       | Quick inbox check - czy są nowe wiadomości              | open   | 2026-03-22 |
| 170 | developer       | Pre-commit hook sprawdzający branch przed dużą zmianą   | open   | 2026-03-22 |
| 163 | prompt_engineer | render.py suggestions — brakuje filtra po roli/obszarze | open   | 2026-03-22 |
| 123 | architect       | Narzędzie do generowania diagramu architektury          | open   | 2026-03-21 |

## Odkrycia (discovery)

| id | autor | tytuł | status | data |
|----|-------|-------|--------|------|
| 196 | developer | recipients w Suggestion było missing field | open | 2026-03-22 |
| 191 | developer | Inbox realtime - wiadomość przyszła podczas sesji | open | 2026-03-22 |
| 190 | architect | Interim solution OK jeśli clear path do final solution — wtyczka (interim) + CLI (final) validated | open | 2026-03-22 |
| 181 | developer | VS Code Terminal API daje interaktywność za darmo | open | 2026-03-22 |
| 178 | architect | Repository pattern eliminuje 90% copy-paste — _find_by() jako proof | open | 2026-03-22 |
| 173 | developer | pyproject.toml konieczne dla pytest imports w modułach | open | 2026-03-22 |
| 167 | architect | invocation_log śledzi wywołania agent→agent | open | 2026-03-22 |
| 165 | architect | Tabele trace i state są martwe/legacy | open | 2026-03-22 |
| 137 | architect | Tabele trace i state są martwe/legacy | open | 2026-03-22 |
| 133 | architect | 75k rekordów tool_calls/token_usage — gotowe do analizy | open | 2026-03-22 |
| 122 | architect | _loom jako seed replikacji | open | 2026-03-21 |

## Obserwacje (observation)

| id | autor | tytuł | status | data |
|----|-------|-------|--------|------|
| 197 | developer | Context manager pattern drastycznie redukuje boilerplate | open | 2026-03-22 |
| 194 | developer | 19 failed testów test_agent_bus.py - do naprawienia w Phase 2-4 | open | 2026-03-22 |
| 188 | architect | STRATEGIC_PLAN Wariant C delivered — równoległe ścieżki works at scale | open | 2026-03-22 |
| 186 | architect | Developer wykonał Senior-level research (E1-E4) — systematyczny i z trade-offami | open | 2026-03-22 |
| 185 | developer | Minor issues nie powinny blokować decyzji architektonicznej | open | 2026-03-22 |
| 182 | developer | Interaktywność human-agent to core feature nie nice-to-have | open | 2026-03-22 |
| 180 | developer | Eksperymentowanie przed decyzją architektoniczną = ROI | open | 2026-03-22 |
| 179 | architect | Context manager eliminuje 160 linii boilerplate — concrete cost/benefit | open | 2026-03-22 |
| 176 | architect | Developer osiągnął Senior-level w M2 — świetna inicjatywa i commitment | open | 2026-03-22 |
| 175 | developer | Typ wiadomości review w agent_bus | open | 2026-03-22 |
| 174 | developer | Repository pattern — separacja działa zgodnie z ADR-001 | open | 2026-03-22 |
| 171 | developer | Context management przy długich sesjach (5h, 88% kontekstu) | open | 2026-03-22 |
| 168 | architect | Moment strategiczny na refaktor | open | 2026-03-22 |
| 166 | architect | Bot wymaga hardeningu przed skalowaniem | open | 2026-03-22 |
| 164 | architect | Dict-based architecture nie skaluje się | open | 2026-03-22 |
| 162 | developer | Verification gates nie działają bez enforcement — backlog #104 był już done | open | 2026-03-22 |
| 155 | prompt_engineer | Inbox rośnie szybciej niż przetwarzamy | open | 2026-03-22 |
| 153 | prompt_engineer | Persona Architekta — 2 iteracje, wciąż nie działa | open | 2026-03-22 |
| 151 | developer | Backlog items mogą być przestarzałe — lifecycle problem | open | 2026-03-22 |
| 138 | architect | Bot wymaga hardeningu przed skalowaniem | open | 2026-03-22 |
| 135 | prompt_engineer | Verification gates — gdzie jeszcze brakuje? | open | 2026-03-22 |
| 131 | architect | Granica Architect vs Developer rozmyta | open | 2026-03-21 |
| 130 | architect | _loom wygląda na porzucony | open | 2026-03-21 |
| 129 | architect | Nazewnictwo narzędzi — brak konwencji | open | 2026-03-21 |
| 128 | architect | tmp/ jako de facto inbox człowieka | open | 2026-03-21 |
| 127 | architect | mrowisko.db — podwójna odpowiedzialność | open | 2026-03-21 |
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

#### [195] Adapter layer importuje core/ - to jest OK ale dokumentuj dependency
**autor:** developer  **status:** open  **data:** 2026-03-22

AgentBus (tools/lib/agent_bus.py) teraz importuje:
```python
from core.repositories.suggestion_repo import SuggestionRepository
from core.entities.messaging import Suggestion, SuggestionType
```

To tworzy dependency: tools/ → core/. Jest to zgodne z adapter pattern (adapter layer zależy od domain layer). Ale warto dokumentować w ARCHITECTURE.md żeby było jasne że to celowa decyzja, nie circular dependency.

#### [193] Status mapping backward compatibility - centralna dokumentacja
**autor:** developer  **status:** open  **data:** 2026-03-22

Adapter M3 Phase 1 mapuje "in_backlog" → "implemented" dla backward compatibility. To powinno być dokumentowane w jednym miejscu (np. agent_bus.py header comment lub osobny plik mappings.py), nie zagrzebane w kodzie. Mogą być inne legacy mappings w Backlog/Message które trzeba będzie obsłużyć w Phase 2-3.

#### [189] CLI fallback to architectural requirement, nie "nice to have" — headless = core use case
**autor:** architect  **status:** open  **data:** 2026-03-22

**Context:**
Wtyczka VS Code ma fundamentalny blocker: **nie działa headless** (wymaga VS Code running).

**Headless environments to core use case dla Horyzont 3:**
- **CI/CD pipelines:** automatyczne testy agentów (np. pytest na repo przed merge)
- **Cron jobs:** scheduled agent tasks (np. "co tydzień audit backlogu przez Analityka")
- **Remote servers:** bez GUI (np. cloud VM running agents 24/7)
- **Replikacja mrowiska:** nowe projekty bez VS Code (użytkownik preferuje Vim/Emacs/CLI-only)

**Impact analysis:**
Jeśli CLI fallback = optional:
- Horyzont 3 (produktyzacja) **zablokowany** — nie można wdrożyć bez headless support
- Replikacja mrowiska **niemożliwa** dla CLI-only users
- Multi-machine sync **ograniczona** (wymaga VS Code na obu maszynach)

Jeśli CLI fallback = obowiązkowy:
- Horyzont 3 możliwy ✓
- Replikacja uniwersalna ✓
- Hybryda (wtyczka dla dev, CLI dla prod) = optymalne rozwiązanie ✓

**Verdict:**
CLI fallback to **architectural requirement**, nie "nice to have".
Must be on roadmap Fazy 4 z **HIGH priority** (równy z multi-agent orchestration).

**Rekomendacja:**
Traktuj CLI fallback jako blocker dla Horyzont 3. Nie ship Faza 4 bez CLI fallback.

#### [187] Hybryda (wtyczka + CLI) to optimal solution — nie wybieraj "albo-albo" gdy możesz "oba"
**autor:** architect  **status:** open  **data:** 2026-03-22

**Realization:**
Wtyczka VS Code **nie zastąpi** CLI subprocess — to komplementarne tools dla różnych use cases:
- **Dev use case:** human-in-the-loop, debugging, multi-agent view → wtyczka wygrywa (interaktywność, widoczność)
- **Production use case:** headless, CI/CD, cron, remote → CLI wygrywa (standalone, no IDE dependency)

Nie trzeba wybierać "albo wtyczka albo CLI" — **oba** w hybrydzie:
- Wtyczka dla Horyzont 1-2 (dev, interim solution)
- CLI fallback dla Horyzont 3 (production, headless, final solution)

**Pattern:**
Często najlepszym rozwiązaniem nie jest "wybierz A lub B", ale "A dla use case X, B dla use case Y".
Pytanie nie "która opcja?", ale "który use case dominuje teraz, który później?".

**Przykłady w projekcie:**
- CLAUDE.md: struktura EN + treść PL (hybryda, nie "albo EN albo PL")
- Prompty: XML tags EN + instrukcje PL (hybryda)
- Runner: wtyczka (dev) + CLI (production) (hybryda)

**Rekomendacja:**
Podejście hybrydowe to wzorzec do rozważenia w innych decyzjach architektonicznych. Nie szukaj "one size fits all" — buduj "right tool for the job".

#### [184] Wszystkie analizy/plany/raporty do pliku md nie inline w czacie
**autor:** developer  **status:** open  **data:** 2026-03-22

Obserwacja: Wszystkie raporty (E1-E4, summary) w plikach .md, nie inline w czacie.

Powód:
- Plik przetrwa kompresję kontekstu
- Można linkować (ścieżka w wiadomości)
- Można wersjonować (git)
- Można czytać poza sesją (markdown reader, IDE)

Inline w czacie:
- Zniknie przy kompresji
- Ciężko zlinkować
- Nie ma poza sesją

Reguła: Wszystkie analizy/plany/raporty → plik .md w documents/human. Inline w czacie = tylko TL;DR + link do pliku.

#### [183] Handoff między rolami musi być explicite z pełnym briefem
**autor:** developer  **status:** open  **data:** 2026-03-22

Good example (ta sesja):
- Developer → PE: message id=188 z pełnym kontekstem (problem, rozwiązanie, output contract)
- Developer → Architect: message id=194 z lokalizacjami raportów, pytaniami, oczekiwaniami

Bad example (ryzyko):
- "PE, zobacz suggestions" ← implicit (nie wiadomo co zrobić, brak kontekstu)

Reguła: Handoff = pełny brief. Nie zakładaj że druga rola "wie co zrobić". Explicite:
1. Problem/kontekst
2. Co zrobiłem
3. Co potrzebuję od Ciebie
4. Gdzie szukać dokumentów

#### [177] Code review feedback loop działa — Developer responds well to structured critique
**autor:** architect  **status:** open  **data:** 2026-03-22

**Obserwacja:**
Code review #191 miał 4 warnings + 3 suggestions.
Developer zaimplementował wszystkie warnings i 2/3 suggestions przed przejściem do M2 part 2.

**Pattern:**
- Structured critique (severity levels: Critical/Warning/Suggestion) → clear priorities
- Timing recommendations ("fix now" vs "fix after M3") → Developer wie co robić kiedy
- Trade-off analysis w review → Developer rozumie *dlaczego* coś jest problem

**Contrast z innymi projektami:**
W wielu projektach code review to "lista rzeczy do poprawy" bez priorytetów → Developer nie wie co jest critical.
Tutaj: severity levels + timing + trade-offs → Developer wie dokładnie co robić.

**Rekomendacja:**
Kontynuuj ten format code review. Działa.

#### [172] TDD dla Repository implementations — testy przed kodem
**autor:** developer  **status:** open  **data:** 2026-03-22

**Problem:** Nie zastosowałem TDD mimo planu. Napisałem kod, potem testy.

**Propozycja:** Dla M2 part 2 (BacklogRepository, MessageRepository) spróbować:
1. Napisać testy najpierw (expected behavior)
2. Implementować repository żeby testy przeszły
3. Refactor

**Uzasadnienie:** Repository ma klarowny interface (CRUD), idealny case dla TDD.

**Warto eksperyment:** 1 repo TDD, 1 kod-first, porównać czas i jakość.

#### [169] Nowy kod w core/, stary w tools/ przez adaptery
**autor:** architect  **status:** open  **data:** 2026-03-22

Strategia migracji: nowe klasy domenowe w core/, stary kod tools/ deleguje przez adaptery. Zachowujemy kompatybilność wsteczną (CLI działa bez zmian). Stopniowa migracja, nie big bang.

#### [161] Onboarding gap — gdzie pracować jako non-developer współpracownik?
**autor:** developer  **status:** open  **data:** 2026-03-22

Arek tworzył pliki w rootcie bo nie miał guidance gdzie pracować.

**Problem:** Dokumentacja zakłada że user = developer lub agent. Nie ma instrukcji dla współpracowników (nie-developerzy, nie-agenci) gdzie tworzyć swoje pliki robocze.

**Rozwiązania:**

**Opcja A:** documents/human/ar/README.md
```markdown
# Pliki robocze Arka

Ten folder to Twoja przestrzeń robocza:
- wyceny/ — pliki wycen klientów
- dokumenty/ — dokumenty Word, mapowania, ikony
- xlsx/ — pliki Excel robocze
- skrypty/ — skrypty .bat do szybkiego uruchamiania narzędzi

Pliki tu są tracked w git i synchronizowane między maszynami.
```

**Opcja B:** CLAUDE.md sekcja dla współpracowników
```markdown
## Dla współpracowników (nie-agenci)

Twoje pliki robocze należą do `documents/human/<twoje_imię>/`:
- Wyceny, dokumenty, Excel → tu
- Skrypty pomocnicze → tu
- NIE do roota projektu (root tylko dla konfiguracji)
```

**Opcja C:** Narzędzie onboardingowe
```bash
python tools/setup_human_workspace.py --name arek
# Tworzy documents/human/arek/ + README.md
```

**Rekomendacja:** A (README.md) teraz, B (CLAUDE.md) jeśli więcej osób dołączy.

#### [158] Narzędzia pomocnicze: maintain actively or delete
**autor:** developer  **status:** open  **data:** 2026-03-22

verify.py pokazuje koszt porzuconych narzędzi — działało, ale straciło aktualność przy refaktorze nazw (search_docs → docs_search).

**Problem:** Narzędzia pomocnicze (verify, setup_machine) w limbo:
- Nie są usuwane (ktoś kiedyś używał)
- Nie są utrzymywane (nazwy się zmieniają, narzędzia przestają działać)
- Result: technical debt + mylące nowych użytkowników

**Zasada:**
Każde narzędzie onboardingowe/pomocnicze ma status:
- **Active:** utrzymywane przy refaktorach, testy, dokumentowane
- **Deprecated:** jawnie oznaczone jako przestarzałe, termin usunięcia
- **Deleted:** usunięte z repo

Nie ma statusu "istnieje ale nie działa".

**Akcja:**
- verify.py → Active (naprawione, przeniesione do tools/)
- Przejrzeć inne narzędzia pomocnicze (setup_machine.py, etc.)

#### [141] Nowy kod w core/, stary w tools/ przez adaptery
**autor:** architect  **status:** open  **data:** 2026-03-22

Strategia migracji: nowe klasy domenowe w core/, stary kod tools/ deleguje przez adaptery. Zachowujemy kompatybilność wsteczną (CLI działa bez zmian). Stopniowa migracja, nie big bang.

#### [132] Audyt Fazy 1-4: findings do wdrożenia
**autor:** architect  **status:** open  **data:** 2026-03-22

Audyt architektoniczny (Fazy 1-4) — główne findings do wdrożenia:

1. **CRITICAL:** bot/pipeline/nlp_pipeline.py — brak obsługi wyjątków Anthropic API (RateLimitError, APIError)
2. **HIGH:** mrowisko.db — cleanup policy dla tool_calls (30k) i token_usage (44k)
3. **MEDIUM:** Usunąć martwą tabelę `trace`, deprecate `state`
4. **MEDIUM:** Rozbić nlp_pipeline.py (218 linii) na mniejsze komponenty
5. **LOW:** Rename search_bi.py → bi_search.py dla spójności nazewnictwa

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

#### [51] Runner: busy = ochrona budżetu tokenowego, nie "subprocess działa"
**autor:** developer  **status:** open  **data:** 2026-03-17

busy w modelu instancji runnera oznacza że sesja jest w toku i nie można jej zagłuszyć nowym wywołaniem — chodzi o ochronę budżetu tokenowego workflow, nie o to że subprocess "żyje". Ta różnica musi być explicite w dokumentacji roli przy projektowaniu runnerów — agenci budujący kolejne runnery muszą to rozumieć żeby nie mylić stanu procesu ze stanem sesji LLM.

### Narzędzia (tool)

#### [192] Quick inbox check - czy są nowe wiadomości
**autor:** developer  **status:** open  **data:** 2026-03-22

Narzędzie CLI do szybkiego sprawdzenia czy inbox ma nowe wiadomości (count only, bez full read):
```
python tools/agent_bus_cli.py inbox-count --role developer
→ {"ok": true, "count": 2}
```
Użycie: na początku sesji + okresowo podczas długich tasków. Unika false assumption "inbox jest pusty".

#### [170] Pre-commit hook sprawdzający branch przed dużą zmianą
**autor:** developer  **status:** open  **data:** 2026-03-22

**Problem:** Dwukrotnie w tej sesji przypadkowo zacząłem pracę na złym branchu (main zamiast feature). Strata czasu na recovery.

**Propozycja:** Pre-commit hook lub reminder w workflow:
- Sprawdza `git branch --show-current` przed utworzeniem nowych plików
- Jeśli branch = main && tworzysz nowy moduł (core/, nowy folder) → warning
- Alternatywa: dodać do DEVELOPER.md workflow checkpoint: "Sprawdź branch przed rozpoczęciem implementacji"

**Zysk:** Uniknięcie 15-30 min straconego czasu per sesja na recovery

#### [163] render.py suggestions — brakuje filtra po roli/obszarze
**autor:** prompt_engineer  **status:** open  **data:** 2026-03-22

type: tool
title: render.py suggestions — brakuje filtra po roli/obszarze

## Problem

`render.py suggestions` i `agent_bus_cli.py suggestions` nie mają filtra po roli docelowej lub obszarze.

Gdy PE przegląda sugestie, dostaje wszystkie 42 (open), z których tylko ~14 dotyczy jego pracy.
Musi ręcznie przeskanować całość i wyłowić relevantne.

## Obecne filtry

agent_bus_cli.py suggestions:
- --status (open/in_backlog/rejected/implemented)
- --from (author)
- --type (rule/tool/discovery/observation)

Brakuje:
- --for-role 
- --area < (analogicznie do backlog --area)

## Propozycja

**Opcja A:** Dodać pole `relevant_for` do tabeli suggestions
```sql
ALTER TABLE suggestions ADD COLUMN relevant_for TEXT; -- JSON array: ["prompt_engineer", "developer"]
```

CLI:
```bash
agent_bus_cli.py suggestions --status open --for-role prompt_engineer
render.py suggestions --format md --for-role prompt_engineer
```

**Opcja B:** Mapping sugestii do obszarów (jak backlog)
```bash
agent_bus_cli.py suggestions --status open --area Prompt
```

**Opcja C:** Heurystyka w render.py
```python
# Jeśli suggestion.type == "rule" i treść zawiera "workflow", "prompt", "PE" → area=Prompt
# Jeśli treść zawiera "ERP", "bi_view" → area=ERP
```

## Rekomendacja

**Opcja A** (explicit field) — najprostsze, deterministyczne.

Author oznacza przy tworzeniu sugestii kogo to dotyczy:
```bash
agent_bus_cli.py suggest --from developer --type rule --relevant-for prompt_engineer,developer --content-file tmp/s.md
```

Jeśli nie podano `--relevant-for` → domyślnie "all" (wyświetla się wszystkim).

#### [123] Narzędzie do generowania diagramu architektury
**autor:** architect  **status:** open  **data:** 2026-03-21

Podczas discovery ręcznie tworzę diagram ASCII.
Potencjalnie przydatne: narzędzie które skanuje strukturę katalogów
i generuje szkielet diagramu do uzupełnienia.

### Odkrycia (discovery)

#### [196] recipients w Suggestion było missing field
**autor:** developer  **status:** open  **data:** 2026-03-22

Stary agent_bus.py serializował recipients do JSON w kolumnie suggestions.recipients, ale nowy Suggestion entity nie miał tego pola. Dodałem recipients: Optional[List[str]] = None + JSON serialization w repository. Gdybyśmy tego nie zrobili teraz, trzeba by migracji danych (wszystkie suggestions z recipients=NULL). Dobrze że złapałem to w Phase 1.

#### [191] Inbox realtime - wiadomość przyszła podczas sesji
**autor:** developer  **status:** open  **data:** 2026-03-22

Na początku sesji inbox był pusty. Architekt wysłał msg #191 o 17:23:47 PODCZAS mojej sesji. Nie sprawdziłem inbox ponownie - zakładałem że jest pusty. Dopiero gdy user powiedział "masz wiadomość od Architekta" zacząłem ręcznie sprawdzać (przez SQLite queries zamiast narzędzia). System działa async/realtime - inbox może się zmienić w trakcie sesji.

#### [190] Interim solution OK jeśli clear path do final solution — wtyczka (interim) + CLI (final) validated
**autor:** architect  **status:** open  **data:** 2026-03-22

**Pattern observed:**
Wtyczka VS Code to **interim solution** (działa dla dev use case, nie dla wszystkich use cases).
Architect zaakceptował to z warunkiem **CLI fallback w Fazie 4**.

**Dlaczego to działa:**
1. **Clear path do final solution:** CLI fallback na roadmap (Faza 4, obowiązkowy)
2. **Interim delivers value:** wtyczka rozwiązuje immediate problem (runner wieloagentowy dla dev)
3. **Incremental delivery:** ship wtyczkę teraz (Faza 2-3), CLI później (Faza 4)
4. **Risk mitigation:** jeśli wtyczka za złożona / nie działa → fallback do CLI

**Contrast z anti-pattern:**
- **Bad:** Ship interim solution bez planu na final → technical debt accumulates, blocker later
- **Good:** Ship interim solution z clear path → incremental value, controlled tech debt

**Przykłady w projekcie:**
- Wtyczka (interim, dev use case) + CLI fallback (final, universal) ✓
- Dict-based agent_bus (interim) + Domain Model (final, ADR-001) ✓
- Prompty w .md (interim) + prompty w DB (final, Faza 3 deferred) ⚠ (brak clear timeline)

**Rekomendacja:**
Interim solution jest akceptowalna architektonicznie **jeśli:**
1. Clear path do final solution (roadmap, timeline, commitment)
2. Interim delivers value (rozwiązuje immediate problem)
3. Risk mitigation (fallback jeśli interim fails)

Jeśli brakuje któregokolwiek z tych 3 — interim solution = tech debt trap. Refuse.

#### [181] VS Code Terminal API daje interaktywność za darmo
**autor:** developer  **status:** open  **data:** 2026-03-22

`vscode.window.createTerminal()` + `terminal.sendText('claude.cmd ...')` automatycznie obsługuje:
- User input (pisanie w terminalu)
- Przekazywanie do procesu
- Wyświetlanie output

Nie trzeba custom input/output handling, parsowania stdout/stderr, przekierowywania stdin, custom rendering.

Implikacja: Interaktywność "za darmo" — największa korzyść wtyczki vs CLI subprocess. Human może dołączyć do sesji spawned agenta bez dodatkowej implementacji.

Game changer dla user experience.

#### [178] Repository pattern eliminuje 90% copy-paste — _find_by() jako proof
**autor:** architect  **status:** open  **data:** 2026-03-22

**Przed:** find_by_status, find_by_author, find_by_type — każda ~20 linii, 90% identyczne
**Łącznie:** ~70 linii copy-paste per repository × 3 repositories = ~210 linii

**Po:** _find_by(field, value) helper — 15 linii
**find_by_* methods:** po 1 linii każda (delegate do _find_by)
**Łącznie:** ~30 linii per repository × 3 = ~90 linii

**Redukcja:** 210 → 90 linii (58% mniej kodu)

**Benefits:**
- Jeśli trzeba dodać nową query method (np. find_by_priority) → 1 linia zamiast 20
- Jeśli trzeba zmienić ORDER BY → jedno miejsce zamiast 9 (3 methods × 3 repos)
- Testy pokrywają _find_by() raz, zamiast testować każdą find_by_* osobno

**Pattern:**
Generic helpers (z f-string dla field name) eliminują copy-paste bez over-engineering.
To jest sweet spot między "copy-paste everything" a "abstract everything".

**Rekomendacja:**
Szukaj podobnych patterns w innych częściach kodu (tools/lib/, bot/pipeline/).

#### [173] pyproject.toml konieczne dla pytest imports w modułach
**autor:** developer  **status:** open  **data:** 2026-03-22

**Odkrycie:** pytest nie widzi modułów bez pyproject.toml + pip install -e .

**Problem:** sys.path insert w conftest.py nie wystarczy.

**Rozwiązanie:** Minimalne pyproject.toml:
```toml
[project]
name = "nazwa"
version = "0.1.0"

[tool.setuptools.packages.find]
include = ["module*"]
```

**Implikacja:** Każdy nowy moduł Pythonowy w projekcie wymaga dodania do pyproject.toml.

#### [167] invocation_log śledzi wywołania agent→agent
**autor:** architect  **status:** open  **data:** 2026-03-22

Tabela do mrowisko_runner — loguje from_role, to_role, depth, turns, cost. 6 rekordów testowych. Będzie kluczowa przy multi-agent.

#### [165] Tabele trace i state są martwe/legacy
**autor:** architect  **status:** open  **data:** 2026-03-22

trace: 0 rekordów, zastąpiona przez tool_calls. state: 34 rekordy, legacy backlog items — dane zmigrowane do backlog/suggestions. Obie do usunięcia przy cleanup.

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

#### [197] Context manager pattern drastycznie redukuje boilerplate
**autor:** developer  **status:** open  **data:** 2026-03-22

Przed context manager: ~16 linii boilerplate per metoda (conn = ..., try, finally, close).
Po context manager: ~3 linie (with self._connection() as conn).

Redukcja ~70% boilerplate + automatic error handling + transaction safety.

Ten wzorzec warto promować dla innych modułów w projekcie (np. tools/ które używają SQLite - bi_discovery.py, data_quality_*.py, etc.). Może być podstawą do "best practices" dokumentu.

#### [194] 19 failed testów test_agent_bus.py - do naprawienia w Phase 2-4
**autor:** developer  **status:** open  **data:** 2026-03-22

test_agent_bus.py: 47 pass, 19 failed. Failures:
- TestState (6 testów) - write_state/get_state używa starego kodu
- TestBacklog.test_backlog_with_source_id (1 test) - prawdopodobnie schema mismatch
- TestTransactions (2 testy) - transaction context manager + adapter conflict

Te testy trzeba będzie naprawić/zaadaptować gdy będziemy robić Phase 2 (Backlog) i Phase 4 (State). Nie są blokerem dla M3 Phase 1 - Suggestions działają.

#### [188] STRATEGIC_PLAN Wariant C delivered — równoległe ścieżki works at scale
**autor:** architect  **status:** open  **data:** 2026-03-22

**Evidence:**
Wariant C (równoległe ścieżki):
```
Ścieżka 1: Eksperymenty (E1-E4) → Decyzja → Runner v2
Ścieżka 2: Porządki (ADR-001 M1-M2) → M3 AgentBus adapter
```

**Status:**
- Ścieżka 1: ✓ E1-E4 zakończone (4 eksperymenty, ~3 sesje)
- Ścieżka 2: ✓ ADR-001 M1-M2 zakończone (61/61 tests pass, ~2 sesje)
- Równoległe ścieżki **nie zablokowały się nawzajem**
- Timeline: ~1 tydzień (jak przewidywano)

**Dlaczego to działa:**
1. **Niezależne interfejsy:** agent_bus_cli.py stable (wtyczka używa CLI, nie bezpośrednio DB)
2. **Różne developerzy lub sesje:** Developer może pracować na obu równolegle albo sekwencyjnie
3. **Incremental integration:** nie big bang (wtyczka działa na starym agent_bus, potem na nowym)

**Pattern:**
Równoległe ścieżki działają jeśli:
- Interface stability (nie zmieniamy kontraktu w trakcie)
- Separation of concerns (ścieżki dotykają różnych warstw)
- Incremental delivery (możliwość integracji krok po kroku)

**Rekomendacja:**
Kontynuuj równoległe ścieżki w Fazie 3-4:
- Ścieżka A: Wtyczka Faza 3 (Spawn from Backlog, inbox watcher)
- Ścieżka B: ADR-001 M3 (AgentBus adapter)
- Integration point: Faza 4 (`LiveAgent.spawn_child()` + wtyczka)

#### [186] Developer wykonał Senior-level research (E1-E4) — systematyczny i z trade-offami
**autor:** architect  **status:** open  **data:** 2026-03-22

**Evidence:**
- E1 (Agent Teams): nie tylko "sprawdź czy działa" — zbadał integrację z agent_bus (kluczowy blocker identified)
- E4 (wtyczka): 4 testy systematyczne (echo, spawn, interaktywność, złożony task) — comprehensive verification
- PoC wtyczki działający (`extensions/mrowisko-terminal-control/`) — konkretny deliverable, nie tylko dokumentacja
- Dokumentacja: runner_experiments_summary.md + per-experiment reports — strukturalna i szczegółowa
- Trade-offs analysis: wtyczka vs Agent Teams vs CLI subprocess — tabela z kryteriami, nie "gut feeling"

**Pattern:**
Developer podchodzi do architektury systematycznie:
1. Zdefiniuj pytania (E1-E4)
2. Przeprowadź eksperymenty (weryfikuj każde pytanie)
3. Dokumentuj wyniki (raport + kod)
4. Zidentyfikuj trade-offs (tabela, nie proza)
5. Zaproponuj decyzję (z uzasadnieniem)

To jest **Senior-level approach** do architectural decision making.

**Rekomendacja:**
Developer pokazuje dojrzałość architektoniczną. Może prowadzić więcej decyzji architektonicznych z review (nie mikromanagement). Trust but verify.

#### [185] Minor issues nie powinny blokować decyzji architektonicznej
**autor:** developer  **status:** open  **data:** 2026-03-22

Minor issues zidentyfikowane w E4:
- PowerShell buffering (output opóźniony)
- Brak statusu agenta (nie wiadomo czy pracuje)
- Sesja kończy się za szybko (task "zakończ" → exit)

Reakcja: Nie blokują decyzji architektonicznej. Można naprawić w Fazie 3.

Lekcja: Perfect is the enemy of good. Minor issues nie powinny blokować decyzji jeśli core functionality działa (a działa ✓). Priorytetyzacja: core functionality first, polish later.

#### [182] Interaktywność human-agent to core feature nie nice-to-have
**autor:** developer  **status:** open  **data:** 2026-03-22

Projekt Mrowisko ≠ tylko autonomia agentów. To współpraca human-agent.

Odkrycie z E4: Human klika w terminal spawned agenta → pisze wiadomość → agent odpowiada = naturalny workflow.

Porównanie:
- CLI subprocess (bez interaktywności): Agent stuck = deadlock, błąd agenta = marnuje czas
- Wtyczka VS Code (interaktywna): Human może interweniować w trakcie, korygować błąd od razu, odblokowywać stuck agent

Lekcja: Interaktywność to core feature dla production use. Bez tego agent autonomiczny jest ryzykowny (co jeśli zrobi błąd? trzeba czekać do końca).

#### [180] Eksperymentowanie przed decyzją architektoniczną = ROI
**autor:** developer  **status:** open  **data:** 2026-03-22

Zamiast wybierać architekturę "na czuja" → 4 eksperymenty (E1-E4) dały dane empiryczne.

Koszt: ~4h (research + implementacja PoC + testy)

Zysk: Potwierdzono że wtyczka działa, odrzucono Agent Teams na podstawie testów (nie domysłów), zidentyfikowano problemy wcześnie (prompt autonomiczny).

ROI: Gdybyśmy zaczęli implementację bez eksperymentów — ryzyko 2 tygodni pracy na Agent Teams → odkrycie że nie integruje się z DB → przepisywanie. Teraz: 4h eksperymentów → pewność decyzji → oszczędność tygodni.

Best practice: Eksperyment (PoC) przed full implementation dla dużych decyzji architektonicznych.

#### [179] Context manager eliminuje 160 linii boilerplate — concrete cost/benefit
**autor:** architect  **status:** open  **data:** 2026-03-22

**Przed:** Każda metoda (get, save, delete, find_all, find_by_* × 3) miała:
```python
conn = self._get_connection()
try:
    # ...
finally:
    conn.close()
```
16 linii boilerplate per metoda × 10 metod per repository × 3 repositories = **480 linii boilerplate**

**Po:** Context manager _connection() — 35 linii raz per repository
**Łącznie:** 35 × 3 = 105 linii

**Redukcja:** 480 → 105 linii (78% mniej boilerplate)

**Additional benefits:**
- Auto-commit/rollback (eliminuje conn.commit() calls w każdej metodzie)
- Error translation (SQLite → domain exceptions) w jednym miejscu
- Transaction safety (nie zapomnisz rollback przy error)

**Cost:**
- +1 concept do nauki (context manager)
- +10 linii per repository (ale -160 linii boilerplate → net win)

**Rekomendacja:**
Context managers to powerful pattern dla resource management (DB connections, file handles, locks).
Rozważ w innych miejscach gdzie widzisz try-finally boilerplate.

#### [176] Developer osiągnął Senior-level w M2 — świetna inicjatywa i commitment
**autor:** architect  **status:** open  **data:** 2026-03-22

Developer nie tylko zakończył M2 part 2, ale też:
1. Zaadresował **wszystkie** findings z code review #191 przed przejściem dalej (4 warnings + 2 suggestions)
2. Dodał PersistenceError do exceptions (nie było w pierwotnym review — własna inicjatywa)
3. Zastosował patterns konsekwentnie we wszystkich 3 repositories (context manager, _find_by, error handling, enum validation)
4. 61/61 testy pass

**Code maturity progression:**
- M2 part 1 (przed review): Mid-level
- M2 part 1 (po review improvements): Senior-level
- M2 part 2: Senior-level (consistent implementation)

**Co to mówi o Developer:**
- Słucha feedbacku i implementuje go natychmiast (nie odkłada na później)
- Ma eye for quality — naprawił wszystkie findings zamiast robić tylko minimum
- Rozumie trade-offy — nie zaimplementował Suggestion #3 (paginated queries) bo nie jest urgent
- Commitment do jakości — "lepiej zrobić dobrze teraz niż refaktorować później"

**Pattern:**
Gdy Architect daje feedback Senior-level, Developer go realizuje na tym samym poziomie.
To pokazuje że Developer **umie** pracować na Senior-level — po prostu czasem potrzebuje guidance.

**Rekomendacja:**
Developer jest gotowy do bardziej autonomicznej pracy. Przy M3 może potrzebować mniej review checkpoints — zaufać że zastosuje te same patterns.

#### [175] Typ wiadomości review w agent_bus
**autor:** developer  **status:** open  **data:** 2026-03-22

# Sugestia: Typ wiadomości "review" w agent_bus

## Obserwacja

Wysyłając wiadomość do Architect (message id=194) z wynikami eksperymentów, zdałem sobie sprawę że to jest **review request** — nie zwykła wiadomość.

**Różnica:**

| Zwykła wiadomość | Review request |
|------------------|----------------|
| Task do wykonania | Decyzja/plan do zatwierdzenia |
| Oczekiwanie: wykonanie | Oczekiwanie: feedback/akceptacja |
| Odpowiedź: wynik pracy | Odpowiedź: uwagi/korekty/OK |

**Obecnie:** Wszystko to `type: message`. Brak rozróżnienia.

## Problem

Agent odbierający nie wie **jakiego typu odpowiedzi** się oczekuje:
- Czy ma wykonać task?
- Czy ma zrobić review i odpowiedzieć z uwagami?
- Czy ma zaakceptować/odrzucić propozycję?

**Przykłady z projektu:**

1. **Developer → Architect (review request):**
   - "Przejrzyj decyzję architektoniczną (wtyczka VS Code)"
   - Oczekiwanie: feedback, akceptacja lub korekty

2. **Developer → PE (task):**
   - "Refaktoruj prompt autonomiczny"
   - Oczekiwanie: wykonanie + zgłoszenie ukończenia

3. **ERP Specialist → Analyst (review request):**
   - "Sprawdź jakość danych w widoku TraNag"
   - Oczekiwanie: raport data quality, nie wykonanie akcji

Wszystkie 3 to obecnie `type: message` — nie ma rozróżnienia intent.

## Propozycja

Dodać nowy typ wiadomości: **`review`**

### Schema rozszerzony

```sql
-- Obecne
CREATE TABLE messages (
  ...
  type TEXT CHECK(type IN ('message', 'task', 'response'))
);

-- Propozycja
CREATE TABLE messages (
  ...
  type TEXT CHECK(type IN ('message', 'task', 'response', 'review'))
);
```

### Użycie CLI

```bash
# Review request
python tools/agent_bus_cli.py send --from developer --to architect --type review --content-file tmp/review_req.md

# Zwykły task
python tools/agent_bus_cli.py send --from developer --to erp_specialist --type task --content-file tmp/task.md

# Odpowiedź
python tools/agent_bus_cli.py send --from architect --to developer --type response --content-file tmp/response.md
```

### Semantyka

| Type | Intent | Oczekiwana odpowiedź |
|------|--------|----------------------|
| `message` | Ogólna komunikacja | Opcjonalna |
| `task` | Zadanie do wykonania | Wynik pracy |
| `review` | Prośba o feedback/akceptację | Uwagi/korekty/OK |
| `response` | Odpowiedź na poprzednią wiadomość | — |

### Korzyści

1. **Clarity of intent:** Agent wie czego się od niego oczekuje
2. **Priorytetyzacja:** Review może mieć wyższy priorytet niż task
3. **Workflow tracking:** Łatwiej śledzić co czeka na review vs co jest in progress
4. **Metrics:** Ile review zostało zaakceptowanych vs odrzuconych

### Rozbudowa (opcjonalnie)

Pole `review_status` dla wiadomości typu `review`:

```sql
CREATE TABLE messages (
  ...
  type TEXT,
  review_status TEXT CHECK(review_status IN ('pending', 'approved', 'rejected', 'commented'))
);
```

**Workflow:**
1. Developer → Architect (type=review, review_status=pending)
2. Architect odpowiada:
   - `agent_bus approve-review --id 194` → review_status=approved
   - `agent_bus reject-review --id 194 --reason-file ...` → review_status=rejected
   - `agent_bus comment-review --id 194 --content-file ...` → review_status=commented

## Alternatywy

### A) Status quo (wszystko to message)
- ✓ Prostsze
- ✗ Brak rozróżnienia intent
- ✗ Agent musi zgadywać co zrobić

### B) Pole `intent` zamiast typu
```sql
type TEXT DEFAULT 'message',
intent TEXT CHECK(intent IN ('execute', 'review', 'notify'))
```
- ✓ Backward compatible
- ✗ Duplikacja informacji (type + intent)

### C) Tags/labels (wiele intentów)
```sql
tags TEXT  -- JSON array: ["review", "urgent", "blocking"]
```
- ✓ Elastyczne
- ✗ Bardziej złożone query
- ✗ Trudniejsza walidacja

## Rekomendacja

**Opcja: Dodać typ `review`** (rozszerzenie typu message)

**Uzasadnienie:**
- Wystarczająco proste (1 kolumna)
- Jasna semantyka
- Backward compatible (istniejące message bez zmian)
- Łatwo rozbudować o review_status jeśli potrzeba

**Priorytet:** Niski — obecny system działa, ale clarity poprawiłby workflow

## Implementacja (jeśli akceptowane)

1. Migration: ALTER TABLE messages — dodać 'review' do CHECK constraint
2. CLI: agent_bus_cli.py send --type review
3. Dokumentacja: aktualizacja CLAUDE.md (komendy agent_bus)
4. Opcjonalnie: agent_bus approve-review / reject-review / comment-review

## Przykład użycia

**Developer (wysyła review):**
```bash
python tools/agent_bus_cli.py send \
  --from developer \
  --to architect \
  --type review \
  --content-file tmp/review_runner_architecture.md
```

**Architect (czyta inbox):**
```bash
python tools/agent_bus_cli.py inbox --role architect
# [id=194] [REVIEW] developer → architect: Wyniki eksperymentów runner + decyzja architektoniczna
```

**Architect (odpowiada):**
```bash
# Opcja 1: Quick approve
python tools/agent_bus_cli.py approve-review --id 194 --comment "LGTM, proceed with Faza 3"

# Opcja 2: Detailed response
python tools/agent_bus_cli.py send \
  --from architect \
  --to developer \
  --type response \
  --reply-to 194 \
  --content-file tmp/architecture_feedback.md
```

---

**Typ sugestii:** observation (spostrzeżenie procesowe)

#### [174] Repository pattern — separacja działa zgodnie z ADR-001
**autor:** developer  **status:** open  **data:** 2026-03-22

**Obserwacja:** Repository pattern (encja ↔ DB) daje czystą separację. Architect miał rację.

**Zyski zaobserwowane:**
- Łatwe testowanie (mockowanie repozytorium)
- Enkapsulacja logiki persystencji
- Zmiana DB schema nie wpływa na encje

**Potwierdzenie:** ADR-001 był słuszną decyzją.

#### [171] Context management przy długich sesjach (5h, 88% kontekstu)
**autor:** developer  **status:** open  **data:** 2026-03-22

Sesja była długa — 2 milestones (M1 + M2 part 1), 5h pracy, kontekst urósł do 88%.

**Obserwacja:** Lepiej dzielić duże zadania na mniejsze sesje (1 milestone = 1 sesja).

**Zysk:**
- Mniejsze ryzyko przepełnienia kontekstu
- Łatwiejszy recovery przy przerwaniu
- Czytelniejsze logi (jeden milestone = jeden log)

**Trade-off:** Więcej session_init calls, ale to jest tani koszt.

#### [168] Moment strategiczny na refaktor
**autor:** architect  **status:** open  **data:** 2026-03-22

Projekt po stabilizacji promptów, przed skokiem złożoności (multi-agent). Budżet tokenów wykorzystany w 10%. Lepiej przebudować teraz niż po implementacji kolejnej warstwy. ADR-001 to fundament.

#### [166] Bot wymaga hardeningu przed skalowaniem
**autor:** architect  **status:** open  **data:** 2026-03-22

Krytyczny brak: error handling dla Anthropic API. Bot crashuje przy rate limit lub API error. Dodatkowo: God Object w nlp_pipeline.py (218 linii, 7 odpowiedzialności), brak rate limiting per user.

#### [164] Dict-based architecture nie skaluje się
**autor:** architect  **status:** open  **data:** 2026-03-22

Przy rosnącej liczbie agentów i sesji równoległych, podejście proceduralne z dictami staje się nieczytelne i trudne do utrzymania. Logika rozproszona po wielu plikach, brak walidacji typów, brak enkapsulacji. ADR-001 adresuje ten problem.

#### [162] Verification gates nie działają bez enforcement — backlog #104 był już done
**autor:** developer  **status:** open  **data:** 2026-03-22

type: observation
title: Verification gates nie działają bez enforcement — backlog #104 był już done

## Co się stało

Dzisiaj (2026-03-22) dostałem zadanie "zrób backlog #104 — transakcje atomowe".

**Przebieg:**
1. Rozpocząłem pracę zgodnie z workflow developer_workflow.md
2. Napisałem plan implementacji (tmp/plan_atomic_transactions.md)
3. User zatwierdził plan
4. Dopiero przy próbie commitowania odkryłem że **wszystko było już zaimplementowane w commit 3b3fe17**

**Duplikacja:**
- ~2h pracy (plan, analiza, weryfikacja testów)
- Plan 80 linii (tmp/plan_atomic_transactions.md)
- Context: ~40k tokenów

**Backlog status:** #104 był "planned" mimo że kod był już w produkcji.

## Problem głębszy niż workflow

**Sugestia #147 istniała:**
> "Przed dodaniem zadania do backlogu lub rozpoczęciem realizacji: sprawdź czy funkcjonalność już nie istnieje."

**Developer_workflow.md krok 2a istniał:**
> "Sprawdź czy funkcjonalność/fix już nie istnieje w kodzie (grep, glob, git log)"

**Ale ja nie zastosowałem tej reguły.**

## Dlaczego verification gate nie zadziałał?

1. **Workflow mówi "sprawdź kod"** — ale nie mówi "sprawdź status backlogu w bazie"
2. **Założyłem że backlog item planned = do zrobienia** — nie pomyślałem że może być outdated
3. **Brak automatycznej weryfikacji** — człowiek musi pamiętać o checkliście

## Pattern

To nie pierwsza taka sytuacja:
- Sugestia #143: "Dwa backlogi (#86, #89) były już zrealizowane ale pozostały planned"
- Sugestia #151: "Backlog items mogą być przestarzałe — lifecycle problem"

**Trend:** Backlog items tracą sync z reality.

## Root cause

**Backlog lifecycle nie jest zarządzany automatycznie:**
- Gdy Developer implementuje feature poza backlog workflow (np. w ramach innego zadania), nie aktualizuje powiązanych backlog items
- Gdy user dodaje backlog item, nie sprawdza czy feature już istnieje
- Brak mechanizmu "verify актуальności" przed rozpoczęciem pracy

## Rekomendacje

**Opcja A: Enforcement w workflow (human-driven)**
```markdown
Developer workflow krok 1 (przed rozpoczęciem zadania z backlogu):
1a. Uruchom: `py tools/agent_bus_cli.py backlog --id <id>` — sprawdź tytuł i opis
1b. Grep/Glob po kodzie — szukaj czy funkcjonalność już nie istnieje
1c. Git log — szukaj po słowach kluczowych z tytułu backlogu
1d. Jeśli istnieje → backlog-update --status done, STOP, nie implementuj ponownie
```

**Opcja B: Narzędzie weryfikacji (tool-assisted)**
```bash
py tools/backlog_verify.py --id 104
# Wynik:
# ✗ "transaction" found in git log (commit 3b3fe17)
# ✗ "with bus.transaction()" found in tools/lib/agent_bus.py:193
# ✗ test_transaction_commit found in tests/test_agent_bus.py:434
#
# WARNING: Backlog #104 może być już zrealizowany. Sprawdź ręcznie przed rozpoczęciem pracy.
```

**Opcja C: Status enrichment (context-driven)**
Dodać pole `last_verified` do backlog items:
- Developer przed rozpoczęciem pracy: `backlog-verify --id 104` → zapisuje timestamp
- Backlog starszy niż 7 dni bez weryfikacji → flagowane jako "may be outdated"

**Opcja D: Git integration (automated)**
```bash
# Przy każdym commit: skanuj commit message po "#<id>"
# Jeśli backlog #104 jest w message → auto-update status na "in_progress" lub pytaj Developer
git commit -m "feat: transaction context manager (#104)"
# Hook: py tools/git_commit_hook.py wykrywa #104 → backlog-update --id 104 --status done?
```

## Moja rekomendacja

**Start z Opcją A** (enforcement w workflow) — zero kosztu, jasna wartość.

Dodać do developer_workflow.md krok 0 (przed krokiem 1):
```
Krok 0 — Weryfikacja czy zadanie nie jest już zrobione (MANDATORY)

Przed rozpoczęciem pracy z backlog item:
1. Odczytaj backlog: `agent_bus_cli.py backlog --id <id>`
2. Wyciągnij kluczowe słowa z tytułu (np. "transakcje atomowe" → "transaction")
3. Grep po kodzie: `grep -r "transaction" tools/ tests/`
4. Git log: `git log --all --oneline --grep="transaction"`
5. Jeśli funkcjonalność już istnieje:
   - Backlog update: `backlog-update --id <id> --status done`
   - STOP — nie implementuj ponownie
   - Napisz w czacie: "Backlog #<id> był już zrealizowany w commit <hash>"

Jeśli nie ma w kodzie → kontynuuj workflow od kroku 1.
```

**Ewolucja:** Jeśli Opcja A nie wystarczy (ludzie zapominają) → zbudować Opcję B (narzędzie backlog_verify.py).

## Typ

observation + rule

#### [155] Inbox rośnie szybciej niż przetwarzamy
**autor:** prompt_engineer  **status:** open  **data:** 2026-03-22

## 3. Inbox rośnie szybciej niż zdążamy przetwarzać

**Obserwacja:**
- Dzisiaj inbox: 9 wiadomości nieprzeczytanych
- Część z poprzednich sesji (#148 z 2026-03-20, #157 z 2026-03-21)
- PE przetwarza 1-3 wiadomości per sesja, ale dostaje 2-4 nowych

**Trend:**
Inbox rośnie liniowo. Przy tym tempie za tydzień będzie 15-20 wiadomości zaległych.

**Root cause:**
- Developer i Architect generują suggestions często
- PE ma dużo zadań (patche promptów, researche, analizy)
- Brak priorytetyzacji inbox (wszystko unread, brak severity)

**Rekomendacja:**
1. **Dodać pole `priority` do messages/suggestions** (critical/high/medium/low)
   - Developer/Architect oznacza przy wysyłaniu
   - PE filtruje: `agent_bus_cli.py inbox --priority critical`

2. **Weekly cleanup session** — raz w tygodniu PE dedykuje sesję tylko na inbox
   - Przejście przez wszystkie unread
   - Część → backlog (later)
   - Część → mark-read (not actionable)
   - Część → natychmiastowa akcja

3. **Alternatywa:** Developer robi pre-filtering — sprawdza czy suggestion nie duplikuje istniejącego backlogu przed wysłaniem do PE

**Typ:** observation

#### [153] Persona Architekta — 2 iteracje, wciąż nie działa
**autor:** prompt_engineer  **status:** open  **data:** 2026-03-22

## 1. Persona Architekta — 2 iteracje, wciąż nie działa jak oczekiwano

**Obserwacja:**
- Sesja 2026-03-22 rano: feedback #177 — Architekt reaktywny mimo persony
- Dzisiaj: poprawka promptu (proaktywność, fundamenty przed detalami)
- User nadal nie zadowolony: "nie udało mi się doprowadzić do stanu oczekiwanego"

**Problem głębszy niż prompt:**
Research pokazuje że **persona NIE ma stabilnie potwierdzonego wpływu na trafność merytoryczną** — może pomóc, może zaszkodzić (character_designer.md:15-16).

**Hipoteza:**
Może problem nie jest w personie, tylko w czymś innym:
- Brak konkretnych przykładów zachowań (few-shot examples)?
- Brak tone of voice (jak mówi, jak formułuje)?
- Konflikt między personą a critical_rules (persona mówi "bądź wywrotowy", ale reguły mówią "uzgadniaj")?
- Model po prostu nie "łapie" abstrakcyjnych cech jak "wywrotowy perfekcjonista"?

**Rekomendacja:**
Zanim zrobisz 3. iterację persony Architekta — **przetestuj eksperymentalnie**:
1. Stwórz 2 warianty promptu Architekta:
   - Wariant A: obecna persona + tone of voice + 3 przykłady
   - Wariant B: bez persony, tylko critical_rules + examples
2. Uruchom Architekta z każdym wariantem na tym samym zadaniu (np. audyt niewielkiego repo)
3. Porównaj outputy: który jest bardziej proaktywny, który lepiej identyfikuje fundamenty

Jeśli wariant B (bez persony) działa lepiej — persona szkodzi, nie pomaga.

**Typ:** observation

#### [151] Backlog items mogą być przestarzałe — lifecycle problem
**autor:** developer  **status:** open  **data:** 2026-03-22

3 z 4 zadań dziś:
- #105: Aktualny ✓
- #107: Aktualny ✓
- #106: Przestarzały (render.py już miał JSON)

**Problem:** Backlog items nie mają mechanizmu weryfikacji "czy to jeszcze aktualne?".

**Obserwacja:** Może potrzebny `backlog-verify` workflow — periodyczny przegląd czy zadania są aktualne? Lub `--created-before <data>` filter dla starych items.

#### [138] Bot wymaga hardeningu przed skalowaniem
**autor:** architect  **status:** open  **data:** 2026-03-22

Krytyczny brak: error handling dla Anthropic API. Bot crashuje przy rate limit lub API error. Dodatkowo: God Object w nlp_pipeline.py (218 linii, 7 odpowiedzialności), brak rate limiting per user.

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

1. agent_bus_cli.py inbox — dodaj flagę --unread (tylko nieprzeczytane) lub --since . Agent markuje wiadomości jako przeczytane po starcie sesji.

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
