import { beforeEach, describe, expect, it } from "vitest";
import { getDeviceId } from "./useDeviceId";

describe("getDeviceId", () => {
  beforeEach(() => localStorage.clear());

  it("returns a UUID and persists it in localStorage", () => {
    const id = getDeviceId();
    expect(id).toMatch(/^[0-9a-f-]{36}$/);
    expect(localStorage.getItem("cb.deviceId")).toBe(id);
  });

  it("is stable across calls", () => {
    expect(getDeviceId()).toBe(getDeviceId());
  });

  it("reuses an id already stored", () => {
    localStorage.setItem("cb.deviceId", "abc");
    expect(getDeviceId()).toBe("abc");
  });
});
