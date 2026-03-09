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

### [Docs] docs_search -- domyślny limit=20 ucina wyniki bez ostrzeżenia

**Źródło:** agent_suggestions
**Sesja:** 2026-03-09 (BI.Zamowienia)
**Wartość:** wysoka
**Pracochłonność:** mała

Agent przeszukał CDN.ZamNag, dostał 20 wyników z 187 kolumn i zbudował plan na niepełnej wiedzy.
Brak sygnału że wynik jest ucięty — agent wnioskuje "to wszystko".

Rozwiązanie: dodać `"truncated": true` do odpowiedzi gdy wynik == limit.
Analogicznie do istniejącego pola `truncated` w sql_query.py.

---

### [Docs] docs_search --useful-only zwraca 0 wyników bez ostrzeżenia

**Źródło:** developer_suggestions
**Sesja:** 2026-03-09
**Wartość:** wysoka
**Pracochłonność:** mała

`is_useful` wypełnione tylko dla kilku tabel. Agent używający `--useful-only` na nieoznaczonej
tabeli dostaje 0 wyników i może błędnie wnioskować "brak dokumentacji".

Rozwiązanie (opcja 3): gdy `useful_only=True` i wynik pusty → dodaj pole
`"warning": "0 wyników z --useful-only; spróbuj bez flagi"` do odpowiedzi JSON.

Dotyczy: `docs_search.py` + testy.

---

### [Narzędzia] bi_plan_generate.py — generowanie planu Excel z pliku SQL metadanych

**Źródło:** agent_suggestions
**Sesja:** 2026-03-09 (BI.Zamowienia)
**Wartość:** średnia
**Pracochłonność:** mała

Agent próbował generować plan Excel przez UNION ALL z 202 wierszami — błąd przy polskich
znakach i myślnikach. Narzędzie `bi_plan_generate.py --src plan_src.sql --output plan.xlsx`
czytałoby plik SQL metadanych (SELECT + stałe wartości) i generowało Excel przez openpyxl.
Eliminuje powtarzający się wzorzec przy każdym nowym widoku BI.

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
