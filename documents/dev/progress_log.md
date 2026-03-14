# Progress Log

---

## Stan bieżący

**Aktualizacja:** 2026-03-14

**Co działa:**
- `tools/lib/agent_bus.py` — AgentBus + `agent_bus_cli.py`: send, inbox, suggest, suggestions, suggest-status, backlog-add, **backlog-add-bulk**, backlog, **backlog-update (--content-file)**, log, flag
- 496 testów łącznie, 495 zielone (1 pre-istniejący fail w telegram_channel)
- `tools/render.py` — output domyślnie do `views/` (gitignored)
- `tools/agent_bus_server.py` — FastAPI localhost:8765, uruchamiany ręcznie
- Komunikacja agent-agent: ERP Specialist ↔ Analyst ↔ Developer przez agent_bus

**Architektura:**
- `tmp/` — pliki pośrednie agentów (gitignored)
- `views/` — rendery dla człowieka (gitignored)
- Reguły Bash przeniesione z DEVELOPER.md → CLAUDE.md (zasada wspólna)
- render.py DB-direct (świadoma decyzja — HTTP gdy pojawi się zewnętrzna komunikacja)

**Widoki BI gotowe:**
- BI.Kontrahenci ✓ (`solutions/bi/views/Kontrahenci.sql`)
- BI.Rezerwacje ✓ (`solutions/bi/views/Rezerwacje.sql`)
- BI.ZamNag ✓ (`solutions/bi/views/ZamNag.sql`) — otwarte: ZaN_PromocjePar=3 (znaczenie nieznane), ZaN_DokZwiazane (bitmask surowy)
- BI.Rozrachunki ✓ (`solutions/bi/views/Rozrachunki.sql`) — fallback Stan & 2 usunięty (commit 1b5d245)
- BI.TwrKarty ✓ (`solutions/bi/views/TwrKarty.sql`) — 66 kolumn, 10 122 wierszy; MRP_Id → CDN.ProdOkresy, Techniczna_Dec1 as-is z komentarzem anomalii

**Następny krok:** BI.TraNag (id=32, nagłówki dokumentów handlowych) — nowa sesja ERP Specialist

---

## Dziennik

### 2026-03-14 — Czyszczenie długu dokumentacyjnego + backlog --area filter

- Usunięto 13 plików (handoffy, przebudowa_wytycznych, human_inbox, developer_notes, solutions/analyst)
- Przeniesiono do `documents/archive/`: 5 progress logów widoków, backlog.md, 4 pliki suggestions, methodology_backlog
- CLAUDE.md: usunięto wyjątki .md suggestions, dodano motivację "dlaczego Bash blokuje projekt", dodano filtrowanie backlogu po roli
- DEVELOPER.md: backlog.md → CLI command
- analyst_start.md: usunięto 3 referencje do developer_notes.md
- `get_backlog()` + CLI: nowy filtr `--area` + 3 testy (66 zielonych)
- Wnioski id=25, id=26, id=27 z inboxu Developer przetworzone

---

### 2026-03-14 — BI.TwrKarty zakończony (Faza 4)

- Draft finalny: 66 kolumn, 10 122 wierszy
- Odkrycie: `Twr_MrpId → CDN.ProdOkresy.POK_Id` (JOIN 100%); dodana kolumna `MRP_Okres_Data` (Clarion DATE)
- Decyzja: `Techniczna_Dec1` eksponowana as-is z komentarzem anomalii (docs: pusta, baza: 13 distinct)
- Poprawki analityka z recenzji wdrożone: Autonumeracja_Kod usunięta, Data_Modyfikacji_O usunięta, JM symbole dla zakup/mobile/dopełniania dodane
- Widok zapisany: `solutions/bi/views/TwrKarty.sql` (commit b8dfcef)

---

### 2026-03-14 — backlog cleanup + zasady + agent_bus task type

