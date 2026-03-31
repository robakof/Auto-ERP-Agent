# Plan: Spawn Policy Config — konfigurowalny tryb auto/approval

**Data:** 2026-03-30
**Trigger:** Dispatcher msg #543 — "Dispatcher nie powinien wiedzieć czy auto czy approval"
**Scope:** Średni — zmiana w 3 plikach + nowy config + testy

---

## Problem

Hook blokuje `spawn`/`resume` → wymusza `-request`. Dispatcher musi wiedzieć że istnieją dwa warianty komendy. To odwrócona odpowiedzialność — system powinien decydować, nie agent.

## Rozwiązanie

### 1. Nowy config: `config/spawn_policy.json`

```json
{
  "spawn": "approval",
  "stop": "auto",
  "resume": "approval"
}
```

Wartości: `"auto"` (wykonaj od razu) | `"approval"` (utwórz invocation, czekaj na dialog VS Code).

### 2. Zmiana w `cmd_spawn` (agent_bus_cli.py)

Obecny flow:
- `spawn` → bezpośredni URI handler → terminal
- `spawn-request` → invocation pending → extension dialog → terminal

Nowy flow:
- `spawn` → czytaj config → auto? wykonaj bezpośrednio : utwórz invocation
- `spawn-request` → zostaje (backward compat, ale nie wymagany)

Analogicznie `cmd_resume`. `cmd_stop` — już teraz nie blokowany.

### 3. Usunięcie LIFECYCLE_GATE z pre_tool_use.py

Hook nie blokuje spawn/resume — routing jest w samym narzędziu.
Testy lifecycle gate → aktualizacja (spawn allowed, resume allowed).

### 4. Pliki do zmiany

| Plik | Zmiana |
|------|--------|
| `config/spawn_policy.json` | NOWY — config per-action |
| `tools/agent_bus_cli.py` | `cmd_spawn` i `cmd_resume` czytają config i routują |
| `tools/hooks/pre_tool_use.py` | Usunięcie LIFECYCLE_GATE |
| `tests/test_pre_tool_use.py` | Aktualizacja testów lifecycle |
| `tests/test_agent_bus_cli.py` | Testy policy routing (auto vs approval) |

### 5. Exit gate

- [ ] Config istnieje i jest czytelny
- [ ] `spawn` z policy=auto → bezpośrednie wykonanie
- [ ] `spawn` z policy=approval → invocation pending
- [ ] Hook nie blokuje spawn/resume
- [ ] Testy PASS
