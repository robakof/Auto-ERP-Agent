# Code Review: F2 Auth — login, register, token management

Date: 2026-04-18
Commit: c19ed12
Plan: `documents/human/plans/serce_f2_auth.md`
Build: `npm run build` — PASS (Developer report), Lint — PASS

---

## Summary

**Overall assessment: PASS (z W1-W2 do naprawy)**
**Code maturity level:** L3 Senior — Poprawna separacja concerns (store / API / UI / validation),
token bridge pattern (setTokenStore), promise dedup na auto-refresh, React 19 compliance
(useState for QueryClient, ref guard for strict mode). Drobne niedociągnięcia nie zmieniają oceny.

---

## Plan compliance

| Deliverable | Plik | Status |
|---|---|---|
| D1 Providers (QueryClient + AuthHydration) | `src/lib/providers.tsx` | ✓ |
| D2 layout.tsx edit (Providers wrapper) | `src/app/layout.tsx` | ✓ |
| D3 Zustand auth store + hydration | `src/hooks/use-auth.ts` | ✓ |
| D4 AuthGuard (protected route wrapper) | `src/components/auth/auth-guard.tsx` | ✓ |
| D5 (auth) layout with AuthGuard | `src/app/(auth)/layout.tsx` | ✓ |
| D6 Dashboard placeholder | `src/app/(auth)/dashboard/page.tsx` | ✓ |
| D7 Zod validators (login, register) | `src/lib/validators/auth.ts` | ✓ |
| D8 Login page (RHF + Zod + toast) | `src/app/(public)/login/page.tsx` | ✓ |
| D9 Register page (RHF + Zod + hCaptcha) | `src/app/(public)/register/page.tsx` | ✓ |
| D10 Verify email sent placeholder | `src/app/(public)/verify-email-sent/page.tsx` | ✓ |
| D11 Public layout (passthrough) | `src/app/(public)/layout.tsx` | ✓ |
| D12 Auth skeleton (loading state) | `src/components/auth/auth-skeleton.tsx` | ✓ |
| D13 .env.local.example update | `.env.local.example` | ✓ |

13/13 deliverables — COMPLETE.

---

## Findings

### Critical Issues (must fix)

- **W1 — `auth.ts` logout endpoint sends no body, backend requires `refresh_token`.**

  Backend (`auth.py:96-101`):
  ```python
  @router.post("/logout")
  async def logout(req: RefreshRequest, ...):   # RefreshRequest = { refresh_token: str }
  ```

  Frontend (`auth.ts:28-29`):
  ```typescript
  logout: () => api.post<MessageResponse>("/auth/logout"),
  // No body → backend returns 422 (Unprocessable Entity)
  ```

  Zustand `logout()` (`use-auth.ts:71-80`) catches the error i czyści tokeny lokalnie,
  więc UX nie łamie się — ale **serwer nie invaliduje sesji**. Refresh token
  pozostaje ważny w bazie (do 30 dni TTL). Security issue.

  **Fix (2 pliki):**
  1. `lib/api/auth.ts` — zmień logout na:
     ```typescript
     logout: (data: RefreshRequest) => api.post<MessageResponse>("/auth/logout", data),
     ```
  2. `hooks/use-auth.ts` — zmień logout action:
     ```typescript
     logout: async () => {
       const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
       set({ isLoading: true });
       try {
         if (refreshToken) {
           await auth.logout({ refresh_token: refreshToken });
         }
       } catch {
         // Ignore — clear tokens regardless
       } finally {
         set({ accessToken: null, user: null, isLoading: false });
         localStorage.removeItem(REFRESH_TOKEN_KEY);
       }
     },
     ```

### Warnings (should fix)

- **W2 — Zustand actions (login/register/refresh) duplicate tokenStore.setTokens logic.**

  `setTokenStore()` definiuje `setTokens(access, refresh)` który robi:
  `set({ accessToken: access })` + `localStorage.setItem(...)`.

  Ale login/register/refresh robią to samo inline:
  ```typescript
  set({ accessToken: tokens.access_token });
  localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
  ```

  Dwa code paths zapisujące do tego samego state. Jeśli logika tokenStore się zmieni
  (np. dodanie cookie fallback w Fazie 3), trzeba pamiętać o obu miejscach.

  **Fix:** Wyciągnij helper `storeTokens(tokens: TokenResponse)` lub użyj
  `tokenStore.setTokens()` wewnątrz akcji zamiast duplikacji.
  Nie krytyczne — oba paths zapisują do tego samego state, ale DRY violation.

