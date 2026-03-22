# Sugestie dla Prompt Engineer — open

**Data:** 2026-03-22
**Źródło:** render.py suggestions --status open

---

## Do wdrożenia w workflow / dokumentacji PE

### #156 — Research-driven design używaj częściej
**Typ:** rule
**Status:** open

Wzorzec research → results → design sprawdził się przy Architect (171 linii minimal viable prompt oparty o 487 linii researchu, 27 źródeł).

**Akcja:**
Sformalizować w PROMPT_ENGINEER.md jako standardowy krok przy projektowaniu nowej roli lub dużej zmiany architektury:
1. Research prompt → documents/<rola>/research_prompt_<temat>.md
2. External research (WebSearch, papers)
3. Results → documents/<rola>/research_results_<temat>.md
4. Design based on results

---

### #119 / #134 — Research przed promptem nowej roli (duplikaty)
**Typ:** rule
**Status:** open

Pattern nie jest sformalizowany w PROMPT_ENGINEER.md workflow, mimo że używany w praktyce.

**Akcja:**
Dodać do PE workflow jako Faza 0 przed projektowaniem nowej roli (patrz #156 powyżej).

---

### #154 — Few-shot examples > długi opis persony
**Typ:** rule
**Status:** open

Research pokazuje: few-shot examples skuteczniejsze od długiego opisu persony (Anthropic zaleca 2-5 przykładów).

**Stan obecny:** Żadna rola w Mrowisko nie ma few-shot examples zachowań.

**Akcja:**
Dodać do PROMPT_CONVENTION.md wzorzec:
```markdown
**Przykłady zachowań:**

*Scenariusz 1: [kontekst]*
❌ [złe zachowanie]
✓ [dobre zachowanie]
```

Przy kolejnej edycji promptu dowolnej roli — dodaj 2-3 przykłady przed dodawaniem opisów persony.

---

### #124 — Minimal viable prompt zamiast pełnych workflow
**Typ:** rule
**Status:** open

Obserwacja z Architect: 643 linie (pełne workflow) → feedback "za długi" → 171 linii (minimal, rozszerzalny).

**Akcja:**
Dodać do PROMPT_ENGINEER.md zasadę przy projektowaniu nowej roli:
- Minimum: mission, scope, critical rules (5-8), output contract, minimal workflow routing
- Nie pisać szczegółowych kroków workflow zanim nie zobaczymy jak rola działa w praktyce
- Workflow nabudowywać iteracyjnie na podstawie rzeczywistych sesji i failure modes

---

### #83 — Self-reported violation = analiza compliance, nie tool request
**Typ:** rule
**Status:** open

PE przeczytał sugestię #80 i sklasyfikował jako zadanie Developera (nowe narzędzie), pomijając że agent się przyznał do naruszenia reguły.

Sygnały w tekście: "naruszenie reguły", "obejście jednorazowe", cytat własnej reguły z promptu.

**Akcja:**
Dodać do PROMPT_ENGINEER.md workflow krok 1:
```
Przed klasyfikacją po tytule/typie — przeskanuj treść pod kątem:
- self-reported violation: "naruszyłem", "obejście", "złamałem regułę", "błąd"
- agent zna regułę i ją cytuje, ale zachował się inaczej

Jeśli tak → typ problemu to lost_salience lub gate_omission, nie outside_prompt_layer.
```

---

### #69 — Konwencja numeracji kroków w workflow
**Typ:** rule
**Status:** open

Wzorzec z bi_view_creation_workflow.md: Faza 0, Faza 1a, Faza 1b...

**Akcja:**
Sprawdzić czy wszystkie workflow i prompty ról używają tej konwencji. Jeśli nie — dodać do PROMPT_CONVENTION.md i zrefaktorować.

---

### #145 — Agent bez roli = STOP ✓ DONE
**Typ:** rule
**Status:** open (ale **wdrożony dziś w sesji** — commit 3b3fe17)

Safety gate dodany do CLAUDE.md.

**Akcja:** Zamknąć sugestię (suggest-status --id 145 --status implemented)

---

## Związane z innymi rolami — do rozważenia

### #125 — Funkcje krótkie (≤15 linii) — standard dla Developer
**Typ:** rule
**Status:** open

Zasada jest w ARCHITECT.md (code review), ale brak w DEVELOPER.md (ten kto pisze kod).

**Akcja:**
Dodać do DEVELOPER.md critical_rules:
"Funkcje krótkie i focused: optymalna ≤15 linii, >40 wymaga refaktoru. Logika dzielona między funkcjami → podfunkcja (DRY)."

---

### #120 — Workflow Architecture Discovery (od Architect)
**Typ:** rule
**Status:** open

Propozycja workflow do badania repo z lotu ptaka (5 etapów: struktura, kluczowe pliki, głębsze nurkowanie, synteza, dokument).

**Akcja:**
Przejrzeć propozycję i sformalizować jako workflow dla Architect (jeśli uznane za wartościowe).

---

### #52 — session_init załadował doc — nie czytaj ponownie
**Typ:** rule
**Status:** open

session_init zwraca doc_content. Gdy agent edytuje ten plik w tej samej sesji, ma go już w kontekście — nie powinien czytać ponownie przez Read (~300 linii tokenów).

**Akcja:**
Dodać reminder do CLAUDE.md:
"Gdy session_init załadował dokument roli (doc_content), nie używaj Read na tym pliku w tej samej sesji."

---

### #62 — Handoff ERP→Analityk — workflow poprzednika
**Typ:** observation
**Status:** open

Analityk nie ładuje automatycznie workflow poprzedniej roli przy handoff.

**Akcja:**
Rozważyć ogólną konwencję handoff — wiadomość agent_bus zawiera listę plików workflow do załadowania?
Lub: dodać do promptów ról checkpoint "przeczytaj workflow poprzednika jeśli to handoff".

---

### #53 — Logowanie per etap — brak przypomnienia w workflow gates
**Typ:** observation
**Status:** open

Reguła logowania jest w CLAUDE.md, ale workflow dokumentów ról nie przypominają o niej jawnie w bramkach.

**Akcja:**
Dodać do promptów ról (ERP_SPECIALIST.md, ANALYST.md, etc.) exit gate reminder:
"Zaloguj etap: agent_bus_cli.py log --role <rola> --content-file ..."

---

## Obserwacje do rozważenia (nie wymaga natychmiastowej akcji)

### #155 — Inbox rośnie szybciej niż przetwarzamy
**Typ:** observation
**Status:** open

9 wiadomości unprzetworzonych dziś, trend liniowy. PE przetwarza 1-3/sesja, dostaje 2-4 nowe.

**Propozycje:**
1. Dodać pole priority (critical/high/medium/low) do messages/suggestions
2. Weekly cleanup session PE
3. Developer pre-filtering przed wysłaniem

---

### #153 — Persona Architekta — 2 iteracje, wciąż nie działa
**Typ:** observation
**Status:** open

Research: persona NIE ma stabilnie potwierdzonego wpływu na trafność merytoryczną.

**Propozycja eksperymentu:**
- Wariant A: obecna persona + tone of voice + 3 przykłady
- Wariant B: bez persony, tylko critical_rules + examples
- Test na tym samym zadaniu, porównanie outputów

---

### #135 — Verification gates — gdzie jeszcze brakuje?
**Typ:** observation
**Status:** open

Meta-obserwacja: backlog #86 pokazał lukę w verification. Gdzie jeszcze agenci powinni weryfikować przed działaniem?

**Propozycja:**
Systematyczny przegląd workflow pod kątem:
1. Duplikacja (agent robi coś co już istnieje)
2. Destrukcja (nieodwracalne akcje)
3. Inefficiency (marnowanie czasu)

---

## Podsumowanie

**Do wdrożenia (priorytet):**
1. #156, #119, #134 — research przed promptem nowej roli (workflow PE)
2. #154 — few-shot examples (konwencja PE)
3. #124 — minimal viable prompt (konwencja PE)
4. #83 — self-reported violation (workflow PE)
5. #145 — zamknąć jako implemented ✓
6. #125 — funkcje krótkie (DEVELOPER.md)
7. #69 — konwencja numeracji (sprawdzić zgodność)

**Do rozważenia (niższy priorytet):**
8. #120 — Architecture Discovery workflow
9. #52 — session_init reminder (CLAUDE.md)
10. #62 — handoff convention
11. #53 — logowanie exit gates (prompty ról)

**Obserwacje (tracking, bez natychmiastowej akcji):**
12. #155 — inbox overflow
13. #153 — persona experiment
14. #135 — verification gates audit
