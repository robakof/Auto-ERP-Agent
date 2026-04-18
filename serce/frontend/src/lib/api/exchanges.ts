import { api } from "./client";
import type {
  CreateExchangeBody,
  ExchangeRead,
  ExchangeListResponse,
} from "./types";

export const exchanges = {
  create: (data: CreateExchangeBody) =>
    api.post<ExchangeRead>("/exchanges", data),

  get: (id: string) =>
    api.get<ExchangeRead>(`/exchanges/${id}`),

  accept: (id: string) =>
    api.post<ExchangeRead>(`/exchanges/${id}/accept`),

  complete: (id: string) =>
    api.post<ExchangeRead>(`/exchanges/${id}/complete`),

  cancel: (id: string) =>
    api.post<ExchangeRead>(`/exchanges/${id}/cancel`),

  list: (params?: Record<string, string | number | boolean | undefined>) =>
    api.get<ExchangeListResponse>("/exchanges", params),
};