- `ERP_SPECIALIST.md`, `ANALYST.md` — usunięto referencje do zdeprecjonowanego `developer_notes.md` (id=43)
- `MEMORY.md` — zaktualizowano status projektu i architekturę ról (id=44)
- `CLAUDE.md` — nowa sekcja "Komunikacja agent-agent" (odpowiedź proporcjonalna do zadania) (id=42)
- `agent_bus.py` — `ALLOWED_MESSAGE_TYPES` + walidacja + typ `task` i `info`; `agent_bus_cli.py` — `choices` dla `--type` (id=45)
- `DEVELOPER.md` — zasada #8: ręczna operacja = sygnał dla narzędzia (id=30)
- 496 testów, 496 zielone

---

### 2026-03-13 — render.py + session_log migracja + API-first decyzja

- `tools/render.py` — uniwersalny renderer: backlog/suggestions/inbox/messages/session-log × md/xlsx/json, 17 testów
- `tools/agent_bus_server.py` — FastAPI localhost:8765, 15 testów, uruchamiany ręcznie
- `tools/migrate_logs.py` — 7 progress logów .md → session_log w DB
- `tools/lib/agent_bus.py` — dodano get_messages() bez obowiązkowego filtra
- Backlog obszary uzupełnione dla 19 pozycji
- Decyzja architektoniczna: API-first, renderery konsumują JSON nie DB bezpośrednio (backlog id=26)
- settings.local.json cleanup, Bash reguły zweryfikowane ($() zablokowane przez hook — reguła zostaje)
- 488 testów łącznie, 487 zielone (1 pre-istniejący fail telegram_channel)

---

### 2026-03-13 — Agent Bus Faza 1.5 + porządek settings

- `tools/lib/agent_bus.py` — nowe tabele: suggestions, backlog, session_log (+ FK, indeksy)
- `tools/agent_bus_cli.py` — nowe komendy: suggest, suggestions, suggest-status, backlog-add, backlog, backlog-update, log; usunięto write-state
- `tools/migrate_state.py` — migracja 34 wpisów state → backlog (24) + suggestions (10)
- CLAUDE.md, ERP_SPECIALIST.md, ANALYST.md, METHODOLOGY.md — write-state → suggest/backlog-add/log
- `.claude/settings.local.json` — cleanup jednorazówek, dodano pytest:*, cp:*
- 458 testów, 457 zielone

---

### 2026-03-13 — Agent Bus Faza 1 + migracja komunikacji

- `tools/lib/agent_bus.py` — AgentBus: SQLite WAL, tabele messages + state, 8 metod
- `tools/agent_bus_cli.py` — CLI: send, inbox, state, write-state, flag
- `tools/migrate_backlog.py` — migracja backlog.md (14 pozycji) do mrowisko.db
- `tools/migrate_suggestions.py` — migracja methodology_suggestions.md (9 wpisów) do mrowisko.db
- Wszystkie role zaktualizowane: agent_bus jako jedyny kanał komunikacji
- Pliki .md refleksji (erp_specialist_suggestions, analyst_suggestions, methodology_suggestions, backlog) — ARCHIWUM
- CLAUDE.md, DEVELOPER.md, ERP_SPECIALIST.md, ANALYST.md, METHODOLOGY.md — routing do agent_bus
- generate_view (faza 3) dodany do backlogu w DB (id=24)
- 26 nowych testów, 430 łącznie
- Pre-istniejący fail: test_telegram_channel::test_authorized_user_gets_answer (mock/parse_mode, niezwiązany)

---

### 2026-03-11 — Rozruch Analityka

- `documents/analyst/analyst_start.md` — dokument rozruchowy: dwie role (weryfikator konwencji pre-prod + data quality post-prod), pierwsze zadanie (audyt istniejących widoków), format handoff i review
- `ANALYST.md` — dodany odczyt `developer_notes.md` na starcie sesji
- Otwarte: krok "Analityk review" do dodania w `ERP_VIEW_WORKFLOW.md` po pierwszym przebiegu

