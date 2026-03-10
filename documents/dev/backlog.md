# Backlog developerski

Przetworzone i priorytetyzowane zadania developerskie.
Źródło: `agent_suggestions.md` + techniczne wątki z `developer_suggestions.md`.

Zarządza: Developer.

## Format wpisu

```
### [P{n}] Tytuł

**Źródło:** agent_suggestions | developer_suggestions
**Sesja:** data
**Wartość:** wysoka | średnia | niska
**Pracochłonność:** mała | średnia | duża

Opis problemu i propozycja rozwiązania.
```

---

## Aktywne

### [Arch] Sygnatury narzędzi powielone w wielu miejscach

**Źródło:** developer_suggestions
**Sesja:** 2026-03-08
**Wartość:** średnia
**Pracochłonność:** mała (opcja 3) / duża (opcja 1)

Nazwy i sygnatury narzędzi zapisane w AGENT.md, ERP_VIEW_WORKFLOW.md,
ERP_COLUMNS_WORKFLOW.md, ERP_FILTERS_WORKFLOW.md i docstringach tools/*.py.

Opcje:
1. gen_docs.py generuje sekcję Narzędzia z docstringów (eliminuje problem u źródła)
2. Jeden plik referencyjny TOOLS.md + dyscyplina
3. Test CI sprawdzający czy narzędzia w AGENT.md istnieją jako pliki w tools/

---

## Archiwum

*(przeniesione z agent_reflections.md — zrealizowane)*

Pozycje #1–#10 z sesji 2026-03-08: zrealizowane, szczegóły w `agent_reflections.md`.

**[P1] excel_export_bi.py — brak --file** — zrealizowane 2026-03-09
**[P2] sql_query.py — --count-only + --quiet** — zrealizowane 2026-03-09
**[P3] bi_verify.py** — zrealizowane 2026-03-09
**[P4] solutions_save_view.py** — zrealizowane 2026-03-09
**[Prompt] Agent edytuje pliki dokumentacji bez zgody** — zrealizowane przez Metodologa
**[Narzędzia] bi_discovery.py** — zrealizowane 2026-03-09
**[Dev] Komendy powłoki** — zrealizowane 2026-03-09 (git -C, mv zamiast git mv, Read zamiast head/cat)
**[Workflow] ERP_VIEW_WORKFLOW + ERP_SCHEMA_PATTERNS** — zrealizowane 2026-03-10 (zasada pominięcia pola, bi_verify/sql_query, excel_read_rows, TrN_ZaNNumer, format roku przez NazwaObiektu)
