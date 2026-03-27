---
workflow_id: exploration
version: "1.0"
owner_role: all
trigger: "Agent nie znalazł istniejącego workflow dla zadania"
participants:
  - agent (dowolna rola)
  - human (zatwierdzenie)
  - prompt_engineer (formalizacja post-hoc)
related_docs:
  - CLAUDE.md (sekcja Workflow gate)
  - documents/conventions/CONVENTION_WORKFLOW.md
  - workflows/workflow_workflow_creation.md
prerequisites:
  - session_init_done
  - workflow_search_done (brak dopasowania w workflows/)
outputs:
  - type: backlog_item
    field: "task do PE — formalizacja workflow"
  - type: message
    field: "wiadomość do PE z opisem sesji"
  - type: log
    field: "step-log per krok zadania"
---

# Workflow: Exploration

Procedura gdy agent nie znajduje istniejącego workflow dla zadania.
Agent NIE może samodzielnie autoryzować pracy bez workflow — musi uzyskać zgodę użytkownika.

**Zasada:** Brak workflow nie upoważnia do pracy na skróty. Każda praca musi być śledzona.

## Outline

1. **Szukanie** — przeszukaj workflows/ pod kątem pasującego workflow
2. **Weryfikacja z użytkownikiem** — STOP, zapytaj czy na pewno brak workflow
3. **Wykonanie z tracking** — workflow-start, step-log per krok, workflow-end
4. **Zgłoszenie do PE** — backlog item + wiadomość z opisem do formalizacji

---

## Faza 1: Szukanie workflow

**Owner:** agent (dowolna rola)

### Steps

1. Wylistuj WSZYSTKIE pliki workflow:
   ```
   Glob: workflows/workflow_*.md
   ```
2. Pokaż użytkownikowi listę znalezionych workflow z nazwami.
3. Dla każdego potencjalnie pasującego — przeczytaj outline (sekcja Outline na górze pliku).
4. Przedstaw użytkownikowi kandydatów:
   "Znalazłem te workflow które mogą pasować do zadania: [lista z nazwami].
   Czy któryś z nich jest właściwy?"

   → HANDOFF: human. STOP.
     Mechanizm: czekaj na user input
     Czekaj na: wskazanie workflow LUB potwierdzenie że żaden nie pasuje.
     Nie przechodź dalej bez odpowiedzi.

5. Użytkownik wskazał workflow → EXIT, wejdź w niego (Wariant 1).
6. Użytkownik potwierdził brak pasującego → przejdź do Fazy 2.

### Forbidden

- Nie deklaruj "nie znalazłem workflow" bez faktycznego przeszukania i pokazania listy.
- Nie oceniaj sam czy workflow pasuje — pokaż kandydatów użytkownikowi.

### Exit gate

PASS: użytkownik potwierdził że żaden workflow nie pasuje.
EXIT: użytkownik wskazał workflow → wejdź w Wariant 1.

---

## Faza 2: Potwierdzenie trybu exploration

**Owner:** agent + human

Faza 1 potwierdziła brak pasującego workflow. Teraz agent pyta o zgodę na pracę w trybie exploration.

### Steps

1. Powiedz użytkownikowi:
   "Żaden istniejący workflow nie pasuje. Potwierdzasz działanie w trybie exploration?"

   → HANDOFF: human. STOP.
     Mechanizm: czekaj na user input
     Czekaj na: potwierdzenie ("tak" / "rób") lub odmowę
     Nie przechodź do Fazy 3 bez odpowiedzi.

2. Użytkownik potwierdził → kontynuuj do Fazy 3.
3. Użytkownik odmówił → STOP, nie wykonuj zadania.

### Exit gate

PASS: użytkownik jawnie potwierdził działanie w trybie exploration.
BLOCKED: brak odpowiedzi lub odmowa użytkownika.

---

## Faza 3: Wykonanie z tracking

**Owner:** agent (dowolna rola)

### Steps

1. Zarejestruj start:
   ```
   py tools/agent_bus_cli.py workflow-start --workflow-id exploration --role <rola>
   ```
   Zapisz `execution_id`.

2. Wykonaj zadanie zgodnie z regułami roli.
   **Każdy krok logowany:**
   ```
   py tools/agent_bus_cli.py step-log --execution-id <id> --step-id <opis_kroku> --status PASS|FAIL
   ```

3. Zamknij workflow:
   ```
   py tools/agent_bus_cli.py workflow-end --execution-id <id> --status completed|failed|abandoned
   ```

### Exit gate

PASS: zadanie wykonane, workflow-end zarejestrowany, wszystkie kroki mają step-log.

---

## Faza 4: Zgłoszenie do PE

**Owner:** agent (dowolna rola)

### Steps

1. Przygotuj opis wykonanego zadania do pliku tymczasowego:
   ```
   Write tmp/workflow_formalization_<temat>.md
   ```
   Treść: co zrobiono, jakie kroki, jakie decyzje, jaki wynik, session_id.

2. Dodaj backlog item dla PE:
   ```
   py tools/agent_bus_cli.py backlog-add --title "Formalizacja workflow: [opis zadania]" --area Prompt --value srednia --effort srednia --content-file tmp/workflow_formalization_<temat>.md
   ```

3. Wyślij wiadomość do PE:
   ```
   py tools/agent_bus_cli.py send --from <rola> --to prompt_engineer --content-file tmp/workflow_formalization_<temat>.md
   ```

### Exit gate

PASS: backlog item dodany, wiadomość do PE wysłana.

---

## Forbidden

1. **Nie deklaruj braku workflow bez faktycznego przeszukania.**
   Faza 1 wymaga: Glob → lista → pokazanie użytkownikowi. Bez tego kroku deklaracja
   "nie znalazłem" jest fałszywa. Właśnie ten skrót powodował omijanie workflow gate.

2. **Nie oceniaj sam czy workflow pasuje — pokaż listę użytkownikowi.**
   Agent widzi nazwy plików; użytkownik zna kontekst. Decyzja o dopasowaniu należy do człowieka.

3. **Nie autoryzuj się sam.**
   Agent NIE MOŻE pominąć Fazy 2 (potwierdzenie exploration). Brak zgody = brak pracy.

4. **Nie pomijaj logowania.**
   Każdy krok w Fazie 3 wymaga step-log. Praca bez logów nie ma audytowalności.

5. **Nie pomijaj zgłoszenia do PE.**
   Faza 4 jest obowiązkowa — bez niej workflow nie zostanie sformalizowany
   i ten sam problem powtórzy się.

---

## Self-check

- [ ] Wylistowano workflow (Glob) i pokazano użytkownikowi listę kandydatów?
- [ ] Użytkownik potwierdził że żaden workflow nie pasuje?
- [ ] Użytkownik jawnie potwierdził działanie w trybie exploration?
- [ ] workflow-start zarejestrowany?
- [ ] Każdy krok ma step-log?
- [ ] workflow-end zarejestrowany?
- [ ] Backlog item do PE dodany?
- [ ] Wiadomość do PE wysłana?

---

## Changelog

| Wersja | Data | Zmiany |
|---|---|---|
| 1.1 | 2026-03-27 | Faza 1 deterministyczna: wymuszenie Glob + pokazanie listy + HANDOFF do usera. Forbidden: zakaz deklaracji braku workflow bez faktycznego przeszukania. |
| 1.0 | 2026-03-27 | Zamknięcie luki Wariantu 2 (CLAUDE.md). Agent musi uzyskać zgodę użytkownika i logować każdy krok. |
