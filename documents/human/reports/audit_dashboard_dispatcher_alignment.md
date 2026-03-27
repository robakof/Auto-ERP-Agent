# Audyt: Dashboard ↔ Dispatcher alignment

**Data:** 2026-03-27
**Autor:** Architect
**Cel:** 100% alignment — brak możliwości aby człowiek i Dispatcher widzieli różne rzeczy

---

## Diagnoza: problem jest fundamentalny

Shared files (session_id.txt, session_data.json) to tylko symptom. Root cause jest głębszy:

**render_dashboard.py zawiera business logic która nie jest dostępna dla Dispatchera.**

Dashboard nie jest "renderingiem danych z DB" — jest osobnym interpretatorem z własnymi regułami.
Dispatcher czyta te same tabele, ale interpretuje je inaczej. Wynik: człowiek i Dispatcher
widzą różne rzeczy patrząc na te same dane.

---

## Znalezione divergencje

### D1: Session status — "Z człowiekiem" vs "active" (CRITICAL)

**Dashboard** (`render_dashboard.py:78-97`):
```
"Z człowiekiem" jeśli:
  (a) session_id == session_data.json (shared file — zepsute w multi-session), LUB
  (b) last_activity < 5 minut temu
"Stoi" jeśli:
  nie spełnia (a) ani (b)
```

**Dispatcher** (`live-agents`):
```
Widzi surowe pola: status='active', last_activity='2026-03-27 14:06:00'
Nie wie o regule 5-minutowej.
Nie wie co znaczy "Stoi" vs "Z człowiekiem".
```

**Efekt:** Dashboard pokazuje sesję jako "Stoi" (bo heartbeat zepsute = stary timestamp).
Dispatcher widzi `status=active` i myśli że agent żyje. **Dwa różne obrazy rzeczywistości.**

### D2: Backlog priorytet — score niewidoczny (WARNING)

**Dashboard** (`render_dashboard.py:28-34`):
```sql
ROUND((value_points + effort_points - 2) * 9.0 / 4 + 1)
```
Top 10 posortowane tym score. Człowiek widzi priorytet.

**Dispatcher:** Widzi surowe `value` i `effort` jako tekst. Nie zna formuły score.
Priorytetyzacja rozbieżna — Dispatcher może zaproponować inne zadanie niż człowiek widzi na dashboardzie.

### D3: Handoffs pending — Dispatcher widzi, Dashboard nie (WARNING)

**Dispatcher** (`handoffs-pending`):
```sql
SELECT m.* FROM messages m
LEFT JOIN live_agents la ON la.role = m.recipient AND la.status IN ('starting', 'active')
WHERE m.type = 'handoff' AND m.status = 'unread' AND la.id IS NULL
```
Krytyczna informacja: "kto czeka na odbiór a nie ma żywego agenta?"

**Dashboard:** Nie pokazuje tego. Człowiek nie wie które handoffy są zablokowane.

### D4: Workflow aggregation — różna granulacja (LOW)

**Dashboard:** "Tworzenie konwencji | 4" (zagregowane).
**Dispatcher:** Widzi 4 osobne execution records z session_id i rolą.
Mniej groźne — Dashboard upraszcza, ale nie kłamie.

### D5: In-progress tasks — Dashboard ukrywa ID (LOW)

**Dashboard:** Pokazuje `| Obszar | Tytuł |` — brak ID.
**Dispatcher:** Ma pełne rekordy z ID, depends_on, timestamps.
Mniej groźne — to kwestia formatu, nie logiki.

---

## Architektura docelowa: Single Interpretation Layer

**Zasada: render_dashboard.py = DUMB RENDERER. Zero business logic.**

Cała interpretacja danych musi żyć w jednym miejscu, dostępnym zarówno dla:
- render_dashboard.py (human view)
- agent_bus_cli.py (Dispatcher view)
- session_init.py (context loading)

### Wariant: SQL Views w DB

Każda "interpretacja" staje się VIEW w SQLite. Dashboard i Dispatcher czytają ten sam view.

