import { createElement, act } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, expect, it, vi } from "vitest";
import { useCountdown } from "./useCountdown";

(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
afterEach(() => vi.useRealTimers());

function C({ s }: { s: number }) {
  return createElement("span", null, useCountdown(s).toFixed(1));
}

it("counts down between ticks and clamps at 0", async () => {
  vi.useFakeTimers();
  const host = document.createElement("div");
  const root = createRoot(host);
  await act(async () => root.render(createElement(C, { s: 10 })));
  expect(host.textContent).toBe("10.0");
  await act(async () => void vi.advanceTimersByTime(2000));
  expect(host.textContent).toBe("8.0");
  await act(async () => void vi.advanceTimersByTime(20000));
  expect(host.textContent).toBe("0.0");
});
