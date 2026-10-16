import { test, expect } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

const oidcOn = fs.existsSync(path.join(__dirname, "..", ".oidc-enabled"));
test.skip(!oidcOn, "OIDC disabled — remove .oidc-enabled to enable");

// Only run when AUTH_OIDC_ISSUER is set. Requires Keycloak on :8180.

const KC_USER = process.env.KC_TEST_USER || "admin";
const KC_PASS = process.env.KC_TEST_PASS || "password";

test("unauthenticated /overview redirects to /login", async ({ page }) => {
  await page.goto("/overview");
  await expect(page).toHaveURL(/\/login/);
  await expect(page.getByText("Sign in to continue")).toBeVisible();
});

test("full login -> overview -> sign out", async ({ page }) => {
  await page.goto("/overview");
  await expect(page).toHaveURL(/\/login/);

  // Click the SSO button -> redirects to Keycloak
  await page.getByRole("button", { name: /Sign in with SSO/i }).click();
  await page.waitForURL(/localhost:8180/);

  // Keycloak login form
  await page.screenshot({ path: "test-results/keycloak-before-fill.png" });
  await page.waitForSelector('input[name="username"], #username', { timeout: 15000 });
  await page.fill('input[name="username"], #username', KC_USER);
  await page.fill('input[name="password"], #password', KC_PASS);
  await page.click('input[name="login"], #kc-login');

  // Back to app, authenticated
  await page.waitForURL(/localhost:3300/);
  await expect(page).toHaveURL(/\/overview/);

  // Session cookie works — backend reachable through proxy
  await expect(page.getByText("Key metrics")).toBeVisible({ timeout: 15_000 });
});

test("authenticated user reaches incidents with real data", async ({ page }) => {
  // log in
  await page.goto("/login");
  await page.getByRole("button", { name: /Sign in with SSO/i }).click();
  await page.waitForURL(/localhost:8180/);
  await page.screenshot({ path: "test-results/keycloak-before-fill.png" });
  await page.waitForSelector('input[name="username"], #username', { timeout: 15000 });
  await page.fill('input[name="username"], #username', KC_USER);
  await page.fill('input[name="password"], #password', KC_PASS);
  await page.click('input[name="login"], #kc-login');
  await page.waitForURL(/localhost:3300/, { timeout: 20000 }).catch(async () => {
    await page.screenshot({ path: "test-results/kc-after-login.png", fullPage: true });
    console.log("AFTER LOGIN URL:", page.url());
    throw new Error("did not return to app; url=" + page.url());
  });

  // navigate
  await page.goto("/incidents");
  await expect(page.getByText("Incidents", { exact: true }).first()).toBeVisible({ timeout: 15_000 });
  await expect(page.locator("ul li a").first()).toBeVisible({ timeout: 15_000 });
});
