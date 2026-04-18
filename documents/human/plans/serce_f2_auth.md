# F2 — Auth: login + register + token management

Date: 2026-04-18
Status: Proposed
Author: Architect
Zależność: F1 COMPLETE (commit 8bd72d3)
Roadmap: `documents/human/plans/serce_faza2_roadmap.md` sekcja F2

---

## Cel

Zaimplementować kompletny flow autentykacji: rejestracja (z hCaptcha), logowanie,
zarządzanie tokenami (Zustand + auto-refresh), ochrona stron, wylogowanie.
Po F2 użytkownik może: register → login → dashboard (placeholder) → logout.

---

## Decyzje architektoniczne (F2-specific)

### A1. Auth storage — client-side only (MVP)

| Element | Gdzie | Dlaczego |
|---|---|---|
| Access token | Zustand (in-memory) | Krótki TTL (15 min), nie przeżywa refresha strony — OK |
| Refresh token | localStorage | Backend zwraca w JSON body, nie cookie. Migracja na httpOnly = backlog Faza 3 |
| User object | Zustand (persisted via `getMe()` on hydration) | Nie persist user — zawsze świeży z API |

**Trade-off:** localStorage refresh token jest podatny na XSS. Mitigacja:
single-use rotation (backend), 30-day TTL, logout-all endpoint. Akceptowalne dla MVP.

### A2. Protected routes — client-side AuthGuard

Next.js 16 oferuje `unauthorized()` + `authInterrupts` (experimental) — wymaga server-side
session check (cookie). Nasza architektura (JWT client-side) nie ma server-side session →
**nie używamy `unauthorized()`**. Zamiast tego: client-side `AuthGuard` component.

Trade-off: flash of unauthenticated content (FOUC). Mitigacja: loading skeleton
wyświetlany do momentu hydration + auth check.

**Backlog Faza 3:** Migracja na httpOnly cookie → wtedy `unauthorized()` + server-side check.

### A3. middleware.ts → proxy.ts (Next.js 16 breaking change)

Next.js 16 renamed `middleware` → `proxy`. Na razie **nie tworzymy proxy.ts** —
auth check jest client-side. Proxy będzie potrzebne dopiero przy httpOnly cookie flow
lub rate limiting na edge.

### A4. Providers architecture

```
layout.tsx
  └── Providers (client component)
        ├── QueryClientProvider (TanStack Query)
        ├── AuthHydration (auto-load user on mount)
        └── Toaster (sonner — already in layout)
```

`Providers` to jeden wrapper — unikamy provider hell. Toaster już jest w layout.tsx.

---

## Nowe zależności

```bash
npm install zustand @tanstack/react-query zod react-hook-form @hookform/resolvers @hcaptcha/react-hcaptcha
```

| Pakiet | Rola | Rozmiar (gzip) |
|---|---|---|
| `zustand` | Auth store (user, tokens, actions) | ~1.5 KB |
| `@tanstack/react-query` | Server state cache (foundation for F3+) | ~13 KB |
| `zod` | Form validation (mirror Pydantic) | ~13 KB |
| `react-hook-form` | Formularze (performant, uncontrolled) | ~9 KB |
| `@hookform/resolvers` | Zod ↔ react-hook-form bridge | ~1 KB |
| `@hcaptcha/react-hcaptcha` | Captcha widget na register | ~3 KB |

---

## Deliverables — file by file

### D1. `src/lib/providers.tsx` (NEW)

Client component. Opakowuje `QueryClientProvider` + `AuthHydration`.

```tsx
"use client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useRef } from "react";
import { AuthHydration } from "@/hooks/use-auth";

export function Providers({ children }: { children: React.ReactNode }) {
  const qc = useRef(new QueryClient({
    defaultOptions: { queries: { staleTime: 30_000, retry: 1 } },
  }));
  return (
    <QueryClientProvider client={qc.current}>
      <AuthHydration />
      {children}
    </QueryClientProvider>
  );
}
```

### D2. `src/app/layout.tsx` (EDIT)

Dodaj `<Providers>` wrapper wokół `{children}`.

### D3. `src/hooks/use-auth.ts` (NEW)

Zustand store. Najważniejszy plik F2.

**Eksporty:**

```typescript
// Store state
interface AuthState {
  user: UserRead | null;
  accessToken: string | null;
  isHydrated: boolean;            // true after initial getMe() attempt
  isLoading: boolean;

  // Actions
  login: (data: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<boolean>;
  hydrate: () => Promise<void>;   // getMe() → set user, called once on mount
}

export const useAuth: UseBoundStore<StoreApi<AuthState>>;

// AuthHydration — component that runs hydrate() once on mount
export function AuthHydration(): null;
```

**Implementacja (key decisions):**

1. `login()` → `auth.login(data)` → store tokens → `auth.getMe()` → store user → redirect `/dashboard`
2. `register()` → `auth.register(data)` → store tokens → `auth.getMe()` → redirect `/verify-email-sent`
3. `logout()` → `auth.logout()` → clear tokens → clear user → redirect `/login`
4. `refresh()` → `auth.refresh({ refresh_token })` → rotate tokens → return success
5. `hydrate()` → if refresh token in localStorage → try `refresh()` → `getMe()` → set user

