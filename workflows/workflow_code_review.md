---
workflow_id: code_review
version: "2.0"
owner_role: architect
trigger: "Developer konczy implementacje feature/taska i przesyla do code review"
participants:
  - developer (autor kodu)
  - architect (reviewer)
related_docs:
  - documents/architect/ARCHITECT.md
  - workflows/workflow_developer_tool.md
  - workflows/workflow_developer_bugfix.md
  - workflows/workflow_plan_review.md
prerequisites:
  - session_init_done
  - implementation_complete
outputs:
  - type: file
    path: "documents/human/reports/code_review_<feature>.md"
  - type: message
    field: "wynik review PASS / NEEDS REVISION / BLOCKED"
---

# Workflow: Code Review

Po implementacji Developer przesyla kod do Architekta.
Architect ocenia kod (poprawnosc, czytelnosc, bezpieczenstwo, dojrzalosc) i wydaje raport.
Developer poprawia jesli trzeba. Petla review max 2 iteracje.

## Outline

1. **Zgloszenie do review** — Developer przesyla zakres zmian
2. **Code review** — Architect analizuje kod i pisze raport
3. **Decyzja** — PASS / NEEDS REVISION / BLOCKED
4. **Iteracja** — Developer poprawia (jesli NEEDS REVISION)
5. **Re-review** — Architect weryfikuje poprawki (max 1 re-review)

---

## Faza 1: Zgloszenie do review

**Owner:** developer

### Inputs required
- [ ] `implementation_complete`: Developer zakonczyl implementacje
- [ ] `files_changed`: Lista zmienionych plikow znana

### Steps

## Step 1: Przygotuj opis zakresu review

**step_id:** prepare_review_request
**action:** Przygotuj opis zakresu review: zmienione pliki, cel implementacji, powiazanie z planem, znane ograniczenia
**tool:** Write
**command:** `Write tmp/code_review_request.md`
**verification:** Plik istnieje i zawiera: liste plikow, cel, powiazanie z planem
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Opis niekompletny. Uzupelnij brakujace sekcje."
**next_step:** send_review_request (if PASS)

---

## Step 2: Wyslij zgloszenie do Architekta

**step_id:** send_review_request
**action:** Wyslij opis zakresu do Architekta przez agent_bus
**tool:** agent_bus_cli
**command:** `py tools/agent_bus_cli.py send --from developer --to architect --content-file tmp/code_review_request.md`
**verification:** Wiadomosc wyslana (brak bledu CLI)
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: yes
  - reason: "Blad wysylki. Sprawdz agent_bus_cli."
**next_step:** read_review_request (if PASS)

→ HANDOFF: architect. STOP.
  Mechanizm: agent_bus send
  Czekaj na: raport code review od Architekta w inbox.
  Nie rozpoczynaj nowych zadan na tych samych plikach do czasu review.

### Exit Gate

**Checklist:**
- [ ] `scope_described`: Opis zakresu przygotowany (pliki, cel, powiazanie z planem)
- [ ] `request_sent`: Wiadomosc wyslana do Architekta

**Status:**
- PASS if: wszystkie == true

---

## Faza 2: Code Review

**Owner:** architect

### Inputs required
- [ ] `review_request`: Zgloszenie od Developera z opisem zakresu

### Steps

## Step 3: Przeczytaj zgloszenie i zidentyfikuj zakres

**step_id:** read_review_request
**action:** Przeczytaj zgloszenie od Developera, zidentyfikuj zakres plikow do review
**tool:** Read
**command:** `Read` zgloszenia + `Glob` / `Grep` do identyfikacji plikow
**verification:** Lista plikow do review znana
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: yes
  - reason: "Zgloszenie niejasne. Zapytaj Developera o konkretny zakres."
**next_step:** read_changed_files (if PASS)

---

## Step 4: Przeczytaj zmienione pliki

**step_id:** read_changed_files
**action:** Przeczytaj kazdy zmieniony plik
**tool:** Read
**command:** `Read <sciezka_pliku>` per zmieniony plik
**verification:** Wszystkie zmienione pliki przeczytane
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Plik niedostepny. Sprawdz sciezke."
**next_step:** identify_tech_stack (if PASS)

---

## Step 5: Zidentyfikuj tech stack

**step_id:** identify_tech_stack
**action:** Zidentyfikuj tech stack kodu (sciezka → tabela w code_maturity_levels ARCHITECT.md)
**tool:** Read
**command:** `Read documents/architect/ARCHITECT.md` (sekcja code_maturity_levels)
**verification:** Tech stack zidentyfikowany, kryteria maturity znane
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "ARCHITECT.md niedostepny. Sprawdz sciezke."
**next_step:** evaluate_code (if PASS)

