# Handoff do Prompt Engineer: documents/human/ — aktualizacja promptów

**Backlog:** #113 | **Status:** Developer done, PE pending

---

## Co zostało zrobione (Developer)

✓ Utworzona struktura `documents/human/` z podkatalogami:
  - backlog/, suggestions/, inbox/, logs/, plans/, reports/, data/

✓ Zaktualizowany `render.py`:
  - Dodana dataclass ViewConfig (obiekty zamiast słowników)
  - Domyślne ścieżki dla każdego view → documents/human/<typ>/
  - --output opcjonalny (override)
  - Przetestowane: backlog, suggestions, session-log ✓

---

## Co wymaga aktualizacji (PE)

### 1. Plik główny: CLAUDE.md

**Sekcja:** "Plany i analizy — zawsze do pliku" (linia ~162-166)

**Obecne:**
```markdown
### Plany i analizy — zawsze do pliku

Plany, analizy i propozycje zmian zapisuj do pliku .md (lub .xlsx gdy workflow tego wymaga),
nie wklejaj inline w czacie. Plik przetrwa sesję, inline zniknie przy kompresji kontekstu.
Pokaż użytkownikowi ścieżkę do pliku.
```

**Proponowane (PE dopracuje):**
```markdown
### Plany i analizy — zawsze do pliku

Plany, analizy i propozycje zmian zapisuj do pliku .md (lub .xlsx gdy workflow tego wymaga),
nie wklejaj inline w czacie. Plik przetrwa sesję, inline zniknie przy kompresji kontekstu.

**Przestrzeń robocza człowieka:** `documents/human/<typ>/`
- Plany, notatki → `plans/`
- Raporty, analizy → `reports/`
- Eksporty danych → `data/`
- Backlog/suggestions (przez render.py) → automatycznie do odpowiedniego podkatalogu

Pokaż użytkownikowi ścieżkę do pliku.
```

---

### 2. Prompty ról (7 plików)

#### A. DEVELOPER.md

**Sekcja:** "Tools" (linia ~119-120)

**Obecne:**
```bash
python tools/render.py suggestions --format md --status open --output tmp/suggestions.md
python tools/render.py backlog --format md --area Dev Arch --output tmp/backlog.md
```

**Proponowane:**
```bash
# Domyślne ścieżki (bez --output) → documents/human/<typ>/
python tools/render.py suggestions --format md --status open
python tools/render.py backlog --format md --area Dev Arch

# Lub z override dla plików roboczych:
python tools/render.py backlog --format md --output tmp/scratch.md
```

**Dodatkowo:** Dodać do <session_start> lub <tools>:
```markdown
Plany implementacyjne zapisuj do `documents/human/plans/`.
```

---

#### B. ERP_SPECIALIST.md

**Szukaj:** Wszystkie odwołania do `tmp/`, `views/`, zapisywania plików

**Przykłady gdzie może być:**
- Instrukcje zapisywania planów widoków BI → `documents/human/plans/`
- Instrukcje zapisywania raportów analizy → `documents/human/reports/`

**Akcja:** Znajdź i zamień zgodnie z wzorem:
- Plany → `documents/human/plans/`
- Raporty → `documents/human/reports/`

---

#### C. ANALYST.md

**Szukaj:** Instrukcje zapisywania raportów data quality, analiz

**Proponowane:**
- Raporty data quality → `documents/human/reports/`
- Analizy jakości danych → `documents/human/reports/`

---

#### D. ARCHITECT.md

**Szukaj:** Instrukcje zapisywania ADR, planów architektonicznych, audytów

**Proponowane:**
- Plany architektoniczne → `documents/human/plans/`
- ADR (Architecture Decision Records) → może zostać w `documents/architecture/` (to dokumentacja projektu, nie workspace człowieka)
- Raporty audytów → `documents/human/reports/`

**Trade-off:** ADR mogą być w documents/architecture/ (trwała dokumentacja) lub documents/human/plans/ (workspace). PE zdecyduje.

---

#### E. METODOLOG.md

**Szukaj:** Zapisywanie metodologicznych analiz, raportów

**Proponowane:**
- Analizy metodologiczne → `documents/human/reports/`
- Plany zmian procesowych → `documents/human/plans/`

---

#### F. PROMPT_ENGINEER.md

**Szukaj:** Plany refaktorów promptów, audyty

