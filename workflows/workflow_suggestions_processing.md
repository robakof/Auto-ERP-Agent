---
workflow_id: suggestions_processing
version: "2.0"
owner_role: prompt_engineer
trigger: "PE przetwarza open suggestions (okresowy cleanup lub konserwacja backlogu)"
participants:
  - prompt_engineer (owner, kroki 1/2/3a/3b/3d/4)
  - human (review mapy grup, review propozycji per group — krok 2.4 i 3.3)
related_docs:
  - documents/conventions/CONVENTION_WORKFLOW.md
  - documents/prompt_engineer/PROMPT_ENGINEER.md
prerequisites:
  - session_init_done
  - suggestions_open_exist
outputs:
  - type: backlog_item
    field: "extracted actionable items"
  - type: state
    field: suggestions_closed
  - type: log
    field: "raport z przetworzenia"
---

# Workflow: Przetwarzanie sugestii

PE przetwarza open suggestions z extraction pattern — wykopywanie actionable items przed zamknięciem.
Workflow obsługuje duże zbiory (200+) przez sekwencyjne przetwarzanie grup: po podziale na grupy,
każda grupa przechodzi pełny cykl (ekstrakcja → export → review → execution) zanim startuje następna.

**Zasada:** Extraction workflow > naive close. Sugestie zawierają lessons learned, patterns, rules — nie zamykaj bez sprawdzenia.

