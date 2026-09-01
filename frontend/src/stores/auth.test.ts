// File: frontend/src/stores/auth.test.ts
import { beforeEach, describe, expect, it } from "vitest";

import { useAuthStore } from "./auth";

const SAMPLE_USER = {
  id: 1,
  email: "user@test.at",
  full_name: "Test User",
  role: "user" as const,
  is_active: true,
  created_at: "2026-04-25T00:00:00Z",
};

describe("useAuthStore", () => {
  beforeEach(() => {
    useAuthStore.getState().logout();
    localStorage.clear();
  });

  it("starts unauthenticated", () => {
    expect(useAuthStore.getState().isAuthenticated()).toBe(false);
  });

  it("becomes authenticated after setTokens", () => {
    useAuthStore.getState().setTokens("access", "refresh");
    expect(useAuthStore.getState().isAuthenticated()).toBe(true);
  });

  it("identifies admins", () => {
    useAuthStore.getState().setUser({ ...SAMPLE_USER, role: "admin" });
    expect(useAuthStore.getState().isAdmin()).toBe(true);
  });

  it("logs out clears state", () => {
    useAuthStore.getState().setTokens("access", "refresh");
    useAuthStore.getState().setUser(SAMPLE_USER);
    useAuthStore.getState().logout();
    expect(useAuthStore.getState().accessToken).toBeNull();
    expect(useAuthStore.getState().user).toBeNull();
  });
});
