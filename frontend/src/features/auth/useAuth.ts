// File: frontend/src/features/auth/useAuth.ts
import { useMutation, useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { authApi } from "@/api/endpoints";
import { useAuthStore } from "@/stores/auth";

export function useLogin() {
  const navigate = useNavigate();
  const { setTokens, setUser } = useAuthStore();

  return useMutation({
    mutationFn: async (creds: { email: string; password: string }) => {
      const tokens = await authApi.login(creds);
      setTokens(tokens.access_token, tokens.refresh_token);
      const me = await authApi.me();
      setUser(me);
      return me;
    },
    onSuccess: (user) => {
      navigate(user.role === "admin" ? "/admin" : "/dashboard", { replace: true });
    },
  });
}

export function useRegister() {
  const navigate = useNavigate();
  return useMutation({
    mutationFn: authApi.register,
    onSuccess: () => {
      navigate("/login", { replace: true, state: { registered: true } });
    },
  });
}

export function useLogout() {
  const navigate = useNavigate();
  const { refreshToken, logout } = useAuthStore();

  return async () => {
    if (refreshToken) {
      // Best-effort: revoke the server-side session, but always clear local
      // state even if the network call fails (e.g. already offline).
      try {
        await authApi.logout(refreshToken);
      } catch {
        // ignored — local logout still proceeds
      }
    }
    logout();
    navigate("/", { replace: true });
  };
}

export function useCurrentUser() {
  const { isAuthenticated, setUser } = useAuthStore();
  return useQuery({
    queryKey: ["auth", "me"],
    queryFn: async () => {
      const me = await authApi.me();
      setUser(me);
      return me;
    },
    enabled: isAuthenticated(),
    staleTime: 60_000,
  });
}
