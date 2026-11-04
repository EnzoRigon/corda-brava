import { request } from "./client";
import type {
  JoinRequest,
  JoinResponse,
  MeResponse,
  PublicMatch,
  PullAccepted,
  PullRequest,
} from "../types/api";

const m = (id: string) => `/api/matches/${id}`;

export const getPublic = (id: string) => request<PublicMatch>(`${m(id)}/public`);
export const join = (id: string, body: JoinRequest) =>
  request<JoinResponse>(`${m(id)}/players`, { body });
export const sendPulls = (id: string, body: PullRequest) =>
  request<PullAccepted>(`${m(id)}/pulls`, { body });
export const getMe = (id: string, playerId: string, token: string) =>
  request<MeResponse>(`${m(id)}/me`, { query: { playerId, token } });
