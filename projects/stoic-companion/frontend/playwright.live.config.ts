import { defineConfig, devices } from "@playwright/test";
export default defineConfig({
  testDir: ".",
  testMatch: "live.acceptance.ts",
  timeout: 180000,
  expect: { timeout: 90000 },
  workers: 1,
  use: {
    ...devices["Desktop Chrome"],
    baseURL: process.env.LIVE_BASE_URL || "http://127.0.0.1:3001",
    trace: "retain-on-failure",
  },
  outputDir: "test-results-live",
});
