import { useEffect, useState } from "react";
import { hostWsUrl } from "../api/hostApi";
import type { CancelledMsg, EndedMsg, HostWsMsg, MatchView, ResetMsg, TickMsg } from "../types/api";

export interface HostSocketState {
  status: MatchView["status"] | null;
  snapshot: MatchView | null;
  lastTick: TickMsg | null;
  ended: EndedMsg | null;
  /** cancelled / reset (with newMatchId): the server closes right after. */
  terminal: CancelledMsg | ResetMsg | null;
  connected: boolean;
  /** Server closed with 1008 (bad/expired token): the page should go to login. */
  authError: boolean;
}

const INITIAL: HostSocketState = {
  status: null, snapshot: null, lastTick: null, ended: null, terminal: null, connected: false, authError: false,
};
const MAX_BACKOFF_MS = 5000;

function apply(s: HostSocketState, m: HostWsMsg): HostSocketState {
  const snap = s.snapshot;
  switch (m.type) {
    case "snapshot":
      return { ...s, snapshot: m.match, status: m.match.status };
    case "player_joined": {
      if (!snap || snap.roster[m.team].some((p) => p.id === m.player.id)) return s;
      const roster = { ...snap.roster, [m.team]: [...snap.roster[m.team], m.player] };
      return { ...s, snapshot: { ...snap, roster } };
    }
    case "tick":
      return {
        ...s,
        lastTick: m,
        status: "RUNNING",
        snapshot: snap && { ...snap, status: "RUNNING", rope: m.rope, remainingS: m.remainingS, scores: m.scores },
      };
    case "ended":
      return {
        ...s,
        ended: m,
        status: "FINISHED",
        snapshot: snap && { ...snap, status: "FINISHED", rope: m.finalRope, result: m.result, endReason: m.endReason },
      };
    default:
      return { ...s, terminal: m };
  }
}

export function useHostSocket(matchId: string, token: string): HostSocketState {
  const [state, setState] = useState<HostSocketState>(INITIAL);

  useEffect(() => {
    let ws: WebSocket | null = null;
    let timer: ReturnType<typeof setTimeout> | undefined;
    let attempt = 0;
    let stopped = false; // unmounted, or ended/cancelled/reset/auth failure: never reconnect

    const connect = () => {
      ws = new WebSocket(hostWsUrl(matchId, token));
      ws.onopen = () => {
        attempt = 0;
        setState((s) => ({ ...s, connected: true }));
      };
      ws.onmessage = (e) => {
        let m: HostWsMsg;
        try {
          m = JSON.parse(e.data as string) as HostWsMsg;
        } catch {
          return;
        }
        if (m.type === "ended" || m.type === "cancelled" || m.type === "reset") stopped = true;
        setState((s) => apply(s, m));
      };
      ws.onclose = (e) => {
        setState((s) => ({ ...s, connected: false, authError: s.authError || e.code === 1008 }));
        if (e.code === 1008) stopped = true;
        if (stopped) return;
        timer = setTimeout(connect, Math.min(500 * 2 ** attempt++, MAX_BACKOFF_MS));
      };
    };
    connect();

    return () => {
      stopped = true;
      clearTimeout(timer);
      if (ws) {
        ws.onclose = ws.onmessage = ws.onopen = null;
        ws.close();
      }
    };
  }, [matchId, token]);

  return state;
}
