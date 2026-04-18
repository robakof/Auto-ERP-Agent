import { api } from "./client";
import type { LocationRead, LocationType } from "./types";

export const locations = {
  list: (params?: { type?: LocationType }) =>
    api.get<LocationRead[]>("/locations", params as Record<string, string | number | boolean | undefined>),
};
