---
workflow_id: plan_review
version: "1.0"
owner_role: architect
trigger: "Developer przesyła plan implementacji do review"
participants:
  - developer (autor planu)
  - architect (reviewer/approver)
  - human (eskalacja decyzji poza architekturą)
related_docs:
  - documents/architect/ARCHITECT.md
  - documents/dev/DEVELOPER.md
  - workflows/workflow_developer.md
outputs:
  - type: message
    field: "decyzja APPROVE / REJECT + feedback"
  - type: file
    path: "documents/human/plans/<nazwa_planu>.md"
---

# Workflow: Plan Review

Developer tworzy plan implementacji i przesyła do Architekta.
Architect ocenia plan i zatwierdza lub odrzuca z feedbackiem.
Po zatwierdzeniu Developer implementuje.

## Outline

1. **Przygotowanie planu** — Developer pisze plan i wysyła do Architekta
2. **Review** — Architect ocenia plan
3. **Decyzja** — APPROVE / REJECT + feedback
4. **Iteracja** — Developer poprawia plan (jeśli REJECT)

---

## Faza 1: Przygotowanie planu

**Owner:** developer

### Steps

1. Developer przygotowuje plan implementacji do pliku:
   ```
   documents/human/plans/<nazwa_planu>.md
   ```
2. Plan MUSI zawierać:
   - **Kontekst** — jaki problem rozwiązujemy, skąd zadanie
   - **Proponowane rozwiązanie** — co i jak
   - **Blast radius** — jakie pliki/moduły dotknięte, jakie role
   - **Pytania do Architekta** — wątpliwości, trade-offy do rozstrzygnięcia
   - **Oczekiwana decyzja** — APPROVE / REJECT + feedback
3. Developer wysyła plan do Architekta:
   ```
   py tools/agent_bus_cli.py send --from developer --to architect --content-file tmp/plan_review_request.md
   ```
   Treść wiadomości: ścieżka do planu + krótki opis.

   → HANDOFF: architect. STOP.
     Mechanizm: agent_bus send
     Czekaj na: decyzję Architekta (APPROVE/REJECT) w inbox.
     Nie przechodź do implementacji bez otrzymania decyzji.

### Exit gate

PASS jeśli:
- [ ] Plan zapisany do `documents/human/plans/`
- [ ] Plan zawiera wszystkie wymagane sekcje
- [ ] Wiadomość wysłana do Architekta

---

## Faza 2: Review planu

**Owner:** architect

### Steps

1. Architect czyta plan z `documents/human/plans/<nazwa_planu>.md`.
2. Ocenia plan pod kątem:
   - Zgodność z architekturą systemu (PATTERNS.md, ADR)
   - Blast radius — czy zakres jest adekwatny do problemu
   - Trade-offy — czy rozwiązanie jest optymalne
   - Kompletność — czy nic nie pominięto
3. Architect podejmuje decyzję:
   - **APPROVE** — plan jest OK, Developer może implementować
   - **REJECT + feedback** — plan wymaga poprawek, Architect wskazuje co zmienić
   - **ESCALATE** — decyzja wykracza poza architekturę (budżet, priorytety, scope reduction) → eskaluj do człowieka

### Decision Point: Ocena planu

**decision_id:** plan_assessment
**condition:** Plan zgodny z architekturą, blast radius adekwatny, brak krytycznych braków
**path_true:** APPROVE → Faza 3a
**path_false:** REJECT → Faza 3b
**default:** ESCALATE → human (jeśli decyzja poza zakresem Architekta)

### Exit gate

PASS jeśli:
- [ ] Plan przeczytany i oceniony
- [ ] Decyzja podjęta (APPROVE / REJECT / ESCALATE)

---

## Faza 3a: Zatwierdzenie (APPROVE)

**Owner:** architect

### Steps

1. Architect wysyła decyzję do Developera:
   ```
   py tools/agent_bus_cli.py send --from architect --to developer --content-file tmp/plan_approved.md
   ```
   Treść: APPROVE + ewentualne uwagi (suggestions, nie blockers).

   → HANDOFF: developer. STOP.
     Mechanizm: agent_bus send
     Czekaj na: Developer implementuje (workflow_code_review po zakończeniu).
     Nie implementuj sam — Architect projektuje, Developer implementuje.

### Exit gate

PASS jeśli:
- [ ] Wiadomość z decyzją APPROVE wysłana do Developera

---

## Faza 3b: Odrzucenie (REJECT)

**Owner:** architect

### Steps

1. Architect wysyła feedback do Developera:
   ```
   py tools/agent_bus_cli.py send --from architect --to developer --content-file tmp/plan_rejected.md
   ```
   Treść MUSI zawierać:
   - Co jest nie tak (konkretne problemy)
   - Co zmienić (konkretne kierunki poprawek)
   - Czego NIE zmieniać (co jest OK)

   → HANDOFF: developer. STOP.
     Mechanizm: agent_bus send
     Czekaj na: Developer poprawia plan i przesyła ponownie (powrót do Fazy 1).
     Nie poprawiaj planu sam.

### Exit gate

PASS jeśli:
- [ ] Feedback konkretny (co zmienić, czego nie)
- [ ] Wiadomość wysłana do Developera

---

## Forbidden

- Architect implementuje kod zamiast oceniać plan — scope leak.
- Developer implementuje bez zatwierdzenia planu — pominięcie gate'u.
- Eskalacja do człowieka decyzji czysto architektonicznych — to rola Architekta.
- Człowiek jako domyślny reviewer planów technicznych — to rola Architekta.

---

## Kiedy eskalacja do człowieka

- Decyzja dotyczy priorytetów biznesowych (co robić najpierw)
- Decyzja dotyczy scope reduction (co wyciąć z planu)
- Decyzja dotyczy budżetu czasowego (ile sesji poświęcić)
- Konflikt Architect ↔ Developer bez rozstrzygnięcia po 1 iteracji REJECT
