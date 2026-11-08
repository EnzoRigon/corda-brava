import { createElement, act } from "react";
import { createRoot } from "react-dom/client";
import { expect, it, vi } from "vitest";
import { PlayAgain } from "./PlayAgain";

(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
const key = (k: string) => act(async () => void window.dispatchEvent(new KeyboardEvent("keydown", { key: k })));
const selected = (h: HTMLElement) => h.querySelector("[data-selected=true] button")?.textContent;

it("arrows move the selection, Enter confirms it", async () => {
  const [yes, no] = [vi.fn(), vi.fn()];
  const host = document.createElement("div");
  document.body.append(host);
  await act(async () => createRoot(host).render(createElement(PlayAgain, { onYes: yes, onNo: no })));
  expect(selected(host)).toBe("SIM");
  await key("ArrowRight");
  expect(selected(host)).toBe("NÃO");
  document.body.focus();
  (document.activeElement as HTMLElement | null)?.blur();
  await key("Enter");
  expect(no).toHaveBeenCalledTimes(1);
  expect(yes).not.toHaveBeenCalled();
  await key("ArrowLeft");
  expect(selected(host)).toBe("SIM");
});