---

## Step 6: Ocen kod per wymiar

**step_id:** evaluate_code
**action:** Ocen kod per wymiar: poprawnosc, czytelnosc, bezpieczenstwo (OWASP), niezawodnosc, dojrzalosc (maturity level), zgodnosc z architektura
**tool:** manual
**command:** Analiza kodu per wymiar. L1 w wymiarze stack-specific = Critical Issue.
**verification:** Kazdy wymiar oceniony, findings sklasyfikowane (Critical/Warning/Suggestion)
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Ocena niekompletna. Sprawdz kazdy wymiar."
**next_step:** write_review_report (if PASS)

---

## Step 7: Napisz raport code review

**step_id:** write_review_report
**action:** Napisz raport code review do pliku w documents/human/reports/
**tool:** Write
**command:** `Write documents/human/reports/code_review_<feature>.md`
**verification:** Plik istnieje, zawiera: Summary (overall assessment + maturity level), Findings (Critical/Warning/Suggestion), Recommended Actions
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Raport niekompletny. Uzupelnij brakujace sekcje."
**next_step:** review_assessment (if PASS)

Format raportu:
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
- [ ] [co zrobic]
```

---

## Decision Point 1: Wynik review

**decision_id:** review_assessment
**condition:** Brak Critical Issues
**path_true:** send_pass (PASS → Faza 3a)
**path_false:** send_needs_revision (NEEDS REVISION → Faza 3b)
**default:** escalate_blocked (BLOCKED → eskalacja — problem architektoniczny)

### Exit Gate

**Checklist:**
- [ ] `all_files_read`: Wszystkie zmienione pliki przeczytane
- [ ] `report_saved`: Raport zapisany do documents/human/reports/
- [ ] `decision_made`: Decyzja podjeta (PASS / NEEDS REVISION / BLOCKED)

**Status:**
- PASS if: wszystkie == true

---

## Faza 3a: PASS

**Owner:** architect

### Steps

## Step 8: Wyslij wynik PASS do Developera

**step_id:** send_pass
**action:** Wyslij PASS + sciezke do raportu + ewentualne Suggestions do Developera
**tool:** agent_bus_cli
**command:** `py tools/agent_bus_cli.py send --from architect --to developer --content-file tmp/review_pass.md`
**verification:** Wiadomosc wyslana
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Blad wysylki. Ponow."
**next_step:** END

→ HANDOFF: developer. STOP.
  Mechanizm: agent_bus send
  Developer moze kontynuowac prace. Suggestions opcjonalne do wdrozenia.

### Exit Gate

**Checklist:**
- [ ] `pass_sent`: Wiadomosc z wynikiem PASS wyslana do Developera

**Status:**
- PASS if: pass_sent == true

---

## Faza 3b: NEEDS REVISION

**Owner:** architect

### Steps

## Step 9: Wyslij wynik NEEDS REVISION do Developera

**step_id:** send_needs_revision
**action:** Wyslij NEEDS REVISION z konkretnym feedbackiem: sciezka raportu, Critical Issues (file:line), Warnings, co jest OK
**tool:** agent_bus_cli
**command:** `py tools/agent_bus_cli.py send --from architect --to developer --content-file tmp/review_needs_revision.md`
**verification:** Wiadomosc wyslana, zawiera Critical Issues z file:line
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Blad wysylki. Ponow."
**next_step:** receive_fixes (if PASS)

→ HANDOFF: developer. STOP.
  Mechanizm: agent_bus send
  Czekaj na: Developer poprawia i zglasza re-review.
  Nie poprawiaj kodu sam.

### Exit Gate

**Checklist:**
- [ ] `revision_sent`: Raport z konkretnym feedbackiem wyslany
- [ ] `critical_specified`: Critical Issues wskazane z file:line

**Status:**
- PASS if: wszystkie == true

---

## Faza 3c: BLOCKED (eskalacja)

**Owner:** architect

### Steps

## Step 10: Eskaluj problem architektoniczny

**step_id:** escalate_blocked
**action:** Eskaluj do czlowieka — problem architektoniczny wykryty, wymaga decyzji
**tool:** agent_bus_cli
**command:** `py tools/agent_bus_cli.py flag --from architect --reason-file tmp/review_blocked.md`
**verification:** Flag wyslany
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: yes
  - reason: "Blad flagu. Poinformuj czlowieka bezposrednio."
**next_step:** END

### Exit Gate

**Checklist:**
- [ ] `escalated`: Problem wyeskalowany do czlowieka

**Status:**
- PASS if: escalated == true

---

## Faza 4: Re-review (po poprawkach)

**Owner:** architect

### Inputs required
- [ ] `fixes_submitted`: Developer poprawil kod i zglasza ponownie

### Steps

## Step 11: Odbierz poprawki od Developera

**step_id:** receive_fixes
**action:** Odbierz ponowne zgloszenie od Developera z opisem poprawek
**tool:** Read
**command:** Przeczytaj wiadomosc od Developera z inbox
**verification:** Opis poprawek otrzymany
**on_failure:**
  - retry: no
  - skip: no
  - escalate: yes
  - reason: "Developer nie zglasza poprawek. Czekaj lub eskaluj."
**next_step:** verify_fixes (if PASS)

---

## Step 12: Zweryfikuj poprawki

**step_id:** verify_fixes
**action:** Zweryfikuj TYLKO wskazane Critical Issues i Warnings. Nie rozszerzaj zakresu review — chyba ze poprawki wprowadzaja nowe problemy.
**tool:** Read
**command:** `Read <zmienione_pliki>` — tylko pliki z Critical Issues
**verification:** Critical Issues naprawione lub wciaz obecne
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: no
  - reason: "Poprawki niekompletne."
**next_step:** re_review_assessment (if PASS)

---

## Decision Point 2: Wynik re-review

**decision_id:** re_review_assessment
**condition:** Critical Issues naprawione
**path_true:** send_pass (PASS — przejdz do Fazy 3a)
**path_false:** escalate_persistent (Critical Issues wciaz obecne po 2 iteracjach → BLOCKED)
**default:** escalate_persistent

---

## Step 13: Eskaluj persistentne Critical Issues

**step_id:** escalate_persistent
**action:** Po 2 iteracjach Critical Issues wciaz nie naprawione — eskaluj do czlowieka
**tool:** agent_bus_cli
**command:** `py tools/agent_bus_cli.py flag --from architect --reason-file tmp/review_persistent_issues.md`
**verification:** Flag wyslany
**on_failure:**
  - retry: yes
  - skip: no
  - escalate: yes
  - reason: "Blad flagu. Poinformuj czlowieka bezposrednio."
**next_step:** END

### Forbidden

- Wiecej niz 2 iteracje review na ten sam zakres — po 2 iteracjach eskalacja.
- Re-review rozszerza zakres poza oryginalne findings.

### Exit Gate

**Checklist:**
- [ ] `fixes_verified`: Critical Issues z pierwszego review zweryfikowane
- [ ] `report_updated`: Raport zaktualizowany lub nowy raport

**Status:**
- PASS if: fixes_verified == true AND critical issues naprawione
- BLOCKED if: critical issues wciaz obecne → eskalacja

---

## Forbidden

1. **Architect edytuje kod zamiast pisac raport** — scope leak.
2. **Developer ignoruje Critical Issues i commituje** — pominiecie gate'u.
3. **Review bez raportu (ustna informacja)** — raport jest artefaktem trwalym.
4. **Review kodu bez przeczytania plikow (ocena po opisie)** — niedopuszczalne.

---

## Kiedy eskalacja do czlowieka

- Po 2 iteracjach review Critical Issues wciaz nie naprawione
- Architektoniczny problem wykryty podczas review (scope creep — zmiana wymaga nowego planu)
- Konflikt Architect ↔ Developer o ocene dojrzalosci kodu

---

## Self-check

- [ ] Wszystkie zmienione pliki przeczytane?
- [ ] Raport zapisany do documents/human/reports/?
- [ ] Decyzja jednoznaczna (PASS / NEEDS REVISION / BLOCKED)?
- [ ] Critical Issues z file:line (jesli sa)?
- [ ] Wiadomosc do Developera wyslana?
- [ ] Max 2 iteracje review?

---

## Changelog

| Wersja | Data | Zmiany |
|---|---|---|
| 2.0 | 2026-03-31 | Konwersja do strict format 04R (DB-ready): wszystkie kroki z step_id, action, tool, command, verification, on_failure, next_step. Decision points z decision_id. Exit gates z item_id. HANDOFF_POINT zachowane. Faza 3c (BLOCKED) wyodrebniona. related_docs zaktualizowane (workflow_developer rozbity). |
| 1.0 | 2026-03-27 | Poczatkowa wersja — formalizacja z praktyki Architect code review |
