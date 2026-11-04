import { defineConfig } from "@playwright/test";

// No webServer block: the stack (backend + Vite, or the Docker stack) must already be running.
export default defineConfig({
  testDir: "./e2e",
  timeout: 120_000,
  reporter: "list",
  use: { baseURL: process.env.E2E_BASE_URL ?? "http://localhost:5173" },
  projects: [{ name: "chromium", use: { browserName: "chromium" } }],
});
