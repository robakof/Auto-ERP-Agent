---
workflow_id: suggestions_processing
version: "1.0"
owner_role: prompt_engineer
trigger: "PE przetwarza open suggestions (okresowy cleanup lub konserwacja backlogu)"
participants:
  - prompt_engineer (owner)
  - dawid (review przy duzych batch)
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

PE przetwarza open suggestions z extraction pattern — wykopywanie actionable items przed zamknieciem.

**Zasada:** Extraction workflow > naive close. Sugestie zawieraja lessons learned, patterns, rules — nie zamykaj bez sprawdzenia.

## Outline

1. **Grupowanie** — group by project/type/clusters
2. **Extraction** — klasyfikacja + wyciaganie actionable items
3. **Verification** — quality gate (extraction ratio)
4. **Execution** — bulk close + raport

---

## Faza 1: Grupowanie

**Owner:** PE

### Steps

1. Pobierz open suggestions.
   ```
   py tools/agent_bus_cli.py suggestions --status open
   ```

2. Zgrupuj po projekcie/feature:
   - M1-M4 Migration
   - Session Init
   - Tool X
   - etc.

3. Zgrupuj po typie:
   - observation
   - rule
   - discovery
   - tool

4. Zidentyfikuj clustery (sugestie o tym samym temacie).

### Exit gate

PASS: lista pogrupowana, clustery zidentyfikowane.

---

## Faza 2: Extraction

**Owner:** PE

### Steps

1. Dla kazdej grupy — przeczytaj PELNA tresc sugestii (nie tylko tytuly).

2. Dla kazdej sugestii zadaj pytania klasyfikacyjne:
   - [ ] Czy to lesson learned? → PE task (aktualizacja promptow)
   - [ ] Czy to pattern do wdrozenia? → Developer/Arch task
   - [ ] Czy to tool/feature? → Developer task
   - [ ] Czy to regula dla rol? → PE update prompts
   - [ ] Czy to audit/research? → Arch/PE task

3. Jesli TAK na ktorekolwiek → extract backlog item:
   3.1. Identify owner (PE/Dev/Arch/Metodolog)
   3.2. Formulate task (konkretny action item)
   3.3. Estimate (value/effort)
   3.4. Create backlog item
        ```
        py tools/agent_bus_cli.py backlog-add --title "..." --area <area> --value <v> --effort <e> --content-file tmp/backlog_item.md
        ```
   3.5. Update suggestion status → `in_backlog`
        ```
        py tools/agent_bus_cli.py suggest-status --id <id> --status in_backlog --backlog-id <backlog_id>
        ```

4. Jesli NIE na wszystkie → zamknij jako:
   - `realized` — projekt complete, obserwacja zrealizowana
   - `noted` — pure observation, nie wymaga akcji

5. Grupuj synergiczne sugestie w 1 backlog item (avoid duplication).

### Exit gate

PASS: wszystkie sugestie sklasyfikowane, actionable wyekstrahowane.

---

## Decision Point 1: Extraction Ratio Check

**decision_id:** check_extraction_ratio
**condition:** extracted_count / total_count >= 0.10
**path_true:** Faza 4 (Execution)
**path_false:** Faza 3 (Verification) — review needed

---

## Faza 3: Verification

**Owner:** PE

### Steps

1. Jesli ratio < 10% → re-read sugestie.
   - Czy cos waznego przepada?
   - High-value suggestions (author=architect, type=rule) → double check

2. Jesli ratio nadal < 10% po review:
   - To OK jesli sugestie naprawde sa pure observations
   - Zapisz uzasadnienie w logu

3. Przy duzym batch (>20 sugestii) → zapytaj usera:
   "Zamykam X sugestii, extracted Y backlog items — review?"

### Exit gate

PASS: ratio zweryfikowany, uzasadnienie zapisane jesli < 10%.

---

## Faza 4: Execution

**Owner:** PE

### Steps

1. Bulk close sugestii:
   ```
   py tools/agent_bus_cli.py suggest-status-bulk --ids "1,2,3" --status realized
   ```

2. Zapisz raport:
   - Total processed: X
   - Extracted to backlog: Y (ratio: Z%)
   - Closed as realized: A
   - Closed as noted: B
   - Status in_backlog: C

3. Log sesji:
   ```
   py tools/agent_bus_cli.py log --role prompt_engineer --content-file tmp/suggestions_report.md
   ```

### Exit gate

PASS: wszystkie sugestie przetworzone, raport zapisany.

---

## Forbidden

1. **Nie zamykaj bez klasyfikacji.**
   Kazda sugestia przechodzi przez pytania klasyfikacyjne.

2. **Nie ignoruj high-value.**
   author=architect, type=rule → zawsze double check.

3. **Nie kopiuj calej sugestii do backlogu.**
   Extract konkretny action item, nie copy-paste.

---

## Self-check

- [ ] Wszystkie sugestie przeszly przez pytania klasyfikacyjne?
- [ ] Extraction ratio sprawdzony?
- [ ] Backlog items maja concrete action (nie "obserwacja X")?
- [ ] Raport zapisany?

---

## Changelog

| Wersja | Data | Zmiany |
|---|---|---|
| 1.0 | 2026-03-24 | Poczatkowa wersja — extraction pattern z sesji fb202ab52fee |
