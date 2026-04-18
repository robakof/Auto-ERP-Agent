# Serce — M17: APScheduler — expire requests

Date: 2026-04-18
Status: Proposed
Author: Architect
Depends on: M7 (Requests CRUD)

---

## Cel

Automatyczne wygaszanie requestów (`OPEN` → `CANCELLED`) po upływie `expires_at`.
Job uruchamiany cyklicznie (co godzinę) kaskaduje PENDING Exchanges i wysyła
Notification `REQUEST_EXPIRED` do ownera każdego wygaszonego requestu.

---

## Decyzje architektoniczne

### D1. Wybór schedulera: APScheduler 4.x (async-native)

**Opcje rozważone:**

| Opcja | Zalety | Wady |
|---|---|---|
| APScheduler 4.x | Async-native, integracja z FastAPI lifespan, lekki, w-process | Brak przeżywania restartów (job nie persystuje) |
| Celery Beat | Persystencja, retry, dead letter | Wymaga brokera (Redis/RabbitMQ), overengineering na MVP |
| asyncio.create_task + sleep loop | Zero zależności | Brak kontroli, brak graceful shutdown, amateur-hour |
| pg_cron (PostgreSQL) | DB-native, persystentny | Vendor lock, brak notyfikacji/email w SQL, wymaga pg_cron extension |

**Decyzja:** APScheduler 4.x — `AsyncScheduler` z `IntervalTrigger(hours=1)`.

**Uzasadnienie:**
- MVP nie wymaga persystencji jobu — restart = ponowne uruchomienie schedulera, job nadrabia natychmiast (batch UPDATE WHERE expires_at < now()).
- Zero dodatkowej infrastruktury (brak brokera).
- Async-native — nie blokuje event loop FastAPI.
- Graceful shutdown przez FastAPI lifespan context manager.
- Gdy projekt urośnie do Celery (Faza 2+) — logika joba (expire function) zostaje, zmienia się tylko trigger.

**Trade-off:** Jeśli app crashuje w momencie gdy job powinien się odpalić — następne uruchomienie nadrobi (idempotentny batch). Okno opóźnienia = max 1h (interwał joba).

### D2. Kaskada PENDING Exchanges

Wygaszony request ma te same konsekwencje co ręczny cancel (M7 `cancel_request`):
- PENDING Exchanges → CANCELLED
- Refund escrow jeśli istnieje (choć w PENDING escrow nie jest zablokowany — weryfikacja)

Użyjemy istniejącej logiki z `request_service.cancel_request` jako referencji, ale
expiry job operuje batch-owo (nie per-request HTTP call) — wyciągniemy wspólną
logikę do wewnętrznej funkcji `_expire_single_request()`.

### D3. Notification + email (best-effort)

- Notification `REQUEST_EXPIRED` INSERT per wygaszony request (w tej samej transakcji co status update).
- Email wysyłany po commicie transakcji (fire-and-forget, jak w M13).
- Email fail nie cofa expiry — best-effort.

### D4. Idempotentność

```sql
UPDATE requests SET status='CANCELLED'
WHERE status='OPEN' AND expires_at < now()
RETURNING id, user_id
```

Job jest idempotentny: jeśli nie ma requestów do wygaszenia — NOP.
Podwójne uruchomienie (race condition) jest bezpieczne: WHERE status='OPEN' eliminuje
już wygaszone requesty.

### D5. Interwał konfigurowalny

`settings.request_expiry_check_interval_minutes: int = 60` — pozwala zmienić
interwał bez zmiany kodu (np. 5 min na dev, 60 min na prod).

---

## Deliverables

### 1. Zależność: `apscheduler>=4.0` w `pyproject.toml`

Dodaj do `dependencies` w `[project]`.

### 2. Config: `request_expiry_check_interval_minutes`

W `app/config.py` → `Settings`:
```python
request_expiry_check_interval_minutes: int = 60
```

### 3. Scheduler service: `app/services/scheduler_service.py`

