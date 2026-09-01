// File: frontend/src/api/endpoints.ts
//
// Thin, typed wrappers over the Axios client. Components use these directly
// or via TanStack Query hooks in src/hooks.

import type {
  AdminStats,
  AdvisorAnswer,
  AdvisorSummaryOut,
  AuditLogEntry,
  CompareResponse,
  Policy,
  ProductLine,
  Provider,
  RecommendationResponse,
  RiskProfile,
  SourceClause,
  TokenResponse,
  UploadOut,
  User,
} from "@/types/domain";

import { api } from "./client";

// ---------- Auth ----------
export const authApi = {
  register: (data: { email: string; password: string; full_name?: string }) =>
    api.post<User>("/auth/register", data).then((r) => r.data),
  login: (data: { email: string; password: string }) =>
    api.post<TokenResponse>("/auth/login", data).then((r) => r.data),
  refresh: (refresh_token: string) =>
    api.post<TokenResponse>("/auth/refresh", { refresh_token }).then((r) => r.data),
  logout: (refresh_token: string) =>
    api.post<void>("/auth/logout", { refresh_token }).then((r) => r.data),
  me: () => api.get<User>("/auth/me").then((r) => r.data),
};

// ---------- Profile ----------
export const profileApi = {
  get: () => api.get<RiskProfile>("/profiles/me").then((r) => r.data),
  upsert: (data: Omit<RiskProfile, "id" | "user_id">) =>
    api.put<RiskProfile>("/profiles/me", data).then((r) => r.data),
};

// ---------- Policies ----------
export const policyApi = {
  list: (params?: { product_line?: ProductLine; active_only?: boolean }) =>
    api.get<Policy[]>("/policies", { params }).then((r) => r.data),
  get: (id: number) => api.get<Policy>(`/policies/${id}`).then((r) => r.data),
  clauses: (id: number) =>
    api.get<SourceClause[]>(`/policies/${id}/clauses`).then((r) => r.data),
  listProviders: () => api.get<Provider[]>("/providers").then((r) => r.data),
  // Admin
  create: (data: Partial<Policy> & { provider_id: number }) =>
    api.post<Policy>("/policies", data).then((r) => r.data),
  update: (id: number, data: Partial<Policy>) =>
    api.patch<Policy>(`/policies/${id}`, data).then((r) => r.data),
  retire: (id: number) =>
    api.post<Policy>(`/policies/${id}/retire`).then((r) => r.data),
  reactivate: (id: number) =>
    api.post<Policy>(`/policies/${id}/reactivate`).then((r) => r.data),
};

// ---------- Providers (admin) ----------
export const providerApi = {
  create: (data: Partial<Provider> & { name: string }) =>
    api.post<Provider>("/providers", data).then((r) => r.data),
  update: (id: number, data: Partial<Provider>) =>
    api.patch<Provider>(`/providers/${id}`, data).then((r) => r.data),
  deactivate: (id: number) =>
    api.post<Provider>(`/providers/${id}/deactivate`).then((r) => r.data),
  reactivate: (id: number) =>
    api.post<Provider>(`/providers/${id}/reactivate`).then((r) => r.data),
};

// ---------- Documents / Uploads ----------
export const uploadApi = {
  upload: async (file: File): Promise<UploadOut> => {
    const fd = new FormData();
    fd.append("file", file);
    const resp = await api.post<UploadOut>("/documents", fd, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return resp.data;
  },
  list: () => api.get<UploadOut[]>("/documents").then((r) => r.data),
  get: (id: number) => api.get<UploadOut>(`/documents/${id}`).then((r) => r.data),
};

// ---------- AI Policy Advisor ----------
export const advisorApi = {
  summary: (uploadId: number, language: "de" | "en") =>
    api
      .get<AdvisorSummaryOut>(`/uploads/${uploadId}/advisor/summary`, { params: { language } })
      .then((r) => r.data),
  ask: (uploadId: number, question: string, language: "de" | "en") =>
    api
      .post<AdvisorAnswer>(`/uploads/${uploadId}/advisor/ask`, { question, language })
      .then((r) => r.data),
};

// ---------- Recommendations ----------
export const recommendationApi = {
  recommend: (params?: {
    product_line?: ProductLine;
    weights?: Record<string, number>;
    top_k?: number;
  }) =>
    api
      .post<RecommendationResponse>("/recommend", params ?? {})
      .then((r) => r.data),
};

// ---------- Compare ----------
export const compareApi = {
  compare: (policy_ids: number[]) =>
    api.post<CompareResponse>("/compare", { policy_ids }).then((r) => r.data),
};

// ---------- Admin ----------
export const adminApi = {
  stats: () => api.get<AdminStats>("/admin/stats").then((r) => r.data),
  users: () => api.get<User[]>("/admin/users").then((r) => r.data),
  audit: (limit = 100) =>
    api.get<AuditLogEntry[]>("/admin/audit", { params: { limit } }).then((r) => r.data),
  uploads: (limit = 100) =>
    api.get<UploadOut[]>("/admin/uploads", { params: { limit } }).then((r) => r.data),
};
