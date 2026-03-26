# Plan: Bootstrap nowego projektu Mrowisko (bez ERP/SQL)

**Data:** 2026-03-26
**Rola:** Developer
**Założenia:**
- Brak haseł i loginów w output
- Projekt pomija całkowicie warstwę ERP i SQL
- Nowa maszyna, nowe git repo od zera

---

## Cel

Stworzyć narzędzie `tools/mrowisko_init.py`, które na nowym komputerze (bez gita, bez serwisów)
bootstrapuje gotowy projekt Mrowisko z pełną platformą agentową — bez domeny ERP.

Output: działający katalog projektu gotowy do `git init` + pierwszego commitu.

---

## Inwentaryzacja: co wchodzi, co nie

### PLATFORMA (zostaje w szablonie)

**tools/ — core platform:**
- `agent_bus_cli.py`, `agent_bus_server.py` — magistrala komunikacji agentów
- `db.py` — warstwa bazy danych
- `session_init.py` — inicjalizacja sesji ról
- `setup_machine.py` — konfiguracja nowej maszyny
- `git_commit.py` — wrapper dla commitów
- `render.py` — renderowanie backlogu/sugestii
- `arch_check.py` — walidator architektury
- `mrowisko_runner.py` — runner agentowy
- `search_conversation.py`, `conversation_search.py` — historia sesji (jeśli istnieje)
- `lib/` — biblioteki wspólne
- `hooks/` — hooki Claude Code
- `prompts/` — szablony promptów (bez ERP)
- narzędzia migracji schematu DB: `migration_m5_1_message_title.py`, `migration_workflow_tracking.py`, `migration_add_handoff_type.py`

**documents/:**
- `dev/` — DEVELOPER.md, PROJECT_START.md
- `methodology/` — SPIRIT.md, METHODOLOGY.md
- `architect/` — ARCHITECT.md
- `conventions/` — CONVENTION_META.md, CONVENTION_WORKFLOW.md, README.md
- `researcher/` — prompts/, research/ (bez wyników ERP)
- `prompt_engineer/` — PROMPT_ENGINEER.md, PROMPT_CONVENTION.md
- `architecture/` — PATTERNS.md, ARCHITECTURE.md
- `human/workflows/` — workflow_developer.md, workflow_convention_creation.md, workflow_workflow_creation.md, workflow_suggestions_processing.md, workflow_prompt_refactor.md
- `human/plans/` — puste (katalog)
- `human/reports/` — puste (katalog)
- `human/suggestions/` — puste (katalog)

**workflows/ (root):**
- `workflow_developer.md`
- `workflow_convention_creation.md`
- `workflow_workflow_creation.md`
- `workflow_suggestions_processing.md`
- `workflow_prompt_refactor.md`

**core/ — cały** (messaging infrastructure, domain-agnostic)

**Pliki root:**
- `CLAUDE.md` (z parametryzowaną nazwą projektu — placeholder)
- `SETUP_MACHINE.md`
- `requirements_platform.txt` (tylko zależności platformy, bez ERP/SQL)
- `.env.example` (struktura bez wartości)
- `.gitignore`

**Baza danych:**
- `mrowisko.db` — TYLKO schemat (bez danych), fresh init

### ERP DOMENA (wykluczone)

**tools/ — ERP/BI:**
- `bi_catalog_add.py`, `bi_discovery.py`, `bi_plan_generate.py`, `bi_search.py`, `bi_verify.py`
- `data_cleanup_m4_3.py`, `data_quality_init.py`, `data_quality_query.py`, `data_quality_records.py`, `data_quality_report.py`, `data_quality_save.py`
- `docs_build_index.py`, `docs_search.py`
- `enum_audit.py`, `verify.py`
- `etykiety_export.py`, `etykiety_ui.py`
- `excel_export.py`, `excel_export_bi.py`, `excel_read_rows.py`, `excel_read_stats.py`, `excel_write_cells.py`
- `jas_client.py`, `jas_export.py`, `jas_mapper.py`
- `offer_data.py`, `offer_generator.py`, `offer_generator_3x3.py`, `offer_pdf.py`, `offer_pdf_3x3.py`, `offer_ui.py`, `offer_ui_3x3.py`
- `photo_preprocess.py`, `photo_preprocess_ui.py`, `photo_workflow_ui.py`
- `solutions_save.py`, `solutions_save_view.py`, `solutions_search.py`
- `sql_query.py`
- `windows_search.py`, `windows_update.py`
- `wycena_generate.py`, `wycena_ui.py`
- `bot_stop.py`, `jsonl_parser.py` (ERP-specific boty)
- `migrate_backlog.py`, `migrate_logs.py`, `migrate_methodology_backlog.py`, `migrate_state.py`, `migrate_suggestions.py` (stare migracje historyczne)

