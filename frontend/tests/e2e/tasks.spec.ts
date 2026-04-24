import { test, expect } from "@playwright/test"

const API = "http://localhost:8000"

test.describe("Tasks", () => {
  test("creates a task via the UI", async ({ page }) => {
    await page.goto("/tasks")
    await page.getByRole("button", { name: "New Task" }).click()

    const dialog = page.getByRole("dialog")
    await expect(dialog).toBeVisible()

    await dialog.getByLabel("Title *").fill("E2E Task — create")
    await dialog.getByRole("button", { name: "Create" }).click()

    await expect(dialog).not.toBeVisible()
    await expect(page.getByText("E2E Task — create")).toBeVisible()
  })

  test("transitions task status via Actions dropdown", async ({ page, request }) => {
    const res = await request.post(`${API}/tasks`, {
      data: { title: "E2E Task — transition", task_type: "daily", priority: "medium" },
    })
    expect(res.ok()).toBeTruthy()

    await page.goto("/tasks")
    await expect(page.getByText("E2E Task — transition")).toBeVisible()

    const row = page.locator("tr").filter({ hasText: "E2E Task — transition" })
    await row.getByRole("button").click()
    await page.getByRole("menuitem", { name: "Todo" }).click()

    await expect(row.getByText("Todo")).toBeVisible()
  })

  test("edits task title", async ({ page, request }) => {
    const res = await request.post(`${API}/tasks`, {
      data: { title: "E2E Task — edit original", task_type: "daily", priority: "medium" },
    })
    expect(res.ok()).toBeTruthy()

    await page.goto("/tasks")
    await expect(page.getByText("E2E Task — edit original")).toBeVisible()

    const row = page.locator("tr").filter({ hasText: "E2E Task — edit original" })
    await row.getByRole("button").click()
    await page.getByRole("menuitem", { name: "Edit" }).click()

    const dialog = page.getByRole("dialog")
    await expect(dialog).toBeVisible()

    const titleInput = dialog.getByLabel("Title *")
    await titleInput.clear()
    await titleInput.fill("E2E Task — edit updated")
    await dialog.getByRole("button", { name: "Save" }).click()

    await expect(dialog).not.toBeVisible()
    await expect(page.getByText("E2E Task — edit updated")).toBeVisible()
    await expect(page.getByText("E2E Task — edit original")).not.toBeVisible()
  })

  test("deletes a task", async ({ page, request }) => {
    const res = await request.post(`${API}/tasks`, {
      data: { title: "E2E Task — delete me", task_type: "daily", priority: "medium" },
    })
    expect(res.ok()).toBeTruthy()

    await page.goto("/tasks")
    await expect(page.getByText("E2E Task — delete me")).toBeVisible()

    const row = page.locator("tr").filter({ hasText: "E2E Task — delete me" })
    await row.getByRole("button").click()
    await page.getByRole("menuitem", { name: "Delete" }).click()

    const alertDialog = page.getByRole("alertdialog")
    await expect(alertDialog).toBeVisible()
    await alertDialog.getByRole("button", { name: "Delete" }).click()

    await expect(page.getByText("E2E Task — delete me")).not.toBeVisible()
  })

  test("shows validation error when title is empty", async ({ page }) => {
    await page.goto("/tasks")
    await page.getByRole("button", { name: "New Task" }).click()

    const dialog = page.getByRole("dialog")
    await expect(dialog).toBeVisible()

    // Submit without filling the title
    await dialog.getByRole("button", { name: "Create" }).click()

    await expect(dialog.getByText("Title is required.")).toBeVisible()
  })
})
