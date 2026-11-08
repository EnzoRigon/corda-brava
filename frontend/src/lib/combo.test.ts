import { beforeEach, describe, expect, it } from "vitest";
import { comboLevel, decayCombo, tapCombo } from "./combo";
import { loadPulls, savePulls } from "./localPulls";

describe("combo", () => {
  it("builds with taps, caps at 1 and shows levels 1..10", () => {
    let m = 0;
    expect(comboLevel(m)).toBe(0);
    for (let i = 0; i < 30; i++) m = tapCombo(m);
    expect(m).toBe(1);
    expect(comboLevel(m)).toBe(10);
    expect(comboLevel(tapCombo(0))).toBe(0); // one tap is not a combo yet
    expect(comboLevel(tapCombo(tapCombo(0)))).toBe(2);
  });
  it("decays to zero when tapping stops", () => {
    expect(decayCombo(1, 1000)).toBeCloseTo(0.6);
    expect(decayCombo(0.2, 10_000)).toBe(0);
  });
  it("a steady 6 taps/s climbs, 2 taps/s fades", () => {
    const run = (tps: number) => {
      let m = 0.5;
      for (let i = 0; i < tps * 5; i++) m = decayCombo(tapCombo(m), 1000 / tps);
      return m;
    };
    expect(run(6)).toBeGreaterThan(0.9);
    expect(run(2)).toBe(0);
  });
});

describe("localPulls", () => {
  beforeEach(() => localStorage.clear());
  it("round-trips per match", () => {
    expect(loadPulls("m1")).toBe(0);
    savePulls("m1", 42);
    expect(loadPulls("m1")).toBe(42);
    expect(loadPulls("m2")).toBe(0);
  });
});