```sql
-- View: v_agent_status
-- Single source of truth for session status
CREATE VIEW v_agent_status AS
SELECT
    session_id,
    role,
    task,
    status AS raw_status,
    last_activity,
    claude_uuid,
    CASE
        WHEN status = 'stopped' THEN 'stopped'
        WHEN status = 'starting' THEN 'starting'
        WHEN last_activity > datetime('now', '-5 minutes') THEN 'working'
        WHEN last_activity > datetime('now', '-30 minutes') THEN 'stale'
        ELSE 'dead'
    END AS display_status,
    created_at
FROM live_agents
WHERE status IN ('starting', 'active');

-- View: v_backlog_scored
-- Single source of truth for backlog priority
CREATE VIEW v_backlog_scored AS
SELECT *,
    ROUND(
        (CASE value WHEN 'wysoka' THEN 3 WHEN 'srednia' THEN 2 ELSE 1 END +
         CASE effort WHEN 'mala' THEN 3 WHEN 'srednia' THEN 2 ELSE 1 END - 2
        ) * 9.0 / 4 + 1
    ) AS score
FROM backlog;

-- View: v_handoffs_blocked
-- Handoffs with no live recipient
CREATE VIEW v_handoffs_blocked AS
SELECT m.*
FROM messages m
LEFT JOIN live_agents la
    ON la.role = m.recipient AND la.status IN ('starting', 'active')
WHERE m.type = 'handoff' AND m.status = 'unread' AND la.id IS NULL;
```

### Efekt

| Komponent | Przed (N interpretacji) | Po (1 interpretacja) |
|---|---|---|
| render_dashboard.py | Own 5-min logic + session_data.json | `SELECT * FROM v_agent_status` |
| agent_bus_cli live-agents | Raw status/last_activity | `SELECT * FROM v_agent_status` |
| session_init context | Raw fields | `SELECT * FROM v_agent_status` |
| Backlog priorytet | Dashboard: score formula / Dispatcher: raw | `SELECT * FROM v_backlog_scored` |
| Handoffs blocked | Dispatcher: query / Dashboard: brak | `SELECT * FROM v_handoffs_blocked` |

**Dashboard i Dispatcher czytają te same views → architektonicznie nie mogą się rozjechać.**

---

## Plan implementacji

### Faza 1: SQL Views (eliminacja divergencji D1, D2, D3)

1. Migracja: dodaj 3 views do mrowisko.db (`v_agent_status`, `v_backlog_scored`, `v_handoffs_blocked`)
2. render_dashboard.py: zamień business logic na SELECT z views
3. agent_bus_cli `live-agents`: zamień raw query na `v_agent_status`
4. Dashboard: dodaj sekcję "Handoffs blocked" (z `v_handoffs_blocked`)

**Efekt: D1, D2, D3 zamknięte. Jedna interpretacja.**

### Faza 2: Heartbeat fix (eliminacja stale data)

1. on_user_prompt.py: heartbeat po `claude_uuid` zamiast shared file (odpowiedź #454)
2. Inline cleanup w render_dashboard: `UPDATE ... WHERE last_activity < datetime('now', '-30 minutes')`

**Efekt: heartbeat wiarygodny → display_status w view poprawny.**

### Faza 3: Dashboard rozszerzenie

1. Mrowisko.md: pokaż `display_status` z view (working/stale/dead zamiast "Z człowiekiem"/"Stoi")
2. Mrowisko.md: dodaj sekcję "Zablokowane handoffy" (z `v_handoffs_blocked`)
3. Kolejka.md: pokaż score z view (już jest, ale teraz z view)

### Faza 4: Deprecation

1. Usuń business logic z render_dashboard.py (`_session_status()`, `SCORE_SQL`)
2. Usuń read session_data.json z render_dashboard.py (view nie potrzebuje pliku)

---

## Trade-offy

| Zyskujemy | Tracimy |
|---|---|
| 100% alignment Dashboard ↔ Dispatcher | Views to dodatkowa warstwa w DB |
| Jedna zmiana logiki = wszędzie zaktualizowane | Migracja views wymaga ~1 sesji Dev |
| Dashboard staje się dumb renderer (prostszy) | Views mogą spowolnić query (negligible w SQLite) |
| Dispatcher może podejmować decyzje widząc to co człowiek | - |

**Odwracalność:** Views można usunąć bez wpływu na dane. Zero risk.

---

## Rekomendacja

Faza 1 (SQL Views) rozwiązuje 3/5 divergencji i ustanawia pattern. Faza 2 naprawia dane źródłowe (heartbeat). Razem = 100% alignment.

Effort: ~2 sesje Dev (Faza 1 + 2), ~1 sesja Dev (Faza 3 + 4).
Value: Dyspozytor staje się wiarygodny. Człowiek i Dispatcher widzą dokładnie to samo.
