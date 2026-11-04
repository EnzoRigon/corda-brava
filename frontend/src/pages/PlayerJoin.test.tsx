import { createElement, act } from "react";
import { createRoot } from "react-dom/client";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "../api/client";
import * as api from "../api/playerApi";
import PlayerJoin from "./PlayerJoin";

(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

const getPublic = vi.spyOn(api, "getPublic");
const join = vi.spyOn(api, "join");
const colors = { primary: "#000", secondary: "#fff" };

function Where() {
  return createElement("div", { "data-testid": "loc" }, useLocation().pathname);
}
let host: HTMLDivElement;
let unmount: () => void;

async function mount() {
  host = document.createElement("div");
  document.body.append(host);
  const root = createRoot(host);
  await act(async () =>
    root.render(
      createElement(
        MemoryRouter,
        { initialEntries: ["/j/m1"] },
        createElement(
          Routes,
          null,
          createElement(Route, { path: "/j/:id", element: createElement(PlayerJoin) }),
          createElement(Route, { path: "*", element: createElement(Where) }),
        ),
      ),
    ),
  );
  unmount = () => act(() => root.unmount());
}
const type = (el: HTMLInputElement, v: string) =>
  act(() => {
    Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value")!.set!.call(el, v);
    el.dispatchEvent(new Event("input", { bubbles: true }));
  });
const click = (el: Element) => act(async () => el.dispatchEvent(new MouseEvent("click", { bubbles: true })));
const byText = (t: string) => [...host.querySelectorAll("button")].find((b) => b.textContent?.includes(t))!;

beforeEach(() => {
  localStorage.clear();
  getPublic.mockReset().mockResolvedValue({
    status: "LOBBY",
    teams: { inter: { name: "Inter", colors }, gremio: { name: "Grêmio", colors } },
    counts: { inter: 2, gremio: 3 },
    durationS: 60,
  });
  join.mockReset();
});
afterEach(() => {
  unmount();
  host.remove();
});

describe("PlayerJoin", () => {
  it("renders PT-BR name input and team options", async () => {
    await mount();
    expect(host.textContent).toContain("Seu nome");
    expect(host.textContent).toContain("Inter");
    expect(host.textContent).toContain("Grêmio");
    expect(host.textContent).toContain("3 jogadores");
    expect(host.querySelector("input")).toBeTruthy();
  });

  it("joins with deviceId, stores the session and goes to wait", async () => {
    join.mockResolvedValue({ playerId: "p1", playerToken: "tok", team: "gremio" });
    await mount();
    type(host.querySelector("input")!, "  Ana  ");
    await click(byText("Grêmio"));
    await click(byText("Entrar"));
    expect(join).toHaveBeenCalledWith("m1", { name: "Ana", team: "gremio", deviceId: expect.any(String) });
    expect(host.querySelector("[data-testid=loc]")!.textContent).toBe("/j/m1/wait");
    expect(JSON.parse(localStorage.getItem("cb.session.m1")!)).toEqual({ playerId: "p1", playerToken: "tok", team: "gremio" });
  });

  it("shows the API detail on 409", async () => {
    join.mockRejectedValue(new ApiError(409, "A partida já começou"));
    await mount();
    type(host.querySelector("input")!, "Ana");
    await click(byText("Inter"));
    await click(byText("Entrar"));
    expect(host.querySelector("[role=alert]")!.textContent).toBe("A partida já começou");
  });

  it("requires a name", async () => {
    await mount();
    await click(byText("Inter"));
    await click(byText("Entrar"));
    expect(join).not.toHaveBeenCalled();
    expect(host.querySelector("[role=alert]")!.textContent).toBe("Digite seu nome.");
  });

  it("skips the form when a session is stored", async () => {
    localStorage.setItem("cb.session.m1", JSON.stringify({ playerId: "p", playerToken: "t", team: "inter" }));
    await mount();
    expect(host.querySelector("[data-testid=loc]")!.textContent).toBe("/j/m1/wait");
  });
});
