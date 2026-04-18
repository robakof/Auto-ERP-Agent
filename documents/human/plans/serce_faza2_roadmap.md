# Serce — Faza 2 roadmapa implementacyjna (Frontend web)

Date: 2026-04-18
Status: Approved
Author: Architect
Podstawa: `documents/human/plans/serce_architecture.md` (v16, sekcja Faza 2)
Zależność: Faza 1 COMPLETE (backend M1-M18 PASS)

---

## Cel

Rozpisanie Fazy 2 (Frontend web — Next.js) na milestone'y z jasnymi deliverables
i definicją ukończenia. Każdy milestone jest commitowalny niezależnie.

---

## Decyzje architektoniczne

### D1. Stack frontendowy

| Warstwa | Wybór | Uzasadnienie |
|---|---|---|
| Framework | **Next.js 15 (App Router)** | SSR/SSG dla SEO (feed publiczny), React Server Components, streaming |
| Język | **TypeScript (strict)** | Typowana integracja z backend Pydantic schemas |
| Styling | **Tailwind CSS 4 + shadcn/ui** | Szybki DX, accessible components (Radix pod spodem), customizable |
| Formulare | **React Hook Form + Zod** | Zod mirrors Pydantic validation; RHF — lekki, performant |
| State | **Zustand** (client state) + **TanStack Query** (server state) | Zustand prostszy od Redux; TanStack Query = cache, refetch, optimistic updates |
| API client | **Typed fetch wrapper** (`lib/api/`) | Współdzielony z React Native (Faza 3); nie axios (brak potrzeby) |
| Auth storage | **Access token: in-memory** (Zustand), **Refresh token: localStorage** | Pragmatyczne MVP; httpOnly cookie = osobna iteracja (wymaga zmian backend) |
| Icons | **Lucide React** | Spójne z shadcn/ui, tree-shakeable |
| Toasts/feedback | **sonner** | Lekki, integracja z shadcn/ui |

**Trade-off: localStorage dla refresh token.**
Idealnie: httpOnly cookie (odporny na XSS). Backend zwraca refresh token w JSON body —
zmiana na cookie wymaga modyfikacji endpointu. Na MVP localStorage + krótki TTL access
tokena (15 min) + refresh rotation (single-use). Backlog na Fazę 3: migracja na httpOnly.

### D2. Struktura katalogów

```
serce/frontend/
  src/
    app/                    # Next.js App Router (pages + layouts)
      (public)/             # Route group: strony bez auth
        page.tsx            # Landing / feed
        login/page.tsx
        register/page.tsx
        verify-email/page.tsx
        reset-password/page.tsx
      (auth)/               # Route group: strony wymagające auth
        dashboard/page.tsx
        requests/
          page.tsx          # Moje prośby
          new/page.tsx      # Nowa prośba
          [id]/page.tsx     # Szczegóły
        offers/
          page.tsx
          new/page.tsx
          [id]/page.tsx
        exchanges/
          page.tsx
          [id]/page.tsx     # Szczegóły + wiadomości
        hearts/page.tsx     # Saldo + ledger
        settings/page.tsx   # Profil, zmiana email/phone/password
        notifications/page.tsx
      layout.tsx            # Root layout (providers, header, footer)
    components/
      ui/                   # shadcn/ui (Button, Input, Card, Dialog, ...)
      layout/               # Header, Footer, Sidebar, MobileNav
      forms/                # Reusable form components (AuthForm, RequestForm)
      feed/                 # RequestCard, OfferCard, FeedFilters
      exchange/             # ExchangeCard, StatusBadge, MessageBubble
    hooks/
      use-auth.ts           # Auth context (login, logout, refresh, user)
      use-api.ts            # TanStack Query wrappers per resource
    lib/
      api/                  # Typed API client (współdzielony z mobile)
        client.ts           # Fetch wrapper z auto-refresh
        types.ts            # Request/response types (mirror Pydantic)
        auth.ts             # Auth endpoints
        requests.ts         # Request endpoints
        offers.ts           # Offer endpoints
        exchanges.ts        # Exchange endpoints
        hearts.ts           # Hearts endpoints
        notifications.ts    # Notification endpoints
        users.ts            # Profile, user resources
      validators/           # Zod schemas (mirror backend validation)
    styles/
      globals.css           # Tailwind directives
  public/
    favicon.ico
    logo.svg
  tailwind.config.ts
  next.config.ts
  tsconfig.json
  package.json
  Dockerfile
```

