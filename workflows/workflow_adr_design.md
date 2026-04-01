---
workflow_id: adr_redesign
version: "1.0"
owner_role: architect
trigger: "Developer eskaluje problem po ≥3 nieudanych próbach naprawy lub identyfikuje fundamentalne ograniczenie architektoniczne"
participants:
  - architect (owner — analiza, design, draft, weryfikacja)
  - prompt_engineer (tworzenie research promptu)
  - human (review ADR, iteracja, acceptance)
related_docs:
  - documents/conventions/CONVENTION_WORKFLOW.md
  - documents/architecture/PATTERNS.md
  - documents/architecture/ADR-INDEX.md
  - workflows/workflow_research_prompt_creation.md
prerequisites:
  - session_init_done
outputs:
  - type: file
    path: "documents/architecture/ADR-NNN-{temat}.md"
  - type: file
    path: "documents/architecture/PATTERNS.md (update)"
  - type: file
    path: "documents/researcher/prompts/research_{temat}.md"
  - type: message
    field: "research request do PE"
  - type: suggestion
    field: "refleksje z procesu projektowania"
  - type: commit
  - type: log
    field: "raport z projektowania ADR"
---

# Workflow: Redesign architektoniczny (ADR)

Architect projektuje ADR w odpowiedzi na problem którego Developer nie potrafi rozwiązać
łatkami — fundamentalne ograniczenie architektoniczne wymaga redesignu.

**Zasada:** Problem → research → mapowanie → draft → self-review → iteracja z userem → weryfikacja → acceptance.
Nie pisz ADR bez researchu. Nie pokazuj userowi bez self-review. Nie finalizuj bez iteracji.

## Outline

1. **Identyfikacja problemu** — zbierz sygnały eskalacji, zdefiniuj problem
2. **Zlecenie researchu** — pytania badawcze → PE tworzy prompt → research zewnętrznie
3. **Research intake** — wczytaj wyniki, oceń czy pogłębić
4. **Mapowanie na system** — mapuj wnioski na architekturę Mrowiska
5. **ADR draft + self-review** — napisz draft, przejdź 9 heurystyk redukcji
6. **Review + iteracja** — user ocenia, upraszczaj (loop, może wymagać dodatkowego researchu)
7. **Weryfikacja spójności** — sprawdź z PATTERNS.md, dodaj/popraw wzorce
8. **Finalizacja** — ADR final + acceptance usera
9. **Zamknięcie** — refleksje, log, powiadomienia, commit

---

## Faza 1: Identyfikacja problemu

**Owner:** Architect

### Steps

## Step 1: Zbierz sygnały eskalacji

**step_id:** collect_signals
**action:** Przejrzyj źródła sygnałów: eskalacja od Developera (wiadomość z diagnozą, history łatek, opis ograniczenia), raporty Dispatchera, obserwacje z code review. Zidentyfikuj fundamentalne ograniczenie architektoniczne.
**tool:** agent_bus_cli
**command:** `py tools/agent_bus_cli.py inbox --role architect --full`
**verification:** Eskalacja od Developera zawiera: (1) diagnozę problemu, (2) historię prób naprawy (≥3 lub opis fundamentalnego ograniczenia), (3) uzasadnienie dlaczego łatki nie wystarczą
**on_failure:**
  - retry: no
  - skip: no
  - escalate: no
  - reason: "Brak wystarczającej diagnozy od Developera. Poproś o uzupełnienie: co próbował, dlaczego nie zadziałało, jakie ograniczenie zidentyfikował."
**next_step:** define_problem (if PASS)

---

## Step 2: Zdefiniuj problem architektoniczny

