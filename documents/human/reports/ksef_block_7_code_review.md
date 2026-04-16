# Code Review: KSeF Block 7 — M6 Observability & Safety

Date: 2026-04-16
Reviewer: Architect
Branch: main (commit 38de527)
Plan: `documents/human/plans/ksef_developer_block_7.md`
Handoff: msg #102 (developer → architect), detale: `tmp/handoff_block_7_review.md`

## Summary

**Overall assessment: PASS**
**Code maturity level: L3 Senior (strong)** — osobny moduł `guards.py` czysto izolowany od pipeline, DI clock/flag_fn/sleep, sliding-window token bucket (dokładniejszy niż fixed bucket), fail-fast Prod guard w `load_config`, escalator one-shot per tick (anty-spam), best-effort subprocess flag (daemon nie crashuje gdy agent_bus offline), dashboard `--summary` jako default UX.

**Tests:** 203/204 PASS (37 nowych + 166 z Block 1-6, 1 deselected — integration bez sieci).

**Acceptance criteria vs deliverable:**

| Criterium | Status |
|---|---|
| `core/ksef/guards.py` — RateLimiter + ErrorEscalator | ✓ 133 L |
| Prod safety guard w `config.py` (KSEF_PROD_CONFIRMED=yes) | ✓ fail-fast |
| `--summary` mode w ksef_status.py (dziś/7 dni/total, alert UWAGA) | ✓ default gdy brak args |
| `count_by_status(since)` w repo.py | ✓ dict[ShipmentStatus, int] |
| Daemon integracja: rate limiter + escalator + CLI args | ✓ `--rate-limit`, `--error-threshold` |
| Dry-run audit test (zero HTTP calls) | ✓ 2 testy |
| Zero zmian w core pipeline (encryption/send/xml_builder) | ✓ constraint respected |
| Tests ≥14 nowych, suite ≥180 | ✓ 37 nowych, suite 203 |

## Decyzje developera — ocena

### Sliding window (deque timestamps) zamiast fixed bucket → **APPROVE**
Dokładniejszy pod burst — tokeny wygasają indywidualnie, nie wszystkie na raz przy przekroczeniu 60s. Plan zostawiał wybór, sliding to lepsza heurystyka dla nierównomiernego ruchu (burst ERP batch o godz. 8:00).

### `ErrorEscalator._flagged` one-shot per tick → **APPROVE**
Eskalacja raz per tick, reset na nowym ticku (`daemon._tick` wywołuje `escalator.reset()` na starcie). Zapobiega 10x flag od tej samej serii błędów. Spójne z zasadą "flaguj pattern, nie pojedyncze zdarzenia".

### `_flag_to_human` best-effort (timeout=30s + catch-all) → **APPROVE**
Subprocess `agent_bus_cli.py flag` z timeout i except. Jeśli agent_bus offline, daemon loguje warning i kontynuuje — nie crashuje. Zgodne z CLAUDE.md "Gdy dispatcher nie żyje — flag do człowieka" + fallback do log gdy nawet flag nie działa.

### `--summary` default (brak args = summary) → **APPROVE**
Najczęstszy use case operatora — szybki podgląd. Istniejące tryby (`--status`, `--gid`, `--today`) bez regresji. Dobry UX call.

### Prod guard w `load_config` (fail-fast) → **APPROVE**
Jeden punkt egzekwowania, na starcie procesu. Nie da się "przypadkiem" wysłać na Prod bez ustawienia `KSEF_PROD_CONFIRMED=yes` w `.env`. Świadomy design — guard chroni przed zapomnieniem, nie przed celowym obejściem.

## Findings

### Critical Issues (must fix)

Brak.

### Warnings (should fix)

**W1: `default_summary` heurystyka ignoruje `--rodzaj`**

`tools/ksef_status.py:63-65`:
```python
default_summary = not any(
    (args.status, args.gid, args.today, args.limit != 20)
)
```

Jeśli operator poda `--rodzaj FS` bez `--gid`, `default_summary=True` → summary (nie tabela). Parser nie wymaga `--gid` razem z `--rodzaj` (brak validacji), więc ścieżka jest osiągalna. Dodaj `args.rodzaj` do tuple lub zwaliduj parser'em.

**W2: `args.gid` truthy check gubi `--gid 0`**

