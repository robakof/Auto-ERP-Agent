import { api } from "./client";
import type {
  CreateReviewBody,
  ReviewRead,
  ReviewListResponse,
} from "./types";

export const reviews = {
  create: (exchangeId: string, data: CreateReviewBody) =>
    api.post<ReviewRead>(`/exchanges/${exchangeId}/reviews`, data),

  listByExchange: (exchangeId: string) =>
    api.get<ReviewRead[]>(`/exchanges/${exchangeId}/reviews`),

  listByUser: (userId: string, params?: Record<string, string | number | boolean | undefined>) =>
    api.get<ReviewListResponse>(`/users/${userId}/reviews`, params),
};
