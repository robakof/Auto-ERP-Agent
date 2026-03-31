---
workflow_id: developer_tool
version: "2.0"
owner_role: developer
trigger: "Developer otrzymuje zadanie: nowe narzedzie lub rozbudowa istniejacego"
participants:
  - developer (owner)
  - architect (plan review, code review)
  - human (feedback)
related_docs:
  - documents/dev/DEVELOPER.md
  - documents/dev/PROJECT_START.md
  - workflows/workflow_plan_review.md
  - workflows/workflow_code_review.md
prerequisites:
  - session_init_done
  - git_clean
outputs:
  - type: file
    path: "tools/{nazwa_narzedzia}.py"
  - type: file
    path: "tests/test_{nazwa}.py"
  - type: commit
  - type: message
    field: "notyfikacje do rol (jesli narzedzie wspolne)"
---

# Workflow: Developer — Nowe narzedzie / rozbudowa

Workflow dla tworzenia nowych narzedzi lub rozbudowy istniejacych.
Duze zadania architektoniczne → `documents/dev/PROJECT_START.md`.

## Outline

1. **Przygotowanie** — czysty working tree, plan
2. **Plan review** — zatwierdzenie planu przez Architekta
3. **Implementacja** — TDD, test checkpoints, blast radius
4. **Feedback** — iteracja z uzytkownikiem
5. **Code review** — review Architekta
6. **Publikacja** — dokumentacja, notyfikacje, commit

---

## Faza 1: Przygotowanie

**Owner:** developer

### Inputs required
- [ ] `session_init_done`: session_init wykonany
- [ ] `task_defined`: Zadanie zdefiniowane (z backlogu, inbox lub od usera)

### Steps

## Step 1: Sprawdz working tree

**step_id:** check_git_clean
**action:** Sprawdz czysty working tree
**tool:** Bash
**command:** `git status`
**verification:** Output zawiera "nothing to commit" LUB uzytkownik zdecydowal o commit/stash
**on_failure:**
  - retry: no
  - skip: no
  - escalate: no
  - reason: "Working tree brudny. Zapytaj usera: commitowac czy stash?"
**next_step:** write_plan (if PASS)

---

## Step 2: Napisz plan

**step_id:** write_plan
**action:** Dla srednich/duzych zadan: napisz plan do pliku documents/human/plans/
**tool:** Write
**command:** `Write documents/human/plans/<nazwa>.md`
**verification:** Plan zapisany, zawiera: cel, podejscie, blast radius, pytania do Architekta
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Plan niekompletny. Uzupelnij."
**next_step:** send_plan_review (if PASS)

### Exit Gate

**Checklist:**
- [ ] `git_clean`: Working tree czysty
- [ ] `plan_written`: Plan zapisany (jesli srednie/duze zadanie)

**Status:**
- PASS if: git_clean == true

---

## Faza 2: Plan review

**Owner:** developer + architect

### Inputs required
- [ ] `plan_written`: Plan z Fazy 1

### Steps

## Step 3: Wyslij plan do Architekta

**step_id:** send_plan_review
**action:** Wyslij plan do Architekta na review
**tool:** agent_bus_cli
**command:** `py tools/agent_bus_cli.py send --from developer --to architect --content-file tmp/plan_review_request.md`
**verification:** Wiadomosc wyslana
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: yes
  - reason: "Blad wysylki. Sprawdz agent_bus_cli."
**next_step:** receive_plan_decision (if PASS)

→ HANDOFF: architect. STOP.
  Mechanizm: agent_bus send
  Czekaj na: decyzje Architekta (APPROVE/REJECT) w inbox.
  Nie przechodz do implementacji bez zatwierdzenia planu.
  Pelny proces: workflows/workflow_plan_review.md

---

## Step 4: Odbierz decyzje Architekta

**step_id:** receive_plan_decision
**action:** Odbierz decyzje Architekta z inbox
**tool:** agent_bus_cli
**command:** `py tools/agent_bus_cli.py inbox --role developer --sender architect`
**verification:** Decyzja otrzymana: APPROVE lub REJECT
**on_failure:**
  - retry: no
  - skip: no
  - escalate: yes
  - reason: "Brak odpowiedzi Architekta. Czekaj lub eskaluj."
**next_step:** plan_decision (if PASS)

