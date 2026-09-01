// File: frontend/e2e/helpers.ts
import { expect, type Page } from "@playwright/test";

const DEMO_USER_EMAIL = "user@test.at";
const DEMO_ADMIN_EMAIL = "admin@insurance.at";

// The "Login as ..." demo buttons fill the form via react-hook-form's
// setValue() rather than a real submit; clicking "Sign In" immediately
// afterwards has occasionally raced ahead of the DOM update in this dev
// (unminified, HMR-instrumented) build, producing a client-side-validation
// no-op instead of a real login POST — the same category of automation
// timing flake already documented in docs/TESTING.md's "Tooling note on
// EN/DE verification". Waiting for the email field's real value removes
// the race without touching application code.
async function loginAs(page: Page, buttonPattern: RegExp, expectedEmail: string, expectedUrl: RegExp) {
  await page.goto("/login");
  await page.getByRole("button", { name: buttonPattern }).click();
  const email = page.getByLabel("Email Address");
  const password = page.getByLabel("Password");
  await expect(email).toHaveValue(expectedEmail);
  // Enter the values through the controls so react-hook-form receives the
  // same input events as a user. This avoids a dev-server race in setValue().
  await email.fill(expectedEmail);
  await password.fill(expectedEmail === DEMO_ADMIN_EMAIL ? "admin123" : "user123");
  await page.getByRole("button", { name: "Sign In" }).click();
  await expect(page).toHaveURL(expectedUrl, { timeout: 30_000 });
}

export async function loginAsUser(page: Page) {
  await loginAs(page, new RegExp(`Login as User \\(${DEMO_USER_EMAIL}\\)`), DEMO_USER_EMAIL, /\/dashboard/);
}

export async function loginAsAdmin(page: Page) {
  await loginAs(page, new RegExp(`Login as Admin \\(${DEMO_ADMIN_EMAIL}\\)`), DEMO_ADMIN_EMAIL, /\/admin/);
}
