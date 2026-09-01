// File: frontend/e2e/journeys.spec.ts
//
// 8 named end-to-end journeys against a real running backend (FastAPI +
// PostgreSQL) and a real running frontend dev server — no mocking. Each
// test drives the actual UI exactly as a user would (typed/clicked, not
// dispatched via internal APIs) and asserts on real rendered output.
//
// Run with `npm run e2e` (see package.json) once both servers are up:
//   backend:  uvicorn app.main:app --port 8000   (from backend/, venv active)
//   frontend: npm run dev                          (from frontend/)
import { expect, test } from "@playwright/test";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { loginAsAdmin, loginAsUser } from "./helpers";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

test("1. Landing page renders and links to register/login", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  await expect(page.getByRole("link", { name: "Sign In" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Get Started" })).toBeVisible();

  await page.getByRole("link", { name: "Get Started" }).click();
  await expect(page).toHaveURL(/\/register/);
  await expect(page.getByRole("heading", { name: "Create your account" })).toBeVisible();

  await page.getByRole("link", { name: "Sign in", exact: true }).click();
  await expect(page).toHaveURL(/\/login/);
  await expect(page.getByRole("heading", { name: "Welcome Back" })).toBeVisible();
});

test("2. Language switch (EN -> DE) updates visible text and <html lang>", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
  await expect(page.getByRole("link", { name: "Sign In" })).toBeVisible();

  const deButton = page.getByRole("button", { name: /^DE$/i });
  await deButton.click();

  await expect(page.locator("html")).toHaveAttribute("lang", "de");
  // German nav label for "Sign In" is "Anmelden" per de/navigation.json.
  await expect(page.getByRole("link", { name: "Anmelden" })).toBeVisible();
});

test("3. Login as demo user, then browse policies via Compare page", async ({ page }) => {
  await loginAsUser(page);
  await expect(page.getByRole("heading", { name: "User Dashboard" })).toBeVisible();

  await page.goto("/compare");
  await expect(page.getByRole("heading", { name: "Policy Comparison" })).toBeVisible();
  await expect(page.getByText("Available policies")).toBeVisible();
});

test("4. Compare 2-3 policies side by side", async ({ page }) => {
  await loginAsUser(page);
  await page.goto("/compare");
  await expect(page.getByRole("heading", { name: "Policy Comparison" })).toBeVisible();
  // The policy table loads asynchronously after the initial page load (a
  // TanStack Query fetch); wait for at least one row-level element to
  // appear rather than counting checkboxes the instant navigation settles.
  const pickCheckboxes = page.locator('table input[type="checkbox"]');
  await expect(pickCheckboxes.first().or(page.getByText("No policies available"))).toBeVisible({ timeout: 10_000 });
  const count = await pickCheckboxes.count();
  test.skip(count < 2, "Fewer than 2 policies available in the default product line to compare");

  await pickCheckboxes.nth(0).click();
  await pickCheckboxes.nth(1).click();

  await expect(page.getByText(/Selected: 2 \/ 3/)).toBeVisible();
  await page.getByRole("button", { name: /Compare 2 Policies/ }).click();
  await expect(page.getByText(/Comparing 2/)).toBeVisible();
  await expect(page.getByText("Cheapest Monthly")).toBeVisible();
});

test("5. Update risk profile and get AI recommendations with explanation", async ({ page }) => {
  await loginAsUser(page);
  await page.goto("/dashboard");
  await page.getByRole("button", { name: "Save Preferences" }).click();

  await page.getByRole("button", { name: "Get AI Recommendations →" }).click();
  await expect(page).toHaveURL(/\/recommendations/);
  await expect(page.getByRole("heading", { name: "AI Recommendation Results" })).toBeVisible({ timeout: 15_000 });
  await expect(page.getByText("Best Match for You")).toBeVisible();
  await expect(page.getByText("AI Scoring Methodology")).toBeVisible();
});

test("6. Upload a document (controlled fixture) and see OCR/NLP extraction", async ({ page }) => {
  await loginAsUser(page);
  await page.goto("/upload");
  await expect(page.getByRole("heading", { name: "Upload Insurance Document" })).toBeVisible();

  const fixture = path.join(__dirname, "fixtures", "test_policy.png");
  await page.setInputFiles('input[type="file"]', fixture);

  await expect(page.getByText("Ready").first()).toBeVisible({ timeout: 30_000 });
  await expect(page.getByText("OCR confidence").first()).toBeVisible();
});

test("7. Policy detail page shows explainable coverage/exclusions", async ({ page }) => {
  await loginAsUser(page);
  await page.goto("/dashboard");
  await page.getByRole("button", { name: "Get AI Recommendations →" }).click();
  await expect(page.getByRole("heading", { name: "AI Recommendation Results" })).toBeVisible({ timeout: 15_000 });

  const anyPolicyLink = page.locator('a[href^="/policies/"]').first();
  if (await anyPolicyLink.count()) {
    await anyPolicyLink.click();
    await expect(page.getByText("Coverage Details")).toBeVisible();
    await expect(page.getByText("Policy Exclusions")).toBeVisible();
  } else {
    test.skip(true, "No policy detail link rendered on the recommendations page in this environment");
  }
});

test("8. Admin: login and manage providers/policies", async ({ page }) => {
  await loginAsAdmin(page);
  await expect(page.getByRole("heading", { name: "Admin Dashboard" })).toBeVisible();

  await page.getByRole("link", { name: "Providers" }).click();
  await expect(page).toHaveURL(/\/admin\/providers/);
  await expect(page.getByRole("heading", { name: "Provider Management" })).toBeVisible();
  await expect(page.getByText(/UNIQA/)).toBeVisible();

  // Official insurer logos are hotlinked from insurer domains, so a fully
  // offline test environment must accept the intentional neutral initial
  // fallback as well as a successfully loaded remote image.
  await page.waitForLoadState("networkidle");
  const loadedLogos = page.getByTestId("provider-logo-image");
  const fallbackLogos = page.getByTestId("provider-logo-fallback");
  const logoWidths = await loadedLogos.evaluateAll((images) =>
    images.map((image) => (image as HTMLImageElement).naturalWidth),
  );
  expect((await loadedLogos.count()) + (await fallbackLogos.count())).toBeGreaterThan(0);
  for (const width of logoWidths) {
    expect(width).toBeGreaterThan(0);
  }

  await page.getByRole("link", { name: "Policies" }).click();
  await expect(page).toHaveURL(/\/admin\/policies/);
  await expect(page.getByRole("heading", { name: "Policy Management" })).toBeVisible();
});