---

### 2026-03-11 — Weryfikacja prefiksów + kanał Developer→ERP Specialist

- `nieznane_prefiksy_query.sql` — zapytanie wykrywające nieznane prefiksy we wszystkich tabelach nagłówkowych (TraNag smart grouping + MIN/MAX próbka dla ZamNag/MemNag/UpoNag/Prod/Zapisy/RK)
- Wynik: pusty — prefiksy `(s)/(A)/(Z)/brak` są kompletne i wyłączne
- Odkrycie: GenDokMag=-1 ma wyższy priorytet niż Stan&2 (ERP_SCHEMA_PATTERNS CASE odwrócony — do korekty)
- Odkrycie: `TrN_TypNumeracji` nie istnieje w CDN.TraNag — prawidłowo `TrN_GIDTyp IN (...)` (jak w Rozrachunki.sql)
- `documents/erp_specialist/developer_notes.md` — nowy kanał Developer→ERP Specialist (dwa wpisy: TrN_TypNumeracji + priorytet prefiksów)
- `ERP_SPECIALIST.md` — dodany odczyt `developer_notes.md` na starcie sesji
- Otwarte: korekta CASE w ERP_SCHEMA_PATTERNS.md (priorytet GenDokMag przed Stan&2) — wymaga zatwierdzenia

---

### 2026-03-11 — Baza wzorców numeracji dokumentów

- `solutions/reference/numeracja_wzorce_query.sql` — zapytanie dla DBA (CDN.NazwaObiektu 4 params, Format=2)
- `solutions/reference/obiekty.tsv` — pełna lista 280+ typów GID z CDN.Obiekty
- `solutions/reference/numeracja_wzorce.tsv` — wzorce formatów z bazy (TraNag 25 typów + ZamNag/ZP/NM/NO/UP/KB/RK)
- Kluczowe odkrycie: CDN.NazwaObiektu(@ObiTyp, @ObiNumer, @ObiLp, @Format) — nie 2 a 4 parametry
- Reguła w ERP_SPECIALIST.md i backlog: dodać zasadę "zbadaj strukturę przed budowaniem"
- Backlog item [Agent] Baza wzorców numeracji — GOTOWY do zamknięcia po dodaniu reguły do ERP_SPECIALIST.md

---

### 2026-03-11 — Węzłowość reguł + kontekst na końcu wiadomości

- CLAUDE.md: reguła `Kontekst: ~XX%` na końcu każdej wiadomości (zasada wspólna dla wszystkich ról)
- DEVELOPER.md: zasada #6 — reguły umieszczaj na najwyższym możliwym węźle hierarchii (analogia dziedziczenia klas)
- methodology_suggestions.md: refleksja "Węzłowość reguł" dla Metodologa

---

### 2026-03-11 — Dokumentacja ERP Specialist + fix docs_search

- ERP_SCHEMA_PATTERNS: TraNag prefiks (Z)/(A)/(s), KB→CDN.Zapisy, CDN.UpoNag typ 2832, CDN.Rozrachunki GIDLp
- ERP_VIEW_WORKFLOW: Typ_Dok pełne nazwy od Fazy 1, artefakt wyścigu, sql_query blokuje CREATE, verify query od razu
- ERP_SPECIALIST: sprawdź COUNT(*) FROM AIBI.* przed użyciem widoku
- docs_search.py: phrase opcjonalny (nargs='?') — `docs_search.py --table CDN.X` bez `""`
- backlog.md: Analityk jako weryfikator konwencji widoku (nowa pozycja)

---

### 2026-03-11 — Separacja pamięci + rename erp_specialist

