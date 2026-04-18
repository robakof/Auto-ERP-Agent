# Plan: F1 Scaffold + konfiguracja + API client

Date: 2026-04-18
Status: Approved
Author: Architect
Roadmap: `documents/human/plans/serce_faza2_roadmap.md` (F1)
Zależność: Faza 1 COMPLETE (backend M1-M18 PASS)

---

## Cel

Postawić projekt frontendowy Next.js 15 z pełnym API clientem typowanym
pod backend Serce. Po F1 developer ma działający scaffold, typed fetch wrapper
z auto-refresh, typy mirrorujące Pydantic schemas i health check ze strony.

---

## Deliverables

### 1. Scaffold Next.js 15

```bash
npx create-next-app@latest serce/frontend \
  --typescript --tailwind --eslint --app --src-dir \
  --import-alias "@/*"
```

Konfiguracja:
- `next.config.ts` — rewrites proxy do backendu (dev):
  ```typescript
  async rewrites() {
    return [
      { source: '/api/:path*', destination: 'http://localhost:8000/api/:path*' }
    ];
  }
  ```
- `tsconfig.json` — strict mode, path alias `@/*` → `src/*`
- `.env.local.example`:
  ```
  NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
  ```
- `.env.local` (gitignored):
  ```
  NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
  ```

### 2. shadcn/ui init

```bash
npx shadcn@latest init
```

Bazowe components (dodać od razu — używane w F2+):
- Button, Input, Label, Card, Separator, Sonner (toast)

Tailwind config:
- Font: Inter (Google Fonts via `next/font`)
- `<html lang="pl">` w root layout

### 3. Root layout

**`src/app/layout.tsx`:**
- `<html lang="pl">`, Inter font, Tailwind globals
- `<Toaster />` (sonner) provider
- Metadata: title "Serce — platforma wzajemnej pomocy", description

**`src/app/page.tsx`:**
- Placeholder: "Serce" + health status z backendu (client-side fetch)
- Wyświetla `{ status: "ok" }` lub error message

### 4. Typed API client

**`src/lib/api/client.ts`** — fetch wrapper:

```typescript
export class ApiClient {
  private baseUrl: string;
  private accessToken: string | null = null;
  private refreshToken: string | null = null;
  private onUnauthorized: (() => void) | null = null;

  constructor(baseUrl: string) { ... }

  setTokens(access: string, refresh: string): void;
  clearTokens(): void;
  getAccessToken(): string | null;
  setOnUnauthorized(callback: () => void): void;

  async request<T>(
    method: 'GET' | 'POST' | 'PATCH' | 'DELETE',
    path: string,
    options?: {
      body?: unknown;
      params?: Record<string, string | number | boolean | undefined>;
      headers?: Record<string, string>;
      skipAuth?: boolean;
    }
  ): Promise<T>;
}
```

Logika `request()`:
1. Buduje URL z params (URLSearchParams, pomija undefined).
2. Dodaje `Authorization: Bearer <accessToken>` (chyba że `skipAuth`).
3. Fetch z `Content-Type: application/json`.
4. Jeśli 401 i jest refreshToken → wywołaj `/auth/refresh` → retry raz.
5. Jeśli refresh fail → `clearTokens()` + `onUnauthorized()`.
6. Jeśli response nie-ok → throw `ApiError` z status, detail, body.
7. Jeśli 204 → return undefined as T.
8. Return `response.json()`.

**`src/lib/api/errors.ts`:**
```typescript
export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
    public body?: unknown
  ) {
    super(detail);
  }
}
```

**`src/lib/api/index.ts`** — singleton:
```typescript
export const api = new ApiClient(
  process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'
);
```

### 5. Typy TypeScript (mirror Pydantic)

**`src/lib/api/types.ts`** — wszystkie typy response/request:

