---
workflow_id: prompt_patch
version: "1.0"
owner_role: prompt_engineer
trigger: "PE otrzymuje suggestion, wiadomość lub cel jakościowy wymagający zmiany w prompcie/workflow"
participants:
  - prompt_engineer (owner)
  - human (review)
related_docs:
  - documents/prompt_engineer/PROMPT_ENGINEER.md
  - documents/conventions/CONVENTION_PROMPT.md
  - documents/conventions/CONVENTION_WORKFLOW.md
prerequisites:
  - session_init_done
  - source_identified (suggestion, inbox msg, lub cel jakościowy)
outputs:
  - type: file
    field: "zmodyfikowany prompt/workflow"
  - type: commit
  - type: message
    field: "notyfikacja do ról dotkniętych zmianą (jeśli cross-role)"
---

# Workflow: Prompt Patch

Pojedyncza zmiana w prompcie lub workflow — nie refaktor (bez archiwizacji, bez audytu).
Używaj gdy zmiana dotyczy jednego pliku, jednej sekcji. Dla zmian wielu plików → `workflow_prompt_refactor`.

**Zasada:** Patch jest domyślną skalą interwencji PE. Refaktor wymaga uzasadnienia.

## Outline

1. **Źródło** — odczytaj zgłoszenie
2. **Weryfikacja** — sprawdź w źródle czy problem jest realny
3. **Diagnoza** — sklasyfikuj typ problemu
4. **Patch** — zaproponuj zmianę (old → new)
5. **Review** — pokaż użytkownikowi
6. **Zastosowanie** — edytuj, commit, powiadom

---

## Faza 1: Źródło

**Owner:** prompt_engineer

### Steps

1. Odczytaj zgłoszenie: suggestion, wiadomość w inbox, lub cel jakościowy.
2. Zanim sklasyfikujesz po tytule — przeskanuj treść pod kątem:
   - self-reported violation: "naruszyłem", "obejście", "złamałem regułę"
   - agent zna regułę i ją cytuje, ale zachował się inaczej
   Jeśli tak → typ problemu to `lost_salience` lub `gate_omission`, nie `outside_prompt_layer`.

### Exit gate

PASS: źródło przeczytane, wstępna ocena typu.

---

## Faza 2: Weryfikacja

**Owner:** prompt_engineer

### Steps

1. Zweryfikuj zgłoszenie w źródle — przeczytaj sesję/konwersację agenta.
   ```
   py tools/search_conversation.py --session <session_id>
   ```
2. Sprawdź:
   - Czy agent w ogóle wszedł w workflow?
   - Czy agent miał regułę i ją zignorował, czy reguła nie istnieje?
   - Czy zgłoszenie opisuje rzeczywisty problem?
3. Przeczytaj aktualny prompt którego dotyczy zgłoszenie.

### Exit gate

PASS: problem potwierdzony w źródle, aktualny prompt przeczytany.
EXIT (KEEP): problem nie potwierdza się — prompt jest OK, zamknij zgłoszenie.

---

## Faza 3: Diagnoza i patch

**Owner:** prompt_engineer

### Steps

1. **Czy problem da się rozwiązać mechanicznie?**
   Zanim napiszesz patch — sprawdź czy można zablokować obejście narzędziem:
   - Hook (pre_tool_use, session_end) który wymusza zachowanie?
   - Walidacja w CLI (agent_bus_cli, git_commit) która odrzuca błędne wywołanie?
   - Zmiana architektury która eliminuje możliwość błędu?

   Jeśli tak → ESCALATE_ARCHITECTURE do Developera. Prompt patch na obejście
   które można zablokować mechanicznie to plaster — nie rozwiązanie.

   Jeśli nie (problem jest w rozumowaniu agenta, nie w braku blokady) → kontynuuj.

2. Sklasyfikuj typ problemu:
   - `scope_leak` — agent robi rzeczy poza zakresem
   - `lost_salience` — krytyczna reguła ignorowana (zakopana)
   - `gate_omission` — agent pomija warunki wejścia/wyjścia fazy
   - `output_ambiguity` — format wyniku niejednoznaczny
   - `conflicting_instructions` — dwie reguły mówią coś innego
   - `unnecessary_length` — duplikacja, prose zamiast kontraktu
   - `missing_checkpoint` — brak weryfikacji w checkliście
   - `structural_debt` — niezgodność z konwencją (→ rozważ refaktor zamiast patch)
   - `outside_prompt_layer` — problem wymaga zmiany narzędzia/architektury (→ ESCALATE)

