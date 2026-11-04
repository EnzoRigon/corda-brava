import { expect, test } from "@playwright/test";

const HOST_PASSWORD = process.env.E2E_HOST_PASSWORD ?? "Inter>Gremio";

test("host creates, player joins and pulls, match ends, results shown", async ({ browser }) => {
  const host = await (await browser.newContext()).newPage();
  const player = await (await browser.newContext()).newPage();

  // 1. Host logs in and creates a minimum-duration match.
  await host.goto("/host/login");
  await host.getByLabel("Senha do host").fill(HOST_PASSWORD);
  await host.getByRole("button", { name: "Entrar" }).click();
  await host.getByLabel("Duração (segundos)").fill("30");
  await host.getByRole("button", { name: "Criar partida" }).click();
  await expect(host).toHaveURL(/\/host\/lobby\/[^/]+$/);
  const matchId = host.url().split("/").pop()!;
  await expect(host.locator(".join-url")).toContainText(`/j/${matchId}`);
  const joinPath = new URL((await host.locator(".join-url").innerText()).trim()).pathname;

  // 2. Player joins from a separate context (separate deviceId).
  await player.goto(joinPath);
  await player.getByLabel("Seu nome").fill("Teste E2E");
  await player.getByRole("radio", { name: /Inter/ }).click();
  await player.getByRole("button", { name: "Entrar" }).click();
  await expect(player.getByRole("heading", { name: "Aguardando o host iniciar" })).toBeVisible();

  // 3. Host sees the player and starts.
  await expect(host.locator(".team-roster").first()).toContainText("Teste E2E");
  await host.getByRole("button", { name: "Iniciar partida" }).click();
  await expect(host).toHaveURL(/\/host\/match\//);

  // 4. Player taps PUXAR; the knot moves away from 50%.
  const puxar = player.getByRole("button", { name: "PUXAR" });
  await expect(puxar).toBeVisible();
  const knotLeft = () => host.getByTestId("knot").evaluate((el) => parseFloat((el as HTMLElement).style.left));
  await expect(async () => {
    for (let i = 0; i < 10; i++) await puxar.dispatchEvent("pointerdown", { button: 0 });
    expect(Math.abs((await knotLeft()) - 50)).toBeGreaterThan(1);
  }).toPass({ timeout: 15_000 });

  // 5-6. Match ends (win or the 30 s timeout); both screens show the end state.
  await expect(player.getByText("Obrigado por jogar!")).toBeVisible({ timeout: 60_000 });
  await expect(host).toHaveURL(/\/host\/results\//);
  await expect(host.locator(".result-banner")).toBeVisible();
  await expect(host.getByRole("heading", { name: "Ranking" })).toBeVisible();
  await expect(host.getByText("Teste E2E").first()).toBeVisible();
});