### D3. API client — kontrakt

```typescript
// lib/api/client.ts
class ApiClient {
  private accessToken: string | null;

  async request<T>(method, path, options?): Promise<T>;
  // Auto-refresh: 401 → refresh token → retry original request
  // Retry once, then redirect to /login

  setAccessToken(token: string): void;
  clearTokens(): void;
}
```

Każdy moduł (`auth.ts`, `requests.ts`, ...) eksportuje typed functions:
```typescript
// lib/api/requests.ts
export const listRequests = (params: ListRequestsParams) => api.request<PaginatedResponse<Request>>('GET', '/requests', { params });
export const createRequest = (data: CreateRequestData) => api.request<Request>('POST', '/requests', { body: data });
```

### D4. Auth flow (frontend)

```
Register → token pair → store → redirect /verify-email-sent
Login → token pair → store → redirect /dashboard
401 on any request → auto-refresh → retry
Refresh fail → clear tokens → redirect /login
Logout → POST /auth/logout → clear tokens → redirect /
```

### D5. SEO — publiczny feed

Feed (prośby + oferty) jest publiczny i powinien być indeksowany:
- Server Component — dane pobierane server-side (no client fetch)
- `<title>`, `<meta description>` per strona
- `sitemap.xml` + `robots.txt`
- Structured data (JSON-LD) — opcjonalne, nice-to-have

### D6. Responsive design

Mobile-first approach. Breakpoints Tailwind:
- `sm` (640px) — mobile landscape
- `md` (768px) — tablet
- `lg` (1024px) — desktop

Brak osobnej aplikacji mobilnej w Fazie 2 — web musi być w pełni użyteczny na telefonie.

---

## Milestone'y Fazy 2

### F1. Scaffold + konfiguracja + API client
**Wejście:** Backend działa (docker-compose).
**Deliverables:**
- `npx create-next-app@latest` z TypeScript, Tailwind, App Router, ESLint.
- Tailwind config + shadcn/ui init (`npx shadcn@latest init`).
- Bazowe components shadcn: Button, Input, Card, Label, Separator.
- `lib/api/client.ts` — typed fetch wrapper z auto-refresh logic.
- `lib/api/types.ts` — typy request/response (mirror `app/schemas/*.py`).
- `docker-compose.yml` update: frontend service (dev: `npm run dev`, prod: multi-stage build).
- Root layout: `<html lang="pl">`, font (Inter), Tailwind globals.
- Health check: frontend łączy się z `GET /api/v1/health` i wyświetla status.
- `.env.local.example` z `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1`.
**DoD:** `npm run dev` startuje, strona wyświetla "Serce" + health status z backendu.
**Rozmiar:** M.

### F2. Auth — login + register + token management
**Wejście:** F1.
**Deliverables:**
- `hooks/use-auth.ts` — Zustand store: `user`, `accessToken`, `login()`, `logout()`, `register()`, `refresh()`.
- `lib/api/auth.ts` — typed auth endpoints (register, login, refresh, logout).
- `/login` page — email + password form, error handling, redirect to dashboard.
- `/register` page — email + username + password + TOS/privacy checkboxes + hCaptcha widget.
- `lib/validators/auth.ts` — Zod schemas (mirror backend: email, password min 8, username min 3).
- Auto-refresh middleware: intercept 401 → refresh → retry → fail = redirect /login.
- Zustand persist: refresh token → localStorage (access token: memory only).
- Protected route wrapper: redirect to /login if no token.
**DoD:** Register → login → dashboard (placeholder) → logout → redirect /login. Token refresh działa.
**Rozmiar:** L. **Ryzyko:** wysokie (fundament auth).