```python
"""Scheduler service — periodic background jobs."""

async def expire_requests_job():
    """
    Batch expire: OPEN requests with expires_at < now().
    For each expired request:
    1. Set status = CANCELLED
    2. Cancel PENDING Exchanges (cascade)
    3. Create Notification REQUEST_EXPIRED
    4. Send email (best-effort, fire-and-forget)
    """
```

**Wymagania implementacyjne:**
- Własna sesja DB (nie zależy od HTTP request context) — użyj `async_session_factory()` bezpośrednio.
- Transakcja per batch (nie per request) — jedno `commit()` na koniec.
- SELECT FOR UPDATE na requestach do wygaszenia (zapobiega race z ręcznym cancel).
- Logging: `logger.info(f"Expired {count} requests")` lub NOP gdy 0.
- Email przez `get_email_service()` — wymaga pobrania user email z DB.

### 4. Lifecycle w `app/main.py` — lifespan

```python
from apscheduler import AsyncScheduler
from apscheduler.triggers.interval import IntervalTrigger

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncScheduler() as scheduler:
        await scheduler.add_schedule(
            expire_requests_job,
            IntervalTrigger(minutes=settings.request_expiry_check_interval_minutes),
            id="expire_requests",
        )
        await scheduler.start_in_background()
        yield
```

**Ważne:** `start_in_background()` — scheduler działa w tle, nie blokuje startup.
Cleanup automatyczny przez `async with` context manager.

### 5. Testy: `tests/test_scheduler.py`

| Test | Opis |
|---|---|
| `test_expire_open_request_past_expiry` | Request OPEN z `expires_at` w przeszłości → po job: status=CANCELLED, Notification REQUEST_EXPIRED istnieje |
| `test_no_expire_open_request_future` | Request OPEN z `expires_at` w przyszłości → bez zmian |
| `test_no_expire_cancelled_request` | Request CANCELLED z `expires_at` w przeszłości → bez zmian (idempotentność) |
| `test_cascade_pending_exchanges` | Request OPEN + PENDING Exchange → po job: oba CANCELLED |
| `test_no_double_cancel` | Dwa wywołania job pod rząd → drugie = NOP (0 zmian) |
| `test_email_sent_on_expire` | Po expire → email service received notification call |

**Podejście testowe:** Bezpośrednie wywołanie `expire_requests_job()` z fake-time
(request z `expires_at` ustawionym w przeszłości). Nie testujemy APScheduler timing —
testujemy logikę joba.

### 6. Alembic migration (jeśli potrzebna)

Prawdopodobnie NIE potrzebna — `expires_at` i `NotificationType.REQUEST_EXPIRED` już istnieją.
Weryfikacja na etapie implementacji.

---

## Nie robimy (out of scope)

- Persystencja scheduler state (job history) — MVP nie wymaga.
- Admin endpoint do ręcznego triggera expire — można dodać później.
- Retry failed emails — M13 ustaliło best-effort pattern, konsekwentnie stosujemy.
- Expire offers — roadmapa tego nie przewiduje; offers mają status PAUSED/INACTIVE (ręczny).

---

## DoD (Definition of Done)

1. `apscheduler>=4.0` w dependencies, zainstalowany.
2. `expire_requests_job()` wygasza OPEN requesty z `expires_at < now()`.
3. Kaskada: PENDING Exchanges dla wygaszonych requestów → CANCELLED.
4. Notification `REQUEST_EXPIRED` tworzony per wygaszony request.
5. Email wysyłany best-effort (fire-and-forget).
6. Scheduler uruchamia się z FastAPI lifespan, zamyka się gracefully.
7. 6 testów PASS (fake-time, idempotentność, kaskada, email).
8. Brak podwójnego anulowania (idempotentność).

---

## Rozmiar: S

Szacunek: 1 nowy plik (scheduler_service.py), edycja 3 plików (main.py, config.py, pyproject.toml), 1 plik testów.