- `documents/agent/` → `documents/erp_specialist/` (8 plików, git rename)
- `AGENT.md` → `ERP_SPECIALIST.md`, `agent_suggestions.md` → `erp_specialist_suggestions.md`
- Nowy plik: `documents/analyst/analyst_suggestions.md`
- ANALYST.md: własny plik suggestions + sekcja progress log per-zakres
- CLAUDE.md, METHODOLOGY.md, DEVELOPER.md: etykiety "Agent ERP" → "ERP Specialist", "Agent" → "Wykonawcy"

---

### 2026-03-10 — Bot: poprawki po testach

- strip_markdown: Haiku owijał SQL w ```sql``` — stripped przed walidatorem
- NO_SQL prompt: zmieniony na częściowe odpowiedzi zamiast odmowy
- HTML formatting: parse_mode=HTML w Telegram, formatter używa <b> zamiast **/#
- max_tokens: 500 → 1500 (złożone SQL analityczne były obcinane)
- HAVING rule: prompt zakazuje HAVING z dzieleniem, sugeruje CASE WHEN w SELECT
- ZamNag.sql: fix Typ_Zamowienia 'ZS'→'Zamówienie sprzedaży', 'ZZ'→'Zamówienie zakupu' (wymaga redeploymentu DBA)
- Backlog: +3 nowe pozycje ([Bot] fallback retry, NO_SQL partial, kontekst firmowy+caching)

---

### 2026-03-10 — KM3: Kanał Telegram

- `bot/channels/telegram_channel.py` — TelegramChannel (async, long polling, whitelist, silent reject, TYPING, split)
- `bot/config/allowed_users.txt` — whitelist user_id (plik txt, komentarze ignorowane)
- `bot/main.py` — entry point (load .env, whitelist, pipeline, channel.run)
- `.env.example` + `requirements.txt` — TELEGRAM_BOT_TOKEN + python-telegram-bot>=21.0
- 6 testów (+6), 405 łącznie, 100% zielone

---

### 2026-03-10 — testy bota + fix ZamNag.sql

- Testy pipeline end-to-end (10 pytań) — 9/10 poprawnych, odmowa poza zakresem działa
- Diagnoza: kolumny catalog.json nieaktualne → bi_catalog_add.py --all (fix)
- Diagnoza: Stan vs Status_Realizacji — bot używał złej kolumny
- Fix: usunięto martwe kolumny Status_Realizacji + Wyslano z ZamNag.sql (oba zawsze NULL/Nie)
- UWAGA: ZamNag wymaga redeploymentu przez DBA + bi_catalog_add.py --view AIBI.ZamNag
- bot/CLAUDE.md: instrukcja uruchomienia z --allowedTools

---

### 2026-03-10 — bi_catalog_add.py + konfiguracja CEIM_AIBI

- `tools/bi_catalog_add.py` — sync kolumn catalog.json z rzeczywistą strukturą widoków AIBI (--view / --all)
- catalog.json zaktualizowany: Rezerwacje (40 kol.), KntKarty (143), Rozrachunki (21), ZamNag (102)
- Konfiguracja SQL Server: AIBI owner → CDN Application Role, GRANT SELECT ON SCHEMA::AIBI TO CEIM_AIBI
- Własność chaining działa: CEIM_AIBI czyta AIBI.*, blokada CDN.* potwierdzona
- Pipeline end-to-end przetestowany: `python bot/pipeline/nlp_pipeline.py --question "pokaż 5 ostatnich zamówień"`

---

### 2026-03-10 — KM2: Bot core