**step_id:** define_problem
**action:** Zapisz strukturalną definicję problemu: (1) co nie działa, (2) jakie łatki próbowano i dlaczego nie wystarczają, (3) jakie fundamentalne ograniczenie zidentyfikowano, (4) jakie pytania badawcze trzeba zbadać (3-5 obszarów). Przeczytaj ponownie cytat usera jeśli istnieje — każda decyzja musi być spójna z jego słowami.
**tool:** manual
**command:** Analiza eskalacji → definicja problemu + pytania badawcze
**verification:** Problem zdefiniowany z konkretnymi pytaniami adresującymi przyczynę, nie objaw. Historia łatek udokumentowana.
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Zbyt ogólna definicja. Wróć do eskalacji Developera, szukaj fundamentalnego ograniczenia."
**next_step:** send_research_request (if PASS)

### Exit Gate

**Checklist:**
- [ ] `escalation_received`: Eskalacja od Developera z diagnozą i historią prób
- [ ] `problem_defined`: Problem zdefiniowany strukturalnie (co, dlaczego łatki nie wystarczają, ograniczenie)
- [ ] `research_areas`: 3-5 obszarów do zbadania zidentyfikowanych

**Status:**
- PASS if: wszystkie == true

---

## Faza 2: Zlecenie researchu

**Owner:** Architect → Prompt Engineer

### Inputs required
- [ ] `problem_defined`: Definicja problemu z Fazy 1
- [ ] `research_areas`: Pytania badawcze do zbadania

### Steps

## Step 3: Wyślij research request do PE

**step_id:** send_research_request
**action:** Napisz research request z: (1) kontekstem problemu, (2) historią łatek i ich porażek, (3) pytaniami badawczymi per obszar, (4) oczekiwanym output path. Wyślij do PE.
**tool:** agent_bus_cli
**command:** `py tools/agent_bus_cli.py send --from architect --to prompt_engineer --content-file tmp/research_request_{temat}.md`
**verification:** Wiadomość wysłana, zawiera kontekst problemu, pytania badawcze i output path
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Błąd wysyłki. Ponów."
**next_step:** wait_for_results (if PASS)

→ HANDOFF: prompt_engineer. STOP.
  Mechanizm: agent_bus send
  Czekaj na: PE tworzy research prompt (workflow_research_prompt_creation), user uruchamia research zewnętrznie.
  Nie przechodź dalej bez sygnału że wyniki są gotowe.

---

## Step 4: Czekaj na wyniki researchu

**step_id:** wait_for_results
**action:** Czekaj na sygnał od usera lub dispatchera że wyniki researchu są gotowe. Wczytaj plik wyników.
**tool:** Read
**command:** `Read documents/researcher/research/research_results_{temat}.md`
**verification:** Plik istnieje i zawiera wyniki badawcze
**on_failure:**
  - retry: no
  - skip: no
  - escalate: no
  - reason: "Wyniki jeszcze nie gotowe. Czekaj na sygnał."
**next_step:** read_research (if PASS)

### Exit Gate

**Checklist:**
- [ ] `research_requested`: Research request wysłany do PE
- [ ] `results_available`: Wyniki researchu dostępne

**Status:**
- PASS if: results_available == true
- BLOCKED if: results_available == false → czekaj na sygnał

---

## Faza 3: Research intake

**Owner:** Architect + Human

### Inputs required
- [ ] `results_available`: Plik wyników researchu istnieje

### Steps

## Step 5: Wczytaj i oceń wyniki researchu

**step_id:** read_research
**action:** Przeczytaj wyniki researchu. Szukaj nowych obszarów mapy — tematów, mechanizmów, wzorców których NIE było w oryginalnych pytaniach badawczych. Pojawienie się nieznanego dużego wątku = sygnał do pogłębienia.
**tool:** Read
**command:** `Read documents/researcher/research/research_results_{temat}.md`
**verification:** Porównaj obszary w wynikach z oryginalnymi pytaniami. Czy pojawiły się nowe duże wątki nieobecne w pytaniach badawczych?
**on_failure:**
  - retry: no
  - skip: no
  - escalate: yes
  - reason: "Plik uszkodzony lub niekompletny. Eskaluj do usera."
**next_step:** assess_depth (if PASS)

---

## Decision Point 1: Pogłębić research?