```typescript
// --- Common ---
export interface PaginatedResponse<T> {
  entries: T[];
  total: number;
  offset: number;
  limit: number;
}

// --- Auth ---
export interface TokenResponse {
  access_token: string;
  token_type: string;
  refresh_token: string;
}

export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
  tos_accepted: boolean;
  privacy_policy_accepted: boolean;
  captcha_token?: string | null;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RefreshRequest {
  refresh_token: string;
}

export interface MessageResponse {
  detail: string;
}

// --- User ---
export interface UserRead {
  id: string;
  email: string;
  username: string;
  email_verified: boolean;
  phone_verified: boolean;
  phone_number: string | null;
  bio: string | null;
  location_id: number | null;
  heart_balance: number;
  status: string;
  role: string;
  created_at: string;
}

// --- Session ---
export interface SessionRead {
  id: string;
  device_info: string | null;
  ip_address: string | null;
  created_at: string;
  expires_at: string;
}

// --- Location ---
export interface LocationRead {
  id: number;
  name: string;
  type: LocationType;
  parent_id: number | null;
}

export type LocationType = 'CITY' | 'VOIVODESHIP';

// --- Category ---
export interface CategoryRead {
  id: number;
  name: string;
  parent_id: number | null;
  icon: string | null;
  sort_order: number;
  active: boolean;
}

// --- Request ---
export type LocationScope = 'CITY' | 'VOIVODESHIP' | 'NATIONAL';
export type RequestStatus = 'ACTIVE' | 'FULFILLED' | 'CANCELLED' | 'EXPIRED';

export interface CreateRequestBody {
  title: string;
  description: string;
  hearts_offered: number;
  category_id: number;
  location_id: number;
  location_scope: LocationScope;
  expires_at?: string | null;
}

export interface UpdateRequestBody {
  title?: string;
  description?: string;
  hearts_offered?: number;
  expires_at?: string | null;
}

export interface RequestRead {
  id: string;
  user_id: string;
  title: string;
  description: string;
  hearts_offered: number;
  category_id: number;
  location_id: number;
  location_scope: string;
  status: string;
  created_at: string;
  expires_at: string | null;
  updated_at: string;
}

export type RequestListResponse = PaginatedResponse<RequestRead>;
export interface CancelResponse { id: string; status: string; }

// --- Offer ---
export type OfferStatus = 'ACTIVE' | 'PAUSED' | 'INACTIVE';

export interface CreateOfferBody {
  title: string;
  description: string;
  hearts_asked: number;
  category_id: number;
  location_id: number;
  location_scope: LocationScope;
}

export interface UpdateOfferBody {
  title?: string;
  description?: string;
  hearts_asked?: number;
}

export interface ChangeOfferStatusBody {
  status: OfferStatus;
}

export interface OfferRead {
  id: string;
  user_id: string;
  title: string;
  description: string;
  hearts_asked: number;
  category_id: number;
  location_id: number;
  location_scope: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export type OfferListResponse = PaginatedResponse<OfferRead>;

// --- Exchange ---
export type ExchangeStatus = 'PENDING' | 'ACCEPTED' | 'COMPLETED' | 'CANCELLED';

export interface CreateExchangeBody {
  request_id?: string | null;
  offer_id?: string | null;
  hearts_agreed: number;
}

export interface ExchangeRead {
  id: string;
  request_id: string | null;
  offer_id: string | null;
  requester_id: string;
  helper_id: string;
  initiated_by: string;
  hearts_agreed: number;
  status: string;
  created_at: string;
  completed_at: string | null;
}

export type ExchangeListResponse = PaginatedResponse<ExchangeRead>;

// --- Hearts ---
export interface GiftRequest {
  to_user_id: string;
  amount: number;
  note?: string | null;
}

export interface BalanceResponse {
  heart_balance: number;
  heart_balance_cap: number;
}

export interface LedgerEntryRead {
  id: string;
  from_user_id: string | null;
  to_user_id: string | null;
  amount: number;
  type: string;
  note: string | null;
  created_at: string;
}

export type LedgerResponse = PaginatedResponse<LedgerEntryRead>;

// --- Message ---
export interface SendMessageBody {
  content: string;
}

export interface MessageRead {
  id: string;
  exchange_id: string;
  sender_id: string;
  content: string;
  is_hidden: boolean;
  created_at: string;
}

export type MessageListResponse = PaginatedResponse<MessageRead>;

// --- Review ---
export interface CreateReviewBody {
  comment: string;
}

export interface ReviewRead {
  id: string;
  exchange_id: string;
  reviewer_id: string;
  reviewed_id: string;
  comment: string;
  created_at: string;
}

export type ReviewListResponse = PaginatedResponse<ReviewRead>;

// --- Notification ---
export type NotificationType =
  | 'EXCHANGE_PROPOSED'
  | 'EXCHANGE_ACCEPTED'
  | 'EXCHANGE_COMPLETED'
  | 'EXCHANGE_CANCELLED'
  | 'REVIEW_RECEIVED'
  | 'HEARTS_RECEIVED'
  | 'REQUEST_EXPIRED';

export interface NotificationRead {
  id: string;
  user_id: string;
  type: string;
  reason: string | null;
  related_exchange_id: string | null;
  related_message_id: string | null;
  is_read: boolean;
  created_at: string;
}

export type NotificationListResponse = PaginatedResponse<NotificationRead>;
export interface UnreadCountResponse { count: number; }
export interface MarkAllReadResponse { updated: number; }

// --- Flag ---
export type FlagReason = 'SPAM' | 'INAPPROPRIATE' | 'FRAUD' | 'OTHER';

export interface CreateFlagBody {
  reason: FlagReason;
  description?: string | null;
}

export interface FlagRead {
  id: string;
  reporter_id: string | null;
  target_type: string;
  target_id: string;
  reason: string;
  description: string | null;
  status: string;
  created_at: string;
}

// --- Admin ---
export type ResolutionAction = 'DISMISS' | 'WARN' | 'SUSPEND' | 'DELETE_CONTENT';

export interface FlagDetailRead extends FlagRead {
  resolved_by: string | null;
  resolved_at: string | null;
  resolution_action: string | null;
  resolution_reason: string | null;
}

export type FlagListResponse = PaginatedResponse<FlagDetailRead>;

export interface ResolveFlagBody {
  action: ResolutionAction;
  reason: string;
  params?: Record<string, unknown> | null;
}

export interface SuspendUserBody {
  reason: string;
  duration_days?: number | null;
}

export interface UserAdminRead {
  id: string;
  email: string;
  username: string;
  status: string;
  role: string;
  suspended_at: string | null;
  suspended_until: string | null;
  suspension_reason: string | null;
  heart_balance: number;
  created_at: string;
}

export interface GrantHeartsBody {
  user_id: string;
  amount: number;
  type: 'ADMIN_GRANT' | 'ADMIN_REFUND';
  reason: string;
}

export interface AuditLogRead {
  id: string;
  admin_id: string;
  action: string;
  target_type: string;
  target_id: string | null;
  payload: Record<string, unknown>;
  reason: string | null;
  created_at: string;
}

export type AuditListResponse = PaginatedResponse<AuditLogRead>;

// --- Account ---
export interface SoftDeleteBody {
  password: string;
  balance_disposition: 'void' | 'transfer';
  transfer_to_user_id?: string | null;
}

// --- User Resources ---
export interface UserSummary {
  active_requests: number;
  active_offers: number;
  pending_exchanges: number;
  completed_exchanges: number;
  heart_balance: number;
  reviews_received: number;
}

export interface PublicProfileRead {
  id: string;
  username: string | null;
  bio: string | null;
  location_id: number | null;
  heart_balance: number;
  created_at: string;
  reviews_received: number;
  completed_exchanges: number;
  is_deleted: boolean;
}

// --- Profile ---
export interface UpdateProfileRequest {
  bio?: string | null;
  location_id?: number | null;
}

export interface ChangeUsernameRequest {
  new_username: string;
}

export interface ChangeEmailRequest {
  password: string;
  new_email: string;
}

export interface ChangePasswordRequest {
  old_password: string;
  new_password: string;
}

export interface ChangePhoneRequest {
  password: string;
  new_phone_number: string;
}

// --- Verification ---
export interface VerifyEmailRequest { token: string; }
export interface ResendVerificationRequest { email: string; }
export interface SendPhoneOtpRequest { phone_number: string; }
export interface VerifyPhoneRequest { phone_number: string; code: string; }
export interface ForgotPasswordRequest { email: string; }
export interface ResetPasswordRequest { token: string; new_password: string; }
```