- `tools/lib/sql_client.py` — refaktor: `SqlCredentials` (frozen dataclass) + fabryki `create_erp_sql_client()` / `create_bot_sql_client()`. Backwards compatible.
- `bot/pipeline/sql_validator.py` — guardrails domenowe: blokada CDN.*, wymuszenie TOP (domyślnie 50, max 200)
- `bot/pipeline/conversation.py` — `ConversationManager`: 3 tury per user, TTL 15 min
- `bot/sql_executor.py` — wykonanie SQL przez konto CEIM_AIBI (max 200 wierszy)
- `bot/answer_formatter.py` — Claude API call 2: dane → odpowiedź PL. Model konfigurowalny przez `BOT_MODEL_FORMAT`
- `bot/pipeline/nlp_pipeline.py` — orkiestrator pipeline + logowanie do `logs/bot/YYYY-MM-DD.jsonl` + CLI `--question`
- `.env.example` + `requirements.txt` uzupełnione (anthropic>=0.40, zmienne BOT_*)
- 59 nowych testów, 399 łącznie, 100% zielone
- KM2 zamknięty

---

### 2026-03-10 — KM1: search_bi.py

- `tools/search_bi.py` — wyszukiwanie widoków AIBI po frazie (name, description, columns, example_questions)
- `solutions/bi/catalog.json` — dodano AIBI.ZamNag, wszystkie nazwy zaktualizowane do AIBI
- AGENT.md — reguła: sprawdź search_bi.py przed budowaniem JOINów z CDN
- Schema AIBI + konto CEIM_AIBI założone na SQL Server przez DBA
- 11 testów (+11), 333 łącznie, 100% zielone
- KM1 zamknięty

---

### 2026-03-10 — git_commit.py

- `tools/git_commit.py` — git add + commit + push w jednym narzędziu (--all, --files, --push, --push-only)
- DEVELOPER.md: sekcja GIT VERSION CONTROL — reguła używania narzędzia, poprawka ścieżki backlogu
- 14 testów (+14), 319 łącznie, 100% zielone
- Backlog: [Dev] git_commit.py zamknięty

---

### 2026-03-10 — Analityk Danych KM1–KM4 (ZAKOŃCZONY)

- KM3: `data_quality_report.py` — raport Excel z zakładkami Obserwacje + Rekordy (dynamiczne kolumny z JSON)
- KM4: `documents/analyst/ANALYST.md` — instrukcje operacyjne roli, inline z metodologią
- CLAUDE.md: routing Analityk Danych + plik chroniony
- 308 testów łącznie, 100% zielone

---

### 2026-03-10 — Analityk Danych KM1 + KM2

- Architektura: `documents/analyst/ARCHITECTURE.md` + `IMPLEMENTATION_PLAN.md`
- KM1: `data_quality_init.py` (eksport widoku/tabeli do SQLite) + `data_quality_query.py` (query lokalne)
- KM2: `data_quality_save.py` (zapis obserwacji) + `data_quality_records.py` (zapis brudnych rekordów jako JSON)
- 43 nowe testy, 296 łącznie, 100% zielone
- W toku: KM3 (data_quality_report — raport Excel), KM4 (ANALYST.md + routing)

---

### 2026-03-10 — [Workflow] ERP_VIEW_WORKFLOW + ERP_SCHEMA_PATTERNS

- Zasada pominięcia pola: rozszerzona do 4 warunków
- bi_verify vs sql_query: reguła kontekstu w Fazie 3
- excel_read_rows: pierwsze przejście z CDN_Pole,Uwzglednic,Komentarz_Usera
- ERP_SCHEMA_PATTERNS: nowa sekcja TrN_ZaNNumer, reguła formatu roku przez NazwaObiektu, poprawka przykładu ZamNag (YY)
- backlog.md: [Workflow] i [Dev] zamknięte

---

### 2026-03-09 — restructuring progress_log

- Wprowadzono sekcję "Stan bieżący" + Archiwum zgodnie z backlogiem [Docs]
- Wpisy sprzed 2026-03-08 przeniesione do Archiwum

---

### 2026-03-09 — bi_plan_generate.py

