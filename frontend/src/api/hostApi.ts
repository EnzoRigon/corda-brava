import { request, wsUrl } from "./client";
import type {
  AnalyticsPayload,
  ConfigOut,
  CreateMatchRequest,
  CreateMatchResponse,
  LoginResponse,
  MatchView,
} from "../types/api";

const m = (id: string) => `/api/host/matches/${id}`;

export const login = (password: string) =>
  request<LoginResponse>("/api/host/login", { body: { password } });
export const createMatch = (token: string, body: CreateMatchRequest = {}) =>
  request<CreateMatchResponse>("/api/host/matches", { body, token });
export const getMatch = (token: string, id: string) => request<MatchView>(m(id), { token });
export const patchMatch = (token: string, id: string, durationS: number) =>
  request<ConfigOut>(m(id), { method: "PATCH", body: { durationS }, token });
export const startMatch = (token: string, id: string) =>
  request<MatchView>(`${m(id)}/start`, { method: "POST", body: {}, token });
/** Returns the NEW match (reset creates a fresh lobby). */
export const resetMatch = (token: string, id: string) =>
  request<CreateMatchResponse>(`${m(id)}/reset`, { method: "POST", body: {}, token });
export const cancelMatch = (token: string, id: string) =>
  request<MatchView>(`${m(id)}/cancel`, { method: "POST", body: {}, token });
export const getAnalytics = (token: string, id: string) =>
  request<AnalyticsPayload>(`${m(id)}/analytics`, { token });
export const hostWsUrl = (id: string, token: string) => wsUrl(`${m(id)}/ws`, { token });