**decision_id:** assess_depth
**condition:** Research odsłonił nowe duże obszary mapy nieobecne w oryginalnych pytaniach
**path_true:** send_research_request (wróć do Fazy 2 — nowy research z doprecyzowanymi pytaniami)
**path_false:** map_to_system (przejdź do Fazy 4 — mapowanie)
**default:** send_research_request (w razie wątpliwości — pogłęb. Architect musi aktywnie uzasadnić że pogłębienie zbędne.)

→ HANDOFF: human. STOP.
  Mechanizm: czekaj na user input
  Czekaj na: decyzja usera — "pogłęb" (podaje nowe pytania lub zatwierdza wykryte obszary) lub "planuj" (Architect uzasadnił że pogłębienie zbędne)
  Nie przechodź dalej bez decyzji usera.

### Exit Gate

**Checklist:**
- [ ] `research_read`: Wyniki wczytane i przeanalizowane
- [ ] `new_areas_assessed`: Nowe obszary mapy zidentyfikowane lub brak nowych potwierdzone
- [ ] `depth_decided`: User zdecydował: pogłębić czy planować

**Status:**
- PASS if: depth_decided == "planuj"
- RETRY if: depth_decided == "pogłęb" → wróć do send_research_request

---

## Faza 4: Mapowanie na system

**Owner:** Architect

### Inputs required
- [ ] `depth_decided`: User zatwierdził przejście do planowania

### Steps

## Step 6: Mapuj wnioski na architekturę Mrowiska

**step_id:** map_to_system
**action:** Mapuj każdy kierunek z researchu na kontekst Mrowiska — stany, sygnały, mechanizmy, istniejące komponenty. Zidentyfikuj co pasuje, co wymaga adaptacji, co odrzucić.
**tool:** Read
**command:** `Read documents/architecture/PATTERNS.md` + przegląd powiązanych ADR
**verification:** Tabela mapowania: kierunek → zastosowanie w Mrowisku (lub "nie pasuje" z uzasadnieniem)
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Niewystarczająca znajomość systemu. Przeczytaj dodatkowe ADR i kod."
**next_step:** write_adr_draft (if PASS)

### Exit Gate

**Checklist:**
- [ ] `mapping_complete`: Każdy kierunek zmapowany na system lub odrzucony z uzasadnieniem
- [ ] `scope_clear`: Jasne co ADR będzie obejmował

**Status:**
- PASS if: wszystkie == true
- RETRY if: mapping_complete == false → przeczytaj więcej kontekstu

---

## Faza 5: ADR draft + self-review

**Owner:** Architect

### Inputs required
- [ ] `mapping_complete`: Mapowanie z Fazy 4

### Steps

## Step 7: Napisz pierwszą wersję ADR

**step_id:** write_adr_draft
**action:** Napisz ADR v1 zgodnie z CONVENTION_ADR (patrz backlog — konwencja do stworzenia). Zapisz do pliku. Status: Proposed.
**tool:** Write
**command:** `Write documents/architecture/ADR-NNN-{temat}.md`
**verification:** Plik istnieje, zawiera wymagane sekcje per CONVENTION_ADR, status: Proposed
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Błąd zapisu. Ponów."
**next_step:** self_iterate (if PASS)

---

## Step 8: Self-review — 9 heurystyk redukcji

**step_id:** self_iterate
**action:** Przejdź draft przez 9 heurystyk ZANIM pokażesz userowi. Uprość co się da. Lekcja z ADR-006: pierwsza wersja miała 5 stanów, hybrid supervisor, cron, monitoring transkryptu — finalna miała 1 kolumnę, 1 skrypt, 2 progi.

Heurystyki (przejdź każdą po kolei):

