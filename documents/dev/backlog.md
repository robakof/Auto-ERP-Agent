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

### [Workflow] ERP_VIEW_WORKFLOW + ERP_SCHEMA_PATTERNS — poprawki po sesji BI.Zamowienia

**Źródło:** agent_suggestions
**Sesja:** 2026-03-09 (BI.Zamowienia Faza 1–4)
**Wartość:** wysoka
**Pracochłonność:** mała

**ERP_VIEW_WORKFLOW.md:**
- Zasada pomijania pól (KLUCZOWA KOREKTA): pomiń TYLKO gdy (1) COUNT DISTINCT = 1 dla całej tabeli, (2) docs wprost "nieużywane", (3) dane wrażliwe, (4) czyste komponenty GID. W każdym innym przypadku — uwzględnij. Rzadko wypełnione, nieznane zastosowanie, mała wartość wg agenta — to NIE są powody do pominięcia.
- bi_verify: używaj tylko na końcu etapu lub przy zmianach wielu kolumn/JOINów. Przy drobnej poprawce (1 kolumna, literówka) — sql_query zamiast bi_verify.
- excel_read_rows: pierwsze przejście przez plan tylko z `--columns CDN_Pole,Uwzglednic,Komentarz_Usera`. Pełne kolumny tylko dla wierszy które tego wymagają.
- Numery dokumentów inline: NIGDY nie zgaduj formatu. Format numerów jest niejednorodny (spięte/niespięte faktury, różne typy dokumentów — różne wzorce). Zawsze: zapytaj bazę o rzeczywiste przykłady przez CDN.NazwaObiektu, pokaż userowi, poczekaj na potwierdzenie PRZED wpisaniem do SQL.

**ERP_VIEW_WORKFLOW.md — nazewnictwo:**
- Reguła: `{NazwaWidoku}` = nazwa tabeli źródłowej bez prefixu CDN (np. `ZamNag`, `KntKarty`). Nigdy polskie nazwy opisowe. Dotyczy katalogu, plików roboczych, views/, catalog.json.
- Istniejące widoki przemianowane: `Zamowienia/` → `ZamNag/`, `Kontrahenci/` → `KntKarty/`, views analogicznie. ✓ zrealizowane

**ERP_SCHEMA_PATTERNS.md:**
- `TrN_ZaNNumer` — link CDN.TraNag ↔ CDN.ZamNag (WHERE TrN_ZaNTyp = 960). Przydatne dla widoków łączących zamówienia z dokumentami WZ/FS/PZ.
- Format roku: ERP wyświetla rok jako YY lub YYYY zależnie od kontekstu — nie zakładaj formatu, weryfikuj przez NazwaObiektu.

---

### [Dev] Komendy powłoki — git i podgląd plików bez zatwierdzeń

**Źródło:** developer_suggestions
**Sesja:** 2026-03-09
**Wartość:** wysoka
**Pracochłonność:** mała

Dwa problemy blokujące płynną pracę:

1. `cd "ścieżka ze spacjami" && git commit` — hook blokuje jako "bare repository attack".
   Rozwiązanie: używać `git -C "ścieżka"` zamiast `cd && git`. Wpisać do DEVELOPER.md sekcja "Komendy powłoki".

2. Zbyt częste git operations w środku zadania (git mv per plik).
   Zasada: git tylko raz — na końcu zadania. Operacje na plikach przez zwykły `mv`/`cp`, nie `git mv`.
   Wpisać jako regułę do DEVELOPER.md.

3. `head -5 plik && echo && head -5 plik2` — hook blokuje. Używać narzędzia `Read` zamiast Bash dla podglądu.

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