3. Zaproponuj patch:
   - Pokaż old → new (lub nową sekcję jeśli brakuje)
   - Uzasadnij dlaczego patch powinien zadziałać

4. Oceń patch 6 wymiarami:
   - **clarity** — czy instrukcja jest jednoznaczna?
   - **salience** — czy jest widoczna w odpowiednim momencie?
   - **scope** — czy nie wychodzi poza zakres roli/pliku?
   - **gates** — czy gate'y workflow są zachowane?
   - **output** — czy format outputu jest deterministyczny?
   - **modularity** — czy zmiana jest w odpowiedniej warstwie (shared > role > workflow)?

   Patch nie może pogarszać 2 wymiarów żeby poprawić 1.

5. Opisz co przetestować — jaki typ sesji agenta uruchomić.

### Exit gate

PASS: patch zaproponowany, 6 wymiarów ocenionych, plan testów opisany.
ESCALATE: problem poza warstwą promptu (→ Developer lub Architect).

---

## Faza 4: Review

**Owner:** prompt_engineer + human

### Steps

1. Pokaż użytkownikowi w formacie output contract:
   ```
   Recommendation: PROMOTE_CANDIDATE | REVISE | KEEP | ESCALATE_ARCHITECTURE
   Agent: <agent_id>
   Prompt file: <ścieżka>
   Problem type: <label>

   Diagnosis:
   - <co nie działało>

   Proposed patch:
   - <old → new>

   Expected effect:
   - <jakie zachowanie powinno się poprawić>

   Risks:
   - <co może pójść nie tak>
   ```

   → HANDOFF: human. STOP.
     Mechanizm: czekaj na user input
     Czekaj na: zatwierdzenie lub poprawki
     Nie edytuj pliku bez zatwierdzenia.

2. Użytkownik zatwierdził → Faza 5.
3. Użytkownik żąda poprawek → wróć do Fazy 3.

### Exit gate

PASS: użytkownik zatwierdził patch.

---

## Faza 5: Zastosowanie

**Owner:** prompt_engineer

### Steps

1. Zastosuj patch (`Edit`).
2. Commit:
   ```
   py tools/git_commit.py --message "fix(PE): <opis patcha>" --all
   ```
3. Jeśli zmiana dotyczy pliku cross-role (CLAUDE.md, workflow wspólny):
   Powiadom dotknięte role:
   ```
   py tools/agent_bus_cli.py send --from prompt_engineer --to <rola> --content-file tmp/patch_notification.md
   ```

### Exit gate

PASS: commit wykonany, notyfikacje wysłane (jeśli cross-role).

---

## Forbidden

1. **Nie patchuj bez weryfikacji w źródle.**
   Faza 2 chroni przed patchowaniem objawu zamiast przyczyny.

2. **Nie łącz wielu niezwiązanych patchy w jeden workflow run.**
   Jeden patch = jeden problem = jeden workflow run. Osobne śledzenie.

3. **Nie eskaluj bez oceny czy reguła była jasna.**
   Jeśli agent zna regułę i ją łamie → lost_salience, nie outside_prompt_layer.

---

## Self-check

- [ ] Źródło przeczytane i zweryfikowane w konwersacji?
- [ ] Typ problemu sklasyfikowany?
- [ ] Patch ma old → new (nie tylko opis)?
- [ ] 6 wymiarów ocenionych?
- [ ] Użytkownik zatwierdził?
- [ ] Commit wykonany?
- [ ] Notyfikacja do ról (jeśli cross-role)?

---

## Changelog

| Wersja | Data | Zmiany |
|---|---|---|
| 1.0 | 2026-03-27 | Formalizacja z praktyki PE: sesje 9b82956c95c0 (gate_omission patch), 2d371a766a10 (pre-gate #0), 3e84306e15bb (workflow gate + exploration) |