1. **Każdy stan musi mieć odrębną akcję.** Stan bez akcji to szum — usuń go.
2. **Każdy concern musi być w scope problemu.** Jeśli usuniesz feature a problem nadal rozwiązany → osobny ADR.
3. **Czy rozwiązanie wprowadza nowy runtime/proces/komponent?** Default: reuse istniejących. Nowy proces = red flag.
4. **Czy jest komponent z fixed interval (cron, timer)?** Szukaj event-driven triggera zamiast stałego interwału.
5. **Policz ruchome części** (kolumny, skrypty, stany, procesy, zależności). Czy każdą kategorię można zredukować o połowę?
6. **Rozdziel recorder od detektora.** Jeden komponent w dwóch rolach = design smell.
7. **Przeczytaj ponownie cytat usera o problemie.** Czy każda decyzja projektowa jest spójna z jego słowami?
8. **Test usuwania.** Dla każdego komponentu: usuń go mentalnie. Jeśli rozwiązanie nadal działa — wywal.
9. **Nie dystrybuj logiki do peryferium.** Nowy komponent = thin client (wywołaj i wyświetl). Stan, czas, cleanup, business logic — to żyje w centralnym systemie (DB, istniejące CLI). Lekcja: Extension v1 dostała registry cleanup, timeout logic, native DB — wszystko mogło żyć w głównej DB + Python CLI.

**tool:** Edit
**command:** `Edit documents/architecture/ADR-NNN-{temat}.md`
**verification:** Draft przeszedł 9 heurystyk. Każda heurystyka dała wynik: OK (nic do zmiany) lub REDUCED (co usunięto/uproszczono). Udokumentuj wyniki w step-log.
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Nie udało się uprościć — możliwe że draft jest już minimalny. Uzasadnij per heurystyka."
**next_step:** present_to_user (if PASS)

### Exit Gate

**Checklist:**
- [ ] `adr_file_exists`: Plik ADR zapisany
- [ ] `self_review_done`: 9 heurystyk przejrzanych z udokumentowanymi wynikami

**Status:**
- PASS if: wszystkie == true

---

## Faza 6: Review + iteracja

**Owner:** Architect + Human

**Pętla:** User może wielokrotnie żądać uproszczeń. Każda iteracja: feedback → edycja → ponowna prezentacja. Pętla kończy się gdy user mówi "OK". Feedback może wymagać dodatkowego researchu — wtedy powrót do Fazy 2.

### Inputs required
- [ ] `self_review_done`: Draft po self-review z Fazy 5

### Steps

## Step 9: Przedstaw ADR userowi

**step_id:** present_to_user
**action:** Pokaż userowi draft ADR. Czekaj na feedback.
**tool:** manual
**command:** Prezentacja pliku ADR-NNN-{temat}.md
**verification:** User odpowiedział (feedback lub "OK")
**on_failure:**
  - retry: no
  - skip: no
  - escalate: no
  - reason: "Czekaj na usera. Nie interpretuj ciszy jako akceptację."
**next_step:** iterate_design (if feedback), verify_patterns (if "OK")

→ HANDOFF: human. STOP.
  Mechanizm: czekaj na user input
  Czekaj na: feedback (uwagi, kierunek uproszczeń) lub "OK"
  Nie przechodź dalej bez odpowiedzi.

---

## Step 10: Iteruj design na podstawie feedbacku

**step_id:** iterate_design
**action:** Uprość ADR zgodnie z feedbackiem usera. Usuń overengineering. Zachowaj esencję. Jeśli feedback wskazuje na braki w wiedzy (nowy obszar, nieznany pattern) — zaproponuj userowi dodatkowy research (powrót do Fazy 2).
**tool:** Edit
**command:** `Edit documents/architecture/ADR-NNN-{temat}.md`
**verification:** Zmiany odzwierciedlają feedback usera.
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Niejasny feedback. Dopytaj usera."
**next_step:** present_to_user (if kolejna iteracja), send_research_request (if potrzeba researchu), verify_patterns (if user "OK")

---

## Decision Point 2: Co dalej po feedbacku?

