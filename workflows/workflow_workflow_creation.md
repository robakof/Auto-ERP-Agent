---
workflow_id: workflow_creation
version: "1.2"
owner_role: prompt_engineer
trigger: "Agent wykonał proces bez workflow i wysłał konwersację do formalizacji"
participants:
  - prompt_engineer (owner, formalizacja)
  - agent_źródłowy (praktyka, konwersacja)
  - dawid (approval)
related_docs:
  - documents/conventions/CONVENTION_WORKFLOW.md
  - documents/methodology/SPIRIT.md
prerequisites:
  - session_init_done
  - conversation_reference (adresacja konwersacji źródłowej)
outputs:
  - type: file
    path: "workflows/workflow_{nazwa}.md"
  - type: message
    field: "powiadomienie agenta źródłowego"
  - type: commit
---

# Workflow: Tworzenie workflow

Formalizacja workflow na podstawie REALNEJ praktyki. Owner: PE.

**Zasada:** Workflow nie wymyślamy — wyłania się z praktyki.

## Outline

1. **Odbiór** — agent przysłał konwersację do formalizacji
2. **Ekstrakcja** — wyciągnięcie kroków, pułapek, learnings z konwersacji
3. **Draft** — minimalna formalizacja
4. **Review** — z userem (notuję → edycje osobno)
5. **Revision** — wdrożenie uwag
6. **Approval + Publication** — zatwierdzenie, commit, powiadomienia

---

## Zasady przewodnie

> "Nie ma wymyślania workflow — jest tylko praktyka."

**Emergencja > planowanie** — workflow wyłania się z tego co agent ZROBIŁ, nie z tego co sobie wyobrazimy.

**Minimum z praktyki** — formalizujemy minimum, rozbudowujemy iteracyjnie.

---

## Jak to działa (perspektywa agenta bez workflow)

Agent który nie ma workflow dla zadania:

1. **ROBI zadanie** (praktyka, nie czeka na workflow)
2. Na koniec sesji wysyła do PE:
   - "Wykonałem [opis zadania]"
   - Adresacja konwersacji (session_id lub link)
   - Opcjonalnie: własne obserwacje (pułapki, co poszło dobrze)

PE formalizuje na podstawie tej konwersacji.

---

## Faza 1: Odbiór

**Owner:** PE

### Steps

1. Odbierz wiadomość od agenta z:
   - Opisem wykonanego procesu
   - Adresacją konwersacji (session_id)
   - Opcjonalnie: obserwacjami agenta

2. Jeśli brak adresacji → poproś o uzupełnienie (intencja: potrzebuję konwersacji źródłowej).

3. Sprawdź czy workflow już istnieje.
   - Jeśli tak → EXIT, użyj istniejącego lub zaproponuj update.

### Exit gate

PASS: mam konwersację źródłową, workflow nie istnieje.

---

## Faza 2: Ekstrakcja

**Owner:** PE

### Steps

1. Przeczytaj konwersację źródłową.
   ```
   py tools/search_conversation.py --session {session_id}
   ```

2. Wyciągnij:
   - Kroki które agent wykonał
   - Pułapki na które wpadł
   - Decyzje które podjął
   - Co poszło dobrze
   - Co wymagało eskalacji

3. Zidentyfikuj wzorzec (liniowy vs multi-scenario).

4. Oceń czy to powtarzalny proces.
   - Jeśli jednorazowy → EXIT, nie formalizuj.
   - Jeśli powtarzalny → kontynuuj.

### Exit gate

PASS: kroki, pułapki, wzorzec wyekstrahowane.
EXIT: proces jednorazowy — nie wymaga workflow.

---

## Faza 3: Draft

**Owner:** PE

### Steps

1. Przeczytaj CONVENTION_WORKFLOW.

2. Utwórz minimalny draft.
   - YAML header
   - Outline
   - Fazy z exit gates
   - Forbidden — TYLKO pułapki z praktyki (z konwersacji źródłowej)

3. Nie dodawaj nic czego nie było w konwersacji.

### Exit gate

PASS: draft minimalny, oparty na praktyce.

---

## Faza 4: Review

**Owner:** PE + user

### Steps

1. Przedstaw draft userowi.

   → HANDOFF: human. STOP.
     Mechanizm: czekaj na user input
     Czekaj na: feedback lub zatwierdzenie draftu
     Nie przechodź do Fazy 5 bez odpowiedzi.

2. Notuję uwagi — NIE edytuję od razu.

3. Po zebraniu → potwierdź zakres edycji.

### Exit gate

PASS: uwagi zebrane, zakres potwierdzony.

---

## Faza 5: Revision

**Owner:** PE

### Steps

1. Wdróż uwagi z Fazy 4.
2. Jeśli zmiany istotne → pokaż userowi ponownie (wróć do Fazy 4).

### Exit gate

PASS: uwagi wdrożone.

---

## Faza 6: Approval + Publication

**Owner:** PE

### Steps

1. Przedstaw finalną wersję userowi do zatwierdzenia.

   → HANDOFF: human. STOP.
     Mechanizm: czekaj na user input
     Czekaj na: zatwierdzenie ("OK" / "poprawki")
     Nie commituj bez zatwierdzenia.

2. Commit:
   ```
   py tools/git_commit.py --message "feat(PE): workflow_{nazwa} v1.0" --all
   ```
3. Powiadom agenta źródłowego:
   ```
   py tools/agent_bus_cli.py send --from prompt_engineer --to <agent> --content-file tmp/workflow_ready.md
   ```
4. Zaktualizuj backlog (jeśli task z backlogu).

### Exit gate

PASS: commit wykonany, agent powiadomiony.

---

## Forbidden

1. **Nie wymyślaj kroków.**
   Wszystko pochodzi z konwersacji źródłowej. Jeśli agent tego nie robił — nie dodawaj.

2. **Nie komplikuj.**
   Minimum z praktyki.

3. **Nie formalizuj jednorazówek.**
   Workflow tylko dla powtarzalnych procesów.

4. **Nie edytuj w trakcie review.**
   Notuję → edycje osobno.

---

## Self-check

- [ ] Mam konwersację źródłową?
- [ ] Kroki wyekstrahowane z praktyki (nie wymyślone)?
- [ ] Draft minimalny?
- [ ] Forbidden = pułapki z konwersacji?
- [ ] Dawid zatwierdził?

---

## Changelog

| Wersja | Data | Zmiany |
|---|---|---|
| 1.1 | 2026-03-24 | Fundamentalna zmiana: Practice-First Workflow — trigger to konwersacja od agenta, nie "potrzeba workflow" |
| 1.0 | 2026-03-24 | Początkowa wersja |
