# Plan: narzędzia startowe Dyspozytora (handoff #414-415)

## Źródło
Specyfikacja od Architekta (msg #415, sesja 6ec1a456959c).
Spec pochodzi od Architekta → implicit plan approval → przechodzę do implementacji.

## Deliverables

### 1. render_dashboard.py (nowe narzędzie)
Generuje pliki .md w `documents/human/dashboard/`:
- `status.md` — live_agents + inbox-summary + handoffs-pending
- `workstreams.md` — workflow_execution running + backlog in_progress
- `backlog_overview.md` — planned tasks per area z priorytetami

Dane z mrowisko.db. Format: czytelny markdown (Obsidian-friendly), nie JSON.
Wywołanie: `py tools/render_dashboard.py`

### 2. backlog-summary (subkomenda agent_bus_cli.py)
GROUP BY area, status. Output JSON:
```json
{"ok": true, "data": {"Arch": {"planned": 8, "in_progress": 1}, ...}}
```

### 3. onboarding_dispatcher.md — aktualizacja
Plik już istnieje (PE stworzył). Sprawdzić czy trzeba dodać:
- `backlog-summary` (nowa komenda)
- `context_usage.py` (nowe narzędzie)
- `render_dashboard.py` (nowe narzędzie)

## Kolejność implementacji
1. backlog-summary (najmniejszy, reuse wzorca inbox-summary)
2. render_dashboard.py (średni, nowe narzędzie)
3. onboarding update (patch)

## Testy
- backlog-summary: empty DB, multiple areas, status filter
- render_dashboard.py: smoke test generacji plików, weryfikacja formatu
