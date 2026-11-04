import { createElement, act } from "react";
import { createRoot } from "react-dom/client";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, expect, it, vi } from "vitest";
import HostResults from "./HostResults";
import type { AnalyticsPayload, MatchResult } from "../types/api";

(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
vi.mock("../components/charts/PullsTimeline", () => ({ default: () => null }));
beforeEach(() => {
  document.body.innerHTML = "";
  sessionStorage.setItem("cb.hostToken", "T");
});

const team = { players: 1, totalPulls: 0, avgPullsPerPlayer: 0, bestPlayer: null, worstPlayer: null };
const analytics = (result: MatchResult): AnalyticsPayload => ({
  result, endReason: result === "DRAW" ? "timeout" : "win", durationS: 30, totalPlayers: 2,
  playersPerTeam: { inter: 1, gremio: 1 }, totalPulls: { overall: 0, inter: 0, gremio: 0 },
  pullsPerSecond: [], peak: { value: 0, t: 0 }, finalRope: 0, teams: { inter: team, gremio: team }, players: [], leaderboard: [],
});

async function render(result: MatchResult) {
  const host = document.createElement("div");
  document.body.append(host);
  await act(async () =>
    createRoot(host).render(
      createElement(MemoryRouter, { initialEntries: [{ pathname: "/host/results/m1", state: { analytics: analytics(result) } }] },
        createElement(Routes, null, createElement(Route, { path: "/host/results/:id", element: createElement(HostResults) }))),
    ),
  );
  return host;
}
const srcs = (h: HTMLElement) => [...h.querySelectorAll<HTMLImageElement>(".results-mascots img")].map((i) => i.src);

it("winner happy, loser crying, banner copy", async () => {
  const h = await render("INTER");
  expect(h.querySelector(".result-banner")?.textContent).toContain("Inter venceu");
  const [i, g] = srcs(h);
  expect(i).toMatch(/saci_happy/);
  expect(g).toMatch(/mosq_cry/);
});

it("draw: both idle", async () => {
  const h = await render("DRAW");
  expect(h.querySelector(".result-banner")?.textContent).toContain("Empate");
  expect(srcs(h).map((s) => /master/.test(s))).toEqual([true, true]);
});
