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
    const poll = async () => {
      try {
        const r = await getMe(matchId, session.playerId, session.playerToken);
        if (!alive) return;
        setMe(r);
        if (r.screen !== page) navigate(`/j/${matchId}/${r.screen}`, { replace: true });
      } catch (e) {
        if (alive && e instanceof ApiError && (e.status === 401 || e.status === 403)) {
          clearSession(matchId);
          navigate(`/j/${matchId}`, { replace: true });
        } // other errors: keep polling
      }
    };
    void poll();
    const id = setInterval(() => void poll(), ME_POLL_MS);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, [matchId, page, session, navigate]);

  return { session, me };
}
