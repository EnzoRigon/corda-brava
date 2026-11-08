import { renderToStaticMarkup } from "react-dom/server";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import PlayerEnd from "./PlayerEnd";

const state = vi.hoisted(() => ({ me: null as unknown }));
vi.mock("../hooks/useMePolling", () => ({
  useMePolling: () => ({ session: { team: "inter" }, me: state.me }),
}));

const render = (result: string | null) => {
  state.me = { screen: "end", result };
  return renderToStaticMarkup(<MemoryRouter><PlayerEnd /></MemoryRouter>);
};

describe("PlayerEnd", () => {
  it("titles a cancelled match, without a pull count", () => {
    localStorage.setItem("cb.pulls.", "9");
    const html = render(null);
    expect(html).toContain("Partida cancelada");
    expect(html).not.toContain("Você puxou");
    expect(html).toContain("Obrigado por jogar!");
  });
  it("win: banner and confetti", () => {
    const html = render("INTER");
    expect(html).toContain("VITÓRIA!");
    expect(html).toContain("confetti");
  });
  it("lose: dimmed scene", () => {
    const html = render("GREMIO");
    expect(html).toContain("DERROTA…");
    expect(html).toContain("end-dim");
    expect(html).not.toContain("confetti");
  });
  it("draw", () => {
    expect(render("DRAW")).toContain("EMPATE!");
  });
  it("shows the local pull count", () => {
    localStorage.setItem("cb.pulls.", "17");
    expect(render("INTER")).toContain("Você puxou 17 vezes!");
  });
});
