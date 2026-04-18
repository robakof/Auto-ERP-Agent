# Serce M16 — Soft delete (account)

**Wejście:** M15 (admin/suspend), M6 (hearts), M9 (exchanges), M12 (user resources)
**Rozmiar:** L
**Autor:** Architect
**ADR:** ADR-SERCE-003 (account lifecycle)

---

## Cel

Użytkownik może usunąć swoje konto (`DELETE /users/me`). Operacja atomowa:
anonimizacja danych, anulowanie aktywnych zasobów, dyspozycja salda serc,
powiadomienie kontrahentów. Brak grace period (v1). Brak hard delete (v1).

---

## Stan zastanego kodu

**Już istnieje (model + tabela + migracja):**
- `User.status = DELETED` w enum
- `User.deleted_at`, `User.anonymized_at` — nullable DateTime fields
- `HeartLedgerType.ACCOUNT_DELETED` w enum
- `HeartLedger.from_user_id`, `to_user_id` — oba nullable
- `Notification.reason` — string field (dla `reason="account_deleted"`)
- `cancel_exchange()` — refund logic (ACCEPTED → EXCHANGE_REFUND)
- `RefreshToken.revoked_at` — bulk revocation pattern (z M15 suspend)
- Login blokuje `status != ACTIVE` → 403 ACCOUNT_NOT_ACTIVE
- Feed queries filtrują po `User.status == ACTIVE`
- `PublicProfileRead` w user_resources — aktualnie 404 dla non-ACTIVE users
- `verify_password()` w core/security.py
- `heart_balance_cap` w settings

**Brakuje:** account_service, soft_delete endpoint, deleted user placeholder, testy.

---

## Architektura

### Decyzja 1: Password confirmation

Operacja destrukcyjna → wymaga hasła. Spójne z email_change i phone_change
(oba wymagają password). Body: `{ password, balance_disposition, transfer_to_user_id }`.

### Decyzja 2: Balance disposition — void vs transfer

