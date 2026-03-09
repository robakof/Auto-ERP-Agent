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

### [Prompt] Agent edytuje pliki dokumentacji bez jawnej zgody

**Źródło:** agent_suggestions
**Sesja:** 2026-03-08 (BI.Kontrahenci)
**Wartość:** wysoka
**Pracochłonność:** mała

Agent zmodyfikował plik z wytycznymi mimo zakazu w DEVELOPER.md.
Lista plików chronionych dodana do CLAUDE.md i AGENT.md (sesja 2026-03-09).
Otwarte: czy sam zakaz tekstowy wystarczy, czy potrzebny mechanizm weryfikowalny (np. test CI).

---

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

### [Narzędzia] bi_discovery.py — automatyczny raport discovery

**Źródło:** agent_suggestions
**Sesja:** 2026-03-08
**Wartość:** średnia
**Pracochłonność:** średnia

Faza discovery widoku BI to zawsze ~10 tych samych zapytań.
`bi_discovery.py CDN.NazwaTabeli [--pk ...] [--filter ...]` zwracałoby raport:
baseline COUNT, pola stałe (COUNT DISTINCT=1), klasyfikacja dat, enumeracje.

---

## Archiwum

*(przeniesione z agent_reflections.md — zrealizowane)*

Pozycje #1–#10 z sesji 2026-03-08: zrealizowane, szczegóły w `agent_reflections.md`.

**[P1] excel_export_bi.py — brak --file** — zrealizowane 2026-03-09
**[P2] sql_query.py — --count-only + --quiet** — zrealizowane 2026-03-09
**[P3] bi_verify.py** — zrealizowane 2026-03-09
**[P4] solutions_save_view.py** — zrealizowane 2026-03-09
