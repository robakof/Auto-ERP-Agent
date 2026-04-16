# Developer Block 7 — KSeF M6 Observability & Safety

Data: 2026-04-16
Autor: Architect
Dotyczy planu: `documents/human/plans/ksef_api_automation.md` (§5 M6)
Dla roli: Developer
Status: Ready to start
Prerequisites: Block 1-4 ✓ (pipeline), Block 6 ✓ (daemon)

---

## Cel bloku

Operacyjne zabezpieczenia i diagnostyka: dashboard rozbudowany, rate limiter,
Prod safety guard, error eskalacja do człowieka. Po ukończeniu daemon jest
production-ready: nie można przypadkowo wysłać na Prod, nie może zalać KSeF
z powodu buga, a operacyjne błędy eskalują natychmiast.

**Constraint:** Zero zmian w core pipeline (encryption, send_invoice, xml_builder).
Block 7 = warstwa ochronna i diagnostyczna nad istniejącym kodem.

---

## Co już istnieje

| Komponent | Lokalizacja | Status |
|---|---|---|
| ksef_status.py (read-only CLI: --status, --gid, --today, --limit) | `tools/ksef_status.py` | ✓ Block 2 |
| ksef_daemon.py (--once, --dry-run, graceful shutdown) | `tools/ksef_daemon.py` | ✓ Block 6 |
| config.py (KSEF_ENV, KSEF_BASE_URL) | `core/ksef/config.py` | ✓ Block 1 |
| Shadow DB z pełnym audit trail | `core/ksef/adapters/repo.py` | ✓ Block 2 |
| agent_bus_cli.py (flag --from --reason-file) | `tools/agent_bus_cli.py` | ✓ Infra |

---

## Scope — co dokładnie powstaje

### 1. Dashboard rozbudowa: `tools/ksef_status.py`

Dodaj tryb `--summary` (domyślny gdy brak filtrów):

```
$ py tools/ksef_status.py --summary

=== KSeF Shadow DB — podsumowanie ===

Dziś (2026-04-16):
  ACCEPTED:  12
  SENT:       1 (w toku)
  ERROR:      0
  REJECTED:   0

Ostatnie 7 dni:
  ACCEPTED:  87
  SENT:       1
  ERROR:      3 ← UWAGA
  REJECTED:   1 ← UWAGA

Łącznie w DB:  412
Ostatnia wysyłka: 2026-04-16 14:32 (FS-73/04/26/SPKR → ACCEPTED)
```

**Implementacja:**
- Nowa metoda w repo: `count_by_status(since: datetime | None = None) -> dict[ShipmentStatus, int]`
- `--summary` jako default behavior (brak argumentów = summary)
- Zachowaj istniejące tryby (--status, --gid, --today) bez zmian
- Oznacz ERROR/REJECTED z `← UWAGA` jeśli count > 0

### 2. Rate limit guard: `core/ksef/guards.py` (NOWY, ~40 linii)

```python
class RateLimiter:
    """Token bucket — max N operations per window."""

    def __init__(
        self,
        max_per_minute: int = 10,
        *,
        clock: Callable[[], float] = time.monotonic,
    ) -> None: ...

    def acquire(self) -> bool:
        """Return True if operation allowed, False if rate limited."""

    def wait_if_needed(self, sleep: Callable[[float], None] = time.sleep) -> None:
        """Block until operation allowed."""
```

**Integracja w daemon:** Przed każdym `_process_one(doc)` wywołaj `rate_limiter.acquire()`.
Jeśli `False` → log warning + skip do następnego tick (nie crash).

**Default: 10 dok/min.** Wystarczający na ~20-30 dok/dzień. Chroni przed bugiem
w scan (np. zwraca duplikaty) lub runaway loop.

**CLI parametr:** `--rate-limit N` (default 10). `--rate-limit 0` = wyłączony.

### 3. Prod safety guard: `core/ksef/config.py` update

```python
def load_config(...) -> KSefConfig:
    ...
    if env == "prod":
        confirmed = (os.getenv("KSEF_PROD_CONFIRMED") or "").strip().lower()
        if confirmed != "yes":
            raise ValueError(
                "KSEF_ENV=prod requires KSEF_PROD_CONFIRMED=yes in .env. "
                "This is a safety measure to prevent accidental production sends."
            )
    ...
```

**Efekt:** Daemon/CLI z `KSEF_ENV=prod` bez `KSEF_PROD_CONFIRMED=yes` → natychmiastowy
błąd na starcie. Zero przypadkowych wysyłek na Prod.

### 4. Error eskalacja: `core/ksef/guards.py` (w tym samym module)

```python
class ErrorEscalator:
    """Eskaluje do człowieka gdy ERROR/REJECTED przekroczy threshold."""

    def __init__(
        self,
        threshold: int = 3,
        *,
        flag_fn: Callable[[str], None] | None = None,  # agent_bus flag
    ) -> None: ...

    def report(self, result: SendResult) -> None:
        """Track result. If error count >= threshold → flag."""

    def reset(self) -> None:
        """Reset counter (po tick bez błędów)."""
```