### F3. Layout + nawigacja + landing page
**Wejście:** F2.
**Deliverables:**
- `components/layout/Header.tsx` — logo, nawigacja (Feed, Moje prośby, Moje oferty, Serca, Profil), user menu (settings, logout), unread notification badge.
- `components/layout/MobileNav.tsx` — bottom navigation (mobile), hamburger menu.
- `components/layout/Footer.tsx` — linki, copyright.
- Landing page (`/`) — hero section, CTA (zarejestruj się / przeglądaj oferty), krótki opis jak działa.
- Responsive: mobile-first, header collapses to hamburger.
**DoD:** Nawigacja działa, responsywna, linki prowadzą do placeholder stron.
**Rozmiar:** M.

### F4. Feed — przeglądanie próśb i ofert
**Wejście:** F3.
**Deliverables:**
- `/` lub `/feed` — lista próśb + ofert (tabbed: "Prośby" / "Oferty").
- `components/feed/RequestCard.tsx` — tytuł, opis (truncated), serca, lokalizacja, kategoria, data.
- `components/feed/OfferCard.tsx` — analogicznie.
- `components/feed/FeedFilters.tsx` — kategoria (select), lokalizacja (select), scope (CITY/VOIVODESHIP/NATIONAL), search (text input).
- Paginacja (infinite scroll lub numbered pages — decyzja implementacyjna).
- `lib/api/requests.ts`, `lib/api/offers.ts` — typed endpoints.
- TanStack Query: `useRequests(filters)`, `useOffers(filters)`.
- Server-side initial data (SSR) dla SEO — client hydration z TanStack Query.
- Szczegóły prośby: `/requests/[id]` — pełny opis, owner info (username, reviews count), przycisk "Zaproponuj pomoc".
- Szczegóły oferty: `/offers/[id]` — analogicznie, przycisk "Poproś o pomoc".
**DoD:** Feed wyświetla dane z backendu, filtry działają, detail pages wyświetlają pełne informacje.
**Rozmiar:** L.

### F5. Request & Offer CRUD (zalogowany)
**Wejście:** F4, F2.
**Deliverables:**
- `/requests/new` — formularz tworzenia prośby (title, description, hearts_offered, category, location, scope, expires_at).
- `/offers/new` — formularz tworzenia oferty (title, description, hearts_asked, category, location, scope).
- Edycja prośby/oferty (inline lub osobna strona).
- Cancel prośby (przycisk + potwierdzenie).
- Zmiana statusu oferty (ACTIVE ↔ PAUSED, → INACTIVE).
- "Moje prośby" (`/requests`) — lista z filtrami status.
- "Moje oferty" (`/offers`) — lista z filtrami status.
- Zod validation na formularzach (client-side, mirror backend).
- Toast feedback (sukces/error) via sonner.
**DoD:** User może stworzyć, edytować, anulować prośbę; stworzyć, edytować, pauzować ofertę.
**Rozmiar:** M.

### F6. Exchange flow
**Wejście:** F4 (detail pages), F2 (auth).
**Deliverables:**
- Tworzenie Exchange z detail page prośby ("Zaproponuj pomoc") lub oferty ("Poproś o pomoc").
- `/exchanges` — lista moich wymian (filtr: role, status).
- `/exchanges/[id]` — szczegóły wymiany:
  - Status badge (PENDING / ACCEPTED / COMPLETED / CANCELLED).
  - Informacje: prośba/oferta, uczestnicy, serca.
  - Akcje kontekstowe:
    - PENDING: Accept (non-initiator) / Cancel.
    - ACCEPTED: Complete (requester) / Cancel.
    - COMPLETED: Write review.
  - Potwierdzenie modalne przed akcjami (accept, complete, cancel).
- Escrow info: "X serc zostanie zablokowanych" przy accept.
- Hearts transfer info: "X serc trafi do helpera" przy complete.
- Error handling: INSUFFICIENT_BALANCE, CAP_EXCEEDED → czytelny komunikat.
**DoD:** Pełny flow PENDING → ACCEPTED → COMPLETED działa z UI. Cancel z refundem widoczny w saldzie.
**Rozmiar:** L. **Ryzyko:** wysokie — rdzeń UX.

