import { createElement, act } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useHostSocket } from "./useHostSocket";

(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

class MockWS {
  static all: MockWS[] = [];
  onopen: (() => void) | null = null;
  onmessage: ((e: { data: string }) => void) | null = null;
  onclose: ((e: { code: number }) => void) | null = null;
  onerror: (() => void) | null = null;
  closed = false;
  constructor(public url: string) {
    MockWS.all.push(this);
  }
  close() {
    this.closed = true;
  }
  send(msg: unknown) {
    void msg;
  }
}
const cfg = { durationS: 60, ropeTarget: 100, balanceMode: "normalized", teams: {} };
const match = {
  id: "m1", status: "LOBBY", config: cfg, roster: { inter: [], gremio: [] },
  rope: 0, remainingS: 60, scores: { inter: { pulls: 0 }, gremio: { pulls: 0 } }, result: null, endReason: null,
};
const last = () => MockWS.all[MockWS.all.length - 1];
const msg = (m: unknown) => act(() => last().onmessage!({ data: JSON.stringify(m) }));
const close = (code = 1006) => act(() => last().onclose!({ code }));

let out: ReturnType<typeof useHostSocket>;
let unmount: () => void;
function Probe() {
  out = useHostSocket("m1", "tok");
  return null;
}
beforeEach(() => {
  vi.useFakeTimers();
  MockWS.all = [];
  (globalThis as unknown as { WebSocket: unknown }).WebSocket = MockWS;
  const root = createRoot(document.createElement("div"));
  act(() => root.render(createElement(Probe)));
  unmount = () => act(() => root.unmount());
  act(() => last().onopen!());
});
afterEach(() => {
  unmount();
  vi.useRealTimers();
});

describe("useHostSocket", () => {
  it("connects with token and exposes the snapshot", () => {
    expect(last().url).toContain("/api/host/matches/m1/ws?token=tok");
    expect(out.connected).toBe(true);
    msg({ type: "snapshot", match });
    expect(out.snapshot?.id).toBe("m1");
    expect(out.status).toBe("LOBBY");
  });
  it("dedupes player_joined by id", () => {
    msg({ type: "snapshot", match });
    const p = { type: "player_joined", team: "inter", player: { id: "p1", name: "A" } };
    msg(p);
    msg(p);
    expect(out.snapshot?.roster.inter).toHaveLength(1);
  });
  it("tick updates rope and scores", () => {
    msg({ type: "snapshot", match });
    msg({ type: "tick", rope: -5, remainingS: 50, delta: { inter: 1, gremio: 0 }, scores: { inter: { pulls: 3 }, gremio: { pulls: 1 } } });
    expect(out.snapshot?.rope).toBe(-5);
    expect(out.snapshot?.scores.inter.pulls).toBe(3);
    expect(out.lastTick?.remainingS).toBe(50);
  });
  it("reconnects with backoff on unexpected close", () => {
    close();
    expect(out.connected).toBe(false);
    expect(MockWS.all).toHaveLength(1);
    act(() => void vi.advanceTimersByTime(1000));
    expect(MockWS.all).toHaveLength(2);
  });
  it("1008 reports auth error and does not reconnect", () => {
    close(1008);
    act(() => void vi.advanceTimersByTime(10000));
    expect(out.authError).toBe(true);
    expect(MockWS.all).toHaveLength(1);
  });
  it.each([
    [{ type: "ended", result: "DRAW", endReason: "timeout", finalRope: 0, analytics: { totalPlayers: 0 } }],
    [{ type: "cancelled" }],
    [{ type: "reset", newMatchId: "m2" }],
  ])("%j is terminal: no reconnect", (m) => {
    msg(m);
    close();
    act(() => void vi.advanceTimersByTime(10000));
    expect(MockWS.all).toHaveLength(1);
    if (m.type === "ended") expect(out.ended?.result).toBe("DRAW");
    else expect(out.terminal?.type).toBe(m.type);
  });
});
