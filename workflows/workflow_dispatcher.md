---
workflow_id: dispatcher_cycle
version: "1.0"
owner_role: dispatcher
trigger: "Dyspozytor rozpoczyna cykl pracy (pętla ciągła, long-running session)"
participants:
  - dispatcher (owner)
  - human (eskalacja, instrukcje strategiczne)
related_docs:
  - documents/dispatcher/DISPATCHER.md
  - documents/human/plans/SCOPE_pm_role.md
prerequisites:
  - session_init_done
outputs:
  - type: state
    field: agents_spawned
  - type: state
    field: handoffs_closed
  - type: log
    field: raport stanu mrowiska
---

# Workflow: Cykl pracy Dyspozytora

Dyspozytor wykonuje ciągłą pętlę: orientacja → dispatch → monitor → raport.
Każda iteracja pętli to jeden cykl. Po cyklu — powrót do kroku 1.

## Outline

1. **Orientacja** — odczytaj stan mrowiska (inbox, backlog, live_agents, handoffs)
2. **Dispatch** — spawuj agentów per zdarzenia (wiadomości, taski, handoffy)
3. **Monitor** — sprawdź aktywnych agentów (utknięci, zakończeni)
4. **Raport** — pokaż stan człowiekowi (heartbeat)
5. **[LOOP]** — wróć do kroku 1

---

## Faza 1: Orientacja

**Owner:** Dispatcher

### Steps

1. Pobierz podsumowanie inboxów:
   ```
   py tools/agent_bus_cli.py inbox-summary
   ```

2. Pobierz listę aktywnych agentów:
   ```
   py tools/agent_bus_cli.py live-agents
   ```

3. Pobierz pending handoffy:
   ```
   py tools/agent_bus_cli.py handoffs-pending
   ```

4. Pobierz planned tasks z backlogu:
   ```
   py tools/agent_bus_cli.py backlog --status planned
   ```

5. Oceń sytuację:
   - Ile ról ma unread wiadomości?
   - Ile agentów aktywnych?
   - Ile handoffów czeka na odbiorcę?
   - Ile planned tasks w backlogu?

### Exit gate

PASS: stan mrowiska znany (inbox, live_agents, handoffs, backlog odczytane).

---

## Faza 2: Dispatch

**Owner:** Dispatcher

Spawn agentów per zdarzenia. Kolejność priorytetów:
1. Handoffy pending (odbiorca nie żyje → spawn)
2. Inbox — role z unread wiadomościami
3. Backlog — planned tasks (highest value first, przy równej wartości lowest effort first)

### Steps

1. **Handoffy:** Dla każdego pending handoffa:
   1.1. Sprawdź czy agent-odbiorca już nie żyje (live-agents).
   1.2. Jeśli nie żyje → spawuj odbiorcę z kontekstem handoffa.
   ```
   py tools/agent_bus_cli.py spawn --from dispatcher --role <rola> --task "Masz handoff w inbox. Przeczytaj i kontynuuj."
   ```

2. **Inbox:** Dla każdej roli z unread:
   2.1. Sprawdź czy agent tej roli już nie pracuje (live-agents).
        Jeśli pracuje → SKIP (agent przeczyta inbox sam).
   2.2. Jeśli nie pracuje → spawuj.
   ```
   py tools/agent_bus_cli.py spawn --from dispatcher --role <rola> --task "Masz wiadomości w inbox. Przeczytaj i zrealizuj."
   ```

3. **Backlog:** Dla najwyższego priorytetu planned task:
   3.1. Sprawdź czy agent docelowej roli już nie pracuje.
   3.2. Jeśli nie → zaktualizuj status i spawuj.
   ```
   py tools/agent_bus_cli.py backlog-update --id <id> --status in_progress
   py tools/agent_bus_cli.py spawn --from dispatcher --role <rola> --task "Backlog #<id>: <tytuł>. Przeczytaj backlog item i zrealizuj."
   ```
   3.3. Spawuj jednego agenta na raz. Czekaj na potwierdzenie spawnu przed kolejnym.

### Forbidden