### F7. Wiadomości w Exchange
**Wejście:** F6.
**Deliverables:**
- Chat w `/exchanges/[id]` — sekcja wiadomości pod szczegółami.
- `components/exchange/MessageBubble.tsx` — wiadomość (sender, content, timestamp), alignment L/R.
- Formularz wysyłania (textarea + send button).
- Paginacja (starsze wiadomości — "Załaduj wcześniejsze").
- Polling co 15s dla nowych wiadomości (TanStack Query `refetchInterval`).
- Wiadomości dostępne we wszystkich statusach Exchange (PENDING, ACCEPTED, COMPLETED).
**DoD:** Dwóch uczestników może wymieniać wiadomości w exchange, nowe pojawiają się po krótkim czasie.
**Rozmiar:** S-M.

### F8. Dashboard + serca + powiadomienia
**Wejście:** F2 (auth), F5, F6.
**Deliverables:**
- `/dashboard` — summary: saldo serc, aktywne prośby/oferty, pending exchanges, ostatnie powiadomienia.
- `/hearts` — saldo + ledger (historia transakcji), filtr po typie, paginacja.
- Gift hearts: formularz (username/id, kwota, notatka), walidacja cap.
- `/notifications` — lista powiadomień (unread bold), mark as read, mark all read.
- Notification badge w header (unread count, polling co 60s).
- `/settings/sessions` — lista aktywnych sesji, revoke (z guardem current session).
**DoD:** Dashboard pokazuje podsumowanie, serca + ledger + gift działają, powiadomienia wyświetlane i mark-read.
**Rozmiar:** L.

### F9. Profil + ustawienia + reviews
**Wejście:** F2 (auth), F6 (exchange).
**Deliverables:**
- `/settings` — edycja profilu (bio, lokalizacja), zmiana username.
- Zmiana email (hasło → token → potwierdzenie nowy email).
- Zmiana telefonu (hasło → OTP → potwierdzenie).
- Zmiana hasła (stare + nowe).
- Email/phone verification status (badge ✓ / ✗).
- Usunięcie konta (`DELETE /users/me`) — modal z dyspozycją salda (void / transfer), potwierdzenie hasłem.
- `/users/[id]/profile` — publiczny profil (username, bio, reviews, completed exchanges, saldo).
- Reviews sekcja na profilu publicznym: lista opinii (received).
- Tworzenie review po COMPLETED exchange (formularz na `/exchanges/[id]`).
**DoD:** User może edytować profil, zmienić email/phone/password, usunąć konto. Publiczny profil wyświetla reviews.
**Rozmiar:** M-L.

### F10. Email/phone verification pages + password reset
**Wejście:** F2.
**Deliverables:**
- `/verify-email?token=X` — landing page po kliknięciu linka, POST verify-email, sukces/error feedback.
- `/verify-email-sent` — informacja "sprawdź email", przycisk resend.
- Phone verification — w settings (po zalogowaniu), OTP input (6 cyfr), auto-submit.
- `/forgot-password` — formularz email, POST forgot-password, feedback.
- `/reset-password?token=X` — formularz nowego hasła, POST reset-password, redirect /login.
**DoD:** Pełny flow: register → verify email → verify phone → INITIAL_GRANT. Password reset E2E.
**Rozmiar:** M.

### F11. Polish — responsive, SEO, a11y, error states
**Wejście:** F1-F10.
**Deliverables:**
- Responsive audit: każda strona testowana na 375px (mobile), 768px (tablet), 1024px+ (desktop).
- SEO: `<title>`, `<meta description>` per strona, `sitemap.xml`, `robots.txt`.
- Error pages: 404, 500 (custom Next.js error pages).
- Loading states: Skeleton components na feed, exchange list, notifications.
- Empty states: "Brak próśb", "Brak powiadomień" — z CTA.
- Toast consistency: success (zielony), error (czerwony), info (niebieski).
- Accessibility: keyboard navigation, focus ring, aria labels na interactive elements.
- `<html lang="pl">` + polskie tłumaczenia (hardcoded — brak i18n w v1).
**DoD:** Wszystkie strony responsywne, SEO meta tags, loading/empty/error states.
**Rozmiar:** M.

