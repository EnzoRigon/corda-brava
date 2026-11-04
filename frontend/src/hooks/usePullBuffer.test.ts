import { createElement } from "react";
import { createRoot } from "react-dom/client";
import { act } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "../api/client";
import * as api from "../api/playerApi";
import { MAX_PULLS_PER_BATCH, usePullBuffer } from "./usePullBuffer";

(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

let hook: ReturnType<typeof usePullBuffer>;
let unmount: () => void;
const send = vi.spyOn(api, "sendPulls");

function Probe() {
  hook = usePullBuffer({ matchId: "m", playerId: "p", playerToken: "t", flushIntervalMs: 500 });
  return null;
}
const tap = (n: number) => act(() => { for (let i = 0; i < n; i++) hook.tap(); });
const tick = () => act(async () => { await vi.advanceTimersByTimeAsync(500); });

beforeEach(() => {
  vi.useFakeTimers();
  send.mockReset().mockResolvedValue({ accepted: 1 });
  const root = createRoot(document.createElement("div"));
  act(() => root.render(createElement(Probe)));
  unmount = () => act(() => root.unmount());
});
afterEach(() => {
  unmount();
  vi.useRealTimers();
  Object.defineProperty(document, "visibilityState", { value: "visible", configurable: true });
});

describe("usePullBuffer", () => {
  it("shows taps instantly and posts one batch per interval", async () => {
    tap(5);
    expect(hook.displayCount).toBe(5);
    expect(send).not.toHaveBeenCalled();
    await tick();
    expect(send).toHaveBeenCalledTimes(1);
    const b = send.mock.calls[0][1];
    expect(b.count).toBe(5);
    expect(b.batchId).toBeTruthy();
    await tick();
    expect(send).toHaveBeenCalledTimes(1); // 2xx cleared it
  });

  it("still posts with a batchId when crypto.randomUUID is missing (http LAN)", async () => {
    vi.stubGlobal("crypto", {});
    tap(2);
    await tick();
    vi.unstubAllGlobals();
    expect(send).toHaveBeenCalledTimes(1);
    expect(send.mock.calls[0][1].batchId).toMatch(/^[0-9a-f-]{36}$/);
  });

  it("resends the same batchId after failure, then uses a new id", async () => {
    send.mockRejectedValueOnce(new Error("net"));
    tap(3);
    await tick();
    tap(2);
    await tick();
    const [a, b] = [send.mock.calls[0][1], send.mock.calls[1][1]];
    expect(b.batchId).toBe(a.batchId);
    expect(b.count).toBe(3);
    await tick();
    const c = send.mock.calls[2][1];
    expect(c.count).toBe(2);
    expect(c.batchId).not.toBe(a.batchId);
  });

  it("retries on 5xx", async () => {
    send.mockRejectedValueOnce(new ApiError(503, "x"));
    tap(1);
    await tick();
    await tick();
    expect(send).toHaveBeenCalledTimes(2);
  });

  it("clamps batches and carries the excess over", async () => {
    tap(MAX_PULLS_PER_BATCH + 7);
    await tick();
    expect(send.mock.calls[0][1].count).toBe(MAX_PULLS_PER_BATCH);
    await tick();
    expect(send.mock.calls[1][1].count).toBe(7);
  });

  it("drops the batch on 409", async () => {
    send.mockRejectedValueOnce(new ApiError(409, "x"));
    tap(4);
    await tick();
    await tick();
    expect(send).toHaveBeenCalledTimes(1);
  });

  const hide = () => {
    Object.defineProperty(document, "visibilityState", { value: "hidden", configurable: true });
    document.dispatchEvent(new Event("visibilitychange"));
  };
  const mockBeacon = () => {
    const beacon = vi.fn().mockReturnValue(true);
    Object.defineProperty(navigator, "sendBeacon", { value: beacon, configurable: true });
    return beacon;
  };

  it("uses sendBeacon when hidden, with a JSON blob body", async () => {
    const beacon = mockBeacon();
    tap(2);
    hide();
    expect(beacon).toHaveBeenCalledTimes(1);
    expect(beacon.mock.calls[0][0]).toBe("/api/matches/m/pulls");
    const blob = beacon.mock.calls[0][1] as Blob;
    expect(blob.type).toBe("application/json");
    const body = JSON.parse(await blob.text());
    expect(Object.keys(body).sort()).toEqual(["batchId", "clientTs", "count", "playerId", "playerToken"]);
    expect(body.count).toBe(2);
  });

  it("resends the beaconed batchId on the next interval", async () => {
    const beacon = mockBeacon();
    tap(2);
    hide();
    const sent = JSON.parse(await (beacon.mock.calls[0][1] as Blob).text());
    await tick();
    expect(send.mock.calls[0][1].batchId).toBe(sent.batchId);
    expect(send.mock.calls[0][1].count).toBe(2);
  });

  it("does not start a second POST while one is in flight", async () => {
    let done!: () => void;
    send.mockReturnValueOnce(new Promise((r) => { done = () => r({ accepted: 1 }); }));
    tap(1);
    await tick();
    tap(1);
    await tick();
    expect(send).toHaveBeenCalledTimes(1);
    done();
    await tick();
    expect(send).toHaveBeenCalledTimes(2);
    expect(send.mock.calls[1][1].count).toBe(1);
  });

  it("drops a 422 batch and sends later taps as a new batch", async () => {
    send.mockRejectedValueOnce(new ApiError(422, "x"));
    tap(3);
    await tick();
    tap(2);
    await tick();
    expect(send).toHaveBeenCalledTimes(2);
    expect(send.mock.calls[1][1].count).toBe(2);
    expect(send.mock.calls[1][1].batchId).not.toBe(send.mock.calls[0][1].batchId);
  });

  it("stops sending after 409 but keeps counting taps", async () => {
    send.mockRejectedValueOnce(new ApiError(409, "x"));
    tap(4);
    await tick();
    tap(2);
    await tick();
    hide();
    await tick();
    expect(send).toHaveBeenCalledTimes(1);
    expect(hook.displayCount).toBe(6);
  });
});
