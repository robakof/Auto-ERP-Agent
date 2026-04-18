# Serce M10 — Messages: Exchange chat

**Wejście:** M9 (exchanges)
**Rozmiar:** S
**Autor:** Architect

---

## Istniejąca infrastruktura

Model `Message` już istnieje (`app/db/models/message.py`):
- id, exchange_id (FK exchanges), sender_id (FK users), content (str), is_hidden (bool), created_at

Brak rating/score — to prosty chat per Exchange.

---

## Pliki do utworzenia / zmodyfikowania

### Nowe pliki

| Plik | Opis |
|---|---|
| `app/services/message_service.py` | Send message, list messages, hide (admin) |
| `app/api/v1/messages.py` | Router: 3 endpointy |
| `app/schemas/message.py` | Request/response models |
| `tests/test_message_service.py` | Unit testy |
| `tests/test_message_api.py` | Auth guard testy |
| `tests/integration/api/test_message_flow.py` | Integration testy |

### Modyfikowane pliki

| Plik | Zmiana |
|---|---|
| `app/api/v1/router.py` | Dodaj `messages_router` |

---

## Endpointy

### 1. `POST /api/v1/exchanges/{exchange_id}/messages` (201)

**Auth:** required (participant only — requester lub helper Exchange)
**Rate limit:** 30/hour
**Body (SendMessageBody):**
```python
content: str = Field(min_length=1, max_length=2000)
```

**Logika service (`send_message`):**
1. Pobierz Exchange → 404 EXCHANGE_NOT_FOUND
2. Sprawdź `current_user.id in (exchange.requester_id, exchange.helper_id)` → 403 NOT_PARTICIPANT
3. Sprawdź `exchange.status != CANCELLED` → 422 EXCHANGE_CANCELLED
4. Utwórz Message(exchange_id, sender_id=current_user.id, content)
5. `db.flush()`, return message

**Wiadomości dozwolone od PENDING** — nie czekamy na ACCEPTED. Uczestnicy mogą rozmawiać
od momentu utworzenia Exchange (negocjacja warunków).

**Wiadomości dozwolone po COMPLETED** — history + podziękowania.

### 2. `GET /api/v1/exchanges/{exchange_id}/messages` (200)

**Auth:** required (participant only)
**Query params:**
```python
offset: int = Query(0, ge=0)
limit: int = Query(50, ge=1, le=100)
```

**Logika service (`list_messages`):**
1. Pobierz Exchange → 404 EXCHANGE_NOT_FOUND
2. Sprawdź participant → 403 NOT_PARTICIPANT
3. Query: `WHERE exchange_id = X AND is_hidden = false` (ukryte przez admina niewidoczne)
4. Sort: `created_at ASC` (chronologicznie)
5. Pagination (offset/limit/total)
6. Return (entries, total)

### 3. `PATCH /api/v1/exchanges/{exchange_id}/messages/{message_id}/hide` (200)

**Auth:** required (admin only)
**Logika service (`hide_message`):**
1. Pobierz Message → 404 MESSAGE_NOT_FOUND
2. Sprawdź `message.exchange_id == exchange_id` → 404 MESSAGE_NOT_FOUND
3. Sprawdź `current_user.role == ADMIN` → 403 ADMIN_ONLY
4. `message.is_hidden = True`
5. `db.flush()`, return message

Moderacja — ukrycie wiadomości bez usuwania. Brak unhide w M10 (M15 admin panel).

---

## Schemas (`app/schemas/message.py`)

```python
class SendMessageBody(BaseModel):
    content: str = Field(min_length=1, max_length=2000)

class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    exchange_id: UUID
    sender_id: UUID
    content: str
    is_hidden: bool
    created_at: datetime

class MessageListResponse(BaseModel):
    entries: list[MessageRead]
    total: int
    offset: int
    limit: int
```

---

## Testy

### Unit testy (`tests/test_message_service.py`)

| Test | Opis |
|---|---|
| **Send** | |
| test_send_message_valid | Participant wysyła wiadomość |
| test_send_not_participant | → 403 |
| test_send_exchange_not_found | → 404 |
| test_send_exchange_cancelled | → 422 |
| test_send_pending_exchange | ✓ (dozwolone od PENDING) |
| test_send_completed_exchange | ✓ (dozwolone po COMPLETED) |
| **List** | |
| test_list_messages_chronological | ASC order |
| test_list_not_participant | → 403 |
| test_list_excludes_hidden | is_hidden=True niewidoczna |
| test_list_pagination | offset/limit + total |
| **Hide** | |
| test_hide_admin_valid | Admin ukrywa wiadomość |
| test_hide_not_admin | → 403 |
| test_hide_wrong_exchange | → 404 |
| test_hide_message_not_found | → 404 |

~14 unit testów.

### Auth guard testy (`tests/test_message_api.py`)

| Test | Opis |
|---|---|
| test_send_no_token | → 401 |
| test_list_no_token | → 401 |
| test_hide_no_token | → 401 |

3 auth guard testy.

### Integration testy (`tests/integration/api/test_message_flow.py`)

| Test | Opis |
|---|---|
| test_send_and_list | Create Exchange → Send → List → verify |
| test_conversation_both_participants | Oba uczestnicy wysyłają → verify order |
| test_send_on_pending | Exchange PENDING → send → 201 |

3 integration testy.

**Total: ~20 testów.**

---

## Wzorce do zachowania

1. **flush-only w service, commit w endpoint**
2. **Participant guard** — reuse wzorca z exchange_service
3. **Sort ASC** (chronologiczny chat, nie DESC jak w feedzie)
4. **Nested route** — `/exchanges/{id}/messages` (nie `/messages`)
5. **is_hidden filter** — admin-only write, excluded from read
