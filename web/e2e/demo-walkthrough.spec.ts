import { test } from "@playwright/test";
import path from "path";

const wait = (ms: number) => new Promise((r) => setTimeout(r, ms));

test.describe("StoreSignal Cinematic Demo", () => {
  test.setTimeout(180_000);

  test("record smooth demo", async ({ page }) => {
    // Inject smooth cursor + CSS scroll-behavior
    await page.addInitScript(() => {
      const style = document.createElement("style");
      style.innerHTML = `
        html, body { scroll-behavior: smooth !important; }
        .custom-cursor {
          position: fixed; width: 22px; height: 22px;
          background: rgba(0,0,0,0.55); border: 2.5px solid white;
          border-radius: 50%; pointer-events: none; z-index: 99999;
          transform: translate(-50%, -50%);
          box-shadow: 0 4px 14px rgba(0,0,0,0.4);
          transition: left 120ms cubic-bezier(0.22,0.61,0.36,1),
                      top 120ms cubic-bezier(0.22,0.61,0.36,1),
                      transform 120ms;
        }
        .custom-cursor.pressed { transform: translate(-50%, -50%) scale(0.85); }
      `;
      document.head.appendChild(style);
      const c = document.createElement("div");
      c.className = "custom-cursor";
      document.body.appendChild(c);
      window.addEventListener("mousemove", (e) => {
        c.style.left = e.clientX + "px";
        c.style.top = e.clientY + "px";
      });
    });

    const scrollTo = async (y: number) => {
      await page.evaluate((vy) => window.scrollTo({ top: vy, behavior: "smooth" }), y);
      await wait(1200);
    };

    const goTo = async (href: string, waitMs = 2000) => {
      // Try clicking sidebar first (smooth Next.js transition)
      const sidebarLink = page.locator(`aside nav a[href="${href}"]`).first();
      if (await sidebarLink.count()) {
        await page.mouse.move(120, 340); // move cursor to sidebar
        await wait(200);
        await sidebarLink.click({ timeout: 5000 }).catch(async () => {
          await page.goto(href);
        });
      } else {
        await page.goto(href);
      }
      await page.waitForLoadState("networkidle").catch(() => {});
      await wait(waitMs);
    };

    // ── 0:00 - 0:06 | Landing (no sidebar — hard nav) ──────────
    await page.goto("/");
    await page.waitForLoadState("networkidle");
    await page.mouse.move(960, 500);
    await wait(2500);
    await scrollTo(350);
    await wait(1500);

    // ── 0:06 - 0:14 | Overview ────────────────────────────────
    await page.goto("/overview");
    await page.waitForLoadState("networkidle");
    await page.mouse.move(960, 500);
    await wait(3000);
    await page.mouse.move(700, 420); // hover a KPI
    await wait(2500);

    // ── 0:14 - 0:26 | Incidents + Evidence ────────────────────
    await goTo("/incidents", 1500);
    const firstInc = page.locator("a").filter({ hasText: /^INC-/ }).first();
    if (await firstInc.count()) {
      await page.mouse.move(500, 400);
      await wait(300);
      await firstInc.hover();
      await wait(600);
      await firstInc.click();
      await page.waitForLoadState("networkidle").catch(() => {});
      await wait(2000);

      const evTab = page.getByRole("tab", { name: "Evidence" });
      if (await evTab.count()) {
        await evTab.hover();
        await wait(400);
        await evTab.click();
        await wait(3000);
      }
      await scrollTo(250);
      await wait(1500);
    }

    // ── 0:26 - 0:36 | Store Map ───────────────────────────────
    await goTo("/stores", 1000);
    await goTo("/stores/map", 5000); // give Leaflet time to load tiles

    // Smooth zoom with wheel
    await page.mouse.move(960, 540);
    for (let i = 0; i < 3; i++) {
      await page.mouse.wheel(0, -200);
      await wait(500);
    }
    await wait(2000);
    // Hover a pin
    await page.mouse.move(880, 460);
    await wait(2500);

    // ── 0:36 - 0:44 | Reports ─────────────────────────────────
    await goTo("/reports", 2500);
    await page.mouse.move(960, 500);
    await scrollTo(350);
    await wait(2000);

    // ── 0:44 - 0:54 | Import (Auto-mapping) ───────────────────
    await goTo("/import", 2000);
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(path.join(__dirname, "demo_upload.csv"));
    await wait(3000); // wait for mapping table
    await page.mouse.move(800, 500);
    await wait(800);
    const validateBtn = page.getByRole("button", { name: /Validate mapping/i });
    if (await validateBtn.count()) {
      await validateBtn.hover();
      await wait(2500);
    }

    // ── 0:54 - 1:00 | Back to Overview (close) ────────────────
    await goTo("/overview", 3000);
    await page.mouse.move(960, 500);
    await wait(2500);
  });
});
