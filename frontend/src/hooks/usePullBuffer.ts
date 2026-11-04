import { useCallback, useEffect, useRef, useState } from "react";
import { API_BASE, ApiError } from "../api/client";
import { sendPulls } from "../api/playerApi";
import type { PullRequest } from "../types/api";

export const MAX_PULLS_PER_BATCH = 200;

interface Opts {
  matchId: string;
  playerId: string;
  playerToken: string;
  flushIntervalMs: number;
  enabled?: boolean;
}

export function usePullBuffer({ matchId, playerId, playerToken, flushIntervalMs, enabled = true }: Opts) {
  const [displayCount, setDisplayCount] = useState(0);
  const pending = useRef(0);
  // Batch sent (or beaconed) but not yet confirmed; resent with the SAME batchId until 2xx.
  const unacked = useRef<{ count: number; batchId: string } | null>(null);
  const inflight = useRef(false);
  const stopped = useRef(false); // set after 401/403/409: no more POSTs until reconfigured
  const cfg = useRef({ matchId, playerId, playerToken });
  useEffect(() => {
    cfg.current = { matchId, playerId, playerToken };
  });
  useEffect(() => {
    stopped.current = false;
  }, [enabled, matchId, playerId, playerToken]);

  const takeBatch = () => {
    if (!unacked.current && pending.current > 0) {
      const count = Math.min(pending.current, MAX_PULLS_PER_BATCH);
      pending.current -= count;
      unacked.current = { count, batchId: crypto.randomUUID() };
    }
    return unacked.current;
  };
  const body = (b: { count: number; batchId: string }): PullRequest => ({
    playerId: cfg.current.playerId,
    playerToken: cfg.current.playerToken,
    count: b.count,
    batchId: b.batchId,
    clientTs: Date.now(),
  });

  const flush = useCallback(async () => {
    if (inflight.current || stopped.current) return;
    const batch = takeBatch();
    if (!batch) return;
    inflight.current = true;
    try {
      await sendPulls(cfg.current.matchId, body(batch));
      unacked.current = null;
    } catch (e) {
      // 4xx (except 408/429) is a poison batch: drop it. 401/403/409 (bad token / match not running) also stop sending.
      if (e instanceof ApiError && e.status >= 400 && e.status < 500 && e.status !== 408 && e.status !== 429) {
        unacked.current = null;
        if ([401, 403, 409].includes(e.status)) {
          stopped.current = true;
          pending.current = 0;
        }
      }
      // otherwise (network, 5xx, 408, 429) keep the batch for an idempotent resend
    } finally {
      inflight.current = false;
    }
  }, []);

  const flushOnHide = useCallback(() => {
    if (stopped.current) return;
    const batch = takeBatch(); // stays unacked: a beacon cannot confirm success
    if (!batch) return;
    const url = `${API_BASE}/api/matches/${cfg.current.matchId}/pulls`;
    const json = JSON.stringify(body(batch));
    const ok =
      typeof navigator.sendBeacon === "function" &&
      navigator.sendBeacon(url, new Blob([json], { type: "application/json" }));
    if (!ok)
      void fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: json,
        keepalive: true,
      }).catch(() => {});
  }, []);

  useEffect(() => {
    if (!enabled) return;
    const id = setInterval(() => void flush(), flushIntervalMs);
    const onVis = () => document.visibilityState === "hidden" && flushOnHide();
    document.addEventListener("visibilitychange", onVis);
    window.addEventListener("pagehide", flushOnHide);
    return () => {
      clearInterval(id);
      document.removeEventListener("visibilitychange", onVis);
      window.removeEventListener("pagehide", flushOnHide);
    };
  }, [enabled, flushIntervalMs, flush, flushOnHide]);

  const tap = useCallback(() => {
    pending.current += 1;
    setDisplayCount((c) => c + 1);
  }, []);

  return { displayCount, tap };
}