**Uwaga konwencyjna:** Workflow zawiera pętlę (loop) po grupach. Konstrukt Loop Block nie jest zdefiniowany
w CONVENTION_WORKFLOW — zgłoszono do Architekta (msg #291). Do czasu decyzji pętla reprezentowana
przez Decision Point.

## Outline

1. **Inicjalizacja** — pobierz i policz open suggestions
2. **Grupowanie** — podziel na grupy, eksportuj mapę do człowieka, czekaj na zatwierdzenie
3. **[LOOP] Przetwarzanie grupy** — dla każdej grupy: ekstrakcja → export → review (human) → execution
4. **Quality Gate** — globalny extraction ratio >= 10%
5. **Zamknięcie** — log sesji

---

## Faza 1: Inicjalizacja

**Owner:** PE

### Steps

1. Pobierz open suggestions.
   ```
   py tools/agent_bus_cli.py suggestions --status open
   ```

2. Policz: N = liczba open suggestions.
   - Jeśli N == 0 → workflow_end (nic do zrobienia).
   - Jeśli N > 0 → kontynuuj do Fazy 2.

### Exit gate

PASS: sugestie załadowane, liczba znana, N >= 1.

---

## Faza 2: Grupowanie

**Owner:** PE (kroki 2.1-2.3), Human (krok 2.4)

### Steps

1. Zgrupuj sugestie tematycznie (projekt/feature/area/typ).
   Przykładowe grupy:
   - M1-M4 Migration
   - Session Init
   - Tool X
   - per type: observation / rule / discovery / tool

2. Ustal rozmiar grup. Rekomendacja: 15-25 sugestii per grupa.
   Jeśli grupa > 25 → podziel na podgrupy (np. "M1-M4 — część 1", "M1-M4 — część 2").

3. Eksportuj mapę grup do pliku:
   ```
   Write documents/human/reports/suggestions_groups_<data>.md
   ```
   Format pliku:
   ```
   ## Mapa grup — <data>

   | Grupa | Liczba sugestii | IDs (zakres) |
   |-------|-----------------|--------------|
   | M1-M4 | 18 | #201-#230 (wybrane) |
   | Session Init | 15 | #231-#260 (wybrane) |

   Kolejność przetwarzania: [lista grup]
   ```

4. **[HUMAN STEP]** Pokaż człowiekowi mapę grup. Czekaj na: APPROVED lub REVISE.
   - REVISE → wróć do kroku 2.1 z nowymi kryteriami.
   - APPROVED → przejdź do Fazy 3.

### Exit gate

PASS: mapa grup zatwierdzona przez człowieka, kolejność przetwarzania ustalona.

---

## Faza 3: Przetwarzanie grup [LOOP]

**Owner:** PE (kroki 3.1, 3.2, 3.4), Human (krok 3.3)

**Pętla:** Faza 3 wykonywana raz per grupa, sekwencyjnie. Po zakończonej grupie — Decision Point.
Zanim startuje następna grupa, aktualna MUSI być w pełni zakończona (exit gate PASS).

**Stan pętli:**
- `current_group` — aktualnie przetwarzana grupa
- `remaining_groups` — grupy jeszcze nieprzetworzne
- `global_extracted_count` — łącznie stworzonych backlog items (kumulowane)
- `global_processed_count` — łącznie przetworzonych sugestii (kumulowane)

---

### Krok 3.1: Ekstrakcja z grupy

**Owner:** PE

1. Wczytaj pełną treść sugestii z `current_group` (nie tylko tytuły).
   ```
   py tools/agent_bus_cli.py suggestions --status open
   ```
   Filtruj po ID z mapy grup.

2. Dla każdej sugestii zadaj pytania klasyfikacyjne:
   - [ ] Czy to lesson learned? → PE task (aktualizacja promptów)
   - [ ] Czy to pattern do wdrożenia? → Developer/Arch task
   - [ ] Czy to tool/feature? → Developer task
   - [ ] Czy to reguła dla ról? → PE update prompts
   - [ ] Czy to audit/research? → Arch/PE task

3. Dla każdej sugestii przygotuj propozycję:
   ```
   - suggestion_id: <ID>
     classification: actionable | observation-only
     owner: prompt_engineer | developer | architect | metodolog
     title: "<konkretny tytuł tasku>"
     value: wysoka | średnia | niska
     effort: mała | średnia | duża
     action: backlog_add | noted | realized
     reason: "<uzasadnienie>"
   ```

4. Synergiczne sugestie można złączyć w 1 backlog item (unikaj duplikacji).

---

### Krok 3.2: Export propozycji do człowieka

**Owner:** PE

1. Zapisz propozycje tasków do pliku:
   ```
   Write documents/human/reports/suggestions_review_<group_name>_<data>.md
   ```
   Format pliku:
   ```
   ## Review: <group_name> — <data>

   ### Propozycje tasków

   | ID sugestii | Klasyfikacja | Owner | Propozycja tasku | Value | Effort | Akcja |
   |-------------|--------------|-------|-----------------|-------|--------|-------|
   | #123 | actionable | PE | "Dodać regułę X do PROMPT_ENGINEER.md" | wysoka | mała | backlog_add |
   | #124 | observation-only | — | — | — | — | noted |

   ### Do zatwierdzenia przez człowieka
   - APPROVED <IDs> — dodaj do backlogu
   - REVISE <ID> <korekta> — zmień tytuł/ownera/wartość
   - SKIP <IDs> — zamknij jako noted/realized bez backlog item
   ```

2. Pokaż człowiekowi ścieżkę do pliku.

---

### Krok 3.3: Review człowieka [HUMAN STEP]

**Owner:** Human

Człowiek przegląda plik z propozycjami i odpowiada w formacie:
```
APPROVED: <suggestion_ids>
REVISE: <suggestion_id> <korekta>
SKIP: <suggestion_ids>
```

- Czekaj na explicit feedback — brak odpowiedzi != APPROVED.
- Jeśli człowiek nie odpowiada → zatrzymaj workflow.

---

### Krok 3.4: Execution — dodaj do backlogu, zamknij sugestie grupy

**Owner:** PE

1. Dla każdego APPROVED tasku — dodaj do backlogu:
   ```
   py tools/agent_bus_cli.py backlog-add --title "..." --area <area> --value <v> --effort <e> --content-file tmp/backlog_item_<id>.md
   ```

2. Dla każdego REVISE — zaktualizuj propozycję i wróć do ludzkiego review (krok 3.3).

3. Zaktualizuj status sugestii w grupie:
   - APPROVED → `in_backlog` (z backlog_id)
   - SKIP → `noted` lub `realized`
   ```
   py tools/agent_bus_cli.py suggest-status --id <id> --status in_backlog --backlog-id <backlog_id>
   py tools/agent_bus_cli.py suggest-status --id <id> --status noted
   ```

4. Zaktualizuj liczniki globalne:
   ```
   global_extracted_count += <backlog items created in this group>
   global_processed_count += <suggestions in this group>
   ```

### Exit gate (per group)

PASS: wszystkie sugestie w grupie mają zaktualizowany status, backlog items dodane dla approved.
BLOCKED: czekaj na feedback człowieka (krok 3.3 nieprzeszedł).

### Self-check przed przejściem do następnej grupy
- [ ] Każda sugestia w grupie ma nowy status (in_backlog / noted / realized)?
- [ ] Każdy approved task ma backlog item?
- [ ] Liczniki global_extracted_count i global_processed_count zaktualizowane?
- [ ] Jeśli nie → BLOCKED.

---

## Decision Point: Następna grupa?

**decision_id:** check_next_group
**condition:** remaining_groups.count > 0
**path_true:** krok 3.1 (następna grupa — wróć do Fazy 3)
**path_false:** Faza 4 (Quality Gate)
**default:** Faza 4

---

## Faza 4: Quality Gate

**Owner:** Human (decyzja), PE (obliczenie ratio)

### Steps

1. Oblicz globalny extraction ratio:
   ```
   extraction_ratio = global_extracted_count / global_processed_count
   ```

2. Jeśli ratio >= 10% → PASS, przejdź do Fazy 5.

3. Jeśli ratio < 10% → eskaluj do człowieka:
   ```
   Extraction ratio: X% (poniżej progu 10%)
   Przetworzone sugestie: N
   Backlog items: M
   Możliwa utrata wartości — czy kontynuować bez re-review?
   ```
   - Człowiek odpowiada: CONTINUE lub RERUN.
   - RERUN → wróć do Fazy 3 od najwcześniejszej nieprzetworzonej grupy.
   - CONTINUE → zaloguj uzasadnienie i przejdź do Fazy 5.

### Exit gate

PASS: ratio >= 10% ALBO człowiek zatwierdził kontynuację z uzasadnieniem.

---

## Faza 5: Zamknięcie

**Owner:** PE

### Steps

1. Zapisz raport:
   ```
   Write tmp/suggestions_report_<data>.md
   ```
   Format:
   ```
   ## Suggestions Processing — <data>

   - Sugestie przetworzone: N
   - Grupy: K
   - Backlog items created: M
   - Extraction ratio: X%
   - Status: COMPLETED
   ```

2. Log sesji:
   ```
   py tools/agent_bus_cli.py log --role prompt_engineer --content-file tmp/suggestions_report_<data>.md
   ```

3. Zamknij workflow tracking:
   ```
   py tools/agent_bus_cli.py workflow-end --execution-id <id> --status completed
   ```

### Exit gate

PASS: raport zapisany, log zalogowany.

---

## Forbidden

1. **Nie zamykaj bez klasyfikacji.**
   Każda sugestia przechodzi przez pytania klasyfikacyjne.

2. **Nie ignoruj high-value.**
   author=architect, type=rule → zawsze double check przed zamknięciem.

3. **Nie kopiuj całej sugestii do backlogu.**
   Wyciągnij konkretny action item, nie copy-paste.

4. **Nie przetwarzaj wielu grup naraz.**
   Każda grupa musi przejść przez pełny cykl (3.1→3.4) zanim startuje następna.

5. **Nie interpretuj braku odpowiedzi człowieka jako APPROVED.**
   Czekaj na explicit feedback (APPROVED / REVISE / SKIP).

---

## Self-check (koniec całego workflow)

- [ ] Wszystkie sugestie przeszły przez pytania klasyfikacyjne?
- [ ] Extraction ratio sprawdzony i zatwierdzony (przez PE lub człowieka)?
- [ ] Backlog items mają concrete action (nie "obserwacja X")?
- [ ] Raport zapisany?

---

## Changelog

| Wersja | Data | Zmiany |
|---|---|---|
| 2.0 | 2026-03-25 | Per-group loop (skalowalność 200+ sugestii). Human jako weryfikator per group (krok 3.3). Export propozycji do człowieka przed execution. Quality Gate z eskalacją do człowieka przy ratio < 10%. Nota o brakującym Loop Block w konwencji (msg #291 do Architekta). |
| 1.0 | 2026-03-24 | Początkowa wersja — extraction pattern z sesji fb202ab52fee |
