// Mirrors backend Pydantic schemas (camelCase JSON). Status/result UPPERCASE, endReason lowercase,
// team ids lowercase ("inter"|"gremio").

export type TeamId = "inter" | "gremio";
export type MatchStatus = "LOBBY" | "RUNNING" | "FINISHED";
export type MatchResult = "INTER" | "GREMIO" | "DRAW";
export type EndReason = "win" | "timeout";
export type BalanceMode = "raw" | "normalized";

export interface TeamColors { primary: string; secondary: string }
export interface TeamConfig { id: TeamId; name: string; colors: TeamColors }
export interface ConfigOut {
  durationS: number;
  ropeTarget: number;
  balanceMode: BalanceMode;
  teams: Record<TeamId, TeamConfig>;
}

export interface RosterPlayer { id: string; name: string }
export interface TeamScore { pulls: number }

/** Host view of a match; also the `match` body of the WS snapshot. */
export interface MatchView {
  id: string;
  status: MatchStatus;
  config: ConfigOut;
  roster: Record<TeamId, RosterPlayer[]>;
  rope: number;
  remainingS: number;
  scores: Record<TeamId, TeamScore>;
  result: MatchResult | null;
  endReason: EndReason | null;
  joinUrl?: string;
}

// ---- Analytics (prompt.md section 15) ----
export interface PlayerStats {
  playerId: string;
  name: string;
  team: TeamId;
  pulls: number;
  pctOfTeam: number;
  pctOfAll: number;
  pullsPerSec: number;
}
export interface TeamStats {
  players: number;
  totalPulls: number;
  avgPullsPerPlayer: number;
  bestPlayer: PlayerStats | null;
  worstPlayer: PlayerStats | null;
}
export interface AnalyticsPayload {
  result: MatchResult | null;
  endReason: EndReason | null;
  durationS: number;
  totalPlayers: number;
  playersPerTeam: Record<TeamId, number>;
  totalPulls: { overall: number; inter: number; gremio: number };
  pullsPerSecond: { t: number; inter: number; gremio: number }[];
  peak: { value: number; t: number };
  finalRope: number;
  teams: Record<TeamId, TeamStats>;
  players: PlayerStats[];
  leaderboard: PlayerStats[];
}

// ---- Host WebSocket messages (prompt.md section 14 + cancelled/reset) ----
export interface Snapshot { type: "snapshot"; match: MatchView }
export interface PlayerJoinedMsg { type: "player_joined"; team: TeamId; player: RosterPlayer }
export interface TickEvent { playerId: string; name: string; team: TeamId; count: number }
export interface TickMsg {
  type: "tick";
  rope: number;
  remainingS: number;
  delta: Record<TeamId, number>;
  scores: Record<TeamId, TeamScore>;
  events: TickEvent[];
}
export interface EndedMsg {
  type: "ended";
  result: MatchResult;
  endReason: EndReason;
  finalRope: number;
  analytics: AnalyticsPayload;
}
export interface CancelledMsg { type: "cancelled" }
export interface ResetMsg { type: "reset"; newMatchId: string }
export type HostWsMsg = Snapshot | PlayerJoinedMsg | TickMsg | EndedMsg | CancelledMsg | ResetMsg;

// ---- Host HTTP ----
export interface LoginResponse { token: string; expiresAt: string }
export interface CreateMatchRequest { durationS?: number; balanceMode?: BalanceMode }
export interface CreateMatchResponse {
  matchId: string;
  joinUrl: string;
  qrPayload: string;
  config: ConfigOut;
}

// ---- Player HTTP ----
export interface PublicMatch {
  status: MatchStatus;
  teams: Record<TeamId, { name: string; colors: TeamColors }>;
  counts: Record<TeamId, number>;
  durationS: number;
}
export interface JoinRequest { name: string; team: TeamId; deviceId: string }
export interface JoinResponse { playerId: string; playerToken: string; team: TeamId }
export interface PullRequest {
  playerId: string;
  playerToken: string;
  count: number;
  clientTs: number;
  batchId: string;
}
export interface PullAccepted { accepted: number }
export interface MeResponse {
  screen: "wait" | "play" | "end";
  team: TeamId;
  matchStatus: MatchStatus;
  result?: MatchResult;
}
