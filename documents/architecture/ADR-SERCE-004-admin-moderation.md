# ADR-SERCE-004: Moderacja administracyjna (ContentFlag, audit log, user status)

Date: 2026-04-11
Status: Accepted

---

## Context

Plan v11 zawiera model `ExchangeFlag` (decyzja #24) i pole `User.is_active`, ale nie precyzuje:

1. **Zakresu moderacji** — tylko Exchange czy też User / Request / Offer / Message?
2. **Endpoints admin** — co faktycznie ląduje w Fazie 1
3. **Audit logu** — jak odtworzyć kto co zrobił (compliance, dyscyplina zespołu moderacyjnego)
4. **Akcji moderacyjnych** — jaki jest skończony zestaw `resolution_action`
5. **Semantyki `is_active`** — flaga dwustanowa nie rozróżnia zawieszenia od soft delete
6. **Zachowania zawieszonego konta** — co z trwającymi Exchanges, saldem, feedem
7. **Autoryzacji** — jak rozróżnić usera od admina na poziomie API

Walkthrough (`documents/human/reports/serce_walkthrough_gaps.md`, gapy #4, #15–#18, #20) pokazał że bez moderacji platforma nie ma mechanizmu obrony przed oszustwami i spamem — a z samym `ExchangeFlag` obejmuje tylko wąski wycinek.

---

## Decision

### D1 — Zakres admin endpoints w Fazie 1

W Fazie 1 wchodzi pełen zestaw potrzebny do samodzielnego moderowania platformy. Ograniczenie zakresu zostawiłoby moderację ślepą (brak audytu) lub bezzębną (brak możliwości przyznania rekompensaty).

**Endpoints:**
```
GET    /admin/flags?status=open&target_type=User|Request|Offer|Exchange|Message
GET    /admin/flags/{id}
POST   /admin/flags/{id}/resolve
POST   /admin/users/{id}/suspend
POST   /admin/users/{id}/unsuspend
POST   /admin/hearts/grant
GET    /admin/audit?actor_id=&action=&target_type=&from=&to=
```

Wszystkie pod prefiksem `/api/v1/admin/`. Paginacja i filtry jak reszta API (decyzja #43).

### D2 — ContentFlag zamiast ExchangeFlag (refactor modelu)

Zamiast wąskiego `ExchangeFlag` wprowadzamy polimorficzny `ContentFlag`:

```
ContentFlag
  id                UUID PK
  reporter_id       FK User (nullable — anonimowe zgłoszenia z publicznego feedu)
  target_type       ENUM(user, request, offer, exchange, message)
  target_id         UUID
  reason            ENUM(spam, scam, abuse, inappropriate, other)
  description       TEXT (nullable, max 1000)
  status            ENUM(open, resolved, dismissed) DEFAULT open
  resolved_by       FK User (admin, nullable)
  resolved_at       TIMESTAMP (nullable)
  resolution_action ENUM (patrz D3, nullable)
  resolution_reason TEXT (nullable, max 1000)
  created_at        TIMESTAMP
```

**Uzasadnienie:** migracja polimorficzna później boli. `target_type + target_id` pokrywa wszystkie obecne i przyszłe obiekty moderowane bez nowych tabel.

**Model `ExchangeFlag` z planu (#24) zostaje usunięty** — zastąpiony ContentFlag z `target_type='exchange'`.

### D3 — Akcje moderacyjne (resolution_action enum)

Skończony zestaw akcji dostępnych w `POST /admin/flags/{id}/resolve`:

| Wartość | Semantyka |
|---|---|
| `dismiss` | Zgłoszenie bezzasadne, nic się nie dzieje |
| `warn_user` | Ostrzeżenie reportowanego usera (notyfikacja, bez sankcji) |
| `hide_content` | Ukrycie targetu z publicznego feedu (Request/Offer → `status=hidden`; Message → `is_hidden=true`) |
| `suspend_user` | Zawieszenie konta reportowanego (wywołuje flow z D6) |
| `ban_user` | Permanentne zawieszenie (alias `suspend_user` z `suspended_until=NULL`) |
| `grant_hearts_refund` | Przyznanie serc poszkodowanemu (body wymaga `refund_to_user_id`, `amount`) |

Endpoint `POST /admin/flags/{id}/resolve` przyjmuje `action` + opcjonalne parametry właściwe dla akcji. Każda akcja zapisuje wpis w `AdminAuditLog`.

### D4 — AdminAuditLog (nowy model)

```
AdminAuditLog
  id            UUID PK
  admin_id      FK User (NOT NULL)
  action        VARCHAR(64) (np. "flag.resolve", "user.suspend", "hearts.grant")
  target_type   ENUM(user, request, offer, exchange, message, flag, system)
  target_id     UUID (nullable — np. przy akcjach systemowych)
  payload       JSONB (pełny request body + istotny kontekst)
  reason        TEXT (wymagane dla akcji sankcyjnych)
  created_at    TIMESTAMP
```

**Immutable** — brak UPDATE/DELETE (enforced w serwisie, nie ma endpointów modyfikujących). Każda akcja admin (w tym `hearts.grant`, `flag.resolve`, `user.suspend`) musi zapisać wpis w tej samej transakcji co akcja właściwa. Brak wpisu = brak akcji.

`GET /admin/audit` zwraca paginowaną listę z filtrami.

### D5 — User.status zamiast is_active (refactor)

`User.is_active: BOOL` zastępujemy `User.status: ENUM('active', 'suspended', 'deleted')`:

| Stan | Znaczenie |
|---|---|
| `active` | Konto działa normalnie |
| `suspended` | Admin zawiesił konto (patrz D6) |
| `deleted` | Soft delete przez usera (ADR-003) |

**Uzasadnienie:** dwie flagi (`is_active`, `deleted_at`) dawały cztery kombinacje, z czego połowa niemożliwa. Enum wymusza konsystencję i czyni intencję stanu explicite.

**Pole usuwane:** `is_active`.
**Pola pozostają:** `deleted_at`, `anonymized_at` (z ADR-003) — uzupełniają `status=deleted`.
**Pola dodawane:** `suspended_at`, `suspended_until` (NULL = permanentny ban), `suspension_reason`.

### D6 — Zachowanie zawieszonego konta

Flow `POST /admin/users/{id}/suspend` (body: `reason`, opcjonalne `until`):

1. `User.status = 'suspended'`, zapis `suspended_at`, `suspended_until`, `suspension_reason`.
2. **Revoke wszystkich refresh tokenów** usera (zgodnie z decyzją #62).
3. Requests/Offers usera **ukryte z publicznego feedu** (filtrowane w query po `owner.status='active'`), ale nie anulowane.
4. Aktywne Exchanges **trwają** — druga strona może dokończyć, wystawić review, odebrać serca. Zawieszony nie może pisać Messages ani podejmować akcji (enforce w dependency).
5. **Saldo serc zamrożone** — user nie może wydawać (PENDING → ACCEPTED blokowane), nie traci salda.
6. Wpis w `AdminAuditLog` z akcją `user.suspend`.

Próba logowania zawieszonego konta: `401 ACCOUNT_SUSPENDED` z polami `suspended_until`, `reason` w payloadzie błędu (fair play — user wie za co).

`POST /admin/users/{id}/unsuspend` odwraca stan: `status='active'`, czyści `suspended_*`, wpis w audit log `user.unsuspend`.

### D7 — Autoryzacja endpointów /admin/*

Nowe pole `User.role: ENUM('user', 'admin') DEFAULT 'user'`.

Dependency FastAPI `require_admin()`:
```python
async def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(403, {"code": "FORBIDDEN_ADMIN_ONLY"})
    return user
```

Wszystkie `/admin/*` używają `Depends(require_admin)`. Pierwszy admin ustawiany ręcznie w DB (seed migration). Promocja user→admin tylko przez SQL (brak endpointu) w Fazie 1 — świadoma decyzja: RBAC bez endpointu zmusza do jawnej decyzji operacyjnej, nie da się przypadkiem nadać admin przez UI.

Brak RBAC z rolami pośrednimi (moderator, support). Dwa stany wystarczają w Fazie 1; rozbudowa w Fazie 2+ jeśli pojawi się potrzeba.

---

## Consequences

### Pozytywne

- **Moderacja ma komplet narzędzi:** zgłoszenia, rozstrzygnięcia, sankcje, rekompensaty, audyt — w jednej fazie.
- **ContentFlag skaluje się** na wszystkie obiekty bez migracji schematu.
- **Audit log jest transakcyjny** — brak sytuacji "sankcja bez wpisu" lub odwrotnie.
- **Status enum** eliminuje nieistniejące kombinacje flag (`is_active=false` + `deleted_at=null` + `suspended_at=null` = co to znaczy?).
- **Zawieszenie nie niszczy trwających transakcji** — druga strona nie traci serc za cudzą winę.
- **Saldo zawieszonego zamrożone** — zgodne z zasadą "waluta usera jego własnością" z ADR-003.
- **require_admin() jako dependency** wymusza explicite opt-in na każdym admin endpoint.

### Negatywne / koszty

- **Refactor modelu User:** migracja `is_active → status`, dodanie `role`, `suspended_*`. Boli raz, potem czystsze.
- **Polimorficzny `target_type+target_id`:** brak FK constraint, wymaga walidacji w serwisie (`target_id` musi istnieć w tabeli określonej przez `target_type`).
- **AdminAuditLog rośnie szybko:** każda akcja admin = wpis. Potrzebna polityka retencji (→ ADR-006 Legal Compliance).
- **`grant_hearts_refund` wymaga rozszerzenia HeartLedger** (ADR-002) o nowy `reason='admin_refund'` — drobna zmiana, ale do odnotowania.
- **Pierwszy admin tylko przez SQL** — operacyjnie uciążliwe, ale bezpieczniejsze niż bootstrap endpoint.

### Otwarte kwestie (poza scope ADR-004)

- **Retencja audit logu** — ile miesięcy trzymamy wpisy → ADR-006.
- **Notyfikacja zawieszenia** — czy user dostaje email/in-app o zawieszeniu → decyzja operacyjna, do planu jako zwykły task.
- **Rate limiting zgłoszeń** — żeby jeden user nie spamował flagami → decyzja operacyjna, do Fazy 1.5.
- **Appeal flow** — możliwość odwołania się od zawieszenia → Faza 2+.

---

## Implementation notes

- Modele dodawane: `ContentFlag`, `AdminAuditLog`.
- Modele usuwane: `ExchangeFlag`.
- Model modyfikowany: `User` — usuwamy `is_active`, dodajemy `status`, `role`, `suspended_at`, `suspended_until`, `suspension_reason`.
- HeartLedger: nowy `reason='admin_refund'` dla `grant_hearts_refund`.
- Dependency: `require_admin()` w `backend/app/api/deps.py`.
- Query filtr w publicznym feedzie: `WHERE owner.status = 'active'` (ukrywa suspended + deleted w jednym warunku).
- Seed migracja: wskazanie pierwszego admina po `email` w env var `INITIAL_ADMIN_EMAIL`.
