---
workflow_id: code_review
version: "1.0"
owner_role: architect
trigger: "Developer kończy implementację feature/taska i przesyła do code review"
participants:
  - developer (autor kodu)
  - architect (reviewer)
related_docs:
  - documents/architect/ARCHITECT.md
  - workflows/workflow_developer.md
  - workflows/workflow_plan_review.md
outputs:
  - type: file
    path: "documents/human/reports/code_review_<feature>.md"
  - type: message
    field: "wynik review PASS / NEEDS REVISION / BLOCKED"
---

# Workflow: Code Review

Po implementacji Developer przesyła kod do Architekta.
Architect ocenia kod (poprawność, czytelność, bezpieczeństwo, dojrzałość) i wydaje raport.
Developer poprawia jeśli trzeba. Pętla review max 2 iteracje.

## Outline

1. **Zgłoszenie do review** — Developer przesyła zakres zmian
2. **Code review** — Architect analizuje kod i pisze raport
3. **Decyzja** — PASS / NEEDS REVISION / BLOCKED
4. **Iteracja** — Developer poprawia (jeśli NEEDS REVISION)
5. **Re-review** — Architect weryfikuje poprawki (max 1 re-review)

---

## Faza 1: Zgłoszenie do review

**Owner:** developer

### Steps

1. Developer przygotowuje opis zakresu review:
   - Jakie pliki zmienione (lista lub branch diff)
   - Co implementowano (krótki opis celu)
   - Powiązanie z planem (jeśli był plan_review — numer planu/backlogu)
   - Znane ograniczenia lub kompromisy
2. Developer wysyła do Architekta:
   ```
   py tools/agent_bus_cli.py send --from developer --to architect --content-file tmp/code_review_request.md
   ```

   → HANDOFF: architect. STOP.
     Mechanizm: agent_bus send
     Czekaj na: raport code review od Architekta w inbox.
     Nie rozpoczynaj nowych zadań na tych samych plikach do czasu review.

### Exit gate

PASS jeśli:
- [ ] Opis zakresu przygotowany (pliki, cel, powiązanie z planem)
- [ ] Wiadomość wysłana do Architekta

---

## Faza 2: Code Review

**Owner:** architect

### Steps

1. Architect czyta zgłoszenie i identyfikuje zakres plików.
2. Architect czyta kod — każdy zmieniony plik.
3. Zidentyfikuj tech stack kodu (ścieżka → tabela w `<code_maturity_levels>` ARCHITECT.md).
4. Architect ocenia per wymiar:
   - **Poprawność** — czy kod robi to co ma robić
   - **Czytelność** — naming, struktura, komentarze
   - **Bezpieczeństwo** — injection, XSS, secrets, OWASP top 10
   - **Niezawodność** — wymiary bazowe + stack-specific per `<code_maturity_levels>` w ARCHITECT.md.
     L1 w wymiarze stack-specific = Critical Issue.
   - **Dojrzałość** — code maturity level (Junior / Mid / Senior) per `<code_maturity_levels>` w ARCHITECT.md
   - **Zgodność z architekturą** — PATTERNS.md, ADR, konwencje
5. Architect pisze raport code review do pliku:
   ```
   documents/human/reports/code_review_<feature>.md
   ```
   Format raportu — per `<output_contract>` w ARCHITECT.md:
   ```
   # Code Review: [Feature Name]
   Date: YYYY-MM-DD

   ## Summary
   Overall assessment: PASS | NEEDS REVISION | BLOCKED
   Code maturity level: Junior | Mid | Senior — [uzasadnienie]

   ## Findings
   ### Critical Issues (must fix)
   ### Warnings (should fix)
   ### Suggestions (nice to have)

   ## Recommended Actions
   - [ ] [co zrobić]
   ```

### Decision Point: Wynik review

**decision_id:** review_assessment
**condition:** Brak Critical Issues
**path_true:** PASS → Faza 3a
**path_false (Critical Issues exist):** NEEDS REVISION → Faza 3b
**default (architektoniczny problem wykryty):** BLOCKED → eskalacja

### Exit gate

PASS jeśli:
- [ ] Wszystkie zmienione pliki przeczytane
- [ ] Raport zapisany do `documents/human/reports/`
- [ ] Decyzja podjęta (PASS / NEEDS REVISION / BLOCKED)

---

## Faza 3a: PASS

**Owner:** architect

### Steps

1. Architect wysyła wynik do Developera:
   ```
   py tools/agent_bus_cli.py send --from architect --to developer --content-file tmp/review_pass.md
   ```
   Treść: PASS + ścieżka do raportu + ewentualne Suggestions (nie blokują).

   → HANDOFF: developer. STOP.
     Mechanizm: agent_bus send
     Developer może kontynuować pracę. Suggestions opcjonalne do wdrożenia.

### Exit gate

PASS jeśli:
- [ ] Wiadomość z wynikiem wysłana do Developera

---

## Faza 3b: NEEDS REVISION

**Owner:** architect

### Steps

1. Architect wysyła wynik do Developera:
   ```
   py tools/agent_bus_cli.py send --from architect --to developer --content-file tmp/review_needs_revision.md
   ```
   Treść MUSI zawierać:
   - Ścieżka do raportu
   - Lista Critical Issues (must fix) — konkretne pliki i linie
   - Lista Warnings (should fix)
   - Co jest OK (nie psuć)

   → HANDOFF: developer. STOP.
     Mechanizm: agent_bus send
     Czekaj na: Developer poprawia i zgłasza re-review.
     Nie poprawiaj kodu sam.

### Exit gate

PASS jeśli:
- [ ] Raport z konkretnym feedbackiem wysłany
- [ ] Critical Issues wskazane z file:line

---

## Faza 4: Re-review (po poprawkach)

**Owner:** architect

### Steps

1. Developer poprawia kod i wysyła ponownie do review (powrót do Fazy 1).
2. Architect weryfikuje TYLKO wskazane Critical Issues i Warnings.
   Nie rozszerza zakresu review — chyba że poprawki wprowadzają nowe problemy.
3. Decyzja:
   - Critical Issues naprawione → PASS
   - Critical Issues wciąż obecne → BLOCKED (eskalacja do człowieka)

### Forbidden

- Więcej niż 2 iteracje review na ten sam zakres — po 2 iteracjach eskalacja.
- Re-review rozszerza zakres poza oryginalne findings.

### Exit gate

PASS jeśli:
- [ ] Critical Issues z pierwszego review naprawione
- [ ] Raport zaktualizowany lub nowy raport

---

## Forbidden

- Architect edytuje kod zamiast pisać raport — scope leak.
- Developer ignoruje Critical Issues i commituje — pominięcie gate'u.
- Review bez raportu (ustna informacja) — raport jest artefaktem trwałym.
- Review kodu bez przeczytania plików (ocena po opisie) — niedopuszczalne.

---

## Kiedy eskalacja do człowieka

- Po 2 iteracjach review Critical Issues wciąż nie naprawione
- Architektoniczny problem wykryty podczas review (scope creep — zmiana wymaga nowego planu)
- Konflikt Architect ↔ Developer o ocenę dojrzałości kodu
