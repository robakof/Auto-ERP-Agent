---
workflow_id: workflow_creation
version: "1.0"
owner_role: prompt_engineer
trigger: "Potrzeba nowego workflow dla powtarzalnego procesu"
participants:
  - prompt_engineer (owner, draft)
  - architect (review architektoniczny)
  - dawid (approval)
related_docs:
  - documents/conventions/CONVENTION_WORKFLOW.md
  - documents/conventions/CONVENTION_META.md
  - documents/methodology/SPIRIT.md
prerequisites:
  - session_init_done
outputs:
  - type: file
    path: "workflows/workflow_{nazwa}.md"
  - type: file
    path: "documents/human/workflows/workflow_{nazwa}.md"
  - type: message
    field: "powiadomienie ról z participants"
  - type: commit
---

# Workflow: Tworzenie workflow

Proces tworzenia nowego workflow. Owner: Prompt Engineer.

## Outline

1. **Identyfikacja** — walidacja że workflow nie istnieje i jest potrzebny
2. **Research** — wzorce orchestracji, istniejące praktyki (pętla)
3. **Draft** — minimalna wersja zgodna z CONVENTION_WORKFLOW
4. **Review** — weryfikacja z userem (notuję → edycje osobno)
5. **Revision** — poprawki
6. **Approval** — zatwierdzenie przez Dawida
7. **Publication** — commit, powiadomienia

---

## Zasady przewodnie

> "Wolałbym żeby była napisana minimalnie dając więcej elastyczności."

**Minimalizm** — mniej kroków > więcej kroków. Workflow rośnie z praktyki, nie z wyobraźni.

**Agent rewolucjonista** — jest lepszy workflow (potwierdzony) → zastępujemy stary.

---

## Faza 1: Identyfikacja

**Owner:** prompt_engineer

**Założenie:** Workflow tworzymy gdy proces się powtarza (≥2 razy) i ma >3 kroki.

### Steps

1. Szukaj istniejącego workflow.
   1.1. Sprawdź `workflows/`
   1.2. Jeśli nie ma → przeszukaj repo (Glob, Grep)
   1.3. Jeśli istnieje → EXIT, użyj istniejącego

2. Waliduj potrzebę z userem.
   - Czy proces się powtarza?
   - Czy ma >3 kroki?
   - Czy ma pułapki (znane anti-patterns)?

3. Sprawdź domenę.
   - Workflow dla agentów = PE
   - Konwencja = Architect (przekaż)
   - Metodologia = Metodolog (przekaż)

4. Nazwij workflow: co, dla kogo, kiedy triggerowany.

### Exit gate

PASS: workflow nie istnieje, potrzeba zwalidowana, to domena PE.
EXIT: workflow istnieje.

---

## Faza 2: Research

**Owner:** PE

Research to pętla: szukaj → nowe wątki → szukaj dalej → aż wyczerpane.

### Steps

1. Sprawdź historię konwersacji — czy proces był już wykonywany?
   - `search_conversation.py` — szukaj podobnych zadań
   - Wyciągnij kroki, pułapki, learnings

2. Sprawdź ecosystem.
   - Czy podobny workflow istnieje w projekcie?
   - Czy CONVENTION_WORKFLOW ma odpowiedni wzorzec (liniowy vs multi-scenario)?

3. Opcjonalnie: research zewnętrzny (orchestracja, wzorce workflow dla agentów).

4. Oceń wyniki.
   - Nowe wątki? → kolejna iteracja.
   - Wyczerpane? → Draft.

### Exit gate

PASS: wzorce i pułapki znane.
ESCALATE do Architect jeśli potrzebna decyzja architektoniczna.

---

## Faza 3: Draft

**Owner:** PE

### Steps

1. Przeczytaj CONVENTION_WORKFLOW.

2. Wybierz styl.
   - Liniowy (fazy sekwencyjne) — proces techniczny
   - Multi-scenario (routing) — różne typy zadań

3. Utwórz draft.
   - YAML header (workflow_id, version, owner_role, trigger, participants, outputs)
   - Outline
   - Fazy z exit gates
   - Forbidden (tylko znane pułapki z praktyki)

4. Przyszłość: tool `workflow_init.py` zautomatyzuje template.

### Exit gate

PASS: YAML header, outline, fazy z exit gates, plik zapisany.

---

## Faza 4: Review

**Owner:** PE + user

**Proces:** Notuję uwagi → edycje w osobnej fazie (kontrola usera).

### Steps

1. Przedstaw draft userowi.

2. Zbieraj uwagi — NOTUJ, nie edytuj od razu.

3. Po zebraniu uwag → potwierdź zakres edycji.

4. Opcjonalnie: review architektoniczny od Architect (jeśli workflow cross-domain).

### Exit gate

PASS: uwagi zebrane, zakres edycji potwierdzony.

---

## Faza 5: Revision

**Owner:** PE

### Steps

1. Wdróż uwagi (wszystkie naraz, nie po jednej).

2. Zaktualizuj version w YAML.

3. Skopiuj do `documents/human/workflows/` (dla Dawida).

### Exit gate

PASS: uwagi wdrożone, kopia dla Dawida.

---

## Faza 6: Approval

**Owner:** dawid

### Steps

1. Dawid zatwierdza.
   - Uwagi → Faza 4 (nowy cykl review).
   - OK → kontynuuj.

### Exit gate

PASS: Dawid zatwierdził.

---

## Faza 7: Publication

**Owner:** PE

### Steps

1. Git commit.

2. Powiadom role z participants.

3. Zaloguj sesję.

### Exit gate

PASS: commit, powiadomienia, log.

---

## Decision Points

### Decision Point 1: Domena

**decision_id:** check_domain
**condition:** Workflow dla agentów (PE) czy inna domena?
**path_workflow:** Kontynuuj
**path_convention:** Przekaż do Architect
**path_other:** Przekaż do właściwej roli
**default:** Zapytaj Architect

---

## Forbidden

1. **Brak przywiązania do legacy.**
   Jest lepszy workflow → zastępujemy stary.

2. **Nie edytuj w trakcie review.**
   Notuję → edycje w osobnej fazie. User ma kontrolę.

3. **Nie gotowe formułki.**
   Wskaż intencję, agent sformułuje naturalnie.

4. **Nie defensywne reguły.**
   Zakładamy porządek. Nie pisz "sprawdź czy X aktualne".

---

## Self-check

- [ ] Workflow nie istniał?
- [ ] Potrzeba zwalidowana z userem?
- [ ] CONVENTION_WORKFLOW przestrzegana?
- [ ] Uwagi zebrane i wdrożone?
- [ ] Dawid zatwierdził?
- [ ] Commit + powiadomienia?

---

## Changelog

| Wersja | Data | Zmiany |
|---|---|---|
| 1.0 | 2026-03-24 | Początkowa wersja — learnings z workflow_convention_creation |
