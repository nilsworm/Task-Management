import { test, expect } from "@playwright/test"

const API = "http://localhost:8000"

test.describe("Goals", () => {
  test("creates a goal via the UI", async ({ page }) => {
    await page.goto("/goals")
    await page.getByRole("button", { name: "New Goal" }).click()

    const dialog = page.getByRole("dialog")
    await expect(dialog).toBeVisible()

    await dialog.getByLabel("Title *").fill("E2E Goal")
    await dialog.getByRole("button", { name: "Create" }).click()

    await expect(dialog).not.toBeVisible()
    await expect(page.getByText("E2E Goal", { exact: true })).toBeVisible()
  })

  test("navigates to seeded goal detail and shows key results section", async ({ page }) => {
    await page.goto("/goals")

    // "Ship v1.0" is a seeded goal with 3 key results
    await page.getByText("Ship v1.0").first().click()

    await expect(page.getByRole("heading", { level: 1 })).toContainText("Ship v1.0")
    await expect(page.getByRole("heading", { name: /Key Results/ })).toBeVisible()
  })

  test("adds a key result to a goal", async ({ page, request }) => {
    // Create a fresh goal via API
    const createRes = await request.post(`${API}/goals`, {
      data: { title: "E2E KR Goal", priority: "medium", tags: [] },
    })
    expect(createRes.ok()).toBeTruthy()
    const goal = (await createRes.json()) as { id: string }

    await page.goto(`/goals/${goal.id}`)
    await expect(page.getByText("E2E KR Goal")).toBeVisible()

    await page.getByRole("button", { name: "Add KR" }).click()

    const dialog = page.getByRole("dialog")
    await expect(dialog).toBeVisible()

    await dialog.getByLabel("Title *").fill("Reach 80% coverage")
    await dialog.getByLabel("Target *").fill("80")
    await dialog.getByRole("button", { name: "Add" }).click()

    await expect(dialog).not.toBeVisible()
    await expect(page.getByText("Reach 80% coverage")).toBeVisible()
  })

  test("deletes a goal", async ({ page, request }) => {
    // Create via API so deletion doesn't affect seeded goals
    const createRes = await request.post(`${API}/goals`, {
      data: { title: "E2E Goal — delete me", priority: "low", tags: [] },
    })
    expect(createRes.ok()).toBeTruthy()

    await page.goto("/goals")
    await expect(page.getByText("E2E Goal — delete me")).toBeVisible()

    // Find the card and click its Delete button (footer stops propagation)
    const card = page.locator("div.rounded-lg").filter({ has: page.getByText("E2E Goal — delete me", { exact: true }) })
    await card.getByRole("button", { name: "Delete" }).click()

    await expect(page.getByText("E2E Goal — delete me")).not.toBeVisible()
  })
})
