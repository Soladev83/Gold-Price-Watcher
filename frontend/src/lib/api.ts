/**
 * Typed API client — axios wrapper.
 * JWT token is stored in localStorage and attached automatically.
 */

import axios from "axios";

export const api = axios.create({ baseURL: "/api" });

// Attach token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Redirect to login on 401
api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("token");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface GoldPrice {
  id: number;
  fetched_at: string;
  price_24k: number;
  price_22k: number | null;
  price_18k: number | null;
  change_24k_abs: number | null;
  change_24k_pct: number | null;
  source_url: string;
  source_label: string;
}

export interface User {
  id: number;
  email: string;
  full_name: string | null;
  is_active: boolean;
  telegram_chat_id: string | null;
  telegram_connected_at: string | null;
  notify_interval_hours: number;
  created_at: string;
}

export interface AlertRule {
  id: number;
  created_at: string;
  rule_type: "above" | "below" | "pct_change";
  threshold: number;
  purity: "24K" | "22K" | "18K";
  is_active: boolean;
  label: string | null;
  last_triggered_at: string | null;
  last_triggered_price: number | null;
}

export interface AlertRulePayload {
  rule_type: "above" | "below" | "pct_change";
  threshold: number;
  purity: "24K" | "22K" | "18K";
  label?: string;
}

export interface TriggerResponse {
  success: boolean;
  message: string;
  record: GoldPrice | null;
}

export interface TelegramLinkResponse {
  link: string;
  token: string;
}

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------

export const register = (email: string, password: string, full_name?: string) =>
  api.post<{ access_token: string }>("/auth/register", { email, password, full_name }).then((r) => r.data);

export const login = (email: string, password: string) => {
  const form = new URLSearchParams();
  form.append("username", email);
  form.append("password", password);
  return api.post<{ access_token: string }>("/auth/login", form, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  }).then((r) => r.data);
};

export const getMe = () => api.get<User>("/auth/me").then((r) => r.data);

export const updateMe = (payload: { full_name?: string; notify_interval_hours?: number }) =>
  api.put<User>("/auth/me", payload).then((r) => r.data);

export const getTelegramLink = () =>
  api.get<TelegramLinkResponse>("/auth/telegram/link").then((r) => r.data);

export const unlinkTelegram = () => api.delete("/auth/telegram/unlink");

// ---------------------------------------------------------------------------
// Prices
// ---------------------------------------------------------------------------

export const fetchLatestPrice = () =>
  api.get<GoldPrice>("/prices/latest").then((r) => r.data);

export const fetchPriceHistory = (limit = 60, offset = 0) =>
  api.get<GoldPrice[]>("/prices", { params: { limit, offset } }).then((r) => r.data);

export const triggerManualFetch = () =>
  api.post<TriggerResponse>("/prices/fetch").then((r) => r.data);

// ---------------------------------------------------------------------------
// Alert rules
// ---------------------------------------------------------------------------

export const fetchAlertRules = () =>
  api.get<AlertRule[]>("/alerts").then((r) => r.data);

export const createAlertRule = (payload: AlertRulePayload) =>
  api.post<AlertRule>("/alerts", payload).then((r) => r.data);

export const updateAlertRule = (id: number, payload: Partial<AlertRulePayload & { is_active: boolean }>) =>
  api.put<AlertRule>(`/alerts/${id}`, payload).then((r) => r.data);

export const deleteAlertRule = (id: number) => api.delete(`/alerts/${id}`);
