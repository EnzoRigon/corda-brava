import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { Crest } from "./Crest";
import { Mascot } from "./Mascot";

const src = (el: React.ReactElement) => /src="([^"]*)"/.exec(renderToStaticMarkup(el))![1];

describe("Mascot/Crest", () => {
  it("inter straining uses saci_pull", () => {
    expect(src(<Mascot team="inter" state="straining" />)).toContain("saci_pull");
  });
  it("gremio happy uses mosq_happy and is mirrored", () => {
    const html = renderToStaticMarkup(<Mascot team="gremio" state="happy" />);
    expect(html).toContain("mosq_happy");
    expect(html).toContain("scaleX(-1)");
  });
  it("inter losing uses saci_defeat", () => {
    expect(src(<Mascot team="inter" state="losing" />)).toContain("saci_defeat");
  });
  it("crest renders gremio png", () => {
    expect(src(<Crest team="gremio" />)).toContain("gremio");
  });
});
