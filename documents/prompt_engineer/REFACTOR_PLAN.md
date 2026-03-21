# Plan refaktoru promptów — PE Faza 1

Data: 2026-03-18
Status: in_progress

---

## Cel

Przepisać wszystkie prompty ról do jednolitej konwencji (`PROMPT_CONVENTION.md`).
Usunąć duplikacje, wydzielić workflow i domain packi, podnieść salience reguł krytycznych.

---

## Workflow PE przy dużym refaktorze

Per każdy plik:

1. **Archiwizacja** — kopia oryginału do `archive_pre_refactor/` ✓ zrobione
2. **Ekstrakcja reguł** — lista wszystkich instrukcji z oryginału
3. **Mapowanie** — każda reguła → dokąd trafia lub dlaczego usunięta
4. **Refaktor** — przepisanie do konwencji (XML tags, stała kolejność sekcji)
5. **Audit** — przejście przez mapowanie, potwierdzenie braku zgubień
6. **Commit** — opis zmian + mapowanie

Artefakt audytu: `tmp/refactor_audit_{rola}.md`

---

## Kolejność

| # | Dokument | Linie | Typ zmiany | Nowe pliki | Status |
|---|---|---|---|---|---|
| 1 | `PROMPT_ENGINEER.md` | 270→140 | Refaktor do konwencji | - | ✓ done |
| 2 | `DEVELOPER.md` | 437→130 | Refaktor + rozbicie | `developer_workflow.md`, `CODE_STANDARDS.md` | ✓ done |
| 3 | `ERP_SPECIALIST.md` | 273→180 | Refaktor do konwencji | - | ✓ done |
| 4 | `ANALYST.md` | 217→150 | Refaktor do konwencji | - | ✓ done |
| 5 | `METHODOLOGY.md` | 367→130 | Esej → prompt + teoria | `METHODOLOGY_THEORY.md` | ✓ done |
| 6 | `CLAUDE.md` | ~200 | Porządkowanie hierarchii | - | planned (ostatni) |

---

## DEVELOPER.md — plan rozbicia (najwyższy priorytet)

### Problem

437 linii. Miesza cztery warstwy:
- Rola developera (reguły, zakres, narzędzia)
- Workflow inicjalizacji projektu (Phase 1-2)
- Workflow implementacji (Phase 3)
- Domain pack (code quality, security, naming)

### Docelowa struktura

```
documents/dev/DEVELOPER.md              ← prompt roli (~100-120 linii)
  routing do:
  ├─ workflows/developer_workflow.md    ← Phase 1-3 jako fazy z gates
  └─ documents/dev/CODE_STANDARDS.md   ← code quality + security (domain pack)
```

### DEVELOPER.md — co zostaje w roli

- Opening statement + metadata
- `<mission>` — miary sukcesu developera
- `<scope>` — w zakresie / poza zakresem
- `<critical_rules>` — obecne "Najważniejsze zasady" (10 reguł, skonsolidowane do 8)
- `<session_start>` — backlog, inbox, suggestions, human inbox
- `<tools>` — routing: które pliki ładować per typ zadania
- `<escalation>` — kiedy do Metodologa
- `<end_of_turn_checklist>`

### workflows/developer_workflow.md — co wydzielamy

- Skala zadania (małe/średnie/duże) → routing
- Phase 1: Dokumentacja projektowa (PRD, Techstack, Architecture)
- Phase 2: Planowanie implementacji (eksperymenty, plan impl.)
- Phase 3: Implementacja (TDD, commit flow, feedback loop)
- Suggestions workflow (odczyt, ocena, backlog)
- Zamknięcie sesji (arch_check, commit)

Format: fazy z gates, forbidden, exit conditions (jak bi_view_creation_workflow.md).

### documents/dev/CODE_STANDARDS.md — co wydzielamy

- Nazewnictwo (opisowe, bez temporal, konwencje językowe)
- Struktura funkcji (5-20 linii, jedna odpowiedzialność)
- Modularność (DRY, SRP, loose coupling)
- Projektowanie baz danych (5 INSERT-ów przed CREATE TABLE)
- Samodokumentujący się kod (type hints, docstrings)
- Error handling, bezpieczeństwo, logowanie

To jest domain pack — ładowany gdy developer pisze kod, nie przy review suggestions.

### Reguły do usunięcia (duplikacja z CLAUDE.md)

- "Komendy powłoki" → już w CLAUDE.md sekcja "Komendy powłoki"
- "Git commit przez git_commit.py" → już w CLAUDE.md
- "Brak emotek" → już w CLAUDE.md "Styl komunikacji"
- "Edycja dużych plików SQL" → specyficzne dla ERP, nie developer

---

## ERP_SPECIALIST.md — plan refaktoru

### Problem
Dobrze napisany merytorycznie, ale format niezgodny z konwencją (Markdown headers,
brak XML tags, brak mission/scope/critical_rules jako osobnych sekcji).

### Zmiana
Przepisanie do szablonu z konwencji. Treść merytoryczna bez zmian.
Sekcja "Narzędzia" jest długa (~70 linii) — zostaje, bo to core tego agenta.

---

## ANALYST.md — plan refaktoru

### Problem
Jak ERP Specialist — dobra treść, zły format.

### Zmiana
Przepisanie do szablonu. Krok 2 (Recenzja planu) odsyła do workflow —
to jest poprawne, zostaje.

---

## METHODOLOGY.md — plan refaktoru

### Problem
Esej pisany dla człowieka i agenta w jednym dokumencie.
Agent Metodolog musi wyłowić swoje instrukcje z tekstu filozoficznego.

### Zmiana
Wydzielić prompt operacyjny Metodologa (do konwencji) z essentials.
Reszta (teoria, uzasadnienia, hipotezy) może zostać jako osobny
dokument referencyjny `documents/methodology/METHODOLOGY_THEORY.md`
— ładowany opcjonalnie.

---

## CLAUDE.md — plan (ostatni)

### Problem
Rośnie bez hierarchii ważności. Wszystko na jednym poziomie.

### Zmiana (po refaktorze ról)
- Wydzielić sekcję `critical_rules` na górze (eskalacja, pliki chronione)
- Reszta jako operacyjne sekcje tematyczne
- Usunąć duplikacje z dokumentów ról
- Dodać regułę: plany zawsze do pliku .md

Robimy na końcu bo dopiero po refaktorze ról wiemy co jest naprawdę shared.

---

## Archiwum

Kopie oryginałów: `documents/prompt_engineer/archive_pre_refactor/`
- DEVELOPER.md ✓
- ERP_SPECIALIST.md ✓
- ANALYST.md ✓
- METHODOLOGY.md ✓
- CLAUDE.md ✓