---

## Decision Point 1: Decyzja o planie

**decision_id:** plan_decision
**condition:** Architect APPROVE
**path_true:** write_tests (APPROVE → Faza 3)
**path_false:** write_plan (REJECT → popraw plan per feedback)
**default:** write_plan

### Exit Gate

**Checklist:**
- [ ] `plan_sent`: Plan wyslany do Architekta
- [ ] `plan_approved`: Architect zatwierdzil (APPROVE)

**Status:**
- PASS if: plan_approved == true
- BLOCKED if: plan_approved == false → popraw plan

---

## Faza 3: Implementacja

**Owner:** developer

### Inputs required
- [ ] `plan_approved`: Plan zatwierdzony przez Architekta

### Steps

## Step 5: Napisz testy (TDD)

**step_id:** write_tests
**action:** Napisz testy najpierw: integration tests (cale flow) + unit tests (funkcje czyste). Happy path + edge cases.
**tool:** Write
**command:** `Write tests/test_<nazwa>.py`
**verification:** Plik testow istnieje, pokrywa happy path + edge cases
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Testy niekompletne. Dodaj brakujace scenariusze."
**next_step:** implement_code (if PASS)

---

## Step 6: Zaimplementuj kod

**step_id:** implement_code
**action:** Zaimplementuj kod spelniajacy testy. Test nie przechodzi → napraw kod, nie test.
**tool:** Write
**command:** `Write tools/<nazwa_narzedzia>.py`
**verification:** Kod zaimplementowany, narzedzie w tools/
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Implementacja niekompletna."
**next_step:** run_tests (if PASS)

---

## Step 7: Test checkpoint

**step_id:** run_tests
**action:** Uruchom wszystkie testy dotykajace zmienionego kodu. Raportuj explicit: test_X.py::TestY — N/N PASS.
**tool:** Bash
**command:** `py -m pytest tests/test_<nazwa>.py -v`
**verification:** Wszystkie testy PASS
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Testy FAIL. Napraw kod, nie test."
**next_step:** blast_radius_check (if PASS), implement_code (if FAIL — popraw kod)

---

## Step 8: Blast radius check

**step_id:** blast_radius_check
**action:** Grep po pattern ktory zmieniles. Gdzie jeszcze ten sam pattern jest uzywany? Czy wszedzie zaktualizowane?
**tool:** Grep
**command:** `Grep <zmieniony_pattern>` w calym repo
**verification:** Wszystkie uzycia pattern zaktualizowane
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Znaleziono nieaktualne uzycia. Zaktualizuj."
**next_step:** commit_implementation (if PASS), implement_code (if FAIL — zaktualizuj pozostale)

---

## Step 9: Commit implementacji

**step_id:** commit_implementation
**action:** Commit per dzialajaca zmiana
**tool:** Bash
**command:** `py tools/git_commit.py --message "feat(dev): <opis>" --files <zmienione_pliki>`
**verification:** Commit wykonany
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: yes
  - reason: "Blad commitu."
**next_step:** get_user_feedback (if PASS)

### Forbidden

- Pliki robocze w root projektu (tmp_*.py) — narzedzie od razu w tools/.
- Kod bez testow jako "gotowy".

### Exit Gate

**Checklist:**
- [ ] `tests_pass`: Testy PASS — explicit lista
- [ ] `existing_tests_pass`: Istniejace testy tez PASS
- [ ] `blast_radius_ok`: Grep po pattern, pokrycie kompletne
- [ ] `tool_in_tools`: Narzedzie w tools/ z testami
- [ ] `committed`: Commit wykonany

**Status:**
- PASS if: wszystkie == true

---

## Faza 4: Feedback

**Owner:** developer + human

### Steps

## Step 10: Pobierz feedback od uzytkownika

**step_id:** get_user_feedback
**action:** Pokaz uzytkownikowi co zrobione, zapytaj o feedback. Iteruj az do zatwierdzenia.
**tool:** manual
**command:** Prezentacja: co zaimplementowano, jak dziala, znane ograniczenia
**verification:** Uzytkownik zaakceptowal implementacje
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Uzytkownik ma uwagi. Wdroz poprawki."
**next_step:** send_code_review (if PASS), implement_code (if FAIL — poprawki)

### Exit Gate

