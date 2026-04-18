import { api } from "./client";
import type {
  CreateRequestBody,
  UpdateRequestBody,
  RequestRead,
  RequestListResponse,
  CancelResponse,
} from "./types";

export const requests = {
  create: (data: CreateRequestBody) =>
    api.post<RequestRead>("/requests", data),

  get: (id: string) =>
    api.get<RequestRead>(`/requests/${id}`),

  update: (id: string, data: UpdateRequestBody) =>
    api.patch<RequestRead>(`/requests/${id}`, data),

  list: (params?: Record<string, string | number | boolean | undefined>) =>
    api.get<RequestListResponse>("/requests", params),

  cancel: (id: string) =>
    api.post<CancelResponse>(`/requests/${id}/cancel`),
};