### 6. Typed endpoint modules

Każdy moduł eksportuje funkcje per endpoint. Poniżej spec — Developer implementuje.

**`src/lib/api/auth.ts`:**
```typescript
register(data: RegisterRequest): Promise<TokenResponse>           // POST /auth/register
login(data: LoginRequest): Promise<TokenResponse>                 // POST /auth/login
refresh(data: RefreshRequest): Promise<TokenResponse>             // POST /auth/refresh
logout(): Promise<MessageResponse>                                // POST /auth/logout
logoutAll(): Promise<MessageResponse>                             // POST /auth/logout-all
getSessions(): Promise<SessionRead[]>                             // GET /auth/sessions
revokeSession(sessionId: string): Promise<MessageResponse>        // DELETE /auth/sessions/:id
getMe(): Promise<UserRead>                                        // GET /auth/me
verifyEmail(data: VerifyEmailRequest): Promise<MessageResponse>   // POST /auth/verify-email
resendVerification(data: ResendVerificationRequest): Promise<MessageResponse>
sendPhoneOtp(data: SendPhoneOtpRequest): Promise<MessageResponse>
verifyPhone(data: VerifyPhoneRequest): Promise<MessageResponse>
forgotPassword(data: ForgotPasswordRequest): Promise<MessageResponse>
resetPassword(data: ResetPasswordRequest): Promise<MessageResponse>
```

