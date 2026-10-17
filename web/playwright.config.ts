import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  fullyParallel: false,
  reporter: "list",
  use: {
    baseURL: "http://localhost:3300",
    trace: "retain-on-failure",
    viewport: { width: 1920, height: 1080 },
    video: process.env.RECORD_DEMO
      ? { mode: "on", size: { width: 1920, height: 1080 } }
      : "retain-on-failure",
  },
});
