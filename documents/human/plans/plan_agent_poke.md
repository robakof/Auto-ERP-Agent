# Plan: Agent poke — komunikacja z żywym agentem

## Problem
Dyspozytor nie może wejść w interakcję z agentem który już żyje w innym terminalu.
Agent czyta inbox tylko raz (session_init) — w trakcie pracy jest głuchy.

## Ograniczenie techniczne
Claude Code hooks:
- `UserPromptSubmit` — **nie może** zwrócić danych do agenta (one-way, observability only)
- `PreToolUse` — **jedyny** hook który może wstrzyknąć feedback (przez `permissionDecisionReason`)
- `PostToolUse` — observability only

## Proponowane rozwiązanie: PreToolUse poke check

### Flow
1. Dyspozytor: `py tools/agent_bus_cli.py send --from dispatcher --to <rola> --type poke --content-file tmp/poke.md`
2. `pre_tool_use.py` — na każdym wywołaniu narzędzia sprawdza inbox po type=poke
3. Jeśli jest unread poke → zwraca `deny` z treścią poke w `permissionDecisionReason`
4. Agent widzi denial → czyta treść poke → reaguje → ponawia narzędzie
5. Po odczytaniu poke jest automatycznie oznaczany jako `read`

### Dlaczego deny a nie allow
- `permissionDecisionReason` przy `allow` nie jest gwarantowanie widoczny dla agenta
- `deny` wymusza odczytanie reason przez agenta (nie może kontynuować bez reakcji)
- Jednorazowy deny per poke — po oznaczeniu jako read, kolejne wywołania przechodzą normalnie

### Zakres zmian

1. **`tools/hooks/pre_tool_use.py`** — nowa funkcja `_check_poke()` (~20 linii)
   - Czyta inbox: `SELECT ... WHERE recipient=? AND type='poke' AND status='unread' LIMIT 1`
   - Jeśli znaleziono → deny z treścią + mark as read
   - Jeśli brak → pass through (nie blokuje)

2. **`tools/agent_bus_cli.py`** — brak zmian (send z --type poke już działa, type jest free-form)

3. **Testy** — test_pre_tool_use.py: test poke check

### Czego NIE robimy
- Nie zmieniamy agent_bus_cli (type jest free-form)
- Nie dodajemy nowego hooka
- Nie ruszamy UserPromptSubmit
- Nie budujemy kolejki / priority system — jeden poke na raz

### Ograniczenia MVP
- Agent widzi poke dopiero przy następnym tool call (nie natychmiast)
- Deny blokuje jedno wywołanie — agent musi ponowić
- Jedno poke na raz (LIMIT 1)
- Brak gwarancji że agent prawidłowo przetworzy poke (prompt-only)

### Exit gate
- [ ] Poke check w pre_tool_use.py
- [ ] Test PASS
- [ ] Smoke test: send poke → agent widzi deny z treścią
- [ ] Commit
