import { createElement, act } from "react";
import { createRoot } from "react-dom/client";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, expect, it, vi } from "vitest";
import * as sock from "../hooks/useHostSocket";
import HostLobby from "./HostLobby";

(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

beforeEach(() => {
  document.body.innerHTML = "";
  sessionStorage.setItem("cb.hostToken", "T");
});

it("QR overlay shows the snapshot joinUrl", async () => {
  const match = { id: "m1", status: "LOBBY", roster: { inter: [], gremio: [] }, joinUrl: "http://lan:5173/j/m1" };
  vi.spyOn(sock, "useHostSocket").mockReturnValue({
    status: "LOBBY", snapshot: match as never, lastTick: null, ended: null, terminal: null, connected: true, authError: false,
  });
  const host = document.createElement("div");
  document.body.append(host);
  await act(async () =>
    createRoot(host).render(
      createElement(
        MemoryRouter,
        { initialEntries: ["/host/lobby/m1"] },
        createElement(Routes, null, createElement(Route, { path: "/host/lobby/:id", element: createElement(HostLobby) })),
      ),
    ),
  );
  expect(host.querySelector(".join-url")?.textContent).toBe("http://lan:5173/j/m1");
  await act(async () => host.querySelector<HTMLButtonElement>(".qr-btn")!.click());
  expect(host.querySelector(".qr-overlay")?.textContent).toContain("http://lan:5173/j/m1");
});
