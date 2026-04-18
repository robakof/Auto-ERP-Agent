# Code Review: M16 Soft delete (account)

Date: 2026-04-17
Commit: 5ae6615 (M16) + e487c27 (M15 W1+W2 fix)
Plan: documents/human/plans/serce_m16_soft_delete.md

## Summary

**Overall assessment:** PASS
**Code maturity level:** L3 Senior — 8-step atomic cascade poprawnie zaimplementowany, `db.refresh(user)` przed disposition zapewnia prawidlowy balance po refundach (autoflush), sha256 anonymization, bulk UPDATE requests/offers, per-exchange refund loop z notification collection. Testy pokrywaja wszystkie scenariusze cascade wlacznie z kluczowym test_soft_delete_refund_then_void.

**Scope vs plan:**
- account_service.py: 8-step atomic cascade (load+verify → validate → cancel exchanges+refund → cancel requests → inactive offers → disposition → anonymize → status → revoke tokens) ✓
- DELETE /users/me endpoint z password confirmation ✓
- SoftDeleteBody z Literal["void", "transfer"] ✓
- Public profile placeholder: DELETED → 200, is_deleted=True (ADR D5) ✓
- PublicProfileRead: username optional, +is_deleted ✓
- Email via BackgroundTasks po commit ✓
- AffectedParty dataclass zwracany z service ✓
- Bonus: M15 W1+W2 fix w osobnym commicie (e487c27) ✓

**Testy:** 399 passed, 0 failed, 3 skipped.

## Findings

### Critical Issues (must fix)

Brak.

### Warnings (should fix)

**W1. Brak SELECT FOR UPDATE na user i recipient**
- **account_service.py:42**: `user = await db.get(User, user_id)` — bez lock
- **account_service.py:125**: `recipient = await db.get(User, transfer_to_user_id)` — bez lock
- **Plan specyfikowal:** "SELECT FOR UPDATE na user i recipient (hearts transfer)"
- **Istniejacy pattern:** `hearts_service.gift_hearts()` uzywa `select(User).where(...).with_for_update()`, `exchange_service.accept_exchange()` rowniez
- **Ryzyko:** niskie — soft delete to jednorazowa operacja per konto, wiec race condition praktycznie nie wystapi. Ale transfer do recipienta moze kolidowac z rownoleglym giftem do tego samego usera (cap violation).
- **Fix:** zamien `db.get(User, user_id)` na `select(User).where(User.id == user_id).with_for_update()` w step 0 i step 5 (transfer). W step 2 refund loop: requester juz wymaga FOR UPDATE (ten sam pattern co exchange_service).

**W2. Missing API tests — public profile placeholder**
- **test_account_api.py**: 1 test (test_delete_no_token). Plan specyfikowal 4 API testy.
- **Brakuje:** test_public_profile_deleted_user (200, is_deleted=True, username=None), test_public_profile_active_user (is_deleted=False)
- **Dlaczego wazne:** zmiana public_profile z 404→200 dla DELETED users to user-visible behavior change. Schema serialization (username: None w JSON) powinna byc zweryfikowana na API level.

### Suggestions (nice to have)

**S1. `db.refresh(user)` przed disposition — poprawne ale redundantne**
- **account_service.py:112**: `await db.refresh(user)` po exchange refund loop
- SQLAlchemy autoflush zapisuje dirty attributes przed SELECT w refresh() — wiec balance jest poprawny. Ale poniewaz identity map zapewnia ze `user` i `requester` (z step 2) to ten sam Python object, balance jest juz zaktualizowany w pamieci bez potrzeby refresh.
- Nie jest bledem — dodatkowy DB round-trip, defensive coding. Moze zostac.

## M15 W1+W2 Fix — Verification (commit e487c27)

**W1 (GrantHeartsBody.type: str → Literal):**
- `schemas/admin.py:65`: `type: Literal["ADMIN_GRANT", "ADMIN_REFUND"]` ✓
- `admin_service.py`: string check `if ledger_type not in (...)` usuniety — Pydantic waliduje ✓
- `test_admin_service.py`: test zmieniony na `pytest.raises(ValidationError)` z GrantHeartsBody — poprawnie testuje schema level ✓

**W2 (_get_target_owner EXCHANGE):**
- `admin_service.py:178-181`: explicit `elif EXCHANGE: raise 422 SUSPEND_VIA_FLAG_NOT_SUPPORTED_FOR_EXCHANGES` ✓
- Czytelny error message, lepszy niz generic CANNOT_DETERMINE_OWNER ✓

## Architecture Review

**Cascade order (account_service.py:55-165):**
Exchanges (refund) → requests → offers → disposition → anonymize → status → tokens. Kolejnosc krytyczna — refund PRZED disposition, zweryfikowana testem test_soft_delete_refund_then_void (balance=5, escrow=10, po refundzie=15, void=15). Poprawne.

**Anonymization (account_service.py:142-150):**
sha256(email)[:16] — deterministyczny, nieodwracalny. `deleted_{hash}@deleted.local` zachowuje UNIQUE constraint. `password_hash="!"` — invalid bcrypt prefix, uniemozliwia login. phone/bio/location cleared.

**Public profile placeholder (user_resources_service.py:154-165):**
DELETED → 200 z nulls + is_deleted=True. SUSPENDED → 404 (hide from public). Reviews/completed_exchanges still counted. Zgodne z ADR D5.

**Router (users.py:152-177):**
Commit w routerze, flush w service. Email po commit via BackgroundTasks — best-effort, nie blokuje. Wzorzec zgodny z M13.

## Recommended Actions

- [ ] W1: Dodaj SELECT FOR UPDATE na user (step 0) i recipient (step 5 transfer)
- [ ] W2: Dodaj 2-3 API testy: public_profile deleted (200, is_deleted=True), public_profile active (is_deleted=False), opcjonalnie delete wrong password via API

## Verdict

Solidna implementacja najzlozoniejszego milestone w Fazie 1. 8-step cascade atomowy, poprawna kolejnosc (refund → disposition), anonymization per ADR, public profile placeholder. 20 unit testow z pelnym pokryciem scenariuszy. M15 W1+W2 naprawione poprawnie w osobnym commicie. W1 (brak FOR UPDATE) to jedyny materialny finding — ryzyko niskie ale niespojne z patterns w reszcie codebase.
