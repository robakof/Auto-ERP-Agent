# Backlog

*26 pozycji*

---

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

---

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

---

### [Dev] Hook blokuje komendy z newline mimo Bash(python:*) w settings

Hook bezpieczenstwa generuje osobny klucz dla komend zaczynajacych sie od znaku nowej linii (__NEW_LINE_hash__ python:*), ktory nie matchuje wzorca Bash(python:*).

Niezbadane: czy Bash(\npython:*) w settings.local.json rozwiazuje problem. Czy problem dotyczy tylko python czy tez innych komend (git, pytest).

Do zbadania: jak hook generuje klucze dla multiline — sprawdzic kod hooka lub przetestowac dodajac Bash(\npython:*) i Bash(\ngit:*).

Zalezy od: potwierdzenia ktore komendy sa blokowane i w jakich warunkach.

---

settings.local.json posprzatany — usunieto 5 jednorazowych hardcoded komend, artefakty __NEW_LINE__, WebFetch(domain:), redundantne git subkomendy. Dodano pytest:*, cp:*. Bash(python:*) pokrywa agent_bus_cli bez blokowania hooka — potwierdzone testem. DONE 2026-03-13.

---

### [Dev] Rewizja reguł Bash w DEVELOPER.md po uporządkowaniu settings.local.json

Po wdrożeniu backlog id=31 (porządek uprawnień) — przejrzeć sekcję "Reguły pisania komend Bash" w DEVELOPER.md.

Pytanie: które reguły istnieją z powodu brakujących uprawnień w settings, a które mają realne uzasadnienie?
Zakaz $() i python -c może być obejściem hooka, nie realną potrzebą bezpieczeństwa.

Cel: usunąć reguły które są prowizorką — zostawić tylko te z realnym uzasadnieniem niezależnym od hooka.

Zależność: zrobić po backlog id=31.


---

### [Dev] settings.local.json — uporzadkowanie uprawnien + agent_bus

Dodac do permissions.allow:
- Bash(python tools/agent_bus_cli.py:*) — agent_bus bez zatwierdzenia
- Bash(python tools/git_commit.py:*) — jesli nie ma
- Bash(python tools/migrate_*:*) — skrypty migracyjne

Posprzatac: usunac hardcoded jednorazowe wpisy (cd && grep -n ..., cd && taskkill, cd && mv ...).
Zostawic tylko wzorce generyczne.

Plik: .claude/settings.local.json

---

### [Dev] Zasada projektowania DB — przykładowe rekordy przed schematem

Przed napisaniem CREATE TABLE napisz 5 przykladowych INSERT-ow dla roznych przypadkow.
Jesli przyklady nie pasuja do schematu — schemat jest zly.

Wdrozenie: dodac do DEVELOPER.md jako zasade projektowania baz danych.
Miejsce: sekcja CODE QUALITY STANDARDS lub nowa sekcja 'Projektowanie danych'.

Uzasadnienie: schemat DB to decyzja o rozumieniu domeny, nie techniczna.
Rozmowy o domenie nie mozna zastapic dobrymi pytaniami — wymaga ze user zobaczy
konkretne dane. Sesja 2026-03-13: 3 iteracje korekcji schematu agent_bus bo
zaczeto od abstrakcji zamiast od przykladow.

---

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

---

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

---

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

---

### Przycinanie ramy teoretycznej

**Źródło:** methodology_suggestions
**Sesja:** 2026-03-08
**Dokument do zmiany:** METHODOLOGY.md (sekcja "Wprowadzenie")

Test operacyjny dla każdego pojęcia: czy zmienia jakąkolwiek decyzję?
Fraktalność — tak (ta sama struktura per poziom złożoności).
Genomiczność, cybernetyka drugiego rzędu — legitymizacja, nie instrukcja.
Zostawić jedną ramę orientacyjną, resztę zastąpić konkretnymi warunkami.

---

---

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

---

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

---

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

---

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

---

### [ERP] Sesja inspekcji schematu CDN

**Źródło:** obserwacja sesji 2026-03-11
**Sesja:** 2026-03-11
**Wartość:** średnia
**Pracochłonność:** mała

Niezbadane: inne funkcje CDN, widoki CDN.* vs tabele, tabele słownikowe powtarzalne w widokach BI.
Propozycja: INFORMATION_SCHEMA + sp_helptext przed kolejnym widokiem BI.

---

---

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

---

### [Arch] Brak backlogu per-rola — eskalacja do Metodologa

**Źródło:** obserwacja sesji 2026-03-11
**Sesja:** 2026-03-11
**Wartość:** średnia
**Pracochłonność:** mała–średnia

Zadania domenowe (ERP, Bot) mieszają się z architektonicznymi w jednym pliku.
Opcje: osobne pliki per-rola vs tagi domenowe.
Decyzja należy do Metodologa.

---

---

### [Arch] arch_check.py — walidator ścieżek w dokumentach

**Źródło:** obserwacja sesji 2026-03-11
**Sesja:** 2026-03-11
**Wartość:** średnia
**Pracochłonność:** mała

Skanuje pliki `.md` w poszukiwaniu wzorców `` `documents/...` `` i sprawdza czy ścieżki istnieją.
Do wdrożenia przy kolejnym dużym refaktorze.

---

---

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

---

### [Bot] Fallback przy błędzie SQL

**Źródło:** obserwacja sesji testowej
**Sesja:** 2026-03-10
**Wartość:** średnia
**Pracochłonność:** średnia

Gdy `execution_result.ok = False` — ponów Call 1 z instrukcją "wygeneruj prostszą wersję".
Max 1 retry.

---

---

### [Bot] Routing model — Haiku dla prostych pytań, Sonnet dla złożonych

**Źródło:** obserwacja sesji testowej
**Sesja:** 2026-03-10
**Wartość:** średnia
**Pracochłonność:** średnia

Classifier w Call 1 — Haiku ocenia złożoność i wybiera model do generowania SQL.

---

---

### [Bot] Reload konfiguracji bez restartu

**Źródło:** obserwacja sesji testowej
**Sesja:** 2026-03-10
**Wartość:** średnia
**Pracochłonność:** mała

Komenda `/reload` przez Telegram (tylko admin) lub watchdog na `.env`.

---

---

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

---

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

---

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
