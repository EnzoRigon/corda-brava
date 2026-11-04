import { createElement, act } from "react";
import { createRoot } from "react-dom/client";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "../api/client";
import * as api from "../api/hostApi";
import HostLogin, { HOST_TOKEN_KEY } from "./HostLogin";

(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
const login = vi.spyOn(api, "login");
const Where = () => createElement("div", { "data-testid": "loc" }, useLocation().pathname);
let host: HTMLDivElement;

async function mount() {
  host = document.createElement("div");
  document.body.append(host);
  await act(async () =>
    createRoot(host).render(
      createElement(
        MemoryRouter,
        { initialEntries: ["/host/login"] },
        createElement(
          Routes,
          null,
          createElement(Route, { path: "/host/login", element: createElement(HostLogin) }),
          createElement(Route, { path: "*", element: createElement(Where) }),
        ),
      ),
    ),
  );
}
async function submit(pw: string) {
  const input = host.querySelector("input")!;
  act(() => {
    Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value")!.set!.call(input, pw);
    input.dispatchEvent(new Event("input", { bubbles: true }));
  });
  await act(async () => host.querySelector("form")!.dispatchEvent(new Event("submit", { bubbles: true, cancelable: true })));
}
beforeEach(() => {
  document.body.innerHTML = "";
  sessionStorage.clear();
  login.mockReset();
});

describe("HostLogin", () => {
  it("stores token and navigates to create", async () => {
    login.mockResolvedValue({ token: "T", expiresAt: "x" });
    await mount();
    await submit("pw");
    expect(login).toHaveBeenCalledWith("pw");
    expect(sessionStorage.getItem(HOST_TOKEN_KEY)).toBe("T");
    expect(host.textContent).toBe("/host/create");
  });
  it("shows API detail on 401", async () => {
    login.mockRejectedValue(new ApiError(401, "Senha incorreta"));
    await mount();
    await submit("bad");
    expect(host.textContent).toContain("Senha incorreta");
    expect(sessionStorage.getItem(HOST_TOKEN_KEY)).toBeNull();
  });
});
