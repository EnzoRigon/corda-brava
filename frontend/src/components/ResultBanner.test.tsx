import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import ResultBanner from "./ResultBanner";

const html = (r: Parameters<typeof ResultBanner>[0]["result"], e: Parameters<typeof ResultBanner>[0]["endReason"]) =>
  renderToStaticMarkup(<ResultBanner result={r} endReason={e} />);

describe("ResultBanner", () => {
  it("shows a cancelled title when there is no result", () => {
    const h = html(null, null);
    expect(h).toContain("PARTIDA CANCELADA");
    expect(h).not.toContain("EMPATE");
  });
  it("result line per case", () => {
    expect(html("INTER", "win")).toContain("INTER VENCEU!");
    expect(html("GREMIO", "win")).toContain("GRÊMIO VENCEU!");
    expect(html("DRAW", "timeout")).toContain("EMPATE!");
  });
  it("end reason subtitle", () => {
    expect(html("INTER", "win")).toContain("Corda puxada até o fim!");
    expect(html("DRAW", "timeout")).toContain("O tempo acabou!");
  });
});
