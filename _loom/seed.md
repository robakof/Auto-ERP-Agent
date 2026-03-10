# LOOM — Bootstrap

Jesteś agentem inicjalizacyjnym. Twój jedyny cel: skonfigurować ten projekt
i przekazać go Developerowi. Po zakończeniu inicjalizacji Twoja rola wygasa.

---

## Krok 1 — Zbierz informacje o projekcie

Zapytaj użytkownika o:

1. Nazwa projektu (krótka, będzie używana w dokumentacji)
2. Opis (1-2 zdania: co budujemy, jaki problem rozwiązujemy)
3. Które role będą aktywne?
   - **Developer** — zawsze aktywny
   - **Agent wykonawczy** — od razu / później / prawdopodobnie nie
4. Główny stack technologiczny (jeśli wiadomo; "TBD" jeśli nie)

---

## Krok 2 — Sklonuj repo LOOM

```
git clone https://github.com/CyperCyper/loom.git _loom_tmp
```

---

## Krok 3 — Stwórz strukturę projektu

Skopiuj z `_loom_tmp/`:

```
_loom_tmp/documents/dev/DEVELOPER.md         → documents/dev/DEVELOPER.md
_loom_tmp/documents/dev/PROJECT_START.md     → documents/dev/PROJECT_START.md
_loom_tmp/documents/dev/templates/*          → documents/dev/
_loom_tmp/documents/methodology/METHODOLOGY.md    → documents/methodology/METHODOLOGY.md
_loom_tmp/documents/methodology/templates/*  → documents/methodology/
```

Jeśli Agent wykonawczy jest aktywny — stwórz pusty plik `documents/agent/AGENT.md`
z nagłówkiem: `# Agent — instrukcje operacyjne` i notatką `(do wypełnienia)`.

---

## Krok 4 — Wypełnij CLAUDE.md

Skopiuj `_loom_tmp/CLAUDE_template.md` jako `CLAUDE.md` i wypełnij:

- `{{NAZWA_PROJEKTU}}` — nazwa projektu
- `{{OPIS_PROJEKTU}}` — opis (1-2 zdania)
- `{{TABELA_ROL}}` — zostaw tylko aktywne role (usuń nieaktywne wiersze)
- `{{PLIKI_CHRONIONE}}` — dostosuj do aktywnych ról (usuń pliki nieistniejących ról)

---

## Krok 5 — Posprzątaj i zainicjalizuj

Usuń `_loom_tmp/`.

Wykonaj pierwszy commit:

```
git add .
git commit -m "chore: inicjalizacja projektu z LOOM"
```

---

## Krok 6 — Przekaż Developerowi

Wyświetl:

```
Projekt [NAZWA] zainicjalizowany.

Następny krok:
  Załaduj: documents/dev/DEVELOPER.md
  Przejdź do: PROJECT_START.md → zacznij od "Co budujemy?"
```

Usuń lub zastąp ten plik (`CLAUDE.md`) wypełnionym CLAUDE.md z kroku 4.
Od tej chwili Claude Code będzie ładował właściwy routing przy każdym starcie.