### Suggestions (nice to have)

- **S1 — Login page: double redirect.**

  useEffect redirectuje do /dashboard gdy user się pojawi,
  PLUS onSubmit robi `router.push("/dashboard")` po login(). Oba triggery uruchomią się
  po udanym loginie. Router obsłuży to gracefully, ale redundantne.
  **Sugestia:** Usuń `router.push` z onSubmit — useEffect obsłuży redirect.
  To samo dotyczy register page (useEffect + router.push do /verify-email-sent).

- **S2 — Register defaultValues type hack.**

  ```typescript
  defaultValues: { tos_accepted: false as unknown as true }
  ```

  Wymuszony przez `z.literal(true)` typ. Działa, ale brzydkie. Alternatywa:
  `z.boolean().refine((v) => v === true, { message: "Wymagane" })` — typ `boolean`,
  walidacja nadal wymaga `true`.

---

## Architecture check

| Kryterium | Wynik |
|---|---|
| Token bridge (setTokenStore)? | ✓ — Zustand wired to API client |
| Auto-refresh on 401 (promise dedup)? | ✓ — delegowane do client.ts |
| Concurrent refresh safety (P3)? | ✓ — hydrate() explicit, auto-refresh in client.ts, nie konkurują |
| SSR safety? | ✓ — all auth code "use client", no server-side localStorage access |
| React 19 compliance? | ✓ — useState for QC, useRef guard for strict mode |
| Zod mirrors Pydantic? | ✓ — email, username min/max, password min/max, literal(true) |
| Route protection? | ✓ — AuthGuard with skeleton, isHydrated flag prevents FOUC |
| Error handling? | ✓ — ApiError → toast, generic fallback |
| hCaptcha integration? | ✓ — state-based key reset on error, conditional render |

---

## Anti-pattern check (PATTERNS.md)

| Anti-pattern | Present? |
|---|---|
| Shared mutable state (SPOF) | ✗ — Zustand is single source of truth, no competing stores |
| Dual-write | ⚠ W2 — tokenStore + inline writes to same state (not breaking, but DRY) |
| Allow-by-Default Security | ✗ — AuthGuard defaults to redirect, not allow |
| Big Bang Refactor | ✗ — incremental, plan-compliant |
| Defensive Programming Hell | ✗ — error handling minimal and appropriate |

---

## Positive highlights

1. **setTokenStore bridge** — clean separation between API client (transport) and state management.
   Zustand owns state, API client delegates to it. Ready for React Native swap (Faza 3).
2. **AuthHydration with ref guard** — handles React 19 strict mode correctly (double mount protection).
3. **hCaptcha state-based key reset** — po error resetuje widget przez key increment zamiast ref.
   React 19 compatible i prostsze od ref approach.
4. **Zod v4 API compliance** — `error:` zamiast `errorMap:`. Developer zweryfikował vs installed version.
5. **Logout graceful degradation** — even with W1 bug, UX not broken (catch + clear).
   Po fixie W1 będzie both secure AND resilient.

---

## Blokada F3?

**NIE po fixie W1.** W1 to 2-liniowy fix (auth.ts + use-auth.ts).
W2 to refactor convenience, nie blokuje. F3 (layout + navigation) nie zależy od logout body.
Ale W1 **MUSI** być naprawiony przed deploy/testing — security issue.

---

## Recommended Actions

1. **W1 (Critical):** Fix logout body — 2 pliki, ~5 linii zmian. Must before any testing.
2. **W2 (Warning):** Extract `storeTokens()` helper — optional, recommended before F8 (sessions).
3. **S1:** Remove double redirect — trivial, optional.
4. **S2:** Zod boolean refine — cosmetic, optional.