**Integracja w daemon:** Po każdym `_process_one`:
- `escalator.report(result)` → śledzi ERROR/REJECTED
- Jeśli ≥3 błędów w jednym tick → `flag` do człowieka z listą GIDów

**Flag wywołanie:**
```python
def _flag_to_human(reason: str) -> None:
    """Write reason to tmp file, call agent_bus flag."""
    # Zapis do tmp/ksef_flag.md
    # subprocess: py tools/agent_bus_cli.py flag --from daemon --reason-file tmp/ksef_flag.md
```

**Default threshold: 3.** CLI parametr: `--error-threshold N` (0 = wyłączony).

### 5. Dry-run audit test

Dodaj test weryfikujący że `--dry-run` = zero HTTP calls:

```python
def test_dry_run_no_http_calls():
    """Verify --dry-run mode makes zero HTTP requests."""
    # Mock httpx.Client to track calls
    # Run daemon.run_once() with dry_run=True
    # Assert httpx call count == 0
```

### 6. Testy

#### Unit: `tests/ksef/test_guards.py` (NOWY)

```
test_rate_limiter_allows_within_limit()
test_rate_limiter_blocks_over_limit()
test_rate_limiter_resets_after_window()
test_rate_limiter_zero_means_disabled()
test_escalator_no_flag_below_threshold()
test_escalator_flags_at_threshold()
test_escalator_reset_clears_counter()
test_escalator_counts_only_errors()
```
Minimum: **≥8 unit**

#### Integration: `tests/ksef/test_config_safety.py` (NOWY)

```
test_prod_without_confirmed_raises()
test_prod_with_confirmed_passes()
test_demo_no_confirmation_needed()
```
Minimum: **≥3 unit**

#### Dashboard: `tests/ksef/test_status_summary.py` (NOWY)

```
test_count_by_status_returns_dict()
test_summary_format_shows_today_and_week()
```
Minimum: **≥2 unit**

#### Dry-run audit:

```
test_dry_run_no_http_calls()
```
Minimum: **≥1**

#### Minimum testów

- Guards (rate limiter + escalator): ≥8
- Config safety: ≥3
- Dashboard: ≥2
- Dry-run: ≥1
- **Total nowych: ≥14 + zachowane 166 z Block 1-6 = ≥180 PASS**

---

## Decyzje zatwierdzone

| Decyzja | Wybór | Uzasadnienie |
|---|---|---|
| Rate limit default | 10 dok/min | ~20-30/dzień, duży zapas, chroni przed runaway |
| Prod guard location | config.py (fail-fast) | Jeden punkt, natychmiast na starcie |
| Error escalation | agent_bus flag (subprocess) | Spójne z architekturą mrowiska |
| Error threshold | 3 per tick | Nie flaguj single error (transient), flaguj pattern |
| Guards module | core/ksef/guards.py | Oddzielne od pipeline — pure safety layer |
| Dashboard default | --summary (gdy brak args) | Najczęstszy use case operatora |
| Alembic-style migrations | OUT OF SCOPE | Schema stabilna, nie rosła od Block 2 |

---

## Out of scope (świadomie)

- **Alembic-style DB migrations** — schema stabilna, nie potrzeba w M6
- **Windows service wrapper** — operator używa Task Scheduler / manual
- **Grafana / web dashboard** — CLI wystarczający na obecną skalę
- **Auto-retry failed documents** — wymaga policy decision, osobny scope
- **Email/Slack notifications** — agent_bus flag wystarczający

---

## Ryzyka

| Ryzyko | Mitygacja |
|---|---|
| agent_bus flag subprocess fail (agent_bus offline) | Fallback: log warning do stdout, nie crash |
| Rate limiter zbyt restrykcyjny | Parametr CLI, 0 = disabled |
| Prod guard obejście (env var set w tym samym .env) | Świadomy design — guard chroni przed ZAPOMNIENIEM, nie celowym obejściem |
| Dashboard count query wolne na dużej DB | SQLite z indeksami (status, created_at) z Block 2 |

---

## Kolejność pracy (rekomendacja)

1. **guards.py** (RateLimiter + ErrorEscalator) + unit testy — izolowane, zero zależności
2. **config.py** update (Prod guard) + testy
3. **repo.py** update (count_by_status) + **ksef_status.py** rozbudowa (--summary)
4. **ksef_daemon.py** integracja: rate limiter + error escalation + CLI args
5. Dry-run audit test
6. Verify: `py tools/ksef_daemon.py --once --dry-run` + `py tools/ksef_status.py --summary`

---

## Workflow i handoff

Developer realizuje przez `workflow_developer_tool`.

Po ukończeniu — handoff do Architekta na `workflow_code_review`:

```
py tools/agent_bus_cli.py handoff \
  --from developer --to architect \
  --phase "ksef_block_7_review" --status PASS \
  --summary "Block 7: observability & safety (guards, Prod lock, dashboard, escalation). 180+ tests PASS." \
  --next-action "Code review — core/ksef/guards.py, tools/ksef_status.py, tools/ksef_daemon.py updates, tests"
```

Po PASS → KSeF pipeline production-ready. Decyzja człowieka: deploy na Prod.