**Checklist:**
- [ ] `user_accepted`: Uzytkownik zaakceptowal implementacje

**Status:**
- PASS if: user_accepted == true

---

## Faza 5: Code review

**Owner:** developer + architect

### Inputs required
- [ ] `user_accepted`: Uzytkownik zaakceptowal (Faza 4 PASS)

### Steps

## Step 11: Wyslij do code review

**step_id:** send_code_review
**action:** Wyslij kod do code review Architekta: zakres zmian, cel, powiazanie z planem
**tool:** agent_bus_cli
**command:** `py tools/agent_bus_cli.py send --from developer --to architect --content-file tmp/code_review_request.md`
**verification:** Wiadomosc wyslana
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: yes
  - reason: "Blad wysylki."
**next_step:** receive_review_decision (if PASS)

→ HANDOFF: architect. STOP.
  Mechanizm: agent_bus send
  Czekaj na: raport code review od Architekta w inbox.
  Nie commituj finalnie bez PASS z code review.
  Pelny proces: workflows/workflow_code_review.md

---

## Step 12: Odbierz wynik code review

**step_id:** receive_review_decision
**action:** Odbierz wynik code review z inbox
**tool:** agent_bus_cli
**command:** `py tools/agent_bus_cli.py inbox --role developer --sender architect`
**verification:** Wynik otrzymany: PASS lub NEEDS REVISION
**on_failure:**
  - retry: no
  - skip: no
  - escalate: yes
  - reason: "Brak odpowiedzi Architekta."
**next_step:** review_decision (if PASS)

---

## Decision Point 2: Wynik code review

**decision_id:** review_decision
**condition:** Architect PASS
**path_true:** update_docs (PASS → Faza 6)
**path_false:** implement_code (NEEDS REVISION → popraw per raport)
**default:** implement_code

### Exit Gate

**Checklist:**
- [ ] `review_sent`: Code review request wyslany
- [ ] `review_pass`: Architect PASS

**Status:**
- PASS if: review_pass == true
- BLOCKED if: review_pass == false → popraw per raport

---

## Faza 6: Publikacja

**Owner:** developer

### Inputs required
- [ ] `review_pass`: Code review PASS od Architekta

### Steps

## Step 13: Zaktualizuj dokumentacje

**step_id:** update_docs
**action:** Jesli narzedzie dotyczy >1 roli → dokumentuj w CLAUDE.md. Jesli nie → w dokumencie roli.
**tool:** Edit
**command:** `Edit <plik_dokumentacji>`
**verification:** Dokumentacja zaktualizowana
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Dokumentacja niekompletna."
**next_step:** notify_roles (if PASS)

---

## Step 14: Powiadom role

**step_id:** notify_roles
**action:** Wyslij powiadomienie do aktywnych rol (nazwa narzedzia, skladnia, kiedy uzywac)
**tool:** agent_bus_cli
**command:** `py tools/agent_bus_cli.py send --from developer --to <rola> --content-file tmp/tool_notification.md`
**verification:** Wiadomosci wyslane
**on_failure:**
  - retry: yes
  - skip: yes
  - escalate: no
  - reason: "Blad wysylki. Notyfikacja jest best-effort."
**next_step:** final_commit (if PASS)

---

## Step 15: Finalny commit + push

**step_id:** final_commit
**action:** Commit + push
**tool:** Bash
**command:** `py tools/git_commit.py --message "feat(dev): <nazwa_narzedzia>" --all --push`
**verification:** Commit i push wykonane
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: yes
  - reason: "Blad commitu/push."
**next_step:** END

### Exit Gate

**Checklist:**
- [ ] `review_pass`: Code review PASS od Architekta
- [ ] `docs_updated`: Dokumentacja zaktualizowana
- [ ] `roles_notified`: Role powiadomione (jesli narzedzie wspolne)
- [ ] `committed_pushed`: Commit + push wykonane

**Status:**
- PASS if: committed_pushed == true

---

## Changelog

| Wersja | Data | Zmiany |
|---|---|---|
| 2.0 | 2026-03-31 | Konwersja do strict format 04R (DB-ready): 15 steps, 2 decisions, 2 HANDOFF. Exit gates z item_id. |
| 1.0 | 2026-03-27 | Wydzielenie z workflow_developer.md (sekcja Narzedzie) |
