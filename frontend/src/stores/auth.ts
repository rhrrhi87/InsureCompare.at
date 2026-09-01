// File: frontend/src/stores/auth.ts
import { create } from "zustand";
import { persist } from "zustand/middleware";

import type { User } from "@/types/domain";

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
  setTokens: (access: string, refresh: string) => void;
  setUser: (user: User | null) => void;
  /** Clears local session state. Does not call the server — see useLogout(). */
  logout: () => void;
  isAuthenticated: () => boolean;
  isAdmin: () => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      accessToken: null,
      refreshToken: null,
      user: null,

      setTokens: (access, refresh) =>
        set({ accessToken: access, refreshToken: refresh }),

      setUser: (user) => set({ user }),

      logout: () =>
        set({ accessToken: null, refreshToken: null, user: null }),

      isAuthenticated: () => Boolean(get().accessToken),
      isAdmin: () => get().user?.role === "admin",
    }),
    { name: "insurecompare.auth" },
  ),
);