W tym samym miejscu — `args.gid` jest intem (`type=int`). `any((..., 0, ...))` = False, więc `--gid 0` triggeruje summary zamiast tabeli. W ERP Comarch XL GID=0 nie istnieje (autoinkrement od 1), ale semantycznie `is not None` byłoby czystsze:
```python
default_summary = not (
    args.status or args.gid is not None or args.today or args.limit != 20
)
```
Non-blocking — GID=0 nie występuje w praktyce.

### Suggestions (nice to have)

**S1: `tmp/ksef_flag.md` — race condition przy wielu instancjach**

`_flag_to_human` zapisuje do stałej ścieżki `tmp/ksef_flag.md`. Jeśli dwa daemon instances działają równolegle (Task Scheduler + manual `--once`), druga nadpisuje plik pierwszej przed wywołaniem subprocess. Rozwiązanie: `ksef_flag_{timestamp}.md` albo lock. Non-blocking — daemon pomyślany jako single instance.

**S2: `escalator.reset()` wywołane także dla pustego scan**

`_tick()` wywołuje reset przed iteracją, nawet gdy `pending=[]`. Tania operacja (clear list + bool), nie bug, ale `if pending and self._escalator:` byłoby ciut czystsze. Minor.

**S3: `_flag_to_human` hardcoded w `main()`**

Daemon nie pozwala podmienić mechanizm eskalacji (np. stdout-only w CI, syslog w produkcji). Nie jest potrzebne teraz — jeśli pojawi się taka potrzeba, łatwo dodać `--flag-mechanism {agent_bus,stdout,syslog}`. Obecny kształt akceptowalny.

## Architecture Assessment

### Module boundaries

```
tools/ksef_daemon.py (CLI wiring + KSeFDaemon loop)
    ↓ DI
core/ksef/guards.py (RateLimiter + ErrorEscalator — pure safety layer)
core/ksef/usecases/scan_erp.py (Block 6 — scan)
core/ksef/usecases/send_invoice.py (Block 4 — send pipeline) ← BEZ ZMIAN
core/ksef/config.py (Prod guard fail-fast)
tools/ksef_status.py (read-only dashboard + --summary)
core/ksef/adapters/repo.py (+count_by_status(since))
```

Guards = pure logic, zero I/O (jedyny side-effect to opcjonalny `flag_fn` callback). Można użyć w innym kontekście (np. HTTP request limiter). **Correct separation.**

### Pattern compliance

| Pattern | Status |
|---|---|
| DI for Testability | ✓ clock, flag_fn, sleep, rate_limiter, error_escalator — wszystkie injectable |
| Fail-Fast at Boundary | ✓ Prod guard w load_config |
| Error Isolation | ✓ _process_one try/except, _flag_to_human try/except |
| Best-Effort Side Effect | ✓ flag subprocess nigdy nie crashuje daemon |
| Structured Logging | ✓ JSON events (rate_limited, flag_failed, flag_sent, flag_exception) |
| Single Responsibility | ✓ RateLimiter = throttling, ErrorEscalator = pattern detection |
| Idempotency | ✓ escalator.report() po threshold = no-op (one-shot flag) |

### Anti-pattern check

| Anti-pattern | Status |
|---|---|
| God Object | ✓ Clean — 2 niezależne klasy w guards.py |
| Silent Failure | ✓ flag exception logged z kontekstem |
| Retry Sprawl | ✓ Escalator = alert, NIE retry — daemon retryuje na następnym ticku |
| Speculative Config | ✓ Tylko dwa knoby: rate-limit i error-threshold |
| Mixed Dimensions | ✓ Guards nie zna pipeline, pipeline nie zna guards (DI przez daemon) |

### Algorithm correctness

**RateLimiter sliding window:**
- Eviction przed `acquire()` — stare tokeny wygasają zanim sprawdzimy limit. Correct.
- `wait_if_needed` sleep = `window - (now - oldest)` — czeka do wygaśnięcia najstarszego. Po sleep re-eviction. Correct.
- Edge case `max=0` — `enabled=False`, zawsze `True`. Correct.
- Edge case negative max — ValueError w `__init__`. Correct.

