# Code Review: F1 Scaffold + konfiguracja + API client

Date: 2026-04-18
Commits: F1 scaffold + poprawki W1-W6 (commit 8bd72d3)
Plan: `documents/human/plans/serce_f1_scaffold.md`
Build: `npm run build` — PASS, Lint — PASS

---

## Summary

**Overall assessment: PASS (z W items do naprawy)**
**Code maturity level:** L3 Senior — API client z auto-refresh i promise deduplication,
kompletne typy, poprawne enum values vs backend.

W1-W6 z pierwszego review naprawione. Znaleziono 7 endpoint path/method mismatches
vs backend routers — trywialne string fixy, nie blokują F2 (core auth paths poprawne).

---

## Plan compliance

| Deliverable | Status |
|---|---|
| Next.js scaffold (TS, Tailwind, App Router, src-dir) | ✓ (Next.js 16 — OK) |
| shadcn/ui init + bazowe components (5 szt.) | ✓ |
| Root layout (`<html lang="pl">`, Inter, metadata, Toaster) | ✓ |
| Health check page | ✓ |
| `lib/api/client.ts` — fetch wrapper z auto-refresh | ✓ |
| `lib/api/types.ts` — response + request types (~50 interfejsów) | ✓ |
| 14 typed endpoint modules | ✓ |
| Sonner (toast) | ✓ |
| `next.config.ts` rewrites proxy | ✓ |
| docker-compose frontend service | ✓ |
| Dockerfile (multi-stage production) | ✓ |
| `.env.local.example` | ✓ |
| `.gitignore` | ✓ |
| LedgerType kompletny (9 wartości) | ✓ |
| globals.css font fix (Inter) | ✓ |

---

## Findings

### Warnings (must fix)

- **W1 — 7 endpoint path/method mismatches vs backend routers.**
  Zweryfikowane vs `@router` dekoratory w backendzie:

  | # | Plik | Frontend | Backend | Typ |
  |---|---|---|---|---|
  | 1 | `auth.ts:47` | `POST /auth/resend-verification` | `POST /auth/resend-verification-email` | path |
  | 2 | `exchanges.ts:16` | `api.post(…/accept)` | `PATCH …/accept` | method |
  | 3 | `exchanges.ts:19` | `api.post(…/complete)` | `PATCH …/complete` | method |
  | 4 | `exchanges.ts:22` | `api.post(…/cancel)` | `PATCH …/cancel` | method |
  | 5 | `users.ts:21` | `api.post(…/username)` | `PATCH /me/username` | method |
  | 6 | `users.ts:24` | `POST /users/me/email` | `POST /users/me/email/change` | path |
  | 7 | `users.ts:30` | `POST /users/me/phone` | `POST /users/me/phone/change` | path |

  **Fix:** Trywialny — zmiana stringów. Każdy mismatch = 404 lub 405 at runtime.

- **W2 — `notifications.ts:14` — `markRead` używa PATCH, backend używa POST.**
  Backend: `@router.post("/{notification_id}/read")`.
  Frontend: `api.patch(…/read)`.
  **Fix:** Zmień `api.patch` na `api.post`.

- **W3 — `admin.ts:33` — audit path `/admin/audit-log`, backend ma `/admin/audit`.**
  Backend: `@router.get("/audit")`.
  Frontend: `api.get("/admin/audit-log")`.
  **Fix:** Zmień na `/admin/audit`.

### Suggestions (nice to have)

- **S1 — `AcceptTermsRequest` brak w types.ts.**
  Backend ma `POST /auth/accept-terms` z `AcceptTermsRequest` body, ale w auth.ts nie ma
  odpowiedniego endpointu. Nie blokuje — accept-terms to edge case.
  **Priorytet:** niski — dodać gdy potrzebne (F2 lub F10).

- **S2 — `ConfirmEmailChangeRequest` / `VerifyPhoneChangeRequest` brak w types.ts.**
  users.ts używa inline typów `{ token: string }` i `{ new_phone_number: string; code: string }`.
  Działa, ale nie jest spójne z resztą (named types).
  **Priorytet:** niski.

---

## Architecture check

| Kryterium | Wynik |
|---|---|
| TypeScript strict mode? | ✓ |
| Path alias `@/*`? | ✓ |
| API client auto-refresh z promise dedup? | ✓ |
| Token store abstraction (Zustand-ready)? | ✓ |
| Enum values vs backend? | ✓ (wszystkie poprawne) |
| shadcn/ui components (5 bazowych)? | ✓ |
| Docker multi-stage build? | ✓ |
| SEO basics? | ✓ |
| Types kompletność (response + request)? | ✓ |
| Endpoint modules kompletność (14)? | ✓ |

---

## Positive highlights

1. **API client** — functional design z convenience methods `api.get/post/patch/delete`.
   Promise deduplication na refresh — zapobiega race condition. L4 pattern.
2. **Token store abstraction** — `setTokenStore()` oddziela storage od logiki.
   Gotowe na Zustand (F2) i React Native (Faza 3).
3. **Enum values** — Developer zweryfikował vs backend modele. Poprawniejsze niż plan
   (plan miał błędne RequestStatus, NotificationType, FlagReason).
4. **Types kompletność** — ~50 interfejsów, pełny mirror backend schemas.
5. **Multi-stage Dockerfile** — produkcyjny standalone build, lepiej niż plan.

---

## Blokada F2?

**NIE.** F2 zależy od auth.ts endpoints: `register`, `login`, `refresh`, `logout`, `getMe`.
Wszystkie 5 mają **poprawne ścieżki i metody** vs backend. Jedyny auth mismatch
to `resendVerification` (F10 scope, nie F2).

W1-W3 muszą być naprawione ale mogą iść **równolegle z F2** — żaden z 9 mismatched
endpoints nie jest używany w F2 flow.

---

## Recommended Actions

Developer naprawia W1-W3 (9 endpoint fixes) — może jako pierwszy commit F2 lub osobny fix commit.
F2 może startować natychmiast — core auth paths są poprawne.
