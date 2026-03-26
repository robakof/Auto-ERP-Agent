# Audit: tools + configs vs prompty ról

Data: 2026-03-26
Backlog: #191
Autor: Prompt Engineer

---

## TL;DR

- **65 narzędzi** w `tools/`, z czego **25 referencowanych** w promptach ról, **40 nie**
- **7 z 9 workflow** nie jest referencowanych w prompcie roli-ownera
- Większość niereferencowanych narzędzi to migracje, UI/apps lub infrastruktura — poprawnie nieobecne
- **Realne luki (wymagają działania): 7 workflow + 3-5 narzędzi**

---

## Kategoria 1: Narzędzia poprawnie referencowane (25)

Wymienione w promptach ról z poprawnym scope (allowed/disallowed):

| Narzędzie | Gdzie referencowane |
|---|---|
| agent_bus_cli | CLAUDE.md + wszystkie role |
| git_commit | CLAUDE.md + wszystkie role |
| conversation_search | CLAUDE.md, DEV, ARCH, METODOLOG, PE |
| session_init | CLAUDE.md, DEV |
| render | CLAUDE.md, DEV, ARCH |
| sql_query | ERP, DEV |
| bi_discovery | ERP, DEV |
| bi_verify | ERP |
| bi_plan_generate | ERP |
| bi_search (search_bi) | ERP, DEV, PE (disallowed) |
| docs_search | ERP, ANALYST, DEV, METODOLOG (disallowed) |
| windows_search | ERP, ANALYST (disallowed) |
| windows_update | ERP, ANALYST (disallowed) |
| excel_export | ERP, ANALYST (disallowed), DEV, PE (disallowed) |
| excel_export_bi | ERP, ANALYST (disallowed), DEV, PE (disallowed) |
| excel_read_stats | ERP |
| excel_read_rows | ERP, ANALYST, DEV, PE (disallowed) |
| solutions_search | ERP, ANALYST (disallowed), METODOLOG (disallowed) |
| solutions_save | ERP |
| solutions_save_view | ERP |
| data_quality_init | ANALYST, ERP (disallowed), DEV, METODOLOG (disallowed), PE (disallowed) |
| data_quality_query | ANALYST, DEV, METODOLOG (disallowed) |
| data_quality_records | ANALYST, DEV, METODOLOG (disallowed) |
| data_quality_report | ANALYST, DEV, METODOLOG (disallowed) |
| data_quality_save | ANALYST, DEV, METODOLOG (disallowed) |

**Status:** ✓ OK, brak akcji.

---

## Kategoria 2: Narzędzia poprawnie NIEREFERENCOWANE (31)

### Migracje jednorazowe (10)
Skrypty uruchamiane raz. Nie potrzebują referencji w promptach.

- migrate_backlog
- migrate_logs
- migrate_methodology_backlog
- migrate_state
- migrate_suggestions
- migration_add_handoff_type
- migration_m4_2_2_check_constraints
- migration_m5_1_message_title
- migration_workflow_tracking
- data_cleanup_m4_3

### UI / Aplikacje ludzkie (17)
Narzędzia z interfejsem graficznym lub generatory dokumentów — uruchamiane przez człowieka, nie agentów.

- etykiety_export, etykiety_ui
- export_ui
- offer_app_3x3, offer_data, offer_generator, offer_generator_3x3
- offer_pdf, offer_pdf_3x3, offer_ui, offer_ui_3x3
- photo_preprocess, photo_preprocess_ui, photo_workflow_ui
- wycena_generate, wycena_ui
- app

### Infrastruktura / biblioteki (4)
Nie wywoływane bezpośrednio przez agentów.

- agent_bus_server (serwer, nie CLI)
- db (moduł bazodanowy)
- docs_build_index (build index)
- jsonl_parser (parser utility)

**Status:** ✓ OK, brak akcji.

---

## Kategoria 3: LUKI — narzędzia wymagające oceny (5)

Narzędzia które mogą być przydatne agentom ale nie są wymienione w żadnym prompcie:

