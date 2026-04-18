/* API types — mirror of backend Pydantic schemas (response + request). */

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

// ---- Session ----------------------------------------------------------------

export interface SessionRead {
  id: string;
  device_info: string | null;
  ip_address: string | null;
  created_at: string;
  expires_at: string;
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
  location_scope: LocationScope;
  status: RequestStatus;
  created_at: string;
  expires_at: string | null;
  updated_at: string;
}

export type RequestListResponse = PaginatedResponse<RequestRead>;
export interface CancelResponse { id: string; status: string; }

// ---- Offer ------------------------------------------------------------------

export type OfferStatus = "ACTIVE" | "PAUSED" | "INACTIVE" | "HIDDEN";

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
  location_scope: LocationScope;
  status: OfferStatus;
  created_at: string;
  updated_at: string;
}

export type OfferListResponse = PaginatedResponse<OfferRead>;

// ---- Exchange ---------------------------------------------------------------

export type ExchangeStatus = "PENDING" | "ACCEPTED" | "COMPLETED" | "CANCELLED";

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
  status: ExchangeStatus;
  created_at: string;
  completed_at: string | null;
}

export type ExchangeListResponse = PaginatedResponse<ExchangeRead>;

// ---- Message ----------------------------------------------------------------

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

// ---- Review -----------------------------------------------------------------

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

export type NotificationListResponse = PaginatedResponse<NotificationRead>;
export interface UnreadCountResponse { count: number; }
export interface MarkAllReadResponse { updated: number; }

// ---- Hearts -----------------------------------------------------------------

export interface GiftRequest {
  to_user_id: string;
  amount: number;
  note?: string | null;
}

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
  | "ACCOUNT_DELETED"
  | "EXCHANGE_ESCROW"
  | "EXCHANGE_COMPLETE"
  | "EXCHANGE_REFUND";

export interface LedgerEntryRead {
  id: string;
  from_user_id: string | null;
  to_user_id: string | null;
  amount: number;
  type: LedgerType;
  note: string | null;
  created_at: string;
}

export type LedgerResponse = PaginatedResponse<LedgerEntryRead>;

// ---- Flag -------------------------------------------------------------------

export type FlagReason = "spam" | "scam" | "abuse" | "inappropriate" | "other";
export type FlagStatus = "open" | "resolved" | "dismissed";

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
  status: FlagStatus;
  created_at: string;
}

// ---- Admin ------------------------------------------------------------------

export type ResolutionAction =
  | "dismiss"
  | "warn_user"
  | "hide_content"
  | "suspend_user"
  | "ban_user"
  | "grant_hearts_refund";

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
  type: "ADMIN_GRANT" | "ADMIN_REFUND";
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

// ---- Account ----------------------------------------------------------------

export interface SoftDeleteBody {
  password: string;
  balance_disposition: "void" | "transfer";
  transfer_to_user_id?: string | null;
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

// ---- Profile ----------------------------------------------------------------

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

// ---- Verification -----------------------------------------------------------

export interface VerifyEmailRequest { token: string; }
export interface ResendVerificationRequest { email: string; }
export interface SendPhoneOtpRequest { phone_number: string; }
export interface VerifyPhoneRequest { phone_number: string; code: string; }
export interface ForgotPasswordRequest { email: string; }
export interface ResetPasswordRequest { token: string; new_password: string; }
