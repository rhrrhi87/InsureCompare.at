// File: frontend/e2e/advisor.spec.ts
//
// End-to-end coverage of the AI Policy Advisor: expand the panel on a
// freshly-processed upload, ask a supported and an unsupported question,
// and verify real, database-backed evidence renders under the answer.
// Runs against LLM_PROVIDER=mock (the backend's default) — no live Gemini
// calls are made in this suite.
import { expect, test } from "@playwright/test";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { loginAsUser } from "./helpers";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

test.setTimeout(90_000);

async function uploadAndOpenAdvisor(page: import("@playwright/test").Page) {
  await loginAsUser(page);
  await page.goto("/upload");

  const fixture = path.join(__dirname, "fixtures", "test_policy.png");
  await page.setInputFiles('input[type="file"]', fixture);
  await page.getByText("Ready").first().waitFor({ timeout: 30_000 });

  await page.getByRole("button", { name: /AI Policy Advisor/i }).first().click();
  await expect(page.getByText("Ask your Advisor")).toBeVisible({ timeout: 5_000 });
  // The upload can be READY before the asynchronous Advisor summary request
  // has completed. Wait for the question action to become usable.
  await expect(page.getByRole("button", { name: "Ask", exact: true }).first()).toBeEnabled({
    timeout: 30_000,
  });
}

test("Advisor answers a supported question with real database evidence", async ({ page }) => {
  await uploadAndOpenAdvisor(page);

  const input = page.getByPlaceholder("Ask about your policy…");
  await input.fill("Ist Diebstahl versichert?");
  await expect(input).toHaveValue("Ist Diebstahl versichert?");
  const [response] = await Promise.all([
    page.waitForResponse((res) => res.url().includes("/advisor/ask"), { timeout: 30_000 }),
    page.getByRole("button", { name: "Ask", exact: true }).first().click(),
  ]);

  const body = await response.json();
  expect(body.supported).toBe(true);
  expect(body.evidence.length).toBeGreaterThan(0);
  // The rendered evidence text must be the real clause from Postgres, not
  // anything the mock LLM invented.
  expect(body.evidence[0].text).toContain("Diebstahl");

  await expect(page.getByText("Source Evidence").first()).toBeVisible();
  await expect(page.getByText(body.evidence[0].text as string).first()).toBeVisible();
});

test("Advisor refuses to confirm coverage the document does not mention", async ({ page }) => {
  await uploadAndOpenAdvisor(page);

  // The fixture document never mentions flood damage.
  const input = page.getByPlaceholder("Ask about your policy…");
  await input.fill("Ist Hochwasser versichert?");
  await expect(input).toHaveValue("Ist Hochwasser versichert?");
  const [response] = await Promise.all([
    page.waitForResponse((res) => res.url().includes("/advisor/ask"), { timeout: 30_000 }),
    page.getByRole("button", { name: "Ask", exact: true }).first().click(),
  ]);

  const body = await response.json();
  expect(body.supported).toBe(false);
  expect(body.evidence.length).toBe(0);
  expect(body.answer.toLowerCase()).not.toContain("hochwasser ist versichert");

  await expect(
    page.getByText("could not be confirmed").or(page.getByText("nicht eindeutig bestätigt")),
  ).toBeVisible();
});