---

### F12. Admin panel
**Wejście:** F2 (auth), F3 (layout).
**Deliverables:**
- `(auth)/admin/` — route group z admin guard (`is_admin` check).
- Admin layout: sidebar (Flags, Users, Audit), odrębny od user layout.
- `/admin/flags` — lista flag (status filter: PENDING/RESOLVED), resolve action (dismiss/action + reason), link do flagowanego zasobu.
- `/admin/users` — lista userów (search by username/email), suspend/unsuspend toggle, grant hearts dialog (amount + reason).
- `/admin/audit` — audit log z filtrami (action type, target user, date range), paginacja.
- TanStack Query hooks: `useFlags()`, `useUsers()`, `useAuditLog()`.
- `lib/api/admin.ts` — typed admin endpoints (mirror backend M15 API).
- Confirmation modals: suspend, grant hearts.
**DoD:** Admin może przeglądać flagi, resolveować, suspend/unsuspend userów, grantować serca, przeglądać audit log.
**Rozmiar:** M.

---

## Graf zależności

```
F1 ──── F2 ──┬── F3 ──── F4 ──┬── F5
             │                 │
             ├── F10           ├── F6 ──── F7
             │                 │
             ├── F12           └── F8 ◄── F5, F6
             │                 
             └─────────────────┬── F9 ◄── F6
                                    
F11 ◄── all (F1-F10, F12)
```

**Ścieżka krytyczna:** F1 → F2 → F3 → F4 → F6 → F7 → F11.

---

## Równoległe pasma (≥2 Developerów)

- Pasmo A (core): F1 → F2 → F3 → F4 → F6 → F7
- Pasmo B (forms): F5 (po F4), F9 (po F6)
- Pasmo C (infra): F10 (po F2), F8 (po F2+F5+F6), F12 (po F2+F3)
- Pasmo D (polish): F11 (po wszystkich)

Przy jednym Developerze: F1 → F2 → F10 → F3 → F4 → F5 → F6 → F7 → F8 → F9 → F12 → F11.

---

## Otwarte pytania (do potwierdzenia z userem)

| # | Pytanie | Propozycja Architekta | Status |
|---|---|---|---|
| F-1 | Next.js 15 czy 14? | **15** (stable, App Router dojrzały) | ✓ Potwierdzone |
| F-2 | Paginacja feed: infinite scroll czy numbered? | **Numbered** (prostsze, lepsze SEO) | ✓ Potwierdzone |
| F-3 | Polling wiadomości (15s) czy WebSocket? | **Polling** (MVP), WebSocket Faza 3+ | ✓ Potwierdzone |
| F-4 | Domena? (potrzebna do deploy i SSL) | **msps.pl** | ✓ Potwierdzone |
| F-5 | Landing page — jakie treści? | **Hero + "jak to działa" (3 kroki) + CTA** | ✓ Potwierdzone |
| F-6 | Dark mode? | **Nie** w MVP (Tailwind ready, łatwe później) | ✓ Potwierdzone |
| F-7 | Admin panel w Fazie 2 czy Fazie 4? | **Faza 2** (milestone F12) | ✓ Potwierdzone |

---

## Konwencje

- **Commit granularity:** jeden milestone = seria spójnych commitów.
- **Review gate:** po każdym milestone handoff do Architekta → code review → PASS.
- **Tests:** Playwright E2E per milestone (happy path). Unit testy komponentów opcjonalne w MVP.
- **Linting:** ESLint + Prettier (Next.js defaults).
- **Naming:** PascalCase components, camelCase functions/hooks, kebab-case files.

---

## Rozmiar Fazy 2

12 milestone'ów. Szacunkowa proporcja do Fazy 1:
- Faza 1: 18 M, ~2 tygodnie
- Faza 2: 12 M, ~1.5-2 tygodnie (UI pracy więcej per milestone, ale mniej logiki)