Per ADR-SERCE-003 D1:
- `void` — serca przepadają. HeartLedger(type=ACCOUNT_DELETED, from=user, to=None).
- `transfer` — przelew do wskazanego usera. HeartLedger(type=GIFT, from=user, to=recipient).
  Walidacja: recipient istnieje, ACTIVE, cap check. Rate limit gift (#50) NIE dotyczy.

Jeśli `heart_balance == 0` → disposition ignorowana (no-op).

### Decyzja 3: Cascade order — exchanges first, then requests/offers

Kolejność ma znaczenie:
1. **Exchanges** (z refundem) → PRZED disposition, bo refund zwiększa balance
2. **Requests** → CANCELLED
3. **Offers** → INACTIVE
4. **Disposition** → void/transfer na FINALNY balance (po refundach)
5. **Anonymize** → dane osobowe
6. **Status + timestamps**
7. **Revoke tokens**

Dlaczego exchanges first: jeśli user ma ACCEPTED exchange (escrow -10 serc),
a balance=5, to po refundzie balance=15. Dopiero wtedy void/transfer operuje na 15.
Odwrotna kolejność → void(5) i potem refund(10) → balance=10 w „skasowanym" koncie = leak.

### Decyzja 4: Request reopen po cancel exchange

ADR D4 mówi: "jeśli Request belongs to other party → reverts to OPEN".
W aktualnej implementacji **Request NIE zmienia statusu** przy accept/create exchange.
Request stays OPEN throughout lifecycle. Partial unique index zapobiega multiple ACCEPTED.

Zatem reopen to no-op w obecnym kodzie. **Implementujemy jako safety check:**
po cancel exchange, jeśli request należy do OTHER party i `status != OPEN` → SET OPEN.
Gdyby kiedyś dodano IN_PROGRESS na accept — ten kod zadziała od razu.

### Decyzja 5: Anonymization format

Per ADR D5:
```python
anon_hash = sha256(user.email.encode()).hexdigest()[:16]
user.email = f"deleted_{anon_hash}@deleted.local"
user.username = f"deleted_{anon_hash}"
user.phone_number = None
user.bio = None
user.location_id = None
user.password_hash = "!"  # invalid bcrypt — prevents login
user.email_verified = False
user.phone_verified = False
```

Hash z email zapewnia determinizm (ten sam email → ten sam hash) ale email
nie da się odtworzyć z hash. `deleted.local` nie jest prawdziwą domeną.

UNIQUE constraints: `email` i `username` zachowane — hash unikalne per user.
`phone_number` → NULL (nullable, unique constraint dopuszcza wiele NULLi w PG).

### Decyzja 6: Deleted user placeholder (public profile)

Per ADR D5: `GET /users/{deleted_uuid}` → 200, nie 404.

Modyfikacja `public_profile()` w user_resources_service:
```python
if user.status == UserStatus.DELETED:
    return {
        "id": user.id,
        "username": None,
        "bio": None,
        "location_id": None,
        "heart_balance": 0,
        "created_at": user.created_at,
        "reviews_received": reviews_count,
        "completed_exchanges": completed_count,
        "is_deleted": True,
    }
```

Schema `PublicProfileRead` → dodaj `is_deleted: bool = False`, `username` i `heart_balance` optional.

### Decyzja 7: Email notifications po usunięciu

Dla każdego anulowanego exchange → email do other party (EXCHANGE_CANCELLED).
Wzorzec: notification tworzona w TX (flush), email via BackgroundTasks po commit.

Service zwraca listę `(user_id, email, exchange_id)` affected parties.
Router iteruje po liście i dodaje BackgroundTasks.

### Decyzja 8: Admin nie może soft-delete przez ten endpoint

`DELETE /users/me` wymaga auth → user kasuje SIEBIE. Admin kasuje usera przez
suspend (M15) + ewentualnie przyszły admin-initiated delete (Faza 2).
Admin nie ma `DELETE /admin/users/{id}` w scope M16.

### Decyzja 9: Suspended users mogą się skasować

User SUSPENDED → login zablokowany → nie może wywołać DELETE /users/me.
Ale jeśli admin odwiesi usera (unsuspend) → user może się skasować normalnie.
Brak specjalnego guard — standard auth (get_current_user) wystarczy.

---

## Pliki do utworzenia / zmodyfikowania

### Nowe pliki

| Plik | Opis |
|---|---|
| `app/services/account_service.py` | soft_delete_account() — 8-step atomic cascade |
| `app/schemas/account.py` | SoftDeleteBody, DeletionPreview |
| `tests/test_account_service.py` | Unit testy cascade |
| `tests/test_account_api.py` | Auth guard + integration testy |

### Modyfikowane pliki

| Plik | Zmiana |
|---|---|
| `app/api/v1/users.py` | +DELETE /users/me endpoint |
| `app/services/user_resources_service.py` | public_profile() handles DELETED users |
| `app/schemas/user_resources.py` | PublicProfileRead: +is_deleted, username optional |

---

## Account Service (`app/services/account_service.py`)

```python
async def soft_delete_account(
    db: AsyncSession,
    user_id: UUID,
    *,
    password: str,
    balance_disposition: str,  # "void" | "transfer"
    transfer_to_user_id: UUID | None = None,
) -> list[AffectedParty]:
    """Atomic 8-step account deletion. Returns list of affected parties for email."""
```

### Step-by-step:

**Step 0. Load user + verify password**
```python
user = SELECT User WHERE id=user_id FOR UPDATE
if not user or user.status != ACTIVE:
    raise 404 USER_NOT_FOUND  # also blocks re-delete
verify_password(password, user.password_hash) → 401 WRONG_PASSWORD
```

**Step 1. Validate disposition**
```python
if balance_disposition == "transfer":
    if not transfer_to_user_id:
        raise 422 TRANSFER_RECIPIENT_REQUIRED
    if transfer_to_user_id == user_id:
        raise 422 CANNOT_TRANSFER_TO_SELF
```

**Step 2. Cancel active exchanges + refund + collect notifications**
```python
exchanges = SELECT Exchange WHERE (requester_id=user_id OR helper_id=user_id)
            AND status IN (PENDING, ACCEPTED)

affected_parties: list[AffectedParty] = []

for ex in exchanges:
    # Refund if ACCEPTED escrow
    if ex.status == ACCEPTED and ex.hearts_agreed > 0:
        requester = SELECT User WHERE id=ex.requester_id FOR UPDATE
        requester.heart_balance += ex.hearts_agreed
        INSERT HeartLedger(EXCHANGE_REFUND, from=requester, to=requester, exchange_id=ex.id)

    ex.status = CANCELLED

    # Safety: reopen other party's request if needed (D4)
    if ex.request_id:
        request = db.get(Request, ex.request_id)
        if request and request.user_id != user_id and request.status != RequestStatus.OPEN:
            request.status = RequestStatus.OPEN

    # Collect notification
    other_id = other_party(ex, user_id)
    await notification_service.create_notification(
        db, other_id, EXCHANGE_CANCELLED,
        reason="account_deleted", related_exchange_id=ex.id,
    )
    affected_parties.append(AffectedParty(user_id=other_id, exchange_id=ex.id))
```

**Step 3. Cancel OPEN requests**
```python
UPDATE Request SET status=CANCELLED WHERE user_id=X AND status=OPEN
```
Nota: powiązane PENDING exchanges dla tych requestów → już anulowane w step 2.

**Step 4. Deactivate offers**
```python
UPDATE Offer SET status=INACTIVE
WHERE user_id=X AND status IN (ACTIVE, PAUSED)
```
Nota: powiązane PENDING exchanges → już anulowane w step 2.

**Step 5. Heart disposition**
```python
if user.heart_balance > 0:
    if balance_disposition == "void":
        INSERT HeartLedger(ACCOUNT_DELETED, from=user, to=None, amount=user.heart_balance)
        user.heart_balance = 0
    elif balance_disposition == "transfer":
        recipient = SELECT User WHERE id=transfer_to_user_id FOR UPDATE
        if not recipient or recipient.status != ACTIVE:
            raise 422 RECIPIENT_NOT_FOUND
        cap check: recipient.heart_balance + user.heart_balance > cap → 422 RECIPIENT_CAP_EXCEEDED
        recipient.heart_balance += user.heart_balance
        INSERT HeartLedger(GIFT, from=user, to=recipient, amount=user.heart_balance,
                           note="Balance transfer — account deletion")
        user.heart_balance = 0
```

**Step 6. Anonymize**
```python
anon = sha256(user.email.encode()).hexdigest()[:16]
user.email = f"deleted_{anon}@deleted.local"
user.username = f"deleted_{anon}"
user.phone_number = None
user.bio = None
user.location_id = None
user.password_hash = "!"
user.email_verified = False
user.phone_verified = False
```

**Step 7. Set status + timestamps**
```python
user.status = UserStatus.DELETED
user.deleted_at = now
user.anonymized_at = now
```

**Step 8. Revoke all refresh tokens**
```python
UPDATE RefreshToken SET revoked_at=now
WHERE user_id=X AND revoked_at IS NULL
```

**flush() + return affected_parties**

### Helper

```python
@dataclass
class AffectedParty:
    user_id: UUID
    exchange_id: UUID
```

---

## Endpointy

### 1. `DELETE /api/v1/users/me` (200)

Auth: get_current_user
Body: SoftDeleteBody (password, balance_disposition, transfer_to_user_id)
Response: MessageResponse ("Konto usunięte.")

```python
@router.delete("/me", response_model=MessageResponse)
async def delete_account(
    body: SoftDeleteBody,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    affected = await account_service.soft_delete_account(
        db, current_user.id,
        password=body.password,
        balance_disposition=body.balance_disposition,
        transfer_to_user_id=body.transfer_to_user_id,
    )
    await db.commit()

    # Send emails to affected parties (best-effort, after commit)
    email_svc = get_email_service()
    for party in affected:
        user = await db.get(User, party.user_id)
        if user and user.email:
            background_tasks.add_task(
                email_svc.send_notification,
                to=user.email, notification_type="EXCHANGE_CANCELLED",
                reason="account_deleted",
            )

    return MessageResponse(detail="Konto usuniete.")
```

---

## Schemas (`app/schemas/account.py`)

```python
class SoftDeleteBody(BaseModel):
    password: str = Field(min_length=1)
    balance_disposition: Literal["void", "transfer"]
    transfer_to_user_id: UUID | None = None
```

---

## Modified schemas (`app/schemas/user_resources.py`)

```python
class PublicProfileRead(BaseModel):
    id: UUID
    username: str | None = None       # was: str (required)
    bio: str | None = None
    location_id: int | None = None
    heart_balance: int = 0            # was: int (required, no default)
    created_at: datetime
    reviews_received: int = 0
    completed_exchanges: int = 0
    is_deleted: bool = False           # NEW
```

---

## Modified user_resources_service.py

```python
async def public_profile(db, user_id):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, "USER_NOT_FOUND")

    # Deleted user placeholder (ADR D5)
    if user.status == UserStatus.DELETED:
        # Still count reviews/exchanges — they remain visible
        reviews_received = ...  # same query as below
        completed_exchanges = ...  # same query as below
        return {
            "id": user.id,
            "username": None,
            "bio": None,
            "location_id": None,
            "heart_balance": 0,
            "created_at": user.created_at,
            "reviews_received": reviews_received,
            "completed_exchanges": completed_exchanges,
            "is_deleted": True,
        }

    # Suspended → 404 (hide from public)
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(404, "USER_NOT_FOUND")

    # ... existing code for ACTIVE users ...
    return { ... , "is_deleted": False }
```

---

## Testy

### Unit testy (`tests/test_account_service.py`)

| Test | Opis |
|---|---|
| **Happy path** | |
| test_soft_delete_void_basic | void disposition, balance zeroed, ACCOUNT_DELETED ledger |
| test_soft_delete_void_zero_balance | balance=0, void → no ledger entry needed, still works |
| test_soft_delete_transfer_basic | transfer to recipient, GIFT ledger, recipient balance increased |
| test_soft_delete_transfer_cap_exceeded | recipient.balance + user.balance > cap → 422 |
| test_soft_delete_transfer_recipient_not_found | invalid UUID → 422 |
| test_soft_delete_transfer_to_self | → 422 CANNOT_TRANSFER_TO_SELF |
| test_soft_delete_transfer_missing_recipient_id | disposition=transfer, no UUID → 422 |
| **Cascade — exchanges** | |
| test_soft_delete_cancels_pending_exchanges | PENDING → CANCELLED, no refund |
| test_soft_delete_cancels_accepted_exchanges_refund | ACCEPTED → CANCELLED + EXCHANGE_REFUND ledger |
| test_soft_delete_notifications_sent | each other party gets EXCHANGE_CANCELLED with reason |
| test_soft_delete_reopens_other_request | safety: other party's request reopened if needed |
| **Cascade — requests/offers** | |
| test_soft_delete_cancels_open_requests | all OPEN → CANCELLED |
| test_soft_delete_inactivates_offers | ACTIVE + PAUSED → INACTIVE |
| test_soft_delete_completed_exchange_untouched | COMPLETED exchange not affected |
| **Anonymization** | |
| test_soft_delete_anonymizes_user | email, username hashed; phone, bio, location NULL |
| test_soft_delete_password_invalidated | password_hash = "!", login impossible |
| **Token revocation** | |
| test_soft_delete_revokes_all_tokens | all refresh tokens revoked |
| **Guards** | |
| test_soft_delete_wrong_password | → 401 WRONG_PASSWORD |
| test_soft_delete_already_deleted | re-delete → 404 (user not ACTIVE) |
| **Balance after refund** | |
| test_soft_delete_refund_then_void | escrow refund first, then void = correct final balance |

~20 unit testow.

### API testy (`tests/test_account_api.py`)

| Test | Opis |
|---|---|
| test_delete_no_token | → 401 |
| test_delete_wrong_password | → 401 |
| test_public_profile_deleted_user | → 200, is_deleted=True, username=None |
| test_public_profile_active_user_has_is_deleted_false | → 200, is_deleted=False |

4 API testow.

**Total: ~24 testy.**

---

## Kolejnosc implementacji

1. Schemas (account.py) — SoftDeleteBody
2. account_service.py — soft_delete_account (8-step cascade)
3. tests/test_account_service.py — po kazdej grupie
4. Modified user_resources_service.py — public_profile placeholder
5. Modified schemas/user_resources.py — PublicProfileRead optional fields + is_deleted
6. Endpoint (users.py) — DELETE /users/me
7. tests/test_account_api.py — auth guard + public profile
8. Run all tests — verify no regressions

---

## Wzorce do zachowania

1. **flush-only w service, commit w router**
2. **SELECT FOR UPDATE** na user i recipient (hearts transfer)
3. **Exchanges first** → refund → disposition → atomowość salda
4. **Notification in-TX, email after commit** (BackgroundTasks)
5. **404 for non-ACTIVE** (except DELETED → placeholder)
6. **Password confirmation** na destrukcyjnych operacjach
7. **sha256 anonymization** — deterministyczna, nieodwracalna

---

## Poza scope M16

- Hard delete (GDPR right to erasure full purge) — Faza 4
- Grace period (undo deletion within 30 days) — Faza 2
- Admin-initiated account deletion (DELETE /admin/users/{id}) — Faza 2
- Message content clearing (ADR D6 mentioned but deferred — messages stay as-is, sender rendered as placeholder)
- Deletion preview endpoint (GET /users/me/deletion-preview) — nice-to-have, not MVP
