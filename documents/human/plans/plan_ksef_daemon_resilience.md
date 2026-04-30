# Plan: KSeF daemon — auto-restart i odporność

**Data:** 2026-04-22
**Scope Developer:** auto-restart + timeouty + watchdog
**Scope Architect (handoff):** raportowanie, dashboard, monitoring długoterminowy

---

## Co jest teraz

- Daemon działa w pętli `while not shutdown`, tick co 15 min (bat) / 60s (py)
- HTTP ma timeout (connect=10s, read=30s) + retry 3x exponential backoff
- SQL connect ma timeout (pyodbc)
- Brak: timeout per-tick, auto-restart po crash, watchdog na zawieszenie

## Co robimy (Developer)

### 1. Tick timeout (Python, wewnątrz daemon)
- Nowy parametr `--tick-timeout` (default 300s = 5 min)
- Jeśli `_tick()` trwa dłużej → przerwij, loguj WARNING, kontynuuj do następnego ticka
- Mechanizm: `threading.Timer` + flaga abort (nie `signal.alarm` — Windows)

### 2. Wrapper watchdog (bat → nowy skrypt Python)
- `tools/ksef_watchdog.py` — uruchamia `ksef_daemon.py` jako subprocess
- Monitoruje:
  - Proces żyje? Jeśli exit code != 0 → restart po 30s
  - Heartbeat file? Daemon co tick zapisuje timestamp do `data/ksef_heartbeat.json`
  - Jeśli heartbeat starszy niż `2 * interval + tick_timeout` → kill + restart
- Max restartów: 5 w ciągu godziny → flag do human, stop
- Logi restartów do `data/ksef_watchdog.log`

### 3. Heartbeat w daemon
- Po każdym `_tick()` (PASS lub FAIL) → zapisz `data/ksef_heartbeat.json`:
  ```json
  {"last_tick": "2026-04-22T12:00:00", "tick_count": 42, "status": "ok"}
  ```

### 4. Nowy bat: `ksef_wyslij_demo.bat` → wywołuje watchdog zamiast daemon bezpośrednio
- `py tools/ksef_watchdog.py --interval 900`
- Watchdog uruchamia daemon z przekazanymi parametrami

## Pliki do zmiany

| Plik | Zmiana |
|---|---|
| `tools/ksef_daemon.py` | + heartbeat write, + tick timeout |
| `tools/ksef_watchdog.py` | NOWY — wrapper z auto-restart |
| `ksef_wyslij_demo.bat` | → wywołuje watchdog |
| `tests/test_ksef_watchdog.py` | NOWY — testy watchdog |

## Czego NIE robimy (→ Architect)

- Raportowanie (ile FV wysłano, błędy, statystyki) — **raporty na maila**
- Dashboard / UI
- Monitoring długoterminowy (Grafana, alerty)
- Decyzje o persistencji raportów (DB vs pliki vs agent_bus)
- Architektura pipeline: daemon → aggregacja → email (SMTP / sendgrid / inne)