- `tools/bi_plan_generate.py` — generuje plan Excel z pliku `*_plan_src.sql`
- Wykonanie SQL w SQLite in-memory (bez SQL Servera) — obsługuje polskie znaki i myślniki
- Domyślna ścieżka output: `*_plan_src.sql` → `*_plan.xlsx` obok pliku src
- 6 testów (+6), łącznie 253 zielone. AGENT.md zaktualizowany.
- Poprawiono 2 wiersze w `Zamowienia_plan_src.sql` (nadmiarowa kolumna w wierszach 115 i 175)

---

### 2026-03-09 — System refleksji trójpoziomowej + przebudowa architektury wytycznych

**System refleksji trójpoziomowej:**
- Nowe pliki refleksji: `agent_suggestions.md`, `developer_suggestions.md`, `methodology_suggestions.md`
- Nowe backlogi: `backlog.md`, `methodology_backlog.md`
- `methodology_progress.md` — progress log warstwy metodologicznej
- CLAUDE.md: krok refleksji po etapie pracy + lista plików chronionych

**Przebudowa architektury wytycznych:**
- CLAUDE.md → czysty routing (~50 linii)
- Nowy: `AGENT.md` — instrukcje operacyjne agenta ERP
- Nowy: `PROJECT_START.md` — workflow inicjalizacji projektu
- Rename: `AI_GUIDELINES.md` → `DEVELOPER.md` (git mv)

---

### 2026-03-09 — LOOM — metodologia jako osobne repo

- `_loom/`: komplet szablonów do bootstrapu nowego projektu (seed.md, CLAUDE_template.md, DEVELOPER.md, PROJECT_START.md, METHODOLOGY.md, szablony refleksji/backlogów)

---

### 2026-03-09 — docs_search: usunięcie --useful-only, limit 1000, fix ERP_SCHEMA_PATTERNS

- `docs_search.py`: usunięto `--useful-only`; domyślny limit 20 → 1000
- `ERP_SCHEMA_PATTERNS.md`: poprawiono błąd w wzorcu numeru ZamNag (WHEN 960 → WHEN 1280 dla ZS)
- 247 testów (-1 test useful_only), 100% zielone

---

### 2026-03-09 — P1 + P2 + P3 + P4 (backlog narzędzia)

- **P1** `excel_export_bi.py --file` — alternatywa dla `--sql`
- **P2** `sql_query.py --count-only + --quiet` — eliminuje 5.8 MB payload
- **P3** `bi_verify.py` — test + eksport + statystyki w 1 kroku
- **P4** `solutions_save_view.py` — draft → views/ bez ładowania treści
- **bi_discovery.py** — raport discovery tabeli CDN (role: empty/constant/enum/id/Clarion_DATE/...)
- Łącznie: 253 testów, 100% zielone

---

### 2026-03-08 — C: gid_types w docs.db + fix docs_search pusta fraza

- `docs_build_index.py`: `parse_gid_types()` — 456 typów GID zaindeksowanych (symbol, internal_name, description)
- `docs_search.py`: `_search_gid_types()` — wyszukiwanie po symbolu/numerze/opisie; `data.gid_types[]`
- fix: `docs_search "" --table CDN.XXX` — zwraca wszystkie kolumny tabeli (bez FTS)
- Testy: +11, łącznie 202 zielone

---

### 2026-03-08 — Poprawki workflow agenta BI (#5–#10)

- **#5** `ExcelWriter`: Excel Table (zebra-stripes, Medium9), nazwa arkusza = `--view-name`
- **#6** Struktura folderów per widok: `solutions/bi/{Widok}/`; usunięto `solutions/bi/drafts/`
- **#7+A** `SqlClient.validate()`: średnik w stringu, strip komentarzy SQL
- **#8** `tools/lib/output.py`: `print_json()` wymusza UTF-8 na stdout — 10 toolsów
- **#9+E** `DEVELOPER.md`: reguły Bash + Edit zamiast Read
- **#10** `ERP_SCHEMA_PATTERNS.md`: zasada `docs_search "[prefiks]GIDNumer"`
- `sql_query.py`: dodano `--file` + `--export`; `excel_export.py`: dodano `--file`
- 191 testów, 100% zielone

