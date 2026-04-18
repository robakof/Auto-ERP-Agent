import { api } from "./client";
import type {
  CreateOfferBody,
  UpdateOfferBody,
  ChangeOfferStatusBody,
  OfferRead,
  OfferListResponse,
} from "./types";

export const offers = {
  create: (data: CreateOfferBody) =>
    api.post<OfferRead>("/offers", data),

  get: (id: string) =>
    api.get<OfferRead>(`/offers/${id}`),

  update: (id: string, data: UpdateOfferBody) =>
    api.patch<OfferRead>(`/offers/${id}`, data),

  changeStatus: (id: string, data: ChangeOfferStatusBody) =>
    api.patch<OfferRead>(`/offers/${id}/status`, data),

  list: (params?: Record<string, string | number | boolean | undefined>) =>
    api.get<OfferListResponse>("/offers", params),
};
