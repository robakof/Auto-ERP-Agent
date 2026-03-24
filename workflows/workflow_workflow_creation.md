---
workflow_id: workflow_creation
version: "1.1"
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
  - type: file
    path: "documents/human/workflows/workflow_{nazwa}.md"
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
5. **Approval** — Dawid
6. **Publication** — commit, powiadomienia

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

2. Notuję uwagi — NIE edytuję od razu.

3. Po zebraniu → potwierdź zakres edycji.

### Exit gate

PASS: uwagi zebrane, zakres potwierdzony.

---

## Faza 5: Revision + Approval + Publication

(Analogicznie do workflow_convention_creation)

1. Wdróż uwagi.
2. Skopiuj do `documents/human/workflows/`.
3. Dawid zatwierdza.
4. Commit + powiadomienia.

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
