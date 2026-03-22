# Plan implementacji: documents/human/ — przestrzeń robocza człowieka

**Backlog:** #113 | **Wartość:** średnia | **Effort:** średnia

**Koncepcja:** Folder `human/` jako dedykowana przestrzeń robocza dla człowieka — wszystkie pliki generowane przez agentów dla użytkownika (backlog, sugestie, logi, plany, raporty, notatki, eksporty danych).

---

## Analiza obecnego stanu

### Obecne lokalizacje eksportów

1. **tmp/** (68 plików .md)
   - Logi sesji, wiadomości agent_bus, sugestie, backlogi, analizy
   - Mieszanka tymczasowych i wartościowych plików
   - Problem: trudno odróżnić co jest ważne, co można usunąć

2. **views/** (domyślna lokalizacja render.py)
   - Folder nie istnieje lub pusty
   - Nie używany w praktyce (agenci zawsze podają `--output tmp/...`)

3. **Root projektu**
   - Tylko INSTALL.md, README.md (należą tu)
   - Nie śmieci

### Narzędzia zapisujące pliki

#### A. Używane przez agentów (do prezentacji użytkownikowi):
- **render.py** — backlog, suggestions, inbox, session-log, messages → `views/<view>.<ext>`
- **data_quality_report.py** — raporty jakości danych
- **bi_plan_generate.py** — plany widoków BI

#### B. Używane przez użytkownika bezpośrednio:
- **wycena_generate.py** — wyceny dla klientów
- **offer_generator.py**, **offer_generator_3x3.py** — oferty
- **excel_export.py**, **excel_export_bi.py** — eksporty do Excel
- **etykiety_export.py** — etykiety JAS

#### C. Infrastrukturalne (nie dotyczą eksportów dla użytkownika):
- agent_bus_cli.py, git_commit.py, session_init.py
- setup_machine.py, solutions_save.py
- docs_build_index.py

---

## Proponowana struktura

```
documents/
└── human/
    ├── backlog/           # render.py backlog
    ├── suggestions/       # render.py suggestions
    ├── inbox/             # wiadomości do człowieka (flagi, eskalacje)
    ├── logs/              # render.py session-log
    ├── plans/             # bi_plan_generate.py, plany architektoniczne, notatki
    ├── reports/           # data_quality_report.py, analizy
    └── data/              # excel_export*.py, offers, pricing, etykiety
```

**Pytanie do użytkownika:** Czy taka struktura jest OK, czy wolisz inną organizację podkatalogów?

---

## Konwencja nazewnictwa

### Wzór dla render.py:
- **Backlog:** `backlog_<status>_<area>.md` lub `backlog.md` (nadpisywany)
- **Suggestions:** `suggestions_<status>_<author>.md` lub `suggestions.md`
- **Logs:** `session_log_<role>_<timestamp>.md` (chroniony, nie nadpisywany)
- **Inbox:** `inbox_<role>_<timestamp>.md`

### Wzór dla innych narzędzi:
- **Plans:** `<temat>_plan_<timestamp>.md` lub `<temat>_plan.md`
- **Reports:** `<nazwa>_report_<timestamp>.md`
- **Data exports:** `<nazwa>_<timestamp>.<ext>`

**Zasada:**
- Pliki nadpisywalne (ostatni stan) → bez timestamp
- Pliki chronologiczne (historia) → z timestamp

---

## Zakres zmian

### Etap 1: Utworzenie struktury folderów

```bash
mkdir -p documents/human/{backlog,suggestions,inbox,logs,plans,reports,data}
```

Dodać `.gitkeep` w każdym podkatalogu żeby git je trackował.

### Etap 2: Aktualizacja narzędzi

#### render.py
- Zmienić domyślną ścieżkę `views/` → `documents/human/<typ>/`
- Mapping:
  - backlog → `documents/human/backlog/`
  - suggestions → `documents/human/suggestions/`
  - inbox → `documents/human/inbox/`
  - session-log → `documents/human/logs/`
  - messages → `documents/human/inbox/`
  - session-trace → `documents/human/logs/`

**Zmiana w kodzie:**
```python
# Stare (linia 159):
output = Path(args.output) if args.output else Path("views") / f"{view}.{ext}"

# Nowe:
default_paths = {
    "backlog": "documents/human/backlog",
    "suggestions": "documents/human/suggestions",
    "inbox": "documents/human/inbox",
    "session-log": "documents/human/logs",
    "messages": "documents/human/inbox",
    "session-trace": "documents/human/logs",
}
output = Path(args.output) if args.output else Path(default_paths[view]) / f"{view}.{ext}"
```

#### Inne narzędzia (mapowanie dla PE — implementacja później):
- **bi_plan_generate.py** → `documents/human/plans/`
- **data_quality_report.py** → `documents/human/reports/`
- **wycena_generate.py** → `documents/human/data/`
- **offer_generator*.py** → `documents/human/data/`
- **excel_export*.py**, **etykiety_export.py** → `documents/human/data/`

**Priorytet:** Najpierw render.py (używany najczęściej), mapowanie reszty dostarczę PE.

### Etap 3: Aktualizacja promptów ról

Pliki do aktualizacji (7 + CLAUDE.md + workflows):

#### CLAUDE.md
Linia 162-166:
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

#### DEVELOPER.md
Linia 119-120:
```bash
# Stare:
python tools/render.py suggestions --format md --status open --output tmp/suggestions.md
python tools/render.py backlog --format md --area Dev Arch --output tmp/backlog.md

# Nowe (bez --output, używa domyślnej lokalizacji):
python tools/render.py suggestions --format md --status open
python tools/render.py backlog --format md --area Dev Arch
```

#### Inne role (ERP_SPECIALIST, ANALYST, ARCHITECT, METODOLOG, PROMPT_ENGINEER)
- Usunąć `--output tmp/` z przykładów render.py
- Dodać przypomnienie: "Plany zapisuj do `documents/human/plans/`, raporty do `documents/human/reports/`"

**Przekazuję mapowanie do PE** — obróbka promptów ról przez Prompt Engineera.

#### Workflows (wszystkie `workflows/*.md`)
- Wyszukać wszystkie odwołania do `tmp/` i zastąpić `documents/human/<typ>/`

**Przekazuję mapowanie do PE** — obróbka workflow przez Prompt Engineera.

### Etap 4: Backward compatibility — migracja tmp/

**Opcje:**

**A. Zostaw tmp/ jak jest, używaj documents/exports/ tylko dla nowych plików**
- ✓ Bezpieczne, zero ryzyka
- ✗ Bałagan pozostaje

**B. Ręczna migracja wartościowych plików z tmp/ do exports/**
- ✓ Kontrolowana
- ✗ Czasochłonne, wymaga decyzji per plik

**C. Dodaj `tmp/` do .gitignore, zostaw jako folder tymczasowy**
- ✓ Proste, czyste rozróżnienie: tmp = truly temporary, human = wartościowe
- ✗ Istniejące pliki w tmp/ nie będą trackowane (ale można je przenieść przed dodaniem do .gitignore)

**Decyzja użytkownika: Opcja B (zostaw tmp/ jak jest).**
- tmp/ pozostaje w repo, tracked
- Od teraz: nowe pliki dla człowieka → `documents/human/`, tmp/ dla roboczych artefaktów agenta

---

## Walidacja przed implementacją

### Pytania do użytkownika:

1. **Czy zgadzasz się na strukturę (6 podkatalogów: backlog, suggestions, logs, plans, reports, data)?**
2. **Czy render.py powinien używać domyślnych ścieżek (bez --output) czy zostawić --output jako obowiązkowy?**
   - Rekomendacja: domyślne ścieżki, --output opcjonalny (override)
3. **Co zrobić z tmp/?**
   - A: Zostawić jak jest
   - B: Migracja ręczna wartościowych plików
   - C: Dodać do .gitignore (+ opcjonalna migracja przed)
4. **Czy aktualizować inne narzędzia (offer_generator, wycena_generate, etc.) w tej samej sesji czy odłożyć?**
   - Rekomendacja: Tylko render.py teraz, reszta w osobnym zadaniu (backlog)

---

## Estymacja pracochłonności

| Etap | Pracochłonność | Ryzyko |
|------|----------------|--------|
| 1. Utworzenie folderów | 5 min | Niskie |
| 2. Aktualizacja render.py | 15 min | Niskie |
| 3. Aktualizacja promptów (8 plików) | 30 min | Średnie (pliki chronione) |
| 4. Workflow files | 20 min | Niskie |
| 5. Migracja tmp/ (opcjonalnie) | 30-60 min | Niskie |
| **Razem** | **70-130 min** | **Niskie-średnie** |

---

## Test plan

1. **Test render.py:**
   - Uruchom bez --output: `py tools/render.py backlog --format md --status planned`
   - Sprawdź czy plik ląduje w `documents/human/backlog/backlog.md`
   - Uruchom z --output: `py tools/render.py backlog --format md --output custom/path.md`
   - Sprawdź czy override działa

2. **Test w sesji agenta:**
   - Wywołaj dowolną rolę (np. Developer)
   - Poproś o wygenerowanie backlogu/suggestions
   - Sprawdź czy agent używa nowej lokalizacji

3. **Test Obsidian:**
   - Podłącz `documents/human/` jako vault w Obsidian
   - Sprawdź czy pliki .md są czytelne
   - Sprawdź czy nawigacja działa

---

## Zakres prac — podział Developer / PE

### Developer (ta sesja):
1. ✓ Utworzenie struktury `documents/human/`
2. ✓ Aktualizacja `render.py` (kod + domyślne ścieżki)
3. ✓ Test render.py
4. Mapowanie wszystkich narzędzi zapisujących pliki → przekazanie do PE
5. Mapowanie wszystkich miejsc w promptach ról wymagających aktualizacji → przekazanie do PE

### Prompt Engineer (osobna sesja):
1. Aktualizacja CLAUDE.md (plik chroniony)
2. Aktualizacja promptów ról (7 plików chronionych)
3. Aktualizacja workflow files
4. Aktualizacja instrukcji w narzędziach (jeśli są hardcoded prompty w kodzie)

---

## Następne kroki (po zatwierdzeniu)

1. ✓ Uzyskaj odpowiedzi na pytania walidacyjne
2. Utwórz strukturę folderów
3. Zaktualizuj render.py
4. Zaktualizuj CLAUDE.md (plik chroniony — wymaga zgody)
5. Zaktualizuj prompty ról (pliki chronione — wymaga zgody per plik lub zbiorczej)
6. Zaktualizuj workflow files
7. Przetestuj rozwiązanie
8. Migracja tmp/ (jeśli opcja B lub C)
9. Commit zmian
10. Zadanie done → backlog-update #113 --status done

---

**Lokalizacja planu:** `documents/dev/exports_folder_implementation_plan.md`
