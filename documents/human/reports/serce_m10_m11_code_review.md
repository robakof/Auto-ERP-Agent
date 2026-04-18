# Code Review: Serce M10 (Messages) + M11 (Reviews)

Date: 2026-04-17
Commit: c35e674

## Summary

**Overall assessment:** PASS
**Code maturity level:** L3 Senior — minimalne, czyste services. Brak nadmiarowej logiki, spójne z M6-M9.

## Scope

| Plik | Opis |
|---|---|
| `app/services/message_service.py` | Send, list, hide (89 LOC) |
| `app/services/review_service.py` | Create, list per exchange, list per user (99 LOC) |
| `app/api/v1/messages.py` | 3 endpointy (nested /exchanges/{id}/messages) |
| `app/api/v1/reviews.py` | 3 endpointy (nested + /users/{id}/reviews) |
| `app/schemas/message.py` | SendMessageBody, MessageRead, MessageListResponse |
| `app/schemas/review.py` | CreateReviewBody, ReviewRead, ReviewListResponse |
| `app/api/v1/router.py` | +messages_router, +reviews_router |
| `tests/test_message_service.py` | 14 unit testów |
| `tests/test_message_api.py` | 3 auth guard testów |
| `tests/test_review_service.py` | 12 unit testów |
| `tests/test_review_api.py` | 3 auth guard testów |

## Test results

- `test_message_service.py` — 14/14 PASS
- `test_message_api.py` — 3/3 PASS
- `test_review_service.py` — 12/12 PASS
- `test_review_api.py` — 3/3 PASS
- **Total: 32/32 PASS**

## Findings

### Brak Critical Issues

### Suggestions (S — nice to have)

**S1: `MessageRead.is_hidden` exposed** — `schemas/message.py:20`
Participant widzi pole `is_hidden=False` na każdej wiadomości. Nie szkodzi (hidden filtrowane w query), ale to informacja wewnętrzna. Nie blokuje.

**S2: Review router — mieszany prefix** — `api/v1/reviews.py`
Router reviews nie ma jednego prefix — dwa endpointy pod `/exchanges/{id}/reviews`, trzeci pod `/users/{id}/reviews`. Poprawne rozwiązanie (sensowne route'y), ale niestandardowe vs inne routery (które mają stały prefix). Akceptowalne — wynika z natury endpointów.

## Architecture compliance

| Wzorzec | Status | Uwagi |
|---|---|---|
| flush-only w service, commit w endpoint | ✓ | |
| Participant guard | ✓ | send, list messages, create review, list exchange reviews |
| Nested routes | ✓ | /exchanges/{id}/messages, /exchanges/{id}/reviews |
| ASC sort (chat) | ✓ | Messages chronologicznie |
| DESC sort (feed) | ✓ | User reviews newest first |
| DB-enforced uniqueness (review) | ✓ | UNIQUE(exchange_id, reviewer_id) + app pre-check |
| Immutable reviews | ✓ | Brak PATCH/DELETE |
| Admin-only hide | ✓ | Role check before DB access |

## Plan compliance

**M10 Messages** — 100% scope pokryty:
- ✓ Send (participant, not CANCELLED, dozwolone od PENDING)
- ✓ List (participant, excludes hidden, ASC, pagination)
- ✓ Hide (admin only, exchange_id validation)

**M11 Reviews** — 100% scope pokryty:
- ✓ Create (COMPLETED only, participant, reviewed_id auto, duplicate check)
- ✓ List per exchange (participant, max 2)
- ✓ List per user (public, pagination, DESC)

## Verdict

**PASS** — oba moduły czyste, minimalne, zgodne z planem. Brak issues do naprawy.
