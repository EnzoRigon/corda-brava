import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const load = async () => {
  vi.resetModules();
  return import("./sfx");
};
const NAMES = ["click", "tap", "join", "countdown", "whistle", "swing", "heartbeat", "win", "draw"] as const;

beforeEach(() => localStorage.clear());
afterEach(() => vi.unstubAllGlobals());

describe("sfx", () => {
  it("persists mute across reloads", async () => {
    const a = await load();
    expect(a.isMuted()).toBe(false);
    a.setMuted(true);
    expect((await load()).isMuted()).toBe(true);
  });

  it("does not throw without AudioContext", async () => {
    const s = await load();
    s.unlock();
    expect(() => NAMES.forEach((n) => s.play(n))).not.toThrow();
  });

  it("is silent when muted and plays when running", async () => {
    const osc = vi.fn(() => ({ type: "", frequency: { setValueAtTime() {}, exponentialRampToValueAtTime() {} }, connect: (n: unknown) => n, start() {}, stop() {} }));
    const node = () => ({ gain: { value: 0, setValueAtTime() {}, linearRampToValueAtTime() {}, exponentialRampToValueAtTime() {} }, connect: (n: unknown) => n });
    vi.stubGlobal("AudioContext", class { state = "running"; currentTime = 0; destination = {}; sampleRate = 8000; createOscillator = osc; createGain = node; resume() {} });
    const s = await load();
    s.unlock();
    s.setMuted(true);
    NAMES.forEach((n) => s.play(n));
    expect(osc).not.toHaveBeenCalled();
    s.setMuted(false);
    s.play("click");
    expect(osc).toHaveBeenCalled();
  });
});
