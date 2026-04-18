# Code Review: M17 APScheduler — expire requests

Date: 2026-04-18
Commit: `b2dd1ff`
Plan: `documents/human/plans/serce_m17_scheduler.md`
Tests: 407/407 PASS (Developer handoff #156)

---

## Summary

**Overall assessment: PASS**
**Code maturity level:** L3 Senior — krótkie, focused funkcje (≤15 linii), czytelna struktura (fetch → mutate → commit → email), idempotentność przez WHERE clause, testy pokrywają happy path + edge cases + kaskadę + idempotentność.

---

## Plan compliance

| Deliverable | Status |
|---|---|
| `apscheduler>=4.0` w pyproject.toml | ✓ (`>=4.0.0a1`) |
| `request_expiry_check_interval_minutes` w config | ✓ (default 60) |
| `scheduler_service.py` z `expire_requests_job()` | ✓ |
| Własna sesja DB (nie HTTP context) | ✓ (`async_session_factory()`) |
| SELECT FOR UPDATE | ✓ |
| Kaskada PENDING Exchanges → CANCELLED | ✓ |
| Notification REQUEST_EXPIRED | ✓ |
| Email best-effort (fire-and-forget) | ✓ |
| Lifespan w main.py | ✓ (`AsyncScheduler` + `IntervalTrigger`) |
| 6 testów | ✓ (6/6) |
| Idempotentność (podwójne wywołanie = NOP) | ✓ (test `test_no_double_cancel`) |

---

## Findings

### Warnings (should fix)

- **W1 — `scheduler_service.py:68` — brak type hint `request_id`.**
  `_cascade_cancel_exchanges(db, request_id)` — parametr `request_id` nie ma type annotation.
  Reszta kodu konsekwentnie typuje UUID. Powinno być `request_id: UUID`.
  **Fix:** `async def _cascade_cancel_exchanges(db: AsyncSession, request_id: UUID) -> int:`
  (dodaj `from uuid import UUID` na górze)

- **W2 — `pyproject.toml` — APScheduler alpha version `>=4.0.0a1`.**
  APScheduler 4.x jest w fazie pre-release. Na MVP akceptowalne, ale na produkcji ryzyko
  (breaking changes między alpha a stable). Gdy APScheduler 4.0 stable wyjdzie — zaktualizować
  constraint do `>=4.0`.
  **Fix (teraz):** Brak — awareness. **Fix (przed prod):** pin do stable release.

### Suggestions (nice to have)

- **S1 — `scheduler_service.py:59` — explicit NULL guard.**
  `Request.expires_at < now` naturalnie wyklucza NULL (SQL NULL comparison → NULL → falsy).
  Dodanie `.where(Request.expires_at.isnot(None))` zwiększyłoby czytelność intencji,
  ale nie zmienia zachowania. Opcjonalne.

- **S2 — brak testu: request z `expires_at = NULL` → nie wygasa.**
  Obecne testy nie weryfikują jawnie tego edge case. W praktyce NULL nie pasuje do `< now`,
  ale explicit test wzmocniłby pewność przy przyszłych zmianach query.

---

## Architecture check

| Kryterium | Wynik |
|---|---|
| Anti-patterny z PATTERNS.md? | Brak — czysta implementacja |
| Prostsze rozwiązanie możliwe? | Nie — APScheduler to minimalny wybór (asyncio sleep loop byłby gorszy) |
| Logika biznesowa w odpowiedniej warstwie? | ✓ service layer |
| Spójność z istniejącym kodem? | ✓ kaskada identyczna jak `cancel_request`, notification/email pattern jak M13 |
| Idempotentność? | ✓ WHERE status=OPEN eliminuje już przetworzone |
| Race condition safety? | ✓ SELECT FOR UPDATE (ignorowane na SQLite w testach, działa na PostgreSQL) |

---

## Recommended Actions

- [ ] W1: Dodaj type hint `request_id: UUID` w `_cascade_cancel_exchanges`
- [ ] W2: (przed prod) Pin APScheduler do stable gdy wyjdzie

Oba warnings to S-size fix. Nie blokują PASS.
