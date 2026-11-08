import { expect, it } from "vitest";
import { emptyFeed, FEED_MAX, isFinalSeconds, leadChange, pushEvents } from "./matchFx";

const ev = (playerId: string, team: "inter" | "gremio", count = 1) => ({ playerId, name: playerId.toUpperCase(), team, count });

it("feed keeps newest first and last N per team", () => {
  let f = emptyFeed();
  for (let i = 0; i < 9; i++) f = pushEvents(f, [ev(`p${i}`, "inter")], i * 10_000);
  expect(f.inter).toHaveLength(FEED_MAX);
  expect(f.inter[0].playerId).toBe("p8");
  expect(f.gremio).toHaveLength(0);
});

it("feed merges the same player inside the window and moves it to the top", () => {
  let f = pushEvents(emptyFeed(), [ev("a", "gremio", 3), ev("b", "gremio", 2)], 0);
  f = pushEvents(f, [ev("a", "gremio", 4)], 100);
  expect(f.gremio.map((e) => [e.playerId, e.count])).toEqual([["a", 7], ["b", 2]]);
  f = pushEvents(f, [ev("a", "gremio", 1)], 10_000); // outside window: new entry
  expect(f.gremio.filter((e) => e.playerId === "a")).toHaveLength(2);
});

it("lead change fires only on a real flip outside the dead-band", () => {
  expect(leadChange(null, -10, 2)).toEqual({ lead: "inter", changed: false });
  expect(leadChange("inter", 1, 2)).toEqual({ lead: "inter", changed: false });
  expect(leadChange("inter", 5, 2)).toEqual({ lead: "gremio", changed: true });
  expect(leadChange("gremio", -5, 2)).toEqual({ lead: "inter", changed: true });
});

it("final seconds window", () => {
  expect(isFinalSeconds(10)).toBe(true);
  expect(isFinalSeconds(10.5)).toBe(false);
  expect(isFinalSeconds(0)).toBe(false);
});
