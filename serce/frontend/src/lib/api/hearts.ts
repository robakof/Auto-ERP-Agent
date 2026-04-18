import { api } from "./client";
import type {
  GiftRequest,
  LedgerEntryRead,
  BalanceResponse,
  LedgerResponse,
} from "./types";

export const hearts = {
  gift: (data: GiftRequest) =>
    api.post<LedgerEntryRead>("/hearts/gift", data),

  getBalance: () =>
    api.get<BalanceResponse>("/hearts/balance"),

  getLedger: (params?: Record<string, string | number | boolean | undefined>) =>
    api.get<LedgerResponse>("/hearts/ledger", params),
};
