import { api } from "./client";
import type {
  NotificationListResponse,
  NotificationRead,
  MarkAllReadResponse,
  UnreadCountResponse,
} from "./types";

export const notifications = {
  list: (params?: Record<string, string | number | boolean | undefined>) =>
    api.get<NotificationListResponse>("/users/me/notifications", params),

  markRead: (id: string) =>
    api.patch<NotificationRead>(`/users/me/notifications/${id}/read`),

  markAllRead: () =>
    api.post<MarkAllReadResponse>("/users/me/notifications/read-all"),

  getUnreadCount: () =>
    api.get<UnreadCountResponse>("/users/me/notifications/unread-count"),
};