**decision_id:** check_iteration_outcome
**condition:** Typ feedbacku usera
**path_a:** User dał feedback wymagający zmian → present_to_user (wróć do Step 9)
**path_b:** User wskazał brak wiedzy / nowy obszar → send_research_request (wróć do Fazy 2)
**path_c:** User powiedział "OK" → verify_patterns (przejdź do Fazy 7)
**default:** present_to_user

### Exit Gate

**Checklist:**
- [ ] `user_reviewed`: User zobaczył ADR i dał feedback
- [ ] `iterations_done`: User zaakceptował kierunek designu ("OK")

**Status:**
- PASS if: iterations_done == true
- BLOCKED if: user_reviewed == false → czekaj

---

## Faza 7: Weryfikacja spójności

**Owner:** Architect

### Inputs required
- [ ] `adr_iterated`: ADR po iteracjach z userem (Faza 6 PASS)

### Steps

## Step 11: Sprawdź spójność z PATTERNS.md

**step_id:** verify_patterns
**action:** Przeczytaj PATTERNS.md. Sprawdź: (1) czy ADR jest spójny z istniejącymi wzorcami, (2) czy istniejące wzorce nie zawierają lepszego rozwiązania (Architect mógł przeoczyć), (3) czy ADR nie wprowadza anti-patternu względem wzorcowni, (4) zidentyfikuj nowe wzorce odkryte podczas designu.
**tool:** Read
**command:** `Read documents/architecture/PATTERNS.md`
**verification:** Lista: (1) wzorce spójne, (2) wzorce wymagające update, (3) nowe wzorce do dodania, (4) potencjalne anti-patterny lub lepsze rozwiązania z wzorcowni
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "PATTERNS.md niedostępny. Sprawdź ścieżkę."
**next_step:** update_patterns (if zmiany potrzebne), finalize_adr (if brak zmian)

---

## Step 12: Zaktualizuj PATTERNS.md

**step_id:** update_patterns
**action:** Dodaj nowe wzorce odkryte podczas designu ADR. Zaktualizuj istniejące jeśli ADR je rozszerza. Format: Problem, Solution, When to use, When NOT to use, Example (ref do ADR).
**tool:** Edit
**command:** `Edit documents/architecture/PATTERNS.md`
**verification:** Nowe/zaktualizowane wzorce w formacie Pattern Format z PATTERNS.md
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Błąd edycji. Ponów."
**next_step:** finalize_adr (if PASS)

### Exit Gate

**Checklist:**
- [ ] `patterns_verified`: Spójność z PATTERNS.md sprawdzona (w obu kierunkach)
- [ ] `patterns_updated`: Nowe wzorce dodane / istniejące zaktualizowane (lub brak zmian — OK)

**Status:**
- PASS if: patterns_verified == true

---

## Faza 8: Finalizacja

**Owner:** Architect + Human

### Inputs required
- [ ] `patterns_verified`: Faza 7 PASS

### Steps

## Step 13: Zapisz finalną wersję ADR

**step_id:** finalize_adr
**action:** Zaktualizuj ADR do finalnej wersji. Uporządkuj sekcje, doprecyzuj sformułowania.
**tool:** Edit
**command:** `Edit documents/architecture/ADR-NNN-{temat}.md`
**verification:** ADR kompletny, sekcje spójne, brak TODO ani placeholderów
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Niekompletny ADR. Sprawdź sekcje."
**next_step:** request_acceptance (if PASS)

---

## Step 14: Poproś usera o acceptance

**step_id:** request_acceptance
**action:** Przedstaw finalny ADR userowi. Poproś o zmianę statusu na Accepted.
**tool:** manual
**command:** Prezentacja finalnego ADR. Pytanie: "Zatwierdzasz ADR? Status → Accepted?"
**verification:** User odpowiedział "tak" / "accepted" / zatwierdził
**on_failure:**
  - retry: no
  - skip: no
  - escalate: no
  - reason: "Czekaj na decyzję usera. Jeśli poprawki → wróć do iterate_design."
**next_step:** set_accepted (if zatwierdzony), iterate_design (if poprawki)

