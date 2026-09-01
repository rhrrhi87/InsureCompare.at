// File: frontend/e2e/accessibility.spec.ts
//
// Automated accessibility scan (axe-core) of key pages, both public and
// authenticated. This is the AUTOMATED half of docs/ACCESSIBILITY.md — it
// catches a real, well-defined subset of WCAG issues (missing alt text,
// contrast ratios, missing form labels, invalid ARIA, etc.) but axe-core
// itself documents that it cannot catch everything (e.g. logical reading
// order, meaningfulness of alt text, keyboard-trap logic) — those remain
// manual checks, written up separately in docs/ACCESSIBILITY.md.
import AxeBuilder from "@axe-core/playwright";
import { test } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { loginAsAdmin, loginAsUser } from "./helpers";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const results: Record<string, { violations: number; details: unknown[] }> = {};

async function scan(page: import("@playwright/test").Page, name: string) {
  const result = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  results[name] = {
    violations: result.violations.length,
    details: result.violations.map((v) => ({
      id: v.id,
      impact: v.impact,
      help: v.help,
      nodes: v.nodes.length,
      targets: v.nodes.map((n) => ({ target: n.target, summary: n.failureSummary })),
    })),
  };
  return result;
}

test.afterAll(() => {
  const outPath = path.join(__dirname, "..", "axe-results.json");
  fs.writeFileSync(outPath, JSON.stringify(results, null, 2), "utf-8");
});

test("axe scan: landing page", async ({ page }) => {
  await page.goto("/");
  await scan(page, "landing_page");
});

test("axe scan: login page", async ({ page }) => {
  await page.goto("/login");
  await scan(page, "login_page");
});

test("axe scan: register page", async ({ page }) => {
  await page.goto("/register");
  await scan(page, "register_page");
});

test("axe scan: dashboard (authenticated)", async ({ page }) => {
  await loginAsUser(page);
  await scan(page, "dashboard");
});

test("axe scan: compare page", async ({ page }) => {
  await loginAsUser(page);
  await page.goto("/compare");
  await scan(page, "compare_page");
});

test("axe scan: recommendations page", async ({ page }) => {
  await loginAsUser(page);
  await page.getByRole("button", { name: "Get AI Recommendations →" }).click();
  await page.waitForURL(/\/recommendations/);
  await page.getByText("Best Match for You").waitFor({ timeout: 15_000 });
  await scan(page, "recommendations_page");
});

test("axe scan: upload page", async ({ page }) => {
  await loginAsUser(page);
  await page.goto("/upload");
  await scan(page, "upload_page");
});

test("axe scan: upload page with Advisor panel expanded", async ({ page }) => {
  await loginAsUser(page);
  await page.goto("/upload");
  const toggle = page.getByRole("button", { name: /AI Policy Advisor/i }).first();
  if (await toggle.count()) {
    await toggle.click();
    await page.getByText("Ask your Advisor").first().waitFor({ timeout: 5_000 }).catch(() => {});
  }
  await scan(page, "upload_page_advisor_expanded");
});

test("axe scan: admin providers page", async ({ page }) => {
  await loginAsAdmin(page);
  await page.goto("/admin/providers");
  await scan(page, "admin_providers_page");
});

test("axe scan: admin policies page", async ({ page }) => {
  await loginAsAdmin(page);
  await page.goto("/admin/policies");
  await scan(page, "admin_policies_page");
});