**`src/lib/api/requests.ts`:**
```typescript
create(data: CreateRequestBody): Promise<RequestRead>
get(id: string): Promise<RequestRead>
update(id: string, data: UpdateRequestBody): Promise<RequestRead>
list(params?: { category_id?, location_id?, location_scope?, status?, q?, sort?, order?, offset?, limit? }): Promise<RequestListResponse>
cancel(id: string): Promise<CancelResponse>
```

**`src/lib/api/offers.ts`:**
```typescript
create(data: CreateOfferBody): Promise<OfferRead>
get(id: string): Promise<OfferRead>
update(id: string, data: UpdateOfferBody): Promise<OfferRead>
changeStatus(id: string, data: ChangeOfferStatusBody): Promise<OfferRead>
list(params?: { category_id?, location_id?, location_scope?, status?, q?, sort?, order?, offset?, limit? }): Promise<OfferListResponse>
```

**`src/lib/api/exchanges.ts`:**
```typescript
create(data: CreateExchangeBody): Promise<ExchangeRead>
get(id: string): Promise<ExchangeRead>
accept(id: string): Promise<ExchangeRead>
complete(id: string): Promise<ExchangeRead>
cancel(id: string): Promise<ExchangeRead>
list(params?: { role?, status?, offset?, limit? }): Promise<ExchangeListResponse>
```

**`src/lib/api/messages.ts`:**
```typescript
send(exchangeId: string, data: SendMessageBody): Promise<MessageRead>
list(exchangeId: string, params?: { offset?, limit? }): Promise<MessageListResponse>
hide(exchangeId: string, messageId: string): Promise<MessageRead>
```

**`src/lib/api/hearts.ts`:**
```typescript
gift(data: GiftRequest): Promise<LedgerEntryRead>
getBalance(): Promise<BalanceResponse>
getLedger(params?: { type?, offset?, limit? }): Promise<LedgerResponse>
```

**`src/lib/api/reviews.ts`:**
```typescript
create(exchangeId: string, data: CreateReviewBody): Promise<ReviewRead>
listByExchange(exchangeId: string): Promise<ReviewRead[]>
listByUser(userId: string, params?: { offset?, limit? }): Promise<ReviewListResponse>
```

**`src/lib/api/notifications.ts`:**
```typescript
list(params?: { unread?, offset?, limit? }): Promise<NotificationListResponse>
markRead(id: string): Promise<NotificationRead>
markAllRead(): Promise<MarkAllReadResponse>
getUnreadCount(): Promise<UnreadCountResponse>
```

**`src/lib/api/flags.ts`:**
```typescript
flagRequest(targetId: string, data: CreateFlagBody): Promise<FlagRead>
flagOffer(targetId: string, data: CreateFlagBody): Promise<FlagRead>
flagExchange(targetId: string, data: CreateFlagBody): Promise<FlagRead>
flagUser(targetId: string, data: CreateFlagBody): Promise<FlagRead>
```

**`src/lib/api/admin.ts`:**
```typescript
listFlags(params?: { status?, target_type?, offset?, limit? }): Promise<FlagListResponse>
getFlag(id: string): Promise<FlagDetailRead>
resolveFlag(id: string, data: ResolveFlagBody): Promise<FlagDetailRead>
suspendUser(userId: string, data: SuspendUserBody): Promise<UserAdminRead>
unsuspendUser(userId: string): Promise<UserAdminRead>
grantHearts(data: GrantHeartsBody): Promise<LedgerEntryRead>
getAuditLog(params?: { actor_id?, action?, target_type?, from_date?, to_date?, offset?, limit? }): Promise<AuditListResponse>
```

