import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ApiError } from "../api/client";
import { getMe } from "../api/playerApi";
import type { JoinResponse, MeResponse } from "../types/api";

export const ME_POLL_MS = 1000;
export type Screen = MeResponse["screen"];
const key = (matchId: string) => `cb.session.${matchId}`;

export function loadSession(matchId: string): JoinResponse | null {
  try {
    const s = JSON.parse(localStorage.getItem(key(matchId)) ?? "null");
    return s?.playerId && s?.playerToken && s?.team ? s : null;
  } catch {
    return null;
  }
}
export function saveSession(matchId: string, s: JoinResponse) {
  try {
    localStorage.setItem(key(matchId), JSON.stringify(s));
  } catch {
    // storage blocked: the player simply cannot resume after a reload
  }
}
function clearSession(matchId: string) {
  try {
    localStorage.removeItem(key(matchId));
  } catch {
    // ignore
  }
}

/** Polls /me with the stored token; navigates when the server's screen differs from `page`. */
export function useMePolling(matchId: string, page: Screen) {
  const navigate = useNavigate();
  const [session] = useState(() => loadSession(matchId));
  const [me, setMe] = useState<MeResponse | null>(null);

  useEffect(() => {
    if (!session) {
      navigate(`/j/${matchId}`, { replace: true });
      return;
    }
    let alive = true;
    let busy = false; // in-flight guard: no overlapping /me requests, no stale out-of-order screens
    const poll = async () => {
      if (busy) return;
      busy = true;
      try {
        const r = await getMe(matchId, session.playerId, session.playerToken);
        if (!alive) return;
        setMe(r);
        if (r.screen === "end") clearInterval(id); // terminal: nothing more to learn
        if (r.screen !== page) navigate(`/j/${matchId}/${r.screen}`, { replace: true });
      } catch (e) {
        if (alive && e instanceof ApiError && [401, 403, 404].includes(e.status)) {
          clearSession(matchId);
          navigate(`/j/${matchId}`, { replace: true });
        } // other errors: keep polling
      } finally {
        busy = false;
      }
    };
    const id = setInterval(() => void poll(), ME_POLL_MS);
    void poll();
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, [matchId, page, session, navigate]);

  return { session, me };
}