→ HANDOFF: human. STOP.
  Mechanizm: czekaj na user input
  Czekaj na: "Accepted" lub poprawki
  Nie przechodź do set_accepted bez zatwierdzenia.

---

## Step 15: Zmień status ADR na Accepted

**step_id:** set_accepted
**action:** Zmień status ADR z Proposed na Accepted w pliku
**tool:** Edit
**command:** `Edit documents/architecture/ADR-NNN-{temat}.md` — zmień "Status: Proposed" → "Status: Accepted"
**verification:** Plik zawiera "Status: Accepted"
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Błąd edycji. Ponów."
**next_step:** write_reflections (if PASS)

### Exit Gate

**Checklist:**
- [ ] `adr_finalized`: ADR w finalnej wersji, brak TODO
- [ ] `user_accepted`: User zatwierdził ADR
- [ ] `status_accepted`: Status == Accepted w pliku

**Status:**
- PASS if: wszystkie == true
- BLOCKED if: user_accepted == false → czekaj

---

## Faza 9: Zamknięcie

**Owner:** Architect

### Inputs required
- [ ] `status_accepted`: ADR zaakceptowany (Faza 8 PASS)

### Steps

## Step 16: Refleksje i sugestie

**step_id:** write_reflections
**action:** Przejrzyj proces projektowania przez trzy warstwy:

**Warstwa 1 — Co odkryłeś?**
- Reguła domenowa, pułapka, odkrycie techniczne, propozycja narzędzia/zmiany

**Warstwa 2 — Gdzie user cię skorygował?**
- Każda korekta to potencjalne usprawnienie promptu lub workflow
- Dlaczego poszedłeś źle? Prompt niejasny, zignorowana reguła, brak wiedzy?

**Warstwa 3 — Jak wyeliminować klasę problemu?**
- Czy istnieje zmiana systemowa eliminująca ten typ błędu?
- Szukaj rozwiązań usuwających potrzebę ręcznej synchronizacji/pamiętania/sprawdzania

Zapisz obserwacje. Pokaż userowi listę sugestii — czekaj na reakcję.
**tool:** agent_bus_cli
**command:** `py tools/agent_bus_cli.py suggest-bulk --from architect --bulk-file tmp/refleksje_adr_{temat}.md`
**verification:** Obserwacje zapisane, user zapoznany
**on_failure:**
  - retry: yes
  - skip: yes
  - escalate: no
  - reason: "Brak obserwacji to OK — nie wymuszaj pustych sugestii."
**next_step:** write_log (if PASS)

---

## Step 17: Zapisz log z output_summary

**step_id:** write_log
**action:** Zapisz log sesji z podsumowaniem: co zaprojektowano, ile iteracji, jakie wzorce dodano, jaki ADR zaakceptowany, jakie self-review heurystyki zadziałały
**tool:** agent_bus_cli
**command:** `py tools/agent_bus_cli.py log --role architect --content-file tmp/log_adr_{temat}.md`
**verification:** Log zapisany (brak błędu CLI)
**on_failure:**
  - retry: yes
  - skip: yes
  - escalate: no
  - reason: "Błąd logowania. ADR jest w pliku — log jest best-effort."
**next_step:** notify_roles (if PASS)

---

## Step 18: Powiadom powiązane role

**step_id:** notify_roles
**action:** Wyślij powiadomienie do PE (nowy ADR do uwzględnienia w promptach) i Developera (ADR gotowy do implementacji — potwierdzenie że jego eskalacja zaowocowała decyzją)
**tool:** agent_bus_cli
**command:** `py tools/agent_bus_cli.py send --from architect --to prompt_engineer --content-file tmp/adr_notify.md`
**verification:** Wiadomości wysłane bez błędu
**on_failure:**
  - retry: yes
  - skip: yes
  - escalate: no
  - reason: "Błąd wysyłki. Powiadomienia są best-effort."
**next_step:** commit_adr (if PASS)

---

## Step 19: Commit

