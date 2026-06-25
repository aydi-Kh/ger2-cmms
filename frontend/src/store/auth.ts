import { create } from "zustand";
import { persist } from "zustand/middleware";
import { api } from "@/api/client";
import type { User } from "@/types";

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  fetchMe: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,

      login: async (email, password) => {
        const { data } = await api.post("/auth/login", { email, password });
        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("refresh_token", data.refresh_token);
        set({
          accessToken: data.access_token,
          refreshToken: data.refresh_token,
          isAuthenticated: true,
        });
        await get().fetchMe();
      },

      logout: () => {
        localStorage.clear();
        set({ user: null, accessToken: null, refreshToken: null, isAuthenticated: false });
      },

      fetchMe: async () => {
        const { data } = await api.get<User>("/auth/me");
        set({ user: data });
      },
    }),
    { name: "ger2-auth-store", partialize: (s) => ({ accessToken: s.accessToken, refreshToken: s.refreshToken }) }
  )
);
