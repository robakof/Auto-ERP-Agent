# Raport: Faza 0 Quick Wins — dispatcher rebuild

**Data:** 2026-03-30
**Autor:** Developer
**Plan źródłowy:** `documents/human/plans/plan_dispatcher_rebuild_v1.md` sekcja F0
**Commity:** `4285f33`, `8fd1bbe`
**Code review:** PASS (Architect, msg #542, poprawki wdrożone)

---

## 1. Hook spawn→spawn-request (backlog #219)

**Problem:** Dispatcher mógł autonomicznie spawnować/stopować agentów przez `agent_bus_cli.py spawn` — bez zatwierdzenia człowieka.

**Rozwiązanie:** Hook już istniał w `tools/hooks/pre_tool_use.py` (wdrożony wcześniej). Mechanizm:
- Pre-tool-use hook przechwytuje komendy Bash
- Regex matchuje `agent_bus_cli.py spawn|resume` (bez `-request`)
- Deny z komunikatem: "Użyj spawn-request zamiast spawn"
- `spawn-request` / `resume-request` (z `-request`) → przepuszcza
- `stop` → przepuszcza (szybkość > bezpieczeństwo, decyzja z plan v2)

**Co zrobiłem:** Brakowało testów. Dodałem 6 testów w `TestLifecycleGate`:
- `spawn` → deny ✓
- `spawn-request` → allow ✓
- `stop` → allow ✓ (nie blokowany per plan v2)
- `resume` → deny ✓
- `resume-request` → allow ✓
- `inbox` (inna komenda) → allow ✓

**Użycie:** Automatyczne — hook działa na każdą komendę Bash. Agent nie musi nic robić.

---

## 2. git_commit.py multi-agent guard (backlog #217)

**Problem:** Przy równoległych sesjach agentów, `git_commit.py --all` wykonuje `git add -A` co wciąga zmiany WSZYSTKICH agentów do jednego commitu. Incydent: PE wciągnęła zmiany Deva.

**Rozwiązanie:** Nowa funkcja `_count_active_agents()` w `tools/git_commit.py`:
```
┌─────────────────────────────────────────┐
│ git_commit.py --all                     │
│                                         │
│  1. Zapytaj mrowisko.db:                │
│     SELECT COUNT(*) FROM live_agents    │
│     WHERE status IN ('starting','active')│
│                                         │
│  2. Jeśli count > 1:                    │
│     → REFUSE: "Wielu aktywnych agentów  │
│       (N). Użyj --files [lista plików]."│
│                                         │
│  3. Jeśli count ≤ 1:                    │
│     → kontynuuj normalnie (git add -A)  │
│                                         │
│  Fallback: błąd DB → return 0 (allow)   │
└─────────────────────────────────────────┘
```

**Co NIE jest blokowane:**
- `--files a.py b.py` → zawsze dozwolone (per-file staging)
- `--dry-run` → zawsze dozwolone
- `--push-only` → nie dotyczy

**Testy:** 5 nowych w `TestMultiAgentGuard`:
- `--all` + 3 agenty → refuse ✓
- `--all` + 1 agent → allow ✓
- `--all` + 0 agentów (DB error) → allow ✓
- `--files` + 5 agentów → allow ✓
- `--dry-run` + 5 agentów → allow ✓

**Weryfikacja na żywo:** Guard zablokował mój własny commit (3 aktywne sesje w momencie commitu). Musiałem użyć `--files`.

---

## 3. Dashboard CLI (backlog #222)

**Problem:** Dispatcher potrzebował 5+ wywołań CLI żeby zorientować się w stanie mrówiska (`inbox-summary`, `live-agents`, `handoffs-pending`, `backlog-summary`, `gaps`). Koszt tokenowy i czasowy.

**Rozwiązanie:** Nowa komenda `py tools/agent_bus_cli.py dashboard` — jeden JSON:

```json
{
  "timestamp": "2026-03-30T10:23:02Z",
  "agents": {
    "active": [
      {"role": "developer", "session_id": "abc", "task": "...", "last_activity": "..."}
    ],
    "stale": [
      {"role": "analyst", "session_id": "def", "display_status": "stale", "last_activity": "..."}
    ],
    "stopped_count": 21
  },
  "inbox": {
    "unread_by_role": {"developer": 1, "dispatcher": 2, "prompt_engineer": 11}
  },
  "handoffs": {
    "pending": [
      {"id": 42, "sender": "developer", "recipient": "architect", "title": "code review"}
    ]
  },
  "backlog": {
    "planned_by_area": {"Dev": 23, "Arch": 12, "Prompt": 4},
    "in_progress": 5
  },
  "alerts": [
    "Agent analyst stale (last_activity: 2026-03-30 09:50:00)",
    "Handoff developer→architect czeka na odbiorcę",
    "2 flag(s) czeka na człowieka"
  ]
}
```

**Źródła danych:**
| Sekcja | Źródło |
|--------|--------|
| agents.active/stale | widok `v_agent_status` (progi: working <5min, stale <30min, dead >30min) |
| agents.stopped_count | `live_agents WHERE status = 'stopped'` |
| inbox.unread_by_role | `messages WHERE status = 'unread' GROUP BY recipient` |
| handoffs.pending | `messages type='handoff'` + LEFT JOIN live_agents (brak żywego odbiorcy) |
| backlog | `backlog GROUP BY area, status` |
| alerts | automatyczne: stale/dead agents + pending handoffs + unread flags |

**Testy:** 3 testy integracyjne w `TestDashboard`:
- Empty DB → wszystko zerowe ✓
- Seeded inbox + backlog → poprawne liczby ✓
- Live agents (active/stale/stopped) → poprawna klasyfikacja + alert ✓

---

## Poprawki z code review (commit `8fd1bbe`)

| Issue | Fix |
|-------|-----|
| W1: `stop` nie powinien być blokowany | Usunięto z LIFECYCLE_GATE, regex zmieniony na `spawn\|resume` |
| W3: `--task` przy złym parserze | Przeniesione z linii po `p_resume_req` do `p_spawn_req` |
| S2: brak testu live_agents w dashboard | Dodany `test_dashboard_with_live_agents` |

---

## Podsumowanie testów

| Suite | Wynik |
|-------|-------|
| test_pre_tool_use.py | 63/63 PASS |
| test_git_commit.py | 27/27 PASS |
| test_agent_bus_cli.py | 75/75 PASS |
| **Razem** | **165/165 PASS** |

---

## Co zostało do Fazy 6 (Publikacja)

- [ ] Dokumentacja `dashboard` w CLAUDE.md (sekcja komendy agent_bus)
- [ ] Notyfikacja do dispatchera o nowym narzędziu
- [ ] Push
