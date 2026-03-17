# Mrowisko Runner — Instance Routing (Faza 1b)

## Problem

Obecny model adresuje wiadomości do roli (`recipient = "analyst"`).
Przy wielu instancjach tej samej roli wszystkie widzą ten sam task i mogą go podjąć.
Brak mechanizmu parowania — agent nie wie do której konkretnie instancji odpowiada.

## Model sesji i kontekstu

Każda sesja agenta jest **efemeryczna** — żyje do progu autocompact, potem clear.
DB jest jedyną pamięcią trwałą (logi sesji, wiadomości, workflow state).
Nowa sesja czyta DB i wznawia workflow dokładnie tam gdzie poprzednia skończyła.
`--resume` niepotrzebne — każde wywołanie subprocess może startować świeżo.

**`busy` = ochrona budżetu tokenowego workflow.**
Instancja busy nie przyjmuje nowych niezwiązanych tasków — chroni pozostałe
okno kontekstowe dla dokończenia aktywnego workflow.
Gdy sesja się wyczyści (clear) → runner restartuje TĘ SAMĄ sesję dla aktywnego
workflow (czyta DB, podnosi kontekst), nie bierze nowego taska.

## Model docelowy (Faza 1b)

```
Wiadomość do roli:      recipient = "analyst"
Wiadomość do instancji: recipient = "analyst:a1b2c3"
```

Routing do roli = dowolna wolna instancja bierze atomic claim.
Routing do instancji = wyłącznie ta instancja odbiera.

Po claimie task ma `claimed_by = "analyst:a1b2c3"`.
Dalsze wiadomości w tej rozmowie idą na `analyst:a1b2c3` — para jest ustalona.

---

## Mapa zmian

### 1. tools/lib/agent_bus.py — JEDYNE źródło logiki DB

**Schemat (migracja addytywna, nie breaking):**

```sql
-- Nowa tabela
CREATE TABLE agent_instances (
    instance_id    TEXT PRIMARY KEY,       -- "erp_specialist:a1b2c3"
    role           TEXT NOT NULL,
    status         TEXT NOT NULL DEFAULT 'idle',  -- idle | busy | terminated
    active_task_id INTEGER,               -- msg_id aktywnego workflow (NULL gdy idle)
    started_at     TEXT NOT NULL DEFAULT (datetime('now')),
    last_seen_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Nowa kolumna w messages (nullable, backward compatible)
ALTER TABLE messages ADD COLUMN claimed_by TEXT;
```

**Nowe metody AgentBus:**

```python
register_instance(instance_id, role) -> None
heartbeat(instance_id) -> None                        # co 10s z runnera
set_instance_busy(instance_id, task_id) -> None       # zapisuje active_task_id
set_instance_idle(instance_id) -> None                # czyści active_task_id
terminate_instance(instance_id) -> None
get_free_instances(role) -> list[dict]                # idle + last_seen < 60s temu
claim_task(msg_id, instance_id) -> bool               # atomic; False = ktoś zdążył
get_pending_tasks(role, instance_id) -> list[dict]    # recipient IN (role, instance_id)
```

**Zmiany istniejących metod:** brak — get_inbox, send_message, mark_read nie są dotknięte.

---

### 2. tools/mrowisko_runner.py

**Zmiany:**
- Generuje `instance_id = f"{role}:{uuid[:6]}"` przy starcie
- Rejestruje instancję przez `bus.register_instance()`
- Heartbeat co 10s w wątku tła (threading.Timer lub pętla)
- `get_pending_tasks` zamiast bezpośredniego SELECT
- `claim_task` atomically przed pokazaniem Y/n; skip jeśli False
- Wyrejestrowuje przy wyjściu (try/finally)
- Wstrzykuje `instance_id` do promptu agenta jako adres zwrotny:
  ```
  [TASK od: developer:x1y2z3]
  [ADRES ZWROTNY: erp_specialist:a1b2c3]
  ...treść...
  ```

---

### 3. tools/agent_bus_cli.py — minimal

Nowe komendy CLI dla runnera (opcjonalnie, do debugowania):

```
python tools/agent_bus_cli.py instances              # lista aktywnych instancji
python tools/agent_bus_cli.py instance-terminate --id "analyst:a1b2c3"
```

Istniejące komendy (`send`, `inbox`, `mark-read`) — bez zmian.

---

### 4. tools/agent_bus_server.py — bez zmian

`get_inbox(role=...)` nadal działa dla roli. Instance routing obsługuje runner bezpośrednio przez AgentBus.

---

### 5. tools/render.py — bez zmian

Renderuje messages.recipient jako-jest (string). Wyświetli zarówno `analyst` jak i `analyst:a1b2c3`.

---

### 6. Testy

- `tests/test_agent_bus.py` — nowe testy: `register_instance`, `claim_task` (atomic), `get_pending_tasks` (routing rola + instancja), `heartbeat`
- `tests/test_mrowisko_runner.py` — testy `build_instance_id`, heartbeat (mock threading), claim failure path

---

## Analiza spaghetti

**Pytanie: ile miejsc trzeba zmienić jeśli zmienia się format `recipient`?**

| Co się zmienia | Gdzie skutek |
|---|---|
| Format `recipient` (string) | agent_bus.py (1 metoda: `get_pending_tasks`) — reszta traktuje recipient jako opaque string |
| Tabela `agent_instances` | agent_bus.py (schema + 4 metody) — zero innych plików |
| Logika claim | agent_bus.py (1 metoda) + mrowisko_runner.py (1 wywołanie) |
| Prompt z adresem zwrotnym | mrowisko_runner.py (1 miejsce: `build_prompt`) |

**Wniosek:** Logika DB jest zamknięta w `agent_bus.py`. Runner to konsument. Render i CLI traktują `recipient` jako opaque — zero zmian. Brak spaghetti.

---

## Co zostaje poza Fazą 1b

- Auto-spawn nowej instancji gdy `get_free_instances` zwróci pustą listę
- Wizualizacja par (sesja A ↔ sesja B) w dashboard
- `pair_id` jako osobne pole (na razie wystarczy `claimed_by`)

---

## Kolejność implementacji

1. Migracja schematu w `agent_bus.py` (addytywna, nie psuje testów)
2. Nowe metody `AgentBus` + testy
3. Nowe komendy CLI (`instances`, `instance-terminate`)
4. Aktualizacja `mrowisko_runner.py` + testy
5. Commit per krok

---

## Otwarte kwestie (wymagają decyzji przed implementacją)

1. **Heartbeat timeout**: 60s — instancja bez heartbeatu przez 60s uznana za nieaktywną. ✓
2. **Busy scope**: busy = aktywny workflow (od claim do zakończenia workflow), nie tylko czas subprocess. Instancja busy nie przyjmuje nowych niezwiązanych tasków. ✓
3. **Claim failure UX**: jeśli atomic claim się nie powiedzie → pomiń cicho (skip do następnego taska) czy informuj użytkownika?
