import { defineConfig, devices } from "@playwright/test";
import path from "node:path";
import fs from "node:fs";
const localPython = path.resolve("../.venv/Scripts/python.exe");
const python = fs.existsSync(localPython) ? `"${localPython}"` : "python";
export default defineConfig({
  testDir: "./tests",
  expect: { timeout: 20000 },
  timeout: 60000,
  fullyParallel: false,
  workers: 1,
  use: { baseURL: "http://127.0.0.1:3100", trace: "retain-on-failure" },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"] } },
    {
      name: "mobile",
      use: { ...devices["iPhone 13"], defaultBrowserType: "chromium" },
    },
  ],
  webServer: [
    {
      command: `${python} -m uvicorn app.main:app --host 127.0.0.1 --port 8000`,
      cwd: "..",
      env: {
        PYTHONPATH: "backend",
        DEMO_MODE: "true",
        GENERATION_PROVIDER: "demo",
        EMBEDDING_PROVIDER: "demo",
        CORPUS_VERSION: "v1",
      },
      url: "http://127.0.0.1:8000/api/v1/ready",
      reuseExistingServer: !process.env.CI,
      timeout: 60000,
    },
    {
      command: "npm run dev -- -p 3100",
      env: { NEXT_DIST_DIR: ".next-e2e" },
      url: "http://127.0.0.1:3100",
      reuseExistingServer: !process.env.CI,
      timeout: 120000,
    },
  ],
});
