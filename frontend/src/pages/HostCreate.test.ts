import { expect, it } from "vitest";
import { fmtDuration, stepDuration } from "./HostCreate";

it("steps by 30s inside 30..600", () => {
  expect(stepDuration(120, 1)).toBe(150);
  expect(stepDuration(120, -1)).toBe(90);
  expect(stepDuration(30, -1)).toBe(30);
  expect(stepDuration(600, 1)).toBe(600);
  expect(stepDuration(590, 1)).toBe(600);
});
it("formats m:ss", () => {
  expect(fmtDuration(90)).toBe("1:30");
  expect(fmtDuration(600)).toBe("10:00");
});
