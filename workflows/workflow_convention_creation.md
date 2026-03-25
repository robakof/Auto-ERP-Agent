---
workflow_id: convention_creation
version: "1.2"
owner_role: architect
trigger: "Potrzeba nowej konwencji dla aspektu projektu"
participants:
  - architect (owner, draft)
  - prompt_engineer (research prompt)
  - dawid (approval)
related_docs:
  - documents/conventions/CONVENTION_META.md
  - documents/conventions/CONVENTION_WORKFLOW.md
  - documents/methodology/SPIRIT.md
prerequisites:
  - session_init_done
outputs:
  - type: file
    path: "documents/conventions/CONVENTION_{ZAKRES}.md"
  - type: file
    path: "documents/human/conventions/CONVENTION_{ZAKRES}.md"
  - type: message
    field: "powiadomienie ról z audience"
  - type: commit
---

# Workflow: Tworzenie konwencji

Proces tworzenia nowej konwencji. Owner: Architect.

## Outline

1. **Identyfikacja** — walidacja że konwencja nie istnieje
2. **Research** — badanie best practices (pętla aż wyczerpane)
3. **Draft** — minimalna wersja
4. **Review** — weryfikacja
5. **Revision** — poprawki
6. **Approval** — zatwierdzenie przez Dawida
7. **Publication** — commit, powiadomienia

---

## Zasady przewodnie

> "Wolałbym żeby była napisana minimalnie dając więcej elastyczności."

> "Każdy aspekt projektu powinniśmy zaczynać od konwencji."

**Convention First Architecture** — zanim implementujesz, zdefiniuj standard.

---

## Faza 1: Identyfikacja

**Owner:** architect

**Założenie:** Projekt ma 100% pokrycia konwencjami. Tworzenie nowej jest rzadkie.

### Steps

1. Szukaj istniejącej konwencji.
   1.1. Sprawdź `documents/conventions/`
   1.2. Jeśli nie ma → przeszukaj repo szerzej (Glob, Grep)
   1.3. Jeśli znaleziona gdzie indziej → przenieś lub użyj
   1.4. Jeśli nie ma → waliduj z użytkownikiem (intencja: upewnij się że naprawdę nie istnieje)

2. Jeśli konwencja istnieje → EXIT. Użyj istniejącej.

3. Sprawdź czy to twoja domena.
   - Konwencja = Architect
   - Workflow = PE (przekaż)
   - Prompt = PE (przekaż)
   - Metodologia = Metodolog (przekaż)

4. Nazwij gap: co, dla kogo, dlaczego teraz.

### Exit gate

PASS: konwencja nie istnieje, użytkownik potwierdził, to domena Architect.
EXIT: konwencja istnieje → użyj istniejącej.

---

## Faza 2: Research

**Owner:** architect (zleca) + PE (prompt)

Research to pętla: research → nowe wątki → kolejny research → aż wyczerpane.

### Steps

1. Określ pytania badawcze (best practices, formaty, anti-patterns).

2. Sprawdź ecosystem Mrowisko — czy jest working pattern jako baseline.

3. Wyślij pytania badawcze do PE przez agent_bus.
   ```
   py tools/agent_bus_cli.py send --from architect --to prompt_engineer --content-file tmp/research_questions.md
   ```
   → HANDOFF: prompt_engineer. STOP.
     Mechanizm: agent_bus send
     Czekaj na: research prompt od PE w inbox (`documents/researcher/prompts/research_{temat}.md`).
     Nie przechodź do kroku 3.5 bez otrzymania promptu od PE.

3.5. [NOWY KROK] Odbierz research prompt od PE. Przekaż go użytkownikowi do wykonania zewnętrznym agentem.
   → HANDOFF: human. STOP.
     Mechanizm: czekaj na user input
     Czekaj na: wyniki researchu w `documents/researcher/research/{temat}.md`.
     Research wykonuje user lub zewnętrzny agent — nie Architect.
     Nie przechodź do kroku 4 bez otrzymania wyników.

4. Odbierz wyniki od użytkownika i oceń.
   - Nowe wątki do eksploracji? → kolejna iteracja od kroku 1 (nowe pytania do PE).
   - Wyczerpane? → kontynuuj do Draft.

### Exit gate

PASS: research wyczerpany, wzorce i anti-patterns znane, wyniki w pliku.
ESCALATE do PE jeśli research prompt nie daje wyników (problem z promptem, nie z researchem).

---

## Faza 3: Draft

**Owner:** architect

### Steps

1. Przeczytaj CONVENTION_META.

2. Utwórz draft (YAML header + wymagane sekcje).
   - Przyszłość: tool `convention_init.py` zautomatyzuje ten krok.

3. Status = draft.

### Exit gate

PASS: YAML header kompletny, wymagane sekcje obecne, plik zapisany.

---

## Faza 4: Review

**Owner:** architect + reviewer (z YAML header konwencji)

### Steps

1. Self-review zgodność z CONVENTION_META.

2. Architektoniczny review (DB-ready, zgodność z SPIRIT.md).

3. Zapisz uwagi.

### Exit gate

PASS: review kompletny, brak critical issues.
BLOCKED: critical issues → Faza 3.

---

## Faza 5: Revision

**Owner:** architect

### Steps

1. Zbierz feedback od reviewerów.

2. Wprowadź poprawki.

3. Zaktualizuj draft (bump `updated` date).

4. Zmień status na `review`.

### Exit gate

PASS: uwagi zaadresowane, status = review.

---

## Faza 6: Approval

**Owner:** dawid

### Steps

1. Skopiuj do `documents/human/conventions/` (dla Dawida).

2. Dawid zatwierdza.
   - Uwagi → Faza 5.
   - OK → status = active.

### Exit gate

PASS: Dawid zatwierdził, status = active.

---

## Faza 7: Publication

**Owner:** architect

### Steps

1. Git commit.

2. Powiadom role z audience.

3. Zaloguj sesję.

### Exit gate

PASS: commit, powiadomienia, log.

---

## Decision Points

### Decision Point 1: Domena

**decision_id:** check_domain
**condition:** Czy to konwencja (Architect) czy inna domena?
**path_convention:** Kontynuuj
**path_workflow:** Przekaż do PE
**path_other:** Przekaż do właściwej roli
**default:** Zapytaj PE (źródło workflow/promptów)

---

## Forbidden

1. **Brak przywiązania do legacy.**
   Jest nowsze, lepsze (potwierdzone researchem) → zastępujemy stare bez sentymentów.

2. **Nie approver = author.**
   Dawid jedyny approver.

3. **Nie cicha edycja aktywnej konwencji.**
   Zmiana = bump version + changelog.

---

## Self-check

- [ ] Konwencja nie istniała (zwalidowane)?
- [ ] Research wyczerpany?
- [ ] YAML header kompletny?
- [ ] Status = active?
- [ ] Commit + powiadomienia?

---

## Changelog

| Wersja | Data | Zmiany |
|---|---|---|
| 1.2 | 2026-03-25 | Faza 2: HANDOFF_POINT po kroku 3 (→ PE, STOP) i nowy krok 3.5 (→ Human, STOP). Usunięcie dwuznaczności: research wykonuje user/zewnętrzny agent, nie Architect. |
| 1.1 | 2026-03-24 | Review: minimalizm, usunięcie defensywnych reguł, research jako pętla, domain check, agent rewolucjonista |
| 1.0 | 2026-03-24 | Początkowa wersja |