- Nie spawuj duplikatów — przed każdym spawnem sprawdź live-agents.
- Nie spawuj agenta do roli która już ma aktywnego agenta BEZ workflow_id (wolny agent obsłuży inbox sam).
- Wyjątek: wieloinstancyjność — jeśli aktywny agent jest w workflow (ma workflow_id), nowy agent dostaje zadania spoza tego workflow.

### Exit gate

PASS: wszystkie pending handoffy obsłużone, role z unread mają agenta (lub uzasadnienie dlaczego nie), top backlog task dispatched (lub brak wolnych slotów).
BLOCKED: spawn failed → eskaluj do człowieka.

---

## Decision Point: Czy eskalować?

**decision_id:** check_escalation
**condition:** Nieznany typ zdarzenia LUB spawn failed LUB konflikt priorytetów
**path_true:** Eskalacja do człowieka (flag)
**path_false:** Faza 3 (Monitor)
**default:** Faza 3

---

## Faza 3: Monitor

**Owner:** Dispatcher

### Steps

1. Sprawdź live-agents:
   ```
   py tools/agent_bus_cli.py live-agents
   ```

2. Dla każdego aktywnego agenta oceń:
   - Czy pracuje normalnie? → OK, nic nie rób.
   - Czy zakończył? → Sprawdź handoffs-pending, spawuj odbiorcę jeśli potrzebny.
   - Czy utknął (długo aktywny, brak postępu)? → Sprawdź transcript:
     ```
     py tools/read_transcript.py --invocation-id <id>
     ```
     Jeśli utknął → eskaluj do człowieka (flag).

### Exit gate

PASS: wszyscy aktywni agenci zdiagnozowani, zakończeni obsłużeni, utknięci eskalowani.

---

## Faza 4: Raport

**Owner:** Dispatcher

### Steps

1. Pokaż człowiekowi stan mrowiska:
   ```
   Agenci aktywni: N (per rola: ...)
   Inbox: M unread (per rola: ...)
   Backlog: K planned tasks
   Handoffy pending: H
   Ostatnie spawny: [lista]
   Następna akcja: [co planujesz]
   ```

2. Zaloguj cykl:
   ```
   py tools/agent_bus_cli.py log --role dispatcher --content-file tmp/log_dispatcher_cycle.md
   ```

### Exit gate

PASS: raport pokazany, log zapisany.

---

## Decision Point: Następny cykl?

**decision_id:** check_next_cycle
**condition:** Sesja aktywna (nie zakończona przez człowieka)
**path_true:** Faza 1 (nowy cykl orientacji)
**path_false:** Zamknięcie sesji
**default:** Faza 1

---

## Zamknięcie sesji

**Owner:** Dispatcher

1. Zapisz końcowy raport stanu.
2. Zaloguj sesję.
3. Self-handoff jeśli są niedokończone sprawy:
   ```
   py tools/agent_bus_cli.py handoff --from dispatcher --to dispatcher --phase "cykl N" --status PASS --summary "..." --next-action "..."
   ```

---

## Routing per typ zdarzenia

| Zdarzenie | Docelowa rola | Jak określić |
|-----------|--------------|-------------|
| Wiadomość w inbox | Rola odbiorcy | inbox-summary |
| Planned task | Per area: Dev→developer, Arch→architect, Prompt→prompt_engineer, ERP→erp_specialist, Metodolog→metodolog | backlog --area |
| Handoff pending | Rola odbiorcy handoffa | handoffs-pending |
| Bloker / nieznana sytuacja | human | flag |

---

## Forbidden

1. Nie spawuj bez sprawdzenia live-agents (ryzyko duplikatu).
2. Nie podejmuj decyzji strategicznych — eskaluj do człowieka.
3. Nie priorytetyzuj autonomicznie (v1) — realizuj kolejkę per backlog.
4. Nie ignoruj pending handoffów — to najwyższy priorytet (kontynuacja pracy).
5. Nie wchodź w szczegóły zadania agenta — Twoja rola to dispatch, nie execution.

---

## Changelog

| Wersja | Data | Zmiany |
|---|---|---|
| 1.0 | 2026-03-26 | Początkowa wersja — cykl orientacja → dispatch → monitor → raport. Narzędzia: inbox-summary, live-agents, handoffs-pending. |