**documents/:**
- `erp_specialist/` — cały
- `analyst/` — cały
- `Wzory plików/` — cały
- `human/` — ERP-specific reports, plans (filtrowane, nie cały katalog)

**Katalogi robocze:**
- `solutions/` — cały (ERP SQL)
- `output/` — cały (ERP outputs)
- `tests/` — testy ERP-specific (testy platformy zostają)

**Dane wrażliwe:**
- `.env` — nie kopiować
- `mrowisko.db` — nie kopiować (tylko fresh init)
- `jas.db` — nie kopiować

---

## Mechanizm dostarczenia

### Wybór: `tools/mrowisko_init.py`

Skrypt Python który na nowej maszynie:

```
python tools/mrowisko_init.py --output-dir /ścieżka/do/nowego/projektu [--project-name "Nazwa"]
```

**Co robi:**
1. Tworzy strukturę katalogów nowego projektu
2. Kopiuje pliki platformy (lista powyżej) z bieżącego repo jako template
3. Parametryzuje CLAUDE.md (zastępuje nazwę projektu placeholderem lub podaną nazwą)
4. Tworzy `requirements.txt` z tylko platformowymi zależnościami
5. Tworzy `.env.example` z kluczami bez wartości
6. Inicjalizuje pustą bazę `mrowisko.db` (schema-only przez db.py)
7. Opcjonalnie: `git init` + pierwszy commit

**Output:** gotowy katalog projektu z pełną platformą agentową Mrowisko, bez ERP.

---

## Kroki implementacji

### Krok 1: Lista plików platformy (manifest)
Plik `tools/mrowisko_platform_manifest.json` — lista plików/katalogów do kopiowania.
Oddzielony od kodu → łatwy do utrzymania.

### Krok 2: `tools/mrowisko_init.py`
- Wczytuje manifest
- Kopiuje pliki z src do output-dir
- Parametryzuje placeholdery
- Inicjalizuje DB
- `git init` opcjonalnie

### Krok 3: `requirements_platform.txt`
Wyciągnąć z requirements.txt tylko zależności platformy.

### Krok 4: Testy
`tests/test_mrowisko_init.py` — weryfikuje że output zawiera oczekiwane pliki i nie zawiera wykluczonych.

### Krok 5: Dokumentacja
Aktualizacja `SETUP_MACHINE.md` o sekcję "Nowy projekt od zera".

---

## Otwarte pytania do zatwierdzenia

1. **Testy platformy** — kopiować `tests/core/` i `tests/test_agent_bus.py`? (nie są ERP)
2. **documents/human/** — kopiować pusty szkielet (katalogi plans/reports/suggestions/workflows) czy pominąć?
3. **git init** — czy `mrowisko_init.py` ma automatycznie robić `git init` + pierwszy commit?
4. **CLAUDE.md** — zastąpić nazwę projektu `[PROJEKT_NAZWA]` placeholderem, czy pozostawić jako-jest z adnotacją?
5. **Docelowa lokalizacja** — czy nowy projekt ma być podkatalogiem obecnego, czy całkiem oddzielny katalog poza tym repo?

---

## Szacowany nakład

- Krok 1 (manifest): ~30 min
- Krok 2 (skrypt): ~2h
- Krok 3 (requirements): ~30 min
- Krok 4 (testy): ~1h
- Krok 5 (docs): ~30 min

Łącznie: ~4-5h roboczych
