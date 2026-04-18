"use client";

import { create } from "zustand";
import { useEffect, useRef } from "react";
import { auth } from "@/lib/api/auth";
import { setTokenStore } from "@/lib/api/client";
import type { UserRead, LoginRequest, RegisterRequest } from "@/lib/api/types";

const REFRESH_TOKEN_KEY = "serce_refresh_token";

interface AuthState {
  user: UserRead | null;
  accessToken: string | null;
  isHydrated: boolean;
  isLoading: boolean;

  login: (data: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<boolean>;
  hydrate: () => Promise<void>;
}

export const useAuth = create<AuthState>()((set, get) => {
  // Wire token store to API client so auto-refresh on 401 works
  setTokenStore({
    getAccessToken: () => get().accessToken,
    getRefreshToken: () => localStorage.getItem(REFRESH_TOKEN_KEY),
    setTokens: (access, refresh) => {
      set({ accessToken: access });
      localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
    },
    clearTokens: () => {
      set({ accessToken: null, user: null });
      localStorage.removeItem(REFRESH_TOKEN_KEY);
    },
  });

  return {
    user: null,
    accessToken: null,
    isHydrated: false,
    isLoading: false,

    login: async (data) => {
      set({ isLoading: true });
      try {
        const tokens = await auth.login(data);
        set({ accessToken: tokens.access_token });
        localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
        const user = await auth.getMe();
        set({ user });
      } finally {
        set({ isLoading: false });
      }
    },

    register: async (data) => {
      set({ isLoading: true });
      try {
        const tokens = await auth.register(data);
        set({ accessToken: tokens.access_token });
        localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
        const user = await auth.getMe();
        set({ user });
      } finally {
        set({ isLoading: false });
      }
    },

    logout: async () => {
      set({ isLoading: true });
      try {
        await auth.logout();
      } catch {
        // Ignore — clear tokens regardless
      } finally {
        set({ accessToken: null, user: null, isLoading: false });
        localStorage.removeItem(REFRESH_TOKEN_KEY);
      }
    },

    refresh: async () => {
      const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
      if (!refreshToken) return false;
      try {
        const tokens = await auth.refresh({ refresh_token: refreshToken });
        set({ accessToken: tokens.access_token });
        localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
        return true;
      } catch {
        set({ accessToken: null, user: null });
        localStorage.removeItem(REFRESH_TOKEN_KEY);
        return false;
      }
    },

    hydrate: async () => {
      const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
      if (!refreshToken) {
        set({ isHydrated: true });
        return;
      }
      set({ isLoading: true });
      try {
        const refreshed = await get().refresh();
        if (refreshed) {
          const user = await auth.getMe();
          set({ user });
        }
      } catch {
        // Silent fail — user stays logged out
      } finally {
        set({ isHydrated: true, isLoading: false });
      }
    },
  };
});

/**
 * Component that runs hydrate() once on mount.
 * Place inside Providers — renders nothing.
 */
export function AuthHydration() {
  const hydrate = useAuth((s) => s.hydrate);
  const started = useRef(false);

  useEffect(() => {
    if (!started.current) {
      started.current = true;
      hydrate();
    }
  }, [hydrate]);

  return null;
}
