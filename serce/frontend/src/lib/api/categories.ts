import { api } from "./client";
import type { CategoryRead } from "./types";

export const categories = {
  list: (params?: { active?: boolean }) =>
    api.get<CategoryRead[]>("/categories", params as Record<string, string | number | boolean | undefined>),
};
