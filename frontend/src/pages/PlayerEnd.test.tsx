import { renderToStaticMarkup } from "react-dom/server";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import PlayerEnd from "./PlayerEnd";

const state = vi.hoisted(() => ({ me: null as unknown }));
vi.mock("../hooks/useMePolling", () => ({
  useMePolling: () => ({ session: { team: "inter" }, me: state.me }),
}));

const render = () => renderToStaticMarkup(<MemoryRouter><PlayerEnd /></MemoryRouter>);

describe("PlayerEnd", () => {
  it("titles a cancelled match", () => {
    state.me = { screen: "end", result: null };
    expect(render()).toContain("Partida cancelada");
  });
  it("keeps the normal result titles", () => {
    state.me = { screen: "end", result: "INTER" };
    expect(render()).toContain("Seu time venceu!");
  });
});
