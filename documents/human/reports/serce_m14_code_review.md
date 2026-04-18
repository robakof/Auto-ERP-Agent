# Code Review: M14 Flag endpoints + ContentFlag

Date: 2026-04-17
Commit: a8c2913
Plan: documents/human/plans/serce_m14_flags.md

## Summary

**Overall assessment:** PASS
**Code maturity level:** L3 Senior — czysty dispatch pattern w service, DRY router (4 thin handlers → 1 service function), pełne pokrycie testami (13 unit + 4 auth guard), wszystkie guardy zaimplementowane (self-flag, duplicate, non-participant). Bonus: W1+W2 fixy z M13 review wlączone.

**Scope vs plan:**
- 4/4 endpointy POST per resource type (request, offer, exchange, user)
- Self-flag prevention: 422 CANNOT_FLAG_OWN_RESOURCE (request/offer/user), 404 non-participant (exchange)
- Duplicate guard: max 1 OPEN flag per (reporter, target_type, target_id)
- Rate limit 10/hour na wszystkich 4 endpointach
- Router registration

**Bonus (poza M14 scope, ale zgodne z M13 review):**
- W1 fix: `other_party()` helper w exchange_service — eliminuje duplikację recipient logic
- W2 fix: `_NOTIFICATION_BODIES` dict z polskimi opisami w ResendEmailService

**Testy:** 335 passed, 0 failed, 3 skipped.

## Findings

### Critical Issues (must fix)

Brak.

### Warnings (should fix)

**W1. `reason: str` w CreateFlagBody — brak walidacji enum**
- **schemas/flag.py:12**: `reason: str` akceptuje dowolny string
- **flags.py:31**: `FlagReason(body.reason)` — jeśli user wyśle `"foo"`, Python Enum rzuci `ValueError` → FastAPI zwróci **500** zamiast 422
- **Fix:** zmień `reason: str` na `reason: FlagReason` w CreateFlagBody. Pydantic zwaliduje automatycznie i zwróci 422 z czytelnym błędem. Usuń `FlagReason(body.reason)` z routera — `body.reason` będzie już enum.

### Suggestions (nice to have)

Brak. Kod jest czysty i minimalistyczny.

## M13 W1+W2 Fixes — Verification

**W1 (recipient logic):** `other_party(exchange, actor_id)` wyciągnięty jako helper w exchange_service.py.
Reuse w: exchange_service (create/cancel notification), exchanges.py (create/cancel email), message_service (notification), messages.py (email). Duplikacja wyeliminowana. ✓

**W2 (email body):** `_NOTIFICATION_BODIES` dict dodany z 8 polskimi opisami. Body zmieniony z `f"Typ: {notification_type}"` na human-readable tekst. ✓

## Recommended Actions

- [ ] W1: Zmień `reason: str` → `reason: FlagReason` w CreateFlagBody, usuń FlagReason() conversion z routera

## Verdict

Architektonicznie poprawny. Dispatch pattern w `_validate_target()` jest czysty i rozszerzalny (dodanie MESSAGE target w M15 = 5 linii). W1 to jednolinijkowy fix. M13 warnings zaadresowane w tym samym commit — pozytywne.