---

### 2026-03-08 — Plan widoków BI + sesja BI.Kontrahenci

- Agent zbudował BI.Kontrahenci (`solutions/bi/views/Kontrahenci.sql`)
- Kolejność widoków: Kontrahenci ✓ → Zamowienia → Rozrachunki → DokumentyHandlowe

---

## Archiwum

### 2026-03-07 — Refaktor tools/: lib/ + rename + excel_read_rows

- Wyekstrahowano `tools/lib/`: SqlClient, ExcelWriter, ExcelReader
- Rename toolsów z prefiksem domenowym (excel_*, docs_*, solutions_*, windows_*)
- Nowy tool: `excel_read_rows.py`
- 170 testów, 100% zielone

---

### 2026-03-07 — Przepisanie ERP_VIEW_WORKFLOW.md

- Inicjalizacja: brudnopis `{Widok}.sql` + progress log przed startem
- Faza 1: plan jako Excel (nie MD); analiza kolumna po kolumnie
- Faza 2: SQL wyłącznie na pliku brudnopisu
- Zasady tłumaczenia wartości, zarządzanie kontekstem, ochrona dokumentacji agenta

---

### 2026-03-04 — Implementacja planu restrukturyzacji

- `excel_export_bi.py`, `read_excel_stats.py` — nowe narzędzia BI
- Separacja `ERP_SQL_SYNTAX.md` → 5 plików (ERP_SQL_SYNTAX, ERP_COLUMNS_WORKFLOW, ERP_FILTERS_WORKFLOW, ERP_SCHEMA_PATTERNS, ERP_VIEW_WORKFLOW)
- 166 testów, 100% zielone

---

### 2026-03-04 — export_excel.py + ERP_SQL_SYNTAX.md + BI.Rezerwacje

- `export_excel.py` — SQL → .xlsx (guardrails, auto-timestamp, bold header)
- `ERP_SQL_SYNTAX.md` — sekcje: parametry AI_ChatERP, funkcje dat CDN, arytmetyka Clarion, wzorce BI
- BI.Rezerwacje: 28 kolumn, 1426 wierszy — odkrycia: ZaN_ZamTyp (960=ZS, 1152=ZZ), Clarion TIMESTAMP (sekundy od 1990-01-01)

---

### 2026-03-01 — Kamień milowy 5 ZAKOŃCZONY (Deployment) + porządki

- Model deploymentu: Git clone, docs.db (6.7 MB) w repo, INSTALL.md + verify.py
- Wszystkie 5 kamieni milowych MVP zakończone

---

### 2026-02-27/28 — Kamienie milowe 1–4 + import solutions/

- KM1: 6 narzędzi CLI + 92 testy
- KM2: `erp_windows.json` + `update_window_catalog.py`; 105 testów
- KM3: `ERP_AGENT.md` (instrukcje agenta)
- KM4: MVP end-to-end — filtr "brak załączników .jpg" — agent autonomicznie, zero iteracji
- Import: 35 kolumn SQL (CDN.DefinicjeKolumn) + 70 filtrów SQL (CDN.Filtry) do solutions/
- `ERP_SQL_SYNTAX.md` rozbudowany o wzorce @PAR, daty Clarion, CDN.NazwaObiektu

---

### 2026-02-26 — Faza 1 (Dokumentacja) + Faza 2 (Eksperymenty)

- Stack: Claude Code + MCP, pyodbc, openpyxl → SQLite FTS5, pliki .sql
- Eksperymenty E-01–E-05: pyodbc ✓, openpyxl ✓, FTS5 ✓, MCP tool ✓, format SQL ERP ✓
- Dokumenty: PRD.md, TECHSTACK.md, ARCHITECTURE.md, ERP_SQL_SYNTAX.md, MVP_IMPLEMENTATION_PLAN.md
