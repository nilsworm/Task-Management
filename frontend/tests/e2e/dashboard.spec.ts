import { test, expect } from "@playwright/test"

test.describe("Dashboard", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/")
  })

  test("shows active sprint name from seed data", async ({ page }) => {
    // After seeding, Sprint 3: Frontend is the active sprint
    await expect(page.getByText("Sprint 3: Frontend")).toBeVisible({ timeout: 10_000 })
  })

  test("Task Metrics widget renders with status data", async ({ page }) => {
    await expect(page.getByText("Task Metrics")).toBeVisible({ timeout: 10_000 })
    // Metrics widget shows a breakdown — verify at least one status label is present
    await expect(page.getByRole("cell", { name: /Done|In Progress|Backlog/i }).first()).toBeVisible()
  })

  test("Velocity widget renders with completed sprint data", async ({ page }) => {
    await expect(page.getByText("Velocity")).toBeVisible({ timeout: 10_000 })
    // Sprint 1 and Sprint 2 are completed — at least one should appear in the chart axis
    await expect(page.getByText(/Sprint [12]/)).toBeVisible()
  })

  test("Goal Progress widget lists seeded goals", async ({ page }) => {
    await expect(page.getByText("Goal Progress")).toBeVisible({ timeout: 10_000 })
    await expect(page.getByText("Ship v1.0")).toBeVisible()
    await expect(page.getByText("Developer Experience")).toBeVisible()
  })
})
