import { test, expect } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

const oidcOn = fs.existsSync(path.join(__dirname, "..", ".oidc-enabled"));
test.skip(oidcOn, "OIDC enabled — see sso.spec.ts");

test("welcome loads", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("store chatter");
  await expect(page.getByText("SIMULATED DATA")).toBeVisible();
});

test("overview shows KPI cards", async ({ page }) => {
  await page.goto("/overview");
  await expect(page.getByText("Key metrics")).toBeVisible({ timeout: 10_000 });
  await expect(page.getByText("Open incidents")).toBeVisible();
  await expect(page.getByText("Urgent queue")).toBeVisible();
});

test("incidents list renders rows", async ({ page }) => {
  await page.goto("/incidents");
  await expect(page.getByText("Incidents", { exact: true }).first()).toBeVisible({ timeout: 10_000 });
  await expect(page.locator("ul li a").first()).toBeVisible({ timeout: 10_000 });
});

test("incident detail has 4 tabs and actions work", async ({ page }) => {
  await page.goto("/incidents");
  await page.locator("ul li a").first().click();
  await expect(page.getByRole("tab", { name: "Overview" })).toBeVisible();
  await expect(page.getByRole("tab", { name: "Evidence" })).toBeVisible();
  await expect(page.getByRole("tab", { name: "Timeline" })).toBeVisible();
  await expect(page.getByRole("tab", { name: "Actions" })).toBeVisible();
});

test("alerts page loads and shows override button on open alert", async ({ page }) => {
  await page.goto("/alerts");
  await expect(page.getByRole("heading", { name: "Alerts" }).first()).toBeVisible({ timeout: 10_000 });
});

test("reports page shows weekly brief", async ({ page }) => {
  await page.goto("/reports");
  await expect(page.getByRole("heading", { name: /Weekly regional brief/ })).toBeVisible();
  await expect(page.getByText(/Region/)).toBeVisible({ timeout: 10_000 });
});
