import { api } from "./client";
import type {
  SendMessageBody,
  MessageRead,
  MessageListResponse,
} from "./types";

export const messages = {
  send: (exchangeId: string, data: SendMessageBody) =>
    api.post<MessageRead>(`/exchanges/${exchangeId}/messages`, data),

  list: (exchangeId: string, params?: Record<string, string | number | boolean | undefined>) =>
    api.get<MessageListResponse>(`/exchanges/${exchangeId}/messages`, params),

  hide: (exchangeId: string, messageId: string) =>
    api.patch<MessageRead>(`/exchanges/${exchangeId}/messages/${messageId}/hide`),
};