**ErrorEscalator one-shot:**
- `_flagged` bool — ustawiany przy przekroczeniu threshold, sprawdzany przed wywołaniem `flag_fn`. Po reset wraca do False. Correct.
- `_ERROR_STATUSES = frozenset({ERROR, REJECTED})` — tylko te traktowane jako błąd. ACCEPTED/SENT/DRAFT nie zwiększają licznika. Correct.

## Test Coverage Analysis

| File | Tests | Plan min | Status |
|---|---|---|---|
| test_guards.py (RateLimiter + Escalator) | 18 | ≥8 | ✓ |
| test_config_safety.py (Prod guard) | 5 | ≥3 | ✓ |
| test_status_summary.py (count + CLI) | 8 | ≥2 | ✓ |
| test_dry_run_audit.py (zero HTTP) | 2 | ≥1 | ✓ |
| test_daemon.py (+guards integration) | +4 | n/a | ✓ |
| **Total new** | **37** | **≥14** | ✓ (264%) |
| + Block 1-6 | 166 | 166 | ✓ |
| **Suite total** | **203** | **≥180** | ✓ |

**RateLimiter tests quality:** Injected `_FakeClock` → deterministyczne, bez sleep w realu. Covers: within-limit, over-limit, window reset, disabled, sliding window (individual token expiry), wait_if_needed block, wait_if_needed no-op when disabled, negative raises. **Solidne.**

**Escalator tests quality:** MagicMock flag_fn → verify call count i args. Covers: below threshold, at threshold (content of reason), one-shot per tick, reset clears counter, reset re-enables flagging, counts only ERROR/REJECTED, REJECTED as error, zero threshold disabled, no flag_fn = no crash, negative raises. **Solidne.**

**Config safety quality:** Isolated env fixture (clear KSEF_* + tmp_path .env) → bez wycieku env między testami. Covers: prod without → raises, prod with "yes" → OK, prod with wrong value → raises, demo → no confirmation, test → no confirmation. **Solidne.**

**Dry-run audit quality:** Patches `httpx.Client`, `KSefHttp`, `KSeFApiClient`, `load_config` → jeśli którykolwiek byłby wywołany, test failuje. 2 warianty: factory-level + full daemon.run_once. **Solidne.**

**Dashboard quality:** subprocess CLI smoke tests (subprocess.run z `--db tmp_path`) → sprawdza realny exit code + stdout. Covers: empty DB, counts, UWAGA alert, default behavior. **Solidne.**

## Recommended Actions

### Before commit (must):

Brak — commit already done (`38de527`).

### Nice-to-have (non-blocking):
- [ ] W1: `args.rodzaj` do tuple `default_summary` (lub walidacja parser'em `--rodzaj requires --gid`)
- [ ] W2: `args.gid is not None` zamiast truthy check (konsystencja)
- [ ] S1: Timestamp w `tmp/ksef_flag_{ts}.md` jeśli wielo-instancja
- [ ] S2: `if pending and self._escalator:` opakować reset

## Verdict

**PASS.** Block 7 to kompletna warstwa ochronna i diagnostyczna nad istniejącym pipelinem: RateLimiter (sliding window, 10/min default), ErrorEscalator (one-shot per tick, threshold=3), Prod safety guard w config (fail-fast), dashboard `--summary` (dziś/7 dni/total + UWAGA), daemon integracja z `--rate-limit`/`--error-threshold`, best-effort subprocess flag. 37 nowych testów, 203/204 PASS. Zero zmian w core pipeline — constraint respected. Dwa warnings w heurystyce `default_summary` (W1 rodzaj niewpięte, W2 gid truthy) są edge-case'owe i non-blocking.

**M6 (observability & safety) complete.** KSeF pipeline production-ready:
- Nie można przypadkowo wysłać na Prod (Prod guard)
- Nie da się zalać KSeF batch'em (rate limiter)
- Pattern błędów eskaluje do człowieka (escalator)
- Operator widzi stan jednym spojrzeniem (`--summary`)
- `--dry-run` gwarantowany zero-HTTP (audit test)

**Next decyzja człowieka:** deploy na Prod (Task Scheduler, monitoring) lub kolejny blok wartości (np. M7 = automatyczna ekstrakcja danych z PDF, korekty cykliczne, KSeF 2.0 upgrade). Pipeline jest feature-complete w zakresie M0-M6 z planu `documents/human/plans/ksef_api_automation.md`.
