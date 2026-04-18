# Code Review: M13 Notifications (in-app + email)

Date: 2026-04-17
Commit: 6c167c7
Plan: documents/human/plans/serce_m13_notifications.md

## Summary

**Overall assessment:** PASS
**Code maturity level:** L3 Senior — spójny z projektem, czyste funkcje <=15 linii, DRY helper `create_notification()`, pełne pokrycie testami (service + hooks + API + integration), brak niepotrzebnej złożoności. Wzorce M6-M12 zachowane (flush-only w service, commit w router, 404 dla security, offset/limit pagination).

**Scope vs plan:**
- 7/7 hook points zaimplementowanych (exchange 4, message 1, review 1, hearts 1)
- 4/4 endpointy (list, mark read, mark all read, unread count)
- Email extension: Protocol + Mock + Resend
- BackgroundTasks w 4 routerach
- Istniejące testy zaktualizowane (Notification table w fixture)

**Testy:** 318 passed, 0 failed, 3 skipped (concurrency/Postgres). Developer raport zweryfikowany przez diff.

## Findings

### Critical Issues (must fix)

Brak.

### Warnings (should fix)

**W1. Duplikacja logiki recipient między service a router**
- **exchange_service.py:96-100** vs **exchanges.py:41-46** — ta sama logika `if initiated_by != requester_id` powtórzona
- Analogicznie: cancel_exchange (service:258-262 vs router:80-84), send_message (service:44-48 vs messages.py:35-41)
- **Ryzyko:** zmiana logiki w jednym miejscu bez drugiego → email idzie do złej osoby
- **Fix:** `create_notification()` zwraca `Notification` z `user_id` — router używa `notification.user_id` do pobrania emaila. Zmiana return type service functions: `return exchange, notification` (tuple) albo osobne pobranie notification po flush.
- **Prostszy fix:** wyciągnij recipient logic do helper function w exchange_service (`_other_party(exchange, actor_id) -> UUID`), reuse w obu miejscach.

**W2. Email body w ResendEmailService — machine-readable**
- **email_service.py:80-82**: `body = f"Typ: {notification_type}"` — user dostaje email z treścią "Typ: NEW_EXCHANGE"
- Plan mówi "prosty tekst" — ale "prosty" != "surowy enum". Użytkownik nie zrozumie "NEW_EXCHANGE".
- **Fix:** dodaj `_NOTIFICATION_BODIES` mapping analogiczny do `_NOTIFICATION_SUBJECTS`, np. `"NEW_EXCHANGE": "Ktoś zaproponował wymianę na Twoją prośbę. Sprawdź szczegóły w aplikacji."`. Koszt: 10 linii.

### Suggestions (nice to have)

**S1. messages.py — re-fetch exchange po commit**
- **messages.py:35**: `exchange = await db.get(Exchange, exchange_id)` po commit — exchange jest już w session cache, więc to nie jest prawdziwy DB hit. Ale kod sugeruje że jest potrzebny nowy fetch.
- Alternatywa: message_service mógłby zwracać `(msg, exchange)` — ale to zmiana API.
- **Verdict:** OK as-is, session cache pokrywa.

**S2. Brak rate limit na `GET /users/me/notifications`**
- Przy aggressive polling (badge check co 1s) load na DB. Ale to standard — rate limit na reads zazwyczaj na reverse proxy.
- **Verdict:** OK for MVP. Rozważ `Cache-Control` header w Fazie 2.

## Recommended Actions

- [ ] W1: Wyciągnij helper `_other_party(exchange, actor_id)` → reuse w service i router (lub zwracaj notification z service)
- [ ] W2: Dodaj `_NOTIFICATION_BODIES` dict z polskimi opisami per type

## Verdict

Kod jest architektonicznie poprawny. Hook pattern (service tworzy notification w tej samej TX) jest czysty i atomowy. BackgroundTasks dla email to właściwy wybór na tym etapie. Testy pokrywają service + hooks + API + integration. W1 i W2 to quality-of-life — nie blokują merge, ale powinny być zaadresowane przed M14.
