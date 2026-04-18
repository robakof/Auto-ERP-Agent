# Code Review: M15 Admin — moderation + audit + hearts grant + suspend

Date: 2026-04-17
Commit: 9b12994
Plan: documents/human/plans/serce_m15_admin.md

## Summary

**Overall assessment:** PASS
**Code maturity level:** L3 Senior — compound resolve_flag z dispatch pattern, atomowe side effects (hide/suspend/refund), bulk token revocation, paginacja z count subquery, audit trail na kazdy mutacja. Czysty separation service (flush) / router (commit). Testy: 31 unit + 12 auth guard = 43 total.

**Scope vs plan:**
- 7/7 endpointow (3 flags + 2 users + 1 hearts + 1 audit)
- require_admin dependency (deps.py)
- Compound resolve_flag z 6 ResolutionAction side effects
- suspend_user z bulk revoke refresh tokens
- unsuspend_user z clear suspension fields
- grant_hearts z cap check i audit
- list_audit z 5 filterow (actor_id, action, target_type, from_date, to_date)
- Router registration
- CLI promote_admin.py
- M14 W1 fix (reason: str -> FlagReason)

**Testy:** 378 passed, 0 failed, 3 skipped (bez zmian w skip count).

## Findings

### Critical Issues (must fix)

Brak.

### Warnings (should fix)

**W1. `GrantHeartsBody.type: str` — brak schema-level validation**
- **schemas/admin.py:64**: `type: str` akceptuje dowolny string
- **admin_service.py:259**: service waliduje `if ledger_type not in ("ADMIN_GRANT", "ADMIN_REFUND")` i zwraca 422 — wiec 500 NIE wystapi (w odroznieniu od M14 W1 gdzie nie bylo wczesnej walidacji)
- **Problem:** OpenAPI spec nie pokazuje dozwolonych wartosci. Klient API nie wie jakie typy sa dostepne. Niespojne z ResolveFlagBody.action ktore uzywa enum (ResolutionAction).
- **Fix:** zmien `type: str` na `type: Literal["ADMIN_GRANT", "ADMIN_REFUND"]` (nie HeartLedgerType — to za szerokie, zawiera GIFT/PAYMENT itp.). Usun string check z service — Pydantic zwaliduje.

**W2. `_get_target_owner` nie obsluguje EXCHANGE**
- **admin_service.py:167-178**: handler dla USER, REQUEST, OFFER — brak EXCHANGE
- **Scenariusz:** admin resolve flag na exchange z action=SUSPEND_USER lub BAN_USER → `_get_target_owner` fallthrough → 422 CANNOT_DETERMINE_OWNER
- **Kontekst:** exchange ma dwoch uczestnikow, brak jednoznacznego "owner". Plan mowi "suspend owner/user" ale nie precyzuje co dla exchange. W praktyce admin uzyje standalone `/admin/users/{id}/suspend`.
- **Fix:** albo dodaj EXCHANGE branch (np. suspend reportowanego usera — `flag.target_id` to exchange_id, wiec potrzeba dodatkowej logiki), albo popraw error message na "SUSPEND_VIA_FLAG_NOT_SUPPORTED_FOR_EXCHANGES — use /admin/users/{id}/suspend". Drugie podejscie prostsze i bezpieczniejsze.

### Suggestions (nice to have)

**S1. BAN_USER resolution nie testowany**
- test_admin_service.py: DISMISS, WARN_USER, HIDE_CONTENT (x2), SUSPEND_USER, GRANT_HEARTS_REFUND — pokryte. BAN_USER (permanent suspend) — brak testu.
- Ryzyko niskie: BAN_USER reuse'uje suspend_user(duration_days=None), wiec logika jest pokryta posrednio. Ale dedykowany test ulatwilby regression detection.

**S2. `get_flag` endpoint brak w auth guard testach**
- test_admin_api.py testuje 6 z 7 endpointow (brak GET /flags/{id}). Mechanizm ten sam (require_admin), wiec ryzyko minimalne.

## M14 W1 Fix — Verification

`schemas/flag.py:13`: `reason: FlagReason` — Pydantic waliduje enum. `flags.py` routery — brak `FlagReason(body.reason)` conversion (poprawnie usuniete). body.reason jest juz enum po walidacji. ✓

## Architecture Review

**Compound resolve_flag (admin_service.py:81-118):**
Atomowe: flag resolution + side effect + audit w jednej TX (flush-only, commit w routerze). Dispatch przez `_execute_resolution` z osobnym handlerem per action. Czysty wzorzec, latwo rozszerzalny.

**Suspend/unsuspend (admin_service.py:183-243):**
Bulk token revocation przez UPDATE WHERE revoked_at IS NULL — poprawne. Clear all suspension fields na unsuspend. Guardy: can't suspend admin, can't suspend already suspended.

**Grant hearts (admin_service.py:249-285):**
Cap check present. from_user_id=None (system action). Audit logged.

**require_admin (deps.py:61-70):**
Reuse'uje get_auth_context (weryfikuje JWT + active status), dodaje role check. Poprawna kompozycja.

**promote_admin.py:**
Async CLI, engine.begin() w try/finally z dispose. Czysty, bezpieczny.

## Recommended Actions

- [ ] W1: `type: str` → `type: Literal["ADMIN_GRANT", "ADMIN_REFUND"]` w GrantHeartsBody, usun string check z service
- [ ] W2: Popraw error message w `_get_target_owner` fallthrough lub dodaj EXCHANGE branch

## Verdict

Solidna implementacja. Compound resolve_flag to najambitniejsza czesc M15 i jest dobrze zrealizowany — atomowe side effects, dispatch pattern, audit na kazdej mutacji. suspend_user z bulk token revocation jest poprawny. Jedyne warnings to schema-level validation (W1 — powtorzenie M14 W1 pattern) i brak EXCHANGE w _get_target_owner (W2 — design gap z planu). Oba fixable w nastepnym commicie.
