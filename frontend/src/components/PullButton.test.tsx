import { createElement, act } from "react";
import { createRoot } from "react-dom/client";
import { describe, expect, it, vi } from "vitest";
import { PullButton } from "./PullButton";

(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

function setup() {
  const onPull = vi.fn();
  const host = document.createElement("div");
  const root = createRoot(host);
  act(() => root.render(createElement(PullButton, { onPull, color: "red" })));
  const btn = host.querySelector("button")!;
  const fire = (type: string, init: MouseEventInit) => act(() => void btn.dispatchEvent(new MouseEvent(type, { bubbles: true, ...init })));
  return { onPull, fire };
}

describe("PullButton", () => {
  it("counts a pointerdown and its following click once", () => {
    const { onPull, fire } = setup();
    fire("pointerdown", { button: 0 });
    fire("click", { detail: 1 });
    expect(onPull).toHaveBeenCalledTimes(1);
  });
  it("counts keyboard activation (click detail 0) once", () => {
    const { onPull, fire } = setup();
    fire("click", { detail: 0 });
    expect(onPull).toHaveBeenCalledTimes(1);
  });
  it("ignores non-primary buttons", () => {
    const { onPull, fire } = setup();
    fire("pointerdown", { button: 2 });
    expect(onPull).not.toHaveBeenCalled();
  });
});