**Obecne (linia ~120, ~128):**
```markdown
1d. Zapisz plan refaktoru do pliku .md — kolejność, mapowanie, nowe pliki.
2e. Zapisz audit do `tmp/refactor_audit_{rola}.md` — ZAWSZE plik, niezależnie od skali.
```

**Proponowane:**
```markdown
1d. Zapisz plan refaktoru do pliku .md w `documents/human/plans/refactor_<temat>.md`
2e. Zapisz audit do `documents/human/reports/refactor_audit_{rola}.md` — ZAWSZE plik, niezależnie od skali.
```

---

### 3. Workflow files

**Lokalizacja:** `workflows/*.md`

**Akcja:** Znajdź wszystkie odwołania do:
- `tmp/` w kontekście zapisywania plików dla użytkownika
- `views/` (stara domyślna lokalizacja render.py)

**Zamień na:** `documents/human/<odpowiedni_typ>/`

**Przykładowe pliki workflow:**
- `workflows/bi_view_creation_workflow.md`
- `workflows/developer_workflow.md`
- Inne workflow z instrukcjami zapisywania plików

**Heurystyka:**
- Plik dla użytkownika (plan, raport, backlog) → `documents/human/`
- Plik roboczy agenta (scratch, debug) → `tmp/` (bez zmian)

---

### 4. Narzędzia (opcjonalnie — może być osobne zadanie)

**Narzędzia do rozważenia (niepriorytety, ale mapowanie):**

#### A. bi_plan_generate.py
- **Obecne:** Prawdopodobnie zapisuje do `solutions/bi/` lub `tmp/`
- **Proponowane:** `documents/human/plans/` (plany widoków BI dla użytkownika)

#### B. data_quality_report.py
- **Obecne:** Prawdopodobnie `tmp/` lub print do stdout
- **Proponowane:** `documents/human/reports/`

#### C. wycena_generate.py
- **Obecne:** Prawdopodobnie `tmp/` lub root
- **Proponowane:** `documents/human/data/`

#### D. offer_generator*.py
- **Obecne:** Prawdopodobnie `tmp/` lub root
- **Proponowane:** `documents/human/data/`

#### E. excel_export*.py, etykiety_export.py
- **Obecne:** Różnie
- **Proponowane:** `documents/human/data/`

**Rekomendacja:** PE może to przekazać z powrotem do Developera jako osobne zadanie backlog (backlog-add) po zakończeniu aktualizacji promptów.

---

## Sugerowany workflow PE

1. **Przeczytaj:** `documents/dev/exports_folder_implementation_plan.md` (pełny plan)
2. **Przeczytaj:** ten handoff
3. **Zacznij od CLAUDE.md** (plik chroniony, User approval)
4. **Batch prompty ról:** Przejrzyj wszystkie 7 plików w jednej sesji, zaproponuj zmiany łącznie
5. **Workflows:** Znajdź wszystkie odwołania, zamień na nowe ścieżki
6. **Narzędzia (opcja):** Jeśli czas pozwala — zaktualizuj też narzędzia. Jeśli nie — backlog-add

---

## Pytania otwarte dla PE

1. **ADR (Architecture Decision Records):**
   - Zostawić w `documents/architecture/` (trwała dokumentacja projektu)?
   - Czy przenieść do `documents/human/plans/` (workspace człowieka)?

2. **Research results:**
   - Obecne: `documents/<rola>/research_results_*.md`
   - Czy zostawić tam czy przenieść do `documents/human/reports/`?
   - Trade-off: research_results to trwała dokumentacja techniczna, nie workspace

3. **tmp/ convention:**
   - Czy warto dodać regułę: "tmp/ = tylko pliki robocze agenta, nie dla człowieka"?
   - Czy zostawić elastyczność?

---

## Test plan dla PE (po zmianach)

1. Uruchom dowolną sesję agenta (np. Developer)
2. Poproś o backlog → sprawdź czy trafia do `documents/human/backlog/`
3. Poproś o plan implementacyjny → sprawdź czy agent zapisuje do `documents/human/plans/`
4. Poproś o raport → sprawdź czy trafia do `documents/human/reports/`

---

**Status:** Developer done ✓, PE pending ⏳

**Lokalizacja tego handoffu:** `documents/human/plans/pe_handoff_human_folder.md`