**Token store bridge:**
On store init, call `setTokenStore()` from `lib/api/client.ts` — connects Zustand to API client.
API client already handles auto-refresh on 401 via `refreshPromise` dedup.

**localStorage contract:**
- Key: `serce_refresh_token`
- On `setTokens()`: save refresh to localStorage, keep access in memory
- On `clearTokens()`: remove from localStorage + null in state
- On hydration: read from localStorage, attempt refresh

### D4. `src/components/auth/auth-guard.tsx` (NEW)

Client component. Protects `(auth)` route group.

```tsx
"use client";
import { useAuth } from "@/hooks/use-auth";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { user, isHydrated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isHydrated && !isLoading && !user) {
      router.replace("/login");
    }
  }, [isHydrated, isLoading, user, router]);

  if (!isHydrated || isLoading) {
    return <AuthSkeleton />;     // full-page loading skeleton
  }
  if (!user) return null;        // redirecting
  return <>{children}</>;
}
```

### D5. `src/app/(auth)/layout.tsx` (NEW)

Layout for protected route group. Wraps children in `AuthGuard`.

```tsx
import { AuthGuard } from "@/components/auth/auth-guard";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return <AuthGuard>{children}</AuthGuard>;
}
```

### D6. `src/app/(auth)/dashboard/page.tsx` (NEW)

Placeholder dashboard. Pokazuje username, saldo, przycisk logout.

```tsx
"use client";
import { useAuth } from "@/hooks/use-auth";

export default function DashboardPage() {
  const { user, logout } = useAuth();
  return (
    <main>
      <h1>Witaj, {user?.username}</h1>
      <p>Saldo: {user?.heart_balance} serc</p>
      <button onClick={logout}>Wyloguj</button>
    </main>
  );
}
```

### D7. `src/lib/validators/auth.ts` (NEW)

Zod schemas — mirror backend `schemas/auth.py`.

```typescript
import { z } from "zod";

export const loginSchema = z.object({
  email: z.string().email("Nieprawidlowy email"),
  password: z.string().min(1, "Haslo wymagane"),
});

export const registerSchema = z.object({
  email: z.string().email("Nieprawidlowy email"),
  username: z.string().min(3, "Min. 3 znaki").max(30, "Max. 30 znakow"),
  password: z.string().min(8, "Min. 8 znakow").max(128),
  tos_accepted: z.literal(true, { errorMap: () => ({ message: "Wymagana akceptacja regulaminu" }) }),
  privacy_policy_accepted: z.literal(true, { errorMap: () => ({ message: "Wymagana akceptacja polityki prywatnosci" }) }),
});

export type LoginFormData = z.infer<typeof loginSchema>;
export type RegisterFormData = z.infer<typeof registerSchema>;
```

### D8. `src/app/(public)/login/page.tsx` (NEW)

Login page. React Hook Form + Zod + error handling.

**UX flow:**
1. Email + password fields
2. Submit → loading state → success → redirect /dashboard
3. Error → toast (sonner) + inline field errors
4. Link: "Nie masz konta? Zarejestruj się" → /register
5. Link: "Zapomniałeś hasła?" → /forgot-password (placeholder, F10)

**Redirect if already logged in:** if `user` exists on mount → redirect /dashboard.

### D9. `src/app/(public)/register/page.tsx` (NEW)

Register page. React Hook Form + Zod + hCaptcha.

**UX flow:**
1. Email, username, password fields
2. Checkboxes: TOS + privacy policy (z.literal(true) validation)
3. hCaptcha widget (invisible or checkbox — decyzja implementacyjna)
4. Submit → loading → success → redirect /verify-email-sent (placeholder info page)
5. Error → toast + inline field errors
6. Link: "Masz konto? Zaloguj się" → /login

**hCaptcha integration:**
- Site key from `NEXT_PUBLIC_HCAPTCHA_SITEKEY` env var
- On submit: execute captcha → get token → append to request body as `captcha_token`
- On error: toast "Weryfikacja nie powiodla sie"

### D10. `src/app/(public)/verify-email-sent/page.tsx` (NEW)

Static info page: "Sprawdź swoją skrzynkę email". Link do /login.
Placeholder — pełny verify flow w F10.

### D11. `src/app/(public)/layout.tsx` (NEW)

Layout for public route group. Redirect to /dashboard if already logged in (optional,
nie krytyczne — login/register robią to same).

### D12. `src/components/auth/auth-skeleton.tsx` (NEW)

Full-page loading skeleton (pulsujący placeholder) wyświetlany
podczas hydration auth state.

### D13. `.env.local.example` (EDIT)

Dodaj: `NEXT_PUBLIC_HCAPTCHA_SITEKEY=10000000-ffff-ffff-ffff-000000000000`
(test key for development).