**`src/lib/api/users.ts`:**
```typescript
getMe(): Promise<UserRead>
updateProfile(data: UpdateProfileRequest): Promise<UserRead>
changeUsername(data: ChangeUsernameRequest): Promise<MessageResponse>
changeEmail(data: ChangeEmailRequest): Promise<MessageResponse>
confirmEmailChange(data: { token: string }): Promise<MessageResponse>
changePhone(data: ChangePhoneRequest): Promise<MessageResponse>
verifyPhoneChange(data: { new_phone_number: string; code: string }): Promise<MessageResponse>
changePassword(data: ChangePasswordRequest): Promise<MessageResponse>
deleteAccount(data: SoftDeleteBody): Promise<MessageResponse>
```

**`src/lib/api/user-resources.ts`:**
```typescript
myRequests(params?: { status?, offset?, limit? }): Promise<RequestListResponse>
myOffers(params?: { status?, offset?, limit? }): Promise<OfferListResponse>
myExchanges(params?: { role?, status?, offset?, limit? }): Promise<ExchangeListResponse>
myReviews(params?: { type?, offset?, limit? }): Promise<ReviewListResponse>
myLedger(params?: { type?, offset?, limit? }): Promise<LedgerResponse>
mySummary(): Promise<UserSummary>
getPublicProfile(userId: string): Promise<PublicProfileRead>
```

**`src/lib/api/locations.ts`:**
```typescript
list(params?: { type?: LocationType }): Promise<LocationRead[]>
```

**`src/lib/api/categories.ts`:**
```typescript
list(params?: { active?: boolean }): Promise<CategoryRead[]>
```

### 7. docker-compose.yml update

Dodaj frontend service do istniejącego `serce/docker-compose.yml`:

```yaml
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000/api/v1
    depends_on:
      - backend
    volumes:
      - ./frontend/src:/app/src
    restart: unless-stopped
```

### 8. Frontend Dockerfile

**`serce/frontend/Dockerfile`:**

```dockerfile
FROM node:20-alpine

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .

EXPOSE 3000
CMD ["npm", "run", "dev"]
```

Produkcyjny multi-stage build — osobne zadanie (F11 lub deploy).

### 9. .gitignore

Standardowy Next.js .gitignore + `.env.local`.

---

## Struktura plików po F1

```
serce/frontend/
  src/
    app/
      layout.tsx          # Root layout (Inter, pl, Toaster)
      page.tsx             # Health check placeholder
      globals.css          # Tailwind directives
    lib/
      api/
        client.ts          # ApiClient class
        errors.ts          # ApiError
        index.ts           # Singleton export
        types.ts           # All TypeScript types
        auth.ts            # Auth endpoints
        requests.ts        # Request endpoints
        offers.ts          # Offer endpoints
        exchanges.ts       # Exchange endpoints
        messages.ts        # Message endpoints
        hearts.ts          # Hearts endpoints
        reviews.ts         # Review endpoints
        notifications.ts   # Notification endpoints
        flags.ts           # Flag endpoints
        admin.ts           # Admin endpoints
        users.ts           # Profile/settings endpoints
        user-resources.ts  # User resources endpoints
        locations.ts       # Locations (public)
        categories.ts      # Categories (public)
    components/
      ui/                  # shadcn/ui (Button, Input, Card, Label, Separator)
  public/
    favicon.ico
  .env.local.example
  .gitignore
  Dockerfile
  next.config.ts
  tailwind.config.ts
  tsconfig.json
  package.json
  components.json          # shadcn config
```

---

## NIE w scope F1

- Zustand store (F2 — auth)
- TanStack Query hooks (F4+)
- Zod validators (F2+)
- Żadne strony poza root placeholder
- Żadne components poza shadcn/ui bazowe
- Testy (brak logiki do testowania)

---

## DoD

1. `npm run dev` startuje bez błędów.
2. Strona wyświetla "Serce" + health status z backendu (`GET /api/v1/health` → `{ status: "ok" }`).
3. `npm run build` przechodzi (zero TS errors).
4. Wszystkie endpoint modules kompilują się (import types, export functions).
5. docker-compose z frontendem startuje i łączy się z backendem.
6. `.env.local.example` istnieje z `NEXT_PUBLIC_API_URL`.

---

## Referencje

- Backend schemas: `serce/backend/app/schemas/*.py`
- Backend routers: `serce/backend/app/api/*.py`
- Backend config: `serce/backend/app/config.py`
- Docker compose: `serce/docker-compose.yml`
- Roadmap F1: `documents/human/plans/serce_faza2_roadmap.md` (sekcja F1)
