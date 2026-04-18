/* API response types — mirror of backend Pydantic schemas. */

// ---- Primitives -------------------------------------------------------------

/** Paginated response wrapper used by all list endpoints. */
export interface PaginatedResponse<T> {
  entries: T[];
  total: number;
  offset: number;
  limit: number;
}

// ---- Auth -------------------------------------------------------------------

export interface TokenResponse {
  access_token: string;
  token_type: string;
  refresh_token: string;
}

export interface MessageResponse {
  detail: string;
}

// ---- User -------------------------------------------------------------------

export type UserStatus = "active" | "suspended" | "deleted";
export type UserRole = "user" | "admin";

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
  status: UserStatus;
  role: UserRole;
  created_at: string;
}

// ---- Category & Location ----------------------------------------------------

export interface CategoryRead {
  id: number;
  name: string;
  parent_id: number | null;
  icon: string | null;
  sort_order: number;
  active: boolean;
}

export type LocationType = "VOIVODESHIP" | "CITY";

export interface LocationRead {
  id: number;
  name: string;
  type: LocationType;
  parent_id: number | null;
}

// ---- Request ----------------------------------------------------------------

export type RequestStatus = "OPEN" | "IN_PROGRESS" | "DONE" | "CANCELLED" | "HIDDEN";
export type LocationScope = "CITY" | "VOIVODESHIP" | "NATIONAL";

export interface RequestRead {
  id: string;
  user_id: string;
  title: string;
  description: string;
  hearts_offered: number;
  category_id: number;
  location_id: number;
  location_scope: LocationScope;
  status: RequestStatus;
  created_at: string;
  expires_at: string | null;
  updated_at: string;
}

// ---- Offer ------------------------------------------------------------------

export type OfferStatus = "ACTIVE" | "PAUSED" | "INACTIVE" | "HIDDEN";

export interface OfferRead {
  id: string;
  user_id: string;
  title: string;
  description: string;
  hearts_asked: number;
  category_id: number;
  location_id: number;
  location_scope: LocationScope;
  status: OfferStatus;
  created_at: string;
  updated_at: string;
}

// ---- Exchange ---------------------------------------------------------------

export type ExchangeStatus = "PENDING" | "ACCEPTED" | "COMPLETED" | "CANCELLED";

export interface ExchangeRead {
  id: string;
  request_id: string | null;
  offer_id: string | null;
  requester_id: string;
  helper_id: string;
  initiated_by: string;
  hearts_agreed: number;
  status: ExchangeStatus;
  created_at: string;
  completed_at: string | null;
}

// ---- Message ----------------------------------------------------------------

export interface MessageRead {
  id: string;
  exchange_id: string;
  sender_id: string;
  content: string;
  is_hidden: boolean;
  created_at: string;
}

// ---- Review -----------------------------------------------------------------

export interface ReviewRead {
  id: string;
  exchange_id: string;
  reviewer_id: string;
  reviewed_id: string;
  comment: string;
  created_at: string;
}

// ---- Notification -----------------------------------------------------------

export type NotificationType =
  | "NEW_EXCHANGE"
  | "EXCHANGE_ACCEPTED"
  | "EXCHANGE_COMPLETED"
  | "EXCHANGE_CANCELLED"
  | "NEW_MESSAGE"
  | "NEW_REVIEW"
  | "HEARTS_RECEIVED"
  | "REQUEST_EXPIRED";

export interface NotificationRead {
  id: string;
  user_id: string;
  type: NotificationType;
  reason: string | null;
  related_exchange_id: string | null;
  related_message_id: string | null;
  is_read: boolean;
  created_at: string;
}

export interface UnreadCountResponse {
  count: number;
}

// ---- Hearts -----------------------------------------------------------------

export interface BalanceResponse {
  heart_balance: number;
  heart_balance_cap: number;
}

export type LedgerType =
  | "GIFT"
  | "PAYMENT"
  | "INITIAL_GRANT"
  | "ADMIN_GRANT"
  | "ADMIN_REFUND"
  | "ACCOUNT_DELETED";

export interface LedgerEntryRead {
  id: string;
  from_user_id: string | null;
  to_user_id: string | null;
  amount: number;
  type: LedgerType;
  note: string | null;
  created_at: string;
}

// ---- Flag -------------------------------------------------------------------

export type FlagReason = "spam" | "scam" | "abuse" | "inappropriate" | "other";
export type FlagStatus = "open" | "resolved" | "dismissed";

export interface FlagRead {
  id: string;
  reporter_id: string | null;
  target_type: string;
  target_id: string;
  reason: string;
  description: string | null;
  status: FlagStatus;
  created_at: string;
}

// ---- User Resources ---------------------------------------------------------

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

// ---- Session ----------------------------------------------------------------

export interface SessionRead {
  id: string;
  device_info: string | null;
  ip_address: string | null;
  created_at: string;
  expires_at: string;
}
