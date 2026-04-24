import { test, expect } from "@playwright/test"

const API = "http://localhost:8000"

test.describe("Sprints", () => {
  test("creates a sprint via the UI", async ({ page }) => {
    await page.goto("/sprints")
    await page.getByRole("button", { name: "New Sprint" }).click()

    const dialog = page.getByRole("dialog")
    await expect(dialog).toBeVisible()

    await dialog.getByLabel("Name *").fill("E2E Sprint")
    await dialog.getByLabel("Start Date *").fill("2026-06-01")
    await dialog.getByLabel("End Date *").fill("2026-06-14")
    await dialog.getByRole("button", { name: "Create" }).click()

    await expect(dialog).not.toBeVisible()
    await expect(page.getByText("E2E Sprint")).toBeVisible()
  })

  test("navigates to active sprint and shows kanban columns", async ({ page }) => {
    await page.goto("/sprints")

    // Sprint 3: Frontend is the active sprint from seed data
    await page.getByText("Sprint 3: Frontend").first().click()

    // All 6 kanban columns should be present
    await expect(page.getByTestId("column-backlog")).toBeVisible()
    await expect(page.getByTestId("column-todo")).toBeVisible()
    await expect(page.getByTestId("column-in_progress")).toBeVisible()
    await expect(page.getByTestId("column-review")).toBeVisible()
    await expect(page.getByTestId("column-done")).toBeVisible()
  })

  test("drags task from review to done in kanban", async ({ page }) => {
    // Use a wide viewport so all 6 columns fit without horizontal scroll
    await page.setViewportSize({ width: 1800, height: 900 })

    await page.goto("/sprints")
    await page.getByText("Sprint 3: Frontend").first().click()

    const reviewCol = page.getByTestId("column-review")
    const doneCol = page.getByTestId("column-done")

    await expect(reviewCol.locator('[data-testid^="task-card-"]').first()).toBeVisible()

    const fromCard = reviewCol.locator('[data-testid^="task-card-"]').first()
    const doneCountBefore = await doneCol.locator('[data-testid^="task-card-"]').count()

    const fromBox = await fromCard.boundingBox()
    const toBox = await doneCol.boundingBox()
    if (!fromBox || !toBox) throw new Error("Kanban elements not found in viewport")

    const startX = fromBox.x + fromBox.width / 2
    const startY = fromBox.y + fromBox.height / 2
    const endX = toBox.x + toBox.width / 2
    // Drop into the card-list area below the column header (~40px)
    const endY = toBox.y + 80

    await page.mouse.move(startX, startY)
    await page.mouse.down()
    // Move slightly first to exceed dnd-kit's activationConstraint distance (8px)
    await page.mouse.move(startX + 12, startY, { steps: 4 })
    // Move to target column
    await page.mouse.move(endX, endY, { steps: 30 })
    await page.mouse.up()

    // Done column should gain one card after the transition settles
    await expect(doneCol.locator('[data-testid^="task-card-"]')).toHaveCount(
      doneCountBefore + 1,
      { timeout: 8_000 },
    )
  })

  test("starts a sprint from its detail page", async ({ page, request }) => {
    // Create a fresh sprint via API so we control its initial state
    const createRes = await request.post(`${API}/sprints`, {
      data: { name: "E2E Start Sprint", start_date: "2026-07-01", end_date: "2026-07-14" },
    })
    expect(createRes.ok()).toBeTruthy()
    const sprint = (await createRes.json()) as { id: string }

    await page.goto(`/sprints/${sprint.id}`)
    await expect(page.getByText("E2E Start Sprint")).toBeVisible()
    await expect(page.getByText("Planned")).toBeVisible()

    await page.getByRole("button", { name: "Start Sprint" }).click()

    await expect(page.getByText("Active")).toBeVisible()
    await expect(page.getByRole("button", { name: "Complete Sprint" })).toBeVisible()
  })
})
