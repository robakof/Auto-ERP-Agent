# Code Review: Serce M8 — Offers CRUD + Status Management

Date: 2026-04-17
Branch: main (uncommitted)

## Summary

**Overall assessment:** PASS
**Code maturity level:** L3 Senior — spójne wzorce z M7 (request_service), czytelna separacja warstw (service/schema/endpoint), status transitions jako whitelist dict, cascade logika izolowana w service. Brak unnecessary abstractions.

## Scope

| Plik | Opis |
|---|---|
| `app/services/offer_service.py` | Core CRUD + listing + status management |
| `app/api/v1/offers.py` | Router: 5 endpointów |
| `app/schemas/offer.py` | Pydantic request/response models |
| `app/api/v1/router.py` | Rejestracja offers_router |
| `tests/test_offer_service.py` | 31 unit testów |
| `tests/test_offer_api.py` | 5 auth guard testów |
| `tests/integration/api/test_offer_flow.py` | 6 integration testów (skipped — Postgres) |

## Test results

- `test_offer_service.py` — 31/31 PASS
- `test_offer_api.py` — 5/5 PASS
- `test_offer_flow.py` — 6/6 SKIPPED (integration, requires Postgres)
- **Total: 36/36 PASS**

## Findings

### Warnings (W — should fix)

**W1: HIDDEN cascade brakuje** — `offer_service.py:128`
Przejście do INACTIVE kaskadowo anuluje PENDING Exchanges — poprawne. Ale przejście do HIDDEN (admin moderacja) NIE kaskaduje PENDING Exchanges. Czy HIDDEN oferta powinna mieć aktywne Exchange? Plan M8 mówi o cascade tylko dla INACTIVE, więc to zgodne z planem — ale semantycznie HIDDEN = "oferta ukryta przez admina" i PENDING Exchanges na ukrytej ofercie wyglądają na anomalię.

**Rekomendacja:** Dodaj cascade PENDING→CANCELLED też dla HIDDEN, albo jawnie udokumentuj decyzję w planie M9 (Exchange guard sprawdzi status oferty przy accept).

**W2: `sort` parameter — injection surface** — `offer_service.py:181`
`sort_col = getattr(Offer, sort, Offer.created_at)` — `getattr` na modelu z user input. Endpoint ogranicza pattern do `^(created_at|hearts_asked)$` (offers.py:98), więc w runtime jest bezpieczne. Ale service sam nie waliduje — defense in depth sugerowałby allowlist w service.

**Rekomendacja:** Identyczny wzorzec jak request_service — OK do zachowania spójności. Jeśli kiedyś service będzie wywoływany poza endpointem, dodaj guard. Nie blokuje PASS.

### Suggestions (S — nice to have)

**S1: `NOT_OWNER` error dla admin denied** — `offer_service.py:118`
Gdy non-admin próbuje ustawić HIDDEN, error to `NOT_OWNER`. Bardziej precyzyjny byłby `ADMIN_ONLY` — ale spójne z request_service, gdzie też jest NOT_OWNER. Niski priorytet.

**S2: Brak testu admin hide z PAUSED oferty** — `test_offer_service.py`
Test `test_status_admin_can_hide` ukrywa ACTIVE ofertę. Brak testu dla hide z PAUSED/INACTIVE. Plan mówi "admin może HIDDEN z dowolnego stanu" — warto pokryć.

## Architecture compliance

| Wzorzec | Status | Uwagi |
|---|---|---|
| flush-only w service, commit w endpoint | ✓ | Spójne z M4-M7 |
| Validation at Boundary → Trust Internally | ✓ | Pydantic (schema) + HTTPException (service) |
| Feed filter (JOIN User WHERE active) | ✓ | list_offers filtruje suspended users |
| ILIKE search | ✓ | Identyczny wzorzec jak M7 |
| Ownership guard | ✓ | get/update/status |
| Cascade pattern | ✓ | INACTIVE → cancel PENDING Exchanges |
| Convention First (schemas) | ✓ | CreateBody/UpdateBody/Read/ListResponse |

## Plan compliance

Implementacja pokrywa 100% scope z `serce_m8_offers.md`:
- ✓ 5 endpointów (POST, GET/{id}, PATCH/{id}, PATCH/{id}/status, GET)
- ✓ Status transitions (ACTIVE↔PAUSED, →INACTIVE, admin→HIDDEN)
- ✓ INACTIVE cascade
- ✓ Feed filter, ILIKE search, pagination
- ✓ Auth guard testy, unit testy, integration testy

## Recommended Actions

- [ ] W1: Zdecyduj o HIDDEN cascade (dodaj cascade lub udokumentuj w M9 Exchange guard)
- [ ] W2: Akceptowalne — spójne z request_service, guard w endpoint wystarczy
- [ ] S2: Opcjonalnie dodaj test admin hide z PAUSED/INACTIVE (low priority)

## Verdict

**PASS** — kod na poziomie L3, spójny z istniejącą architekturą M7, brak critical issues. W1 (HIDDEN cascade) to decyzja designowa do podjęcia przy M9, nie bloker M8.
