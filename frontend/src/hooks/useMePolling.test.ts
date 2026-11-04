import { createElement, act } from "react";
import { createRoot } from "react-dom/client";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "../api/client";
import * as api from "../api/playerApi";
import { useMePolling } from "./useMePolling";

(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

const getMe = vi.spyOn(api, "getMe");
let loc: string;
let unmount: () => void;

function Waiting() {
  useMePolling("m1", "wait");
  loc = useLocation().pathname;
  return null;
}
function Other() {
  loc = useLocation().pathname;
  return null;
}
const tick = (ms = 1000) => act(async () => { await vi.advanceTimersByTimeAsync(ms); });

beforeEach(async () => {
  vi.useFakeTimers();
  localStorage.setItem("cb.session.m1", JSON.stringify({ playerId: "p", playerToken: "t", team: "inter" }));
  getMe.mockReset().mockResolvedValue({ screen: "wait", team: "inter", matchStatus: "LOBBY" });
  const root = createRoot(document.createElement("div"));
  await act(async () =>
    root.render(
      createElement(
        MemoryRouter,
        { initialEntries: ["/j/m1/wait"] },
        createElement(
          Routes,
          null,
          createElement(Route, { path: "/j/:id/wait", element: createElement(Waiting) }),
          createElement(Route, { path: "*", element: createElement(Other) }),
        ),
      ),
    ),
  );
  unmount = () => act(() => root.unmount());
});
afterEach(() => {
  unmount();
  vi.useRealTimers();
});

describe("useMePolling", () => {
  it("polls with the stored token and navigates when the screen changes", async () => {
    expect(getMe).toHaveBeenCalledWith("m1", "p", "t");
    expect(loc).toBe("/j/m1/wait");
    getMe.mockResolvedValue({ screen: "play", team: "inter", matchStatus: "RUNNING" });
    await tick();
    expect(loc).toBe("/j/m1/play");
  });

  it("returns to join and clears the session on 401", async () => {
    getMe.mockRejectedValue(new ApiError(401, "x"));
    await tick();
    expect(loc).toBe("/j/m1");
    expect(localStorage.getItem("cb.session.m1")).toBeNull();
  });

  it("stops polling on unmount", async () => {
    unmount();
    const n = getMe.mock.calls.length;
    await tick(3000);
    expect(getMe.mock.calls.length).toBe(n);
    unmount = () => {};
  });
});
