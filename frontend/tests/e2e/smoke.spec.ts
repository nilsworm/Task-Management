import { test, expect } from "@playwright/test"

/**
 * Smoke test — verifies the app boots and all main routes render without crashing.
 * Requires `pnpm dev` running (or started automatically via playwright.config webServer).
 * The backend does NOT need to be running; pages render their loading/empty states.
 */

test.describe("Navigation smoke test", () => {
  test("Dashboard loads", async ({ page }) => {
    await page.goto("/")
    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible()
    // Sidebar navigation is present
    await expect(page.getByRole("link", { name: "Tasks" })).toBeVisible()
    await expect(page.getByRole("link", { name: "Sprints" })).toBeVisible()
    await expect(page.getByRole("link", { name: "Goals" })).toBeVisible()
  })

  test("Tasks page loads", async ({ page }) => {
    await page.goto("/tasks")
    await expect(page.getByRole("heading", { name: "Tasks" })).toBeVisible()
    await expect(page.getByRole("button", { name: "New Task" })).toBeVisible()
  })

  test("Sprints page loads", async ({ page }) => {
    await page.goto("/sprints")
    await expect(page.getByRole("heading", { name: "Sprints" })).toBeVisible()
    await expect(page.getByRole("button", { name: "New Sprint" })).toBeVisible()
  })

  test("Goals page loads", async ({ page }) => {
    await page.goto("/goals")
    await expect(page.getByRole("heading", { name: "Goals" })).toBeVisible()
    await expect(page.getByRole("button", { name: "New Goal" })).toBeVisible()
  })

  test("sidebar navigation works", async ({ page }) => {
    await page.goto("/")
    await page.getByRole("link", { name: "Tasks" }).click()
    await expect(page).toHaveURL("/tasks")

    await page.getByRole("link", { name: "Sprints" }).click()
    await expect(page).toHaveURL("/sprints")

    await page.getByRole("link", { name: "Goals" }).click()
    await expect(page).toHaveURL("/goals")

    await page.getByRole("link", { name: "Dashboard" }).click()
    await expect(page).toHaveURL("/")
  })

  test("New Task modal opens and closes", async ({ page }) => {
    await page.goto("/tasks")
    await page.getByRole("button", { name: "New Task" }).click()
    await expect(page.getByRole("dialog")).toBeVisible()
    await page.getByRole("button", { name: "Cancel" }).click()
    await expect(page.getByRole("dialog")).not.toBeVisible()
  })

  test("New Sprint modal opens and closes", async ({ page }) => {
    await page.goto("/sprints")
    await page.getByRole("button", { name: "New Sprint" }).click()
    await expect(page.getByRole("dialog")).toBeVisible()
    await page.getByRole("button", { name: "Cancel" }).click()
    await expect(page.getByRole("dialog")).not.toBeVisible()
  })

  test("New Goal modal opens and closes", async ({ page }) => {
    await page.goto("/goals")
    await page.getByRole("button", { name: "New Goal" }).click()
    await expect(page.getByRole("dialog")).toBeVisible()
    await page.getByRole("button", { name: "Cancel" }).click()
    await expect(page.getByRole("dialog")).not.toBeVisible()
  })
})