---

## Endpoint contract — weryfikacja

Endpointy auth.ts wymagane w F2 (potwierdzone vs backend `auth.py`):

| Frontend (auth.ts) | Method | Path | Backend router | Match? |
|---|---|---|---|---|
| `register` | POST | `/auth/register` | `@router.post("/register")` | ✓ |
| `login` | POST | `/auth/login` | `@router.post("/login")` | ✓ |
| `refresh` | POST | `/auth/refresh` | `@router.post("/refresh")` | ✓ |
| `logout` | POST | `/auth/logout` | `@router.post("/logout")` | ✓ |
| `getMe` | GET | `/auth/me` | `@router.get("/me")` | ✓ |

Wszystkie 5 core auth paths — MATCH. Żaden z 9 endpoint mismatches (known debt) nie dotyczy F2.

---

## Nie w scope F2

| Element | Milestone |
|---|---|
| Email verification flow (verify-email page + resend) | F10 |
| Phone verification (OTP input) | F10 |
| Password reset (forgot + reset) | F10 |
| Session management (list + revoke) | F8 |
| Accept terms endpoint | F10 or later |
| Header / navigation | F3 |

---

## Potencjalne pułapki

### P1. Zustand + server rendering
Zustand store jest client-only. Server Components nie mają dostępu do auth state.
Rozwiązanie: wszystkie strony wymagające auth są `"use client"` lub wrapped w
client-side AuthGuard. Nie próbujemy server-side auth w MVP.

### P2. hydrate() race condition
Hydration (read localStorage → refresh → getMe) musi zakończyć się ZANIM
AuthGuard podejmie decyzję o redirect. `isHydrated` flag zapobiega premature redirect.

### P3. Concurrent refresh
API client ma promise deduplication (`refreshPromise` in client.ts).
Zustand `refresh()` musi delegować do API client, NIE robić osobnego fetch.
Jeden mechanizm refresh — nie dwa.

### P4. hCaptcha w dev mode
Backend: `captcha_token` jest nullable (`str | None = None`).
Dev: użyj test sitekey `10000000-ffff-ffff-ffff-000000000000` — zawsze przechodzi.
Prod: prawdziwy klucz w env.

### P5. Next.js 16 + React 19.2
- `useEffect` cleanup semantics mogą się różnić — testuj redirect logic
- `useRef` for QueryClient (nie `useState`) — unika re-creation on re-render (React 19 strict mode)

---

## Testy (DoD)

### Manual acceptance tests
1. Register → token pair stored → redirect /verify-email-sent
2. Login → token pair → /dashboard shows username + saldo
3. Refresh page → hydration → user stays logged in (refresh token works)
4. Logout → tokens cleared → redirect /login
5. Access /dashboard without login → redirect /login (AuthGuard)
6. Access /login while logged in → redirect /dashboard
7. Invalid credentials → error toast
8. Register with existing email → error toast
9. Form validation: empty fields, short password, unchecked TOS → inline errors
10. hCaptcha: widget renders, token attached to request

### Build gates
- `npm run build` — PASS (TypeScript strict, no errors)
- `npm run lint` — PASS (ESLint)

---

## Struktura plików (podsumowanie)

```
src/
  lib/
    providers.tsx           ← NEW (QueryClient + AuthHydration)
    validators/
      auth.ts               ← NEW (Zod: login, register)
  hooks/
    use-auth.ts             ← NEW (Zustand store: user, tokens, actions)
  components/
    auth/
      auth-guard.tsx        ← NEW (protected route wrapper)
      auth-skeleton.tsx     ← NEW (loading state)
  app/
    layout.tsx              ← EDIT (add Providers)
    (public)/
      layout.tsx            ← NEW (optional: redirect if logged in)
      login/page.tsx        ← NEW
      register/page.tsx     ← NEW
      verify-email-sent/page.tsx ← NEW (placeholder)
    (auth)/
      layout.tsx            ← NEW (AuthGuard wrapper)
      dashboard/page.tsx    ← NEW (placeholder)
```

---

## Kolejność implementacji (sugerowana)

1. Zależności: `npm install zustand @tanstack/react-query zod react-hook-form @hookform/resolvers @hcaptcha/react-hcaptcha`
2. `lib/validators/auth.ts` (D7) — standalone, no deps
3. `hooks/use-auth.ts` (D3) — core store + token bridge
4. `lib/providers.tsx` (D1) + edit `layout.tsx` (D2)
5. `components/auth/auth-skeleton.tsx` (D12) + `auth-guard.tsx` (D4)
6. `app/(auth)/layout.tsx` (D5) + `app/(auth)/dashboard/page.tsx` (D6)
7. `app/(public)/login/page.tsx` (D8) — test login flow E2E
8. `app/(public)/register/page.tsx` (D9) — test register flow E2E
9. `app/(public)/verify-email-sent/page.tsx` (D10) + `app/(public)/layout.tsx` (D11)
10. `.env.local.example` update (D13)
11. Build + lint gates
