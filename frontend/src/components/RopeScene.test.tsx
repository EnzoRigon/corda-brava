import { createElement, act } from "react";
import { createRoot } from "react-dom/client";
import { expect, it } from "vitest";
import RopeScene, { knotLeftPercent } from "./RopeScene";

(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

it("knotLeftPercent maps rope to 10..90%", () => {
  expect(knotLeftPercent(-100, 100)).toBeCloseTo(10);
  expect(knotLeftPercent(100, 100)).toBeCloseTo(90);
  expect(knotLeftPercent(0, 100)).toBeCloseTo(50);
});

it.each([[-100, "10%"], [100, "90%"], [0, "50%"]])("renders knot for rope=%i", async (rope, left) => {
  const host = document.createElement("div");
  await act(async () => createRoot(host).render(createElement(RopeScene, { rope, target: 100, interpolate: false })));
  expect(host.querySelector<HTMLElement>("[data-testid=knot]")!.style.left).toBe(left);
});
