---
workflow_id: suggestions_processing
version: "4.0"
owner_role: architect
trigger: "Architect triazuje open suggestions (batch per sesja)"
participants:
  - architect (owner triage — Faza 2)
  - prompt_engineer (realizacja — sugestie typu prompt/konwencja/workflow)
  - developer (realizacja — sugestie typu narzedzie/kod)
  - metodolog (realizacja — sugestie typu proces/metoda)
  - human (review mapy grup, review propozycji per group)
related_docs:
  - documents/conventions/CONVENTION_WORKFLOW.md
  - documents/architect/ARCHITECT.md
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

Architect triazuje open suggestions (widok systemowy), routuje do odpowiedniej roli, rola realizuje.
Workflow obsluguje duze zbiory (200+) przez sekwencyjne przetwarzanie grup.

**Zasada:** Extraction workflow > naive close. Sugestie zawieraja lessons learned, patterns, rules — nie zamykaj bez sprawdzenia.

**Uwaga konwencyjna:** Workflow zawiera petle (loop) po grupach. Konstrukt Loop Block nie jest zdefiniowany
w CONVENTION_WORKFLOW — zgloszono do Architekta (msg #291). Do czasu decyzji petla reprezentowana
przez Decision Point.

## Outline

1. **Inicjalizacja** — pobierz i policz open suggestions
2. **Grupowanie i triage** — Architect dzieli na grupy, klasyfikuje, routuje
3. **[LOOP] Przetwarzanie grupy** — ekstrakcja → export → review (human) → execution
4. **Quality Gate** — globalny extraction ratio >= 10%
5. **Zamkniecie** — log sesji

---

## Faza 1: Inicjalizacja

**Owner:** Architect

### Inputs required
- [ ] `session_init_done`: session_init wykonany z rola architect
- [ ] `suggestions_open_exist`: istnieja open suggestions w bazie

### Steps

## Step 1: Pobierz open suggestions

**step_id:** fetch_open_suggestions
**action:** Pobierz liste open suggestions z bazy
**tool:** agent_bus_cli
**command:** `py tools/agent_bus_cli.py suggestions --status open`
**verification:** Output zawiera liste sugestii (count > 0)
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: yes
  - reason: "Baza niedostepna lub brak sugestii. Sprawdz polaczenie z mrowisko.db."
**next_step:** count_suggestions (if PASS), END (if FAIL — brak sugestii)

---

## Step 2: Policz sugestie

**step_id:** count_suggestions
**action:** Ustaw N = liczba open suggestions. Jesli N == 0 → END.
**tool:** manual
**command:** `N = len(suggestions)`
**verification:** N >= 1
**on_failure:**
  - retry: no
  - skip: no
  - escalate: no
  - reason: "N == 0 oznacza brak pracy. Zamknij workflow."
**next_step:** group_suggestions (if PASS), END (if FAIL — N == 0)

### Exit Gate

**Checklist:**
- [ ] `suggestions_loaded`: Sugestie zaladowane z bazy
- [ ] `count_positive`: N >= 1

**Status:**
- PASS if: wszystkie == true
- BLOCKED if: count_positive == false → END (nic do zrobienia)

---

## Faza 2: Grupowanie i triage

**Owner:** Architect (kroki 3-7), Human (krok 6)

### Inputs required
- [ ] `suggestions_loaded`: Lista open suggestions z Fazy 1

### Steps

## Step 3: Zgrupuj sugestie tematycznie

**step_id:** group_suggestions
**action:** Zgrupuj sugestie tematycznie (projekt/feature/area/typ). Rekomendacja: 15-25 sugestii per grupa. Jesli grupa > 25 → podziel na podgrupy.
**tool:** manual
**command:** Analiza tresci sugestii, grupowanie po temacie
**verification:** Kazda sugestia przypisana do dokladnie jednej grupy, kazda grupa ma 15-25 elementow
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Przeglad sugestii i ponowne grupowanie."
**next_step:** export_group_map (if PASS)

---

## Step 4: Eksportuj mape grup

**step_id:** export_group_map
**action:** Zapisz mape grup do pliku w documents/human/reports/
**tool:** Write
**command:** `Write documents/human/reports/suggestions_groups_<data>.md`
**verification:** Plik istnieje i zawiera tabele z grupami (nazwa, liczba sugestii, IDs)
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Blad zapisu pliku. Ponow probe."
**next_step:** human_approve_groups (if PASS)

---

## Step 5: Review mapy grup przez czlowieka

**step_id:** human_approve_groups
**action:** Pokaz czlowiekowi mape grup. Czekaj na APPROVED lub REVISE.
**tool:** manual
**command:** Prezentacja pliku suggestions_groups_<data>.md czlowiekowi
**verification:** Czlowiek odpowiedzial APPROVED lub REVISE
**on_failure:**
  - retry: no
  - skip: no
  - escalate: yes
  - reason: "Brak odpowiedzi czlowieka. Czekaj — nie interpretuj ciszy jako APPROVED."
**next_step:** route_groups (if PASS — APPROVED), group_suggestions (if FAIL — REVISE)

→ HANDOFF: human. STOP.
  Mechanizm: czekaj na user input
  Czekaj na: APPROVED lub REVISE z korektami
  Nie przechodz do route_groups bez odpowiedzi.

---

## Step 6: Routing grup do rol

**step_id:** route_groups
**action:** Przypisz kazda grupe do roli realizujacej i wyslij wiadomosc
**tool:** agent_bus_cli
**command:** `py tools/agent_bus_cli.py send --from architect --to <rola> --content-file tmp/suggestions_group_<name>.md`
**verification:** Kazda grupa ma przypisana role, wiadomosc wyslana
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: yes
  - reason: "Blad wysylki wiadomosci. Sprawdz agent_bus_cli."
**next_step:** load_group_suggestions (if PASS)

Routing rules:
- prompt / konwencja / workflow → prompt_engineer
- narzedzie / kod → developer
- architektura → architect (sam realizuje)
- proces / metoda → metodolog
- duplikat / stale → zamknij (bez backlog item)

→ HANDOFF: <rola realizujaca>. STOP.
  Mechanizm: agent_bus send
  Czekaj na: rola realizuje Faze 3 per grupa i raportuje wynik.

### Exit Gate

**Checklist:**
- [ ] `groups_created`: Sugestie zgrupowane tematycznie
- [ ] `map_approved`: Mapa grup zatwierdzona przez czlowieka
- [ ] `groups_routed`: Kazda grupa ma przypisana role realizujaca

**Status:**
- PASS if: wszystkie == true
- BLOCKED if: map_approved == false → czekaj na czlowieka
- RETRY if: groups_routed == false → ponow wysylke

---

## Faza 3: Przetwarzanie grup [LOOP]

**Owner:** rola przypisana w kroku route_groups (kroki 7-12), Human (krok 10)

**Petla:** Faza 3 wykonywana raz per grupa, sekwencyjnie. Po zakonczonej grupie — Decision Point.
Zanim startuje nastepna grupa, aktualna MUSI byc w pelni zakonczona (exit gate PASS).

**Stan petli:**
- `current_group` — aktualnie przetwarzana grupa
- `remaining_groups` — grupy jeszcze nieprzetworzone
- `global_extracted_count` — lacznie stworzonych backlog items (kumulowane)
- `global_processed_count` — lacznie przetworzonych sugestii (kumulowane)

### Inputs required
- [ ] `current_group`: Grupa z mapy do przetworzenia
- [ ] `group_suggestions_ids`: IDs sugestii w grupie

### Steps

## Step 7: Wczytaj sugestie z grupy

**step_id:** load_group_suggestions
**action:** Wczytaj pelna tresc sugestii z current_group (nie tylko tytuly)
**tool:** agent_bus_cli
**command:** `py tools/agent_bus_cli.py suggestions --status open`
**verification:** Tresc sugestii z grupy wczytana, IDs zgodne z mapa
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: yes
  - reason: "Nie mozna wczytac sugestii. Sprawdz baze."
**next_step:** classify_suggestions (if PASS)

---

## Step 8: Klasyfikuj sugestie

**step_id:** classify_suggestions
**action:** Dla kazdej sugestii odpowiedz na pytania klasyfikacyjne i przygotuj propozycje
**tool:** manual
**command:** Analiza tresci. Per sugestia: classification (actionable/observation-only), owner, title, value, effort, action (backlog_add/noted/realized), reason.
**verification:** Kazda sugestia w grupie ma kompletna klasyfikacje
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Niekompletna klasyfikacja. Wroc do sugestii bez propozycji."
**next_step:** export_proposals (if PASS)

Pytania klasyfikacyjne per sugestia:
- [ ] Czy to lesson learned? → PE task (aktualizacja promptow)
- [ ] Czy to pattern do wdrozenia? → Developer/Arch task
- [ ] Czy to tool/feature? → Developer task
- [ ] Czy to regula dla rol? → PE update prompts
- [ ] Czy to audit/research? → Arch/PE task

Synergiczne sugestie mozna zlaczyc w 1 backlog item (unikaj duplikacji).

---

## Step 9: Eksportuj propozycje do czlowieka

**step_id:** export_proposals
**action:** Zapisz propozycje taskow do pliku review
**tool:** Write
**command:** `Write documents/human/reports/suggestions_review_<group_name>_<data>.md`
**verification:** Plik istnieje, zawiera tabele z propozycjami (ID, klasyfikacja, owner, tytul, value, effort, akcja)
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Blad zapisu. Ponow probe."
**next_step:** human_review_proposals (if PASS)

---

## Step 10: Review propozycji przez czlowieka

**step_id:** human_review_proposals
**action:** Pokaz czlowiekowi plik z propozycjami. Czekaj na APPROVED/REVISE/SKIP per sugestia.
**tool:** manual
**command:** Prezentacja pliku suggestions_review_<group_name>_<data>.md
**verification:** Czlowiek odpowiedzial z decyzja per sugestia (APPROVED <IDs> / REVISE <ID> <korekta> / SKIP <IDs>)
**on_failure:**
  - retry: no
  - skip: no
  - escalate: yes
  - reason: "Brak odpowiedzi czlowieka. Czekaj — nie interpretuj ciszy jako APPROVED."
**next_step:** execute_approved (if PASS — feedback otrzymany), classify_suggestions (if FAIL — REVISE wymaga ponownej klasyfikacji)

→ HANDOFF: human. STOP.
  Mechanizm: czekaj na user input
  Czekaj na: APPROVED <IDs> / REVISE <ID> <korekta> / SKIP <IDs>
  Nie przechodz do execute_approved bez odpowiedzi.

---

## Step 11: Dodaj approved do backlogu

**step_id:** execute_approved
**action:** Dla kazdego APPROVED tasku dodaj backlog item. Dla SKIP — zamknij jako noted/realized.
**tool:** agent_bus_cli
**command:** `py tools/agent_bus_cli.py backlog-add --title "..." --area <area> --value <v> --effort <e> --content-file tmp/backlog_item_<id>.md`
**verification:** Kazdy APPROVED ma backlog item (z backlog_id). Kazdy SKIP ma status noted/realized.
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: yes
  - reason: "Blad dodawania do backlogu. Sprawdz agent_bus_cli."
**next_step:** close_group_suggestions (if PASS)

---

## Step 12: Zamknij sugestie grupy i zaktualizuj liczniki

**step_id:** close_group_suggestions
**action:** Zaktualizuj status kazdej sugestii w grupie. Zaktualizuj globalne liczniki.
**tool:** agent_bus_cli
**command:** `py tools/agent_bus_cli.py suggest-status --id <id> --status in_backlog --backlog-id <backlog_id>` lub `--status noted`
**verification:** Kazda sugestia w grupie ma nowy status (in_backlog/noted/realized). Liczniki global_extracted_count i global_processed_count zaktualizowane.
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: yes
  - reason: "Blad aktualizacji statusu. Sprawdz IDs."
**next_step:** check_next_group (if PASS)

### Self-check przed przejsciem do nastepnej grupy
- [ ] Kazda sugestia w grupie ma nowy status (in_backlog / noted / realized)?
- [ ] Kazdy approved task ma backlog item?
- [ ] Liczniki global_extracted_count i global_processed_count zaktualizowane?
- [ ] Jesli nie → BLOCKED.

### Exit Gate (per group)

**Checklist:**
- [ ] `all_classified`: Kazda sugestia w grupie sklasyfikowana
- [ ] `human_reviewed`: Czlowiek zatwierdzil propozycje
- [ ] `backlog_created`: Approved tasks maja backlog items
- [ ] `statuses_updated`: Statusy sugestii zaktualizowane
- [ ] `counters_updated`: Globalne liczniki zaktualizowane

**Status:**
- PASS if: wszystkie == true
- BLOCKED if: human_reviewed == false → czekaj na czlowieka

---

## Decision Point 1: Nastepna grupa?

**decision_id:** check_next_group
**condition:** remaining_groups.count > 0
**path_true:** load_group_suggestions (nastepna grupa — wroc do Fazy 3)
**path_false:** calculate_ratio (Faza 4 — Quality Gate)
**default:** calculate_ratio

---

## Faza 4: Quality Gate

**Owner:** Architect (obliczenie), Human (decyzja przy niskim ratio)

### Inputs required
- [ ] `global_extracted_count`: Laczna liczba stworzonych backlog items
- [ ] `global_processed_count`: Laczna liczba przetworzonych sugestii

### Steps

## Step 13: Oblicz extraction ratio

**step_id:** calculate_ratio
**action:** Oblicz globalny extraction ratio = global_extracted_count / global_processed_count
**tool:** manual
**command:** `extraction_ratio = global_extracted_count / global_processed_count`
**verification:** Ratio obliczony, wartosc liczbowa
**on_failure:**
  - retry: no
  - skip: no
  - escalate: yes
  - reason: "Division by zero — global_processed_count == 0. Nie powinno wystapic."
**next_step:** check_ratio (if PASS)

---

## Decision Point 2: Extraction ratio check

**decision_id:** check_ratio
**condition:** extraction_ratio >= 0.10
**path_true:** write_report (ratio OK — przejdz do Fazy 5)
**path_false:** escalate_ratio (ratio za niski — eskaluj do czlowieka)
**default:** escalate_ratio

---

## Step 14: Eskaluj niski ratio do czlowieka

**step_id:** escalate_ratio
**action:** Pokaz czlowiekowi extraction ratio i zapytaj: CONTINUE lub RERUN?
**tool:** manual
**command:** Prezentacja: "Extraction ratio: X% (ponizej progu 10%). Przetworzone: N. Backlog items: M. Kontynuowac bez re-review?"
**verification:** Czlowiek odpowiedzial CONTINUE lub RERUN
**on_failure:**
  - retry: no
  - skip: no
  - escalate: yes
  - reason: "Brak odpowiedzi czlowieka. Czekaj."
**next_step:** write_report (if PASS — CONTINUE), load_group_suggestions (if FAIL — RERUN od najwczesniejszej nieprzetworzonej grupy)

→ HANDOFF: human. STOP.
  Mechanizm: czekaj na user input
  Czekaj na: CONTINUE lub RERUN
  Nie przechodz bez odpowiedzi.

### Exit Gate

**Checklist:**
- [ ] `ratio_calculated`: Extraction ratio obliczony
- [ ] `ratio_acceptable`: Ratio >= 10% LUB czlowiek zatwierdzil kontynuacje

**Status:**
- PASS if: ratio_acceptable == true
- BLOCKED if: ratio_acceptable == false → czekaj na czlowieka

---

## Faza 5: Zamkniecie

**Owner:** Architect

### Inputs required
- [ ] `ratio_acceptable`: Quality gate przeszedl (Faza 4 PASS)

### Steps

## Step 15: Zapisz raport

**step_id:** write_report
**action:** Zapisz raport z przetworzenia sugestii
**tool:** Write
**command:** `Write tmp/suggestions_report_<data>.md`
**verification:** Plik istnieje, zawiera: liczbe przetworzonych, liczbe grup, backlog items, extraction ratio, status COMPLETED
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Blad zapisu raportu. Ponow."
**next_step:** log_session (if PASS)

---

## Step 16: Log sesji

**step_id:** log_session
**action:** Zapisz log sesji do agent_bus
**tool:** agent_bus_cli
**command:** `py tools/agent_bus_cli.py log --role architect --content-file tmp/suggestions_report_<data>.md`
**verification:** Log zapisany (brak bledu CLI)
**on_failure:**
  - retry: yes
  - skip: yes
  - escalate: no
  - reason: "Blad logowania. Raport jest w pliku — log jest opcjonalny."
**next_step:** close_workflow (if PASS)

---

## Step 17: Zamknij workflow tracking

**step_id:** close_workflow
**action:** Zamknij workflow execution
**tool:** agent_bus_cli
**command:** `py tools/agent_bus_cli.py workflow-end --execution-id <id> --status completed`
**verification:** Execution status == completed
**on_failure:**
  - retry: yes
  - skip: yes
  - escalate: no
  - reason: "Blad zamkniecia execution. Workflow jest faktycznie zakonczony."
**next_step:** END

### Exit Gate

**Checklist:**
- [ ] `report_written`: Raport zapisany do pliku
- [ ] `session_logged`: Log sesji w agent_bus
- [ ] `workflow_closed`: Execution zamkniete

**Status:**
- PASS if: report_written == true (log i workflow_close sa best-effort)

---

## Forbidden

1. **Nie zamykaj bez klasyfikacji.**
   Kazda sugestia przechodzi przez pytania klasyfikacyjne.

2. **Nie ignoruj high-value.**
   author=architect, type=rule → zawsze double check przed zamknieciem.

3. **Nie kopiuj calej sugestii do backlogu.**
   Wyciagnij konkretny action item, nie copy-paste.

4. **Nie przetwarzaj wielu grup naraz.**
   Kazda grupa musi przejsc przez pelny cykl (load→classify→export→review→execute→close) zanim startuje nastepna.

5. **Nie interpretuj braku odpowiedzi czlowieka jako APPROVED.**
   Czekaj na explicit feedback (APPROVED / REVISE / SKIP).

---

## Self-check (koniec calego workflow)

- [ ] Wszystkie sugestie przeszly przez pytania klasyfikacyjne?
- [ ] Extraction ratio sprawdzony i zatwierdzony (przez PE lub czlowieka)?
- [ ] Backlog items maja concrete action (nie "obserwacja X")?
- [ ] Raport zapisany?

---

## Changelog

| Wersja | Data | Zmiany |
|---|---|---|
| 4.0 | 2026-03-31 | Konwersja do strict format 04R (DB-ready): wszystkie kroki z step_id, action, tool, command, verification, on_failure, next_step. Decision points z decision_id. Exit gates z item_id. HANDOFF_POINT zachowane. |
| 3.0 | 2026-03-25 | Triage ownership: PE → Architect (msg #316). Faza 2: Architect grupuje i routuje. HANDOFF_POINT po routing. |
| 2.0 | 2026-03-25 | Per-group loop. Human jako weryfikator per group. Quality Gate. |
| 1.0 | 2026-03-24 | Poczatkowa wersja — extraction pattern z sesji fb202ab52fee |
