import { test, expect } from "@playwright/test";

const wait = (ms: number) => new Promise((r) => setTimeout(r, ms));

test.describe("StoreSignal demo walkthrough", () => {
  test.setTimeout(240_000);

  test("full auto walkthrough", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await wait(3500);
    await page.mouse.wheel(0, 600);
    await wait(2500);
    await page.mouse.wheel(0, 600);
    await wait(2000);

    await page.goto("/overview");
    await page.waitForLoadState("networkidle");
    await wait(4000);
    await page.mouse.wheel(0, 400);
    await wait(2500);

    await page.goto("/alerts");
    await page.waitForLoadState("networkidle");
    await wait(2500);
    const mandatoryFilter = page.getByRole("button", { name: /mandatory|policy/i }).first();
    if (await mandatoryFilter.count()) {
      await mandatoryFilter.click().catch(() => {});
      await wait(2500);
    }
    await page.mouse.wheel(0, 300);
    await wait(3000);

    await page.goto("/incidents");
    await page.waitForLoadState("networkidle");
    await wait(2500);
    const firstInc = page.locator("a").filter({ hasText: /^INC-/ }).first();
    if (await firstInc.count()) {
      await firstInc.click();
      await page.waitForLoadState("networkidle");
      await wait(3000);
      const evTab = page.getByRole("tab", { name: "Evidence" });
      if (await evTab.count()) {
        await evTab.click().catch(() => {});
        await wait(2500);
      }
      const tlTab = page.getByRole("tab", { name: "Timeline" });
      if (await tlTab.count()) {
        await tlTab.click().catch(() => {});
        await wait(2000);
      }
    }

    await page.goto("/trends");
    await page.waitForLoadState("networkidle");
    await wait(4000);

    await page.goto("/stores/map");
    await page.waitForLoadState("networkidle");
    await wait(5000);
    await page.mouse.wheel(0, -300);
    await wait(2000);
    await page.mouse.wheel(0, -200);
    await wait(2000);

    await page.goto("/reports");
    await page.waitForLoadState("networkidle");
    await wait(4000);
    await page.mouse.wheel(0, 500);
    await wait(2500);

    await page.goto("/audit");
    await page.waitForLoadState("networkidle");
    await wait(3000);

    await page.goto("/data-health");
    await page.waitForLoadState("networkidle");
    await wait(2500);
    await page.mouse.wheel(0, 400);
    await wait(2500);

    await page.goto("/overview");
    await page.waitForLoadState("networkidle");
    await wait(3000);
  });
});
