import { api } from "./client";
import type {
  RequestListResponse,
  OfferListResponse,
  ExchangeListResponse,
  ReviewListResponse,
  LedgerResponse,
  UserSummary,
  PublicProfileRead,
} from "./types";

export const userResources = {
  myRequests: (params?: Record<string, string | number | boolean | undefined>) =>
    api.get<RequestListResponse>("/users/me/requests", params),

  myOffers: (params?: Record<string, string | number | boolean | undefined>) =>
    api.get<OfferListResponse>("/users/me/offers", params),

  myExchanges: (params?: Record<string, string | number | boolean | undefined>) =>
    api.get<ExchangeListResponse>("/users/me/exchanges", params),

  myReviews: (params?: Record<string, string | number | boolean | undefined>) =>
    api.get<ReviewListResponse>("/users/me/reviews", params),

  myLedger: (params?: Record<string, string | number | boolean | undefined>) =>
    api.get<LedgerResponse>("/users/me/ledger", params),

  mySummary: () =>
    api.get<UserSummary>("/users/me/summary"),

  getPublicProfile: (userId: string) =>
    api.get<PublicProfileRead>(`/users/${userId}/profile`),
};