**step_id:** commit_adr
**action:** Commituj ADR i zaktualizowany PATTERNS.md
**tool:** Bash
**command:** `py tools/git_commit.py --message "feat(arch): ADR-NNN-{temat} — Accepted" --all`
**verification:** Commit wykonany, brak błędu
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: yes
  - reason: "Błąd commita. Sprawdź git status."
**next_step:** close_workflow (if PASS)

---

## Step 20: Zamknij workflow

**step_id:** close_workflow
**action:** Zamknij workflow execution
**tool:** agent_bus_cli
**command:** `py tools/agent_bus_cli.py workflow-end --execution-id <id> --status completed`
**verification:** Execution status == completed
**on_failure:**
  - retry: yes
  - skip: yes
  - escalate: no
  - reason: "Błąd zamknięcia. Workflow jest faktycznie zakończony."
**next_step:** END

### Exit Gate

**Checklist:**
- [ ] `reflections_written`: Refleksje z trzech warstw przejrzane
- [ ] `log_written`: Log z output_summary zapisany
- [ ] `roles_notified`: PE i Developer powiadomieni
- [ ] `committed`: ADR + PATTERNS.md w git
- [ ] `workflow_closed`: Execution zamknięte

**Status:**
- PASS if: committed == true (refleksje, log, notify, workflow_close są best-effort)

---

## Forbidden

1. **Nie pisz ADR bez researchu.**
   Każdy ADR zaczyna się od wyników researchu. Bez badań — nie ma podstaw do decyzji. Lekcja: ADR-006 miał research z 5 obszarami, 487 linii wyników — to fundament.

2. **Nie pokazuj draftu userowi bez self-review.**
   Przejdź 9 heurystyk redukcji. ADR-006: pierwszy draft miał 5 stanów i hybrid supervisor, finał miał 1 kolumnę i 2 progi. User nie powinien robić pracy którą Architect może zrobić sam.

3. **Nie poprzestawaj na pierwszym researchu.**
   Jeśli wyniki odsłaniają nowe duże wątki — pogłęb. Default: pogłęb. Architect musi aktywnie uzasadnić że wie wystarczająco.

4. **Nie zamykaj workflow bez refleksji i logu.**
   Trzy warstwy refleksji + log z output_summary PRZED zamknięciem. Lekcja z ADR-006: 2 szczątkowe step-logi na cały workflow.

5. **Nie finalizuj bez iteracji z userem.**
   Pierwsza wersja jest zawsze za skomplikowana. User wskazuje overengineering — upraszczaj.

6. **Nie loguj step-logów szczątkowo.**
   Loguj kroki na bieżąco (step-log per krok), nie 2 wpisy na cały workflow.

---

## Self-check (koniec workflow)

- [ ] Problem zidentyfikowany z eskalacji Developera (diagnoza + historia łatek)?
- [ ] Research zlecony i wyniki otrzymane?
- [ ] User zdecydował: pogłębić research czy planować?
- [ ] Draft przeszedł self-review (9 heurystyk)?
- [ ] ADR przeszedł review z userem (≥1 iteracja)?
- [ ] PATTERNS.md sprawdzony w obu kierunkach i zaktualizowany?
- [ ] Status ADR == Accepted?
- [ ] Refleksje z trzech warstw przejrzane i zapisane?
- [ ] Log z output_summary zapisany PRZED zamknięciem?
- [ ] Commit wykonany?

---

## Changelog

| Wersja | Data | Zmiany |
|---|---|---|
| 1.0 | 2026-03-31 | Formalizacja z praktyki Architekta (msg #649, sesja ADR-006). Scope: redesign (nie new feature). Pełny flow: eskalacja Dev → research (PE + external) → intake z oceną pogłębienia → mapowanie → draft + self-review (9 heurystyk) → iteracja z userem (może wymagać dodatkowego researchu) → weryfikacja PATTERNS (dwukierunkowa) → acceptance → refleksje → zamknięcie. Format strict 04R. Źródła: msg #515, #530, #560, #600, #621, #623, #625, #649. |
