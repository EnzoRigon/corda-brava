// Drives a real match against the running dev stack and saves PNG frames for the README GIF.
// Usage: node scripts/record-readme-gif.mjs [framesDir]   (then assemble with Pillow)
import { chromium } from "@playwright/test";
import { mkdirSync } from "node:fs";
import { join } from "node:path";

const BASE = process.env.E2E_BASE_URL ?? "http://localhost:5173";
const PASSWORD = process.env.E2E_HOST_PASSWORD ?? "Inter>Gremio";
const FRAMES = process.argv[2] ?? "frames";
mkdirSync(FRAMES, { recursive: true });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const post = async (path, body, token) => {
  const r = await fetch(BASE + path, {
    method: "POST",
    headers: { "content-type": "application/json", ...(token && { authorization: `Bearer ${token}` }) },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!r.ok) throw new Error(`${path} -> ${r.status} ${await r.text()}`);
  return r.status === 204 ? null : r.json();
};

const { token } = await post("/api/host/login", { password: PASSWORD });
const { matchId } = await post("/api/host/matches", { durationS: 30 }, token);
const players = [];
for (const [name, team] of [["Gabi", "inter"], ["Rafa", "inter"], ["Duda", "gremio"], ["Lucas", "gremio"]]) {
  const p = await post(`/api/matches/${matchId}/players`, { name, team, deviceId: `readme-${name}` });
  players.push({ ...p, name });
}

const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 1280, height: 720 } });
const page = await ctx.newPage();
try {
  await page.goto(`${BASE}/host`);
  await page.evaluate((t) => sessionStorage.setItem("cb.hostToken", t), token);
  await post(`/api/host/matches/${matchId}/start`, null, token);
  await page.goto(`${BASE}/host/match/${matchId}`);
  await sleep(1000);

  // Pull loop: teams alternate dominance so the rope swings both ways (cap: 25 per 500 ms tick per player).
  let stop = false;
  let n = 0;
  const puller = (async () => {
    const t0 = Date.now();
    while (!stop) {
      const phase = Math.sin(((Date.now() - t0) / 1000) * 0.8);
      for (const p of players) {
        const mine = p.team === "inter" ? -phase : phase;
        const count = Math.max(1, Math.round(3 + mine * 2.5 + Math.random() * 2)); // small swings so the match lasts the whole clip
        post(`/api/matches/${matchId}/pulls`, {
          playerId: p.playerId, playerToken: p.playerToken, count,
          clientTs: Date.now() / 1000, batchId: `${p.playerId}-${n++}`,
        }).catch(() => {});
      }
      await sleep(250);
    }
  })();

  for (let i = 0; i < 56; i++) {
    await page.screenshot({ path: join(FRAMES, `f${String(i).padStart(3, "0")}.png`) });
    await sleep(150);
  }
  stop = true;
  await puller;
} finally {
  await post(`/api/host/matches/${matchId}/cancel`, null, token).catch(() => {});
  await browser.close();
}
console.log("done", matchId);
