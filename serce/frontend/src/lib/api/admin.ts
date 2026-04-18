import { api } from "./client";
import type {
  FlagListResponse,
  FlagDetailRead,
  ResolveFlagBody,
  SuspendUserBody,
  UserAdminRead,
  GrantHeartsBody,
  LedgerEntryRead,
  AuditListResponse,
} from "./types";

export const admin = {
  listFlags: (params?: Record<string, string | number | boolean | undefined>) =>
    api.get<FlagListResponse>("/admin/flags", params),

  getFlag: (id: string) =>
    api.get<FlagDetailRead>(`/admin/flags/${id}`),

  resolveFlag: (id: string, data: ResolveFlagBody) =>
    api.post<FlagDetailRead>(`/admin/flags/${id}/resolve`, data),

  suspendUser: (userId: string, data: SuspendUserBody) =>
    api.post<UserAdminRead>(`/admin/users/${userId}/suspend`, data),

  unsuspendUser: (userId: string) =>
    api.post<UserAdminRead>(`/admin/users/${userId}/unsuspend`),

  grantHearts: (data: GrantHeartsBody) =>
    api.post<LedgerEntryRead>("/admin/hearts/grant", data),

  getAuditLog: (params?: Record<string, string | number | boolean | undefined>) =>
    api.get<AuditListResponse>("/admin/audit-log", params),
};
