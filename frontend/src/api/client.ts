// File: frontend/src/api/client.ts
import axios, {
  AxiosError,
  AxiosHeaders,
  type AxiosInstance,
  type InternalAxiosRequestConfig,
} from "axios";

import i18n from "@/i18n/config";
import { useAuthStore } from "@/stores/auth";

const baseURL = import.meta.env.VITE_API_BASE_URL ?? "/api";

export const api: AxiosInstance = axios.create({
  baseURL,
  timeout: 30_000,
  headers: { "Content-Type": "application/json" },
});

// ---- Request: attach access token ----
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    if (!config.headers) config.headers = new AxiosHeaders();
    (config.headers as AxiosHeaders).set("Authorization", `Bearer ${token}`);
  }
  return config;
});

// ---- Response: refresh-on-401 ----
let refreshPromise: Promise<string> | null = null;

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (
      error.response?.status === 401 &&
      original &&
      !original._retry &&
      !original.url?.includes("/auth/refresh")
    ) {
      original._retry = true;
      const refreshToken = useAuthStore.getState().refreshToken;
      if (!refreshToken) {
        useAuthStore.getState().logout();
        return Promise.reject(error);
      }

      try {
        if (!refreshPromise) {
          refreshPromise = axios
            .post<{ access_token: string; refresh_token: string }>(
              `${baseURL}/auth/refresh`,
              { refresh_token: refreshToken },
              { headers: { "Content-Type": "application/json" } },
            )
            .then((resp) => {
              useAuthStore
                .getState()
                .setTokens(resp.data.access_token, resp.data.refresh_token);
              return resp.data.access_token;
            })
            .finally(() => {
              refreshPromise = null;
            });
        }
        const newToken = await refreshPromise;
        if (!original.headers) original.headers = new AxiosHeaders();
        (original.headers as AxiosHeaders).set("Authorization", `Bearer ${newToken}`);
        return api(original);
      } catch (refreshError) {
        useAuthStore.getState().logout();
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  },
);

/**
 * Translate a known backend error string (the literal English `detail`
 * raised by a DomainError) into the active UI language. Backend errors are
 * plain English by design (see docs/LOCALISATION.md for the rationale and
 * limitation); unrecognised messages are passed through unchanged rather
 * than hidden, since a raw-but-readable message beats a generic fallback.
 */
function translateBackendDetail(detail: string): string {
  // Looked up as a direct object key (not a dotted i18next key path) because
  // backend detail strings are full sentences that may themselves contain
  // periods, which would otherwise be misread as nested-key separators.
  const language = i18n.resolvedLanguage ?? i18n.language ?? "en";
  const map =
    (i18n.getResource(language, "errors", "backend") as Record<string, string> | undefined) ??
    (i18n.getResource("en", "errors", "backend") as Record<string, string> | undefined);
  return map?.[detail] ?? detail;
}

/** Pull a clean, localised error string out of an Axios error. */
export function extractErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = (error.response?.data as { detail?: string } | undefined)?.detail;
    if (detail) return translateBackendDetail(detail);
    if (error.code === "ECONNABORTED" || !error.response) {
      return i18n.t("errors:network");
    }
    return error.message;
  }
  if (error instanceof Error) return error.message;
  return i18n.t("errors:generic");
}
