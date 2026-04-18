import { api } from "./client";
import type { CreateFlagBody, FlagRead } from "./types";

export const flags = {
  flagRequest: (targetId: string, data: CreateFlagBody) =>
    api.post<FlagRead>(`/requests/${targetId}/flag`, data),

  flagOffer: (targetId: string, data: CreateFlagBody) =>
    api.post<FlagRead>(`/offers/${targetId}/flag`, data),

  flagExchange: (targetId: string, data: CreateFlagBody) =>
    api.post<FlagRead>(`/exchanges/${targetId}/flag`, data),

  flagUser: (targetId: string, data: CreateFlagBody) =>
    api.post<FlagRead>(`/users/${targetId}/flag`, data),
};