| Narzędzie | Potencjalny owner | Uwagi |
|---|---|---|
| **arch_check** | Developer, Architect | Sprawdza spójność ścieżek/dokumentacji. Częściowo referencowane w workflow_developer (sekcja Zamknięcie) ale NIE w DEVELOPER.md ani ARCHITECT.md |
| **bi_catalog_add** | ERP Specialist | Dodaje widok do katalogu BI. Brak w ERP_SPECIALIST.md |
| **enum_audit** | Architect, Analyst | Audyt enumów. Brak w jakimkolwiek prompcie |
| **excel_write_cells** | ERP Specialist, Analyst | Zapis do Excel. Brak w promptach (read jest, write nie) |
| **verify** | Developer | Weryfikacja — wymaga sprawdzenia co robi |
| **setup_machine** | Developer | Setup środowiska — jednorazowy? |
| **mrowisko_runner** | Developer | Runner agentów — wymaga sprawdzenia |
| **bot_stop** | Developer | Zatrzymanie bota — operacyjne |

**Akcja:** Sprawdzić co robią verify, setup_machine, mrowisko_runner. Zdecydować czy dodać do promptów.

---

## Kategoria 4: LUKI — workflow niereferencowane w promptach ról (7)

Każdy workflow ma owner_role — ale 7 z 9 NIE jest wymienionych w prompcie tego ownera.

| Workflow | Owner | Referencja w prompcie ownera? |
|---|---|---|
| workflow_bi_view_creation | erp_specialist | ✓ ERP_SPECIALIST.md |
| workflow_developer | developer | ✓ DEVELOPER.md |
| **workflow_code_review** | architect | ✗ brak w ARCHITECT.md |
| **workflow_plan_review** | architect | ✗ brak w ARCHITECT.md |
| **workflow_convention_creation** | architect/PE | ✗ brak w obu |
| **workflow_prompt_refactor** | prompt_engineer | ✗ brak w PROMPT_ENGINEER.md |
| **workflow_research_prompt_creation** | prompt_engineer | ✗ brak w PROMPT_ENGINEER.md |
| **workflow_suggestions_processing** | architect (triage) / PE (realizacja) | ✗ brak w obu |
| **workflow_workflow_creation** | PE | ✗ brak w PROMPT_ENGINEER.md |

**Skutek:** Agent rozpoczynając workflow gate ("czy istnieje workflow?") nie wie o tych workflow bo nie są wymienione w jego prompcie. Musi polegać na Glob/grep zamiast mieć je w kontekście.

**Akcja wymagana:** Dodać referencje do workflow w promptach odpowiednich ról.

---

## Kategoria 5: Config

| Plik | Owner | Referencja |
|---|---|---|
| session_init_config.json | PE | ✓ PROMPT_ENGINEER.md (linia 182) |

**Status:** ✓ OK.

---

## Rekomendacje

### P1: Workflow → prompty ról (7 luk, wysoki priorytet)

Dodać sekcję "Available workflows" lub rozszerzyć `<tools>` w promptach:

1. **ARCHITECT.md** — dodać: workflow_code_review, workflow_plan_review, workflow_suggestions_processing (triage), workflow_convention_creation
2. **PROMPT_ENGINEER.md** — dodać: workflow_prompt_refactor, workflow_research_prompt_creation, workflow_suggestions_processing (realizacja), workflow_workflow_creation, workflow_convention_creation
3. **DEVELOPER.md** — dodać: workflow_plan_review (jako participant), workflow_code_review (jako participant)

### P2: Narzędzia → prompty ról (3-5 luk, średni priorytet)

Po weryfikacji co robią:
- arch_check → DEVELOPER.md + ARCHITECT.md
- bi_catalog_add → ERP_SPECIALIST.md (jeśli aktywne)
- excel_write_cells → ERP_SPECIALIST.md lub ANALYST.md

### P3: Porządki (niski priorytet)

- verify, setup_machine — one-time setup, nie potrzebują referencji
- mrowisko_runner — infrastruktura, Developer zna z kodu
- bot_stop — operacyjne, niche
- Rozważyć czy migracje jednorazowe powinny trafić do archive/

---

## Realizacja

### P1: Workflow → prompty ról (2026-03-26) ✓

- **ARCHITECT.md** — dodano: workflow_plan_review, workflow_code_review, workflow_suggestions_processing, workflow_convention_creation
- **DEVELOPER.md** — dodano jako participant: workflow_plan_review, workflow_code_review
- **PROMPT_ENGINEER.md** — dodano: workflow_research_prompt_creation, workflow_prompt_refactor, workflow_convention_creation, workflow_workflow_creation, workflow_suggestions_processing

### P2: Narzędzia → prompty ról (2026-03-26) ✓

- **ERP_SPECIALIST.md** — dodano: bi_catalog_add, excel_write_cells
- **ARCHITECT.md** — dodano: arch_check
- verify, setup_machine, mrowisko_runner, bot_stop — ocenione, pominięte (one-time/infra/operacyjne)
