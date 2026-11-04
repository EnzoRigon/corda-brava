import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import ResultBanner from "./ResultBanner";

describe("ResultBanner", () => {
  it("shows a cancelled title when there is no result", () => {
    const html = renderToStaticMarkup(<ResultBanner result={null} endReason={null} />);
    expect(html).toContain("Partida cancelada");
    expect(html).not.toContain("Empate");
  });
  it("still shows a draw", () => {
    expect(renderToStaticMarkup(<ResultBanner result="DRAW" endReason="timeout" />)).toContain("Empate!");
  });
});
