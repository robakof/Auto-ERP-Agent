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

### [Arch] Separacja pamięci między agentami wykonawczymi

**Źródło:** developer_suggestions
**Sesja:** 2026-03-10
**Wartość:** wysoka
**Pracochłonność:** średnia

Pojawienie się Analityka Danych obok Agenta ERP ujawniło dwa problemy:

**1. Nazwa poziomu "Agent" jest zbyt wąska.**
Mamy wiele ról wykonawczych (ERP, Analityk, potencjalnie więcej).
Poziom powinien mieć nazwę ogólną (np. "Executor" lub "Agenci").
Dotyczy: CLAUDE.md (tabela ról), METHODOLOGY.md (tabela poziomów), DEVELOPER.md.

**2. Współdzielona pamięć refleksji jest błędna.**
Obecny stan: Analityk i Agent ERP dzielą `agent_suggestions.md`.
Problem: różne role mają różne wzorce obserwacji — mieszanie zaszumi plik.
Każdy agent powinien mieć własny plik suggestions (np. `analyst_suggestions.md`).

**3. Progress log analityka — otwarte pytanie.**
Agent ERP: progress log na poziomie projektu (widok, filtr, kolumna).
Analityk: co jest jednostką pracy? Per zakres (widok/tabela)? Sesja?
Wymaga decyzji przed wdrożeniem.

**Uwaga:** punkty 1 i 2 mają wymiar metodologiczny — warto rozważyć eskalację
do sesji Metodologa przed wdrożeniem. Punkt 3 może być rozwiązany na poziomie Dev.

---

### [Dev] Informacja o kontekście na końcu każdej wiadomości

**Źródło:** developer_suggestions
**Sesja:** 2026-03-10
**Wartość:** wysoka
**Pracochłonność:** mała

Agent powinien kończyć każdą wiadomość informacją o aktualnym zużyciu kontekstu
(np. "Kontekst: ~54%"). Cel: świadomość co zużywa kontekst, sygnał do optymalizacji,
bezpieczeństwo przy długich sesjach. Wpisać jako regułę do DEVELOPER.md.

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
