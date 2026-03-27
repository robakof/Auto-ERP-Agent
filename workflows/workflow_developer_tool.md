---
workflow_id: developer_tool
version: "1.0"
owner_role: developer
trigger: "Developer otrzymuje zadanie: nowe narzędzie lub rozbudowa istniejącego"
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
  - git_clean (lub decyzja o commit/stash)
outputs:
  - type: file
    path: "tools/{nazwa_narzedzia}.py"
  - type: file
    path: "tests/test_{nazwa}.py"
  - type: commit
  - type: message
    field: "notyfikacje do ról (jeśli narzędzie wspólne)"
---

# Workflow: Developer — Nowe narzędzie / rozbudowa

Workflow dla tworzenia nowych narzędzi lub rozbudowy istniejących.
Duże zadania architektoniczne → `documents/dev/PROJECT_START.md`.

## Outline

1. **Przygotowanie** — czysty working tree, plan
2. **Plan review** — zatwierdzenie planu przez Architekta
3. **Implementacja** — TDD, test checkpoints, blast radius
4. **Feedback** — iteracja z użytkownikiem
5. **Code review** — review Architekta
6. **Publikacja** — dokumentacja, notyfikacje, commit

---

## Faza 1: Przygotowanie

**Owner:** developer

### Steps

1. Sprawdź czysty working tree (`git status`). Jeśli brudny → zapytaj czy commitować.
2. Dla średnich zadań: plan do pliku `documents/human/plans/<nazwa>.md`
   (uwzględnij otwarte wątki z poprzednich sesji).

### Exit gate

PASS: working tree czysty, plan zapisany (jeśli średnie zadanie).

---

## Faza 2: Plan review

**Owner:** developer + architect

### Steps

1. Wyślij plan do Architekta na review:
   ```
   py tools/agent_bus_cli.py send --from developer --to architect --content-file tmp/plan_review_request.md
   ```
   Pełny proces: `workflows/workflow_plan_review.md`.

   → HANDOFF: architect. STOP.
     Mechanizm: agent_bus send
     Czekaj na: decyzję Architekta (APPROVE/REJECT) w inbox.
     Nie przechodź do implementacji bez zatwierdzenia planu.

2. REJECT → popraw plan per feedback Architekta, wyślij ponownie.
3. APPROVE → przejdź do Fazy 3.

### Exit gate

PASS: plan zatwierdzony przez Architekta (APPROVE).

---

## Faza 3: Implementacja

**Owner:** developer

### Steps

1. Zaproponuj pisanie testów najpierw (TDD preferowane).
   1.1. Napisz testy: integration tests (całe flow) + unit tests (funkcje czyste).
        Happy path + edge cases. Mockuj zależności zewnętrzne (DB, API, sieć).
   1.2. Zaimplementuj kod spełniający testy. Test nie przechodzi → napraw kod, nie test.
2. **Test checkpoint po każdej metodzie/funkcji** — nie po całej fazie.
   Uruchom wszystkie testy dotykające zmienionego kodu (nie tylko nowe).
   Raportuj explicit: "test_X.py::TestY — N/N PASS".
3. **Blast radius check** przed commitem: grep po pattern który zmieniłeś.
   Gdzie jeszcze ten sam pattern jest używany? Czy wszędzie zaktualizowane?
   Mechanizm: `Grep <pattern> <pliki>` → lista miejsc → weryfikacja pokrycia.
4. Commit per działająca zmiana.

### Forbidden

- Pliki robocze w root projektu (`tmp_*.py`) — narzędzie od razu w `tools/`.
- Kod bez testów jako "gotowy".

### Exit gate

PASS jeśli:
- [ ] Testy przechodzą — explicit lista: `test_X.py::TestY — N/N PASS`
- [ ] Istniejące testy dotykające zmienionego kodu też passują
- [ ] Blast radius check — grep po zmienionym pattern, pokrycie kompletne
- [ ] Narzędzie w `tools/` z testami

---

## Faza 4: Feedback

**Owner:** developer + human

### Steps

1. Przy nieomawianych kwestiach w trakcie implementacji — pytaj użytkownika na bieżąco.
2. Po implementacji: przetestuj, pokaż co zrobione, zapytaj o feedback.
3. Poprawki na feedback użytkownika — iteruj aż do zatwierdzenia.

### Exit gate

PASS: użytkownik zaakceptował implementację.

---

## Faza 5: Code review

**Owner:** developer + architect

### Steps

1. Wyślij kod do code review Architekta:
   ```
   py tools/agent_bus_cli.py send --from developer --to architect --content-file tmp/code_review_request.md
   ```
   Treść: zakres zmian (pliki), cel, powiązanie z planem.
   Pełny proces: `workflows/workflow_code_review.md`.

   → HANDOFF: architect. STOP.
     Mechanizm: agent_bus send
     Czekaj na: raport code review od Architekta w inbox.
     Nie commituj finalnie bez PASS z code review.

2. NEEDS REVISION → popraw per raport, wyślij ponownie do review.
3. PASS → przejdź do Fazy 6.

### Exit gate

PASS: code review PASS od Architekta.

---

## Faza 6: Publikacja

**Owner:** developer

### Steps

1. Czy narzędzie dotyczy >1 roli? Tak → dokumentuj w CLAUDE.md. Nie → w dokumencie roli.
2. Wyślij `agent_bus send` do aktywnych ról (nazwa, składnia, kiedy używać).
3. Zapisz log sesji.
4. Commit + push.

### Exit gate

PASS jeśli:
- [ ] Code review PASS od Architekta
- [ ] Dokumentacja zaktualizowana
- [ ] Notyfikacja do ról (jeśli narzędzie wspólne)
- [ ] Commit + push

---

## Changelog

| Wersja | Data | Zmiany |
|---|---|---|
| 1.0 | 2026-03-27 | Wydzielenie z workflow_developer.md (sekcja Narzędzie) |
