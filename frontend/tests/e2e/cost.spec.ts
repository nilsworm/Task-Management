import { test, expect } from "@playwright/test"

const API = "http://localhost:8000"
const YEAR = 2026
const MONTH_GENERATE = 11 // November — no seed data
const MONTH_DUPLICATE = 12 // December — no seed data

// Serial: generate-monthly tests depend on DB state; parallel runs cause false 409s
test.describe.configure({ mode: "serial" })

test.describe("Cost Management", () => {
  test("shows Cost Management page with three tabs", async ({ page }) => {
    await page.goto("/cost")
    await expect(page.getByRole("heading", { name: "Cost Management" })).toBeVisible()
    await expect(page.getByText("Übersicht")).toBeVisible()
    await expect(page.getByText("Regelmäßig")).toBeVisible()
    await expect(page.getByText("Analyse")).toBeVisible()
  })

  test("shows summary cards on Übersicht tab", async ({ page }) => {
    await page.goto("/cost")
    await expect(page.getByText("Einnahmen", { exact: true })).toBeVisible()
    await expect(page.getByText("Ausgaben", { exact: true })).toBeVisible()
    await expect(page.getByText("Saldo", { exact: true })).toBeVisible()
  })

  test("creates a transaction via UI", async ({ page }) => {
    await page.goto("/cost")

    await page.getByRole("button", { name: "Neue Buchung" }).click()
    const dialog = page.getByRole("dialog")
    await expect(dialog).toBeVisible()

    await dialog.getByLabel("Titel *").fill("E2E Testausgabe")
    await dialog.getByLabel("Betrag (€) *").fill("42.50")
    await dialog.getByRole("button", { name: "Speichern" }).click()

    await expect(dialog).not.toBeVisible()
    await expect(page.getByText("E2E Testausgabe")).toBeVisible()
  })

  test("switches to Regelmäßig tab and creates a recurring entry", async ({ page }) => {
    await page.goto("/cost")
    await page.getByText("Regelmäßig").click()

    await page.getByRole("button", { name: "Neuer Eintrag" }).click()
    const dialog = page.getByRole("dialog")
    await expect(dialog).toBeVisible()

    await dialog.getByLabel("Titel *").fill("E2E Abo")
    await dialog.getByLabel("Betrag (€) *").fill("9.99")
    await dialog.getByRole("button", { name: "Speichern" }).click()

    await expect(dialog).not.toBeVisible()
    await expect(page.getByText("E2E Abo")).toBeVisible()
  })

  test("generate-monthly API creates transactions for a clean month", async ({ request }) => {
    await request.post(`${API}/cost/recurring`, {
      data: {
        title: "E2E Recurring Nov",
        amount: "25.00",
        transaction_type: "expense",
        interval: "monthly",
        day_of_month: 1,
      },
    })

    const gen = await request.post(
      `${API}/cost/generate-monthly?year=${YEAR}&month=${MONTH_GENERATE}`,
    )
    expect(gen.status()).toBe(201)
    const created = await gen.json() as Array<{ title: string }>
    expect(created.length).toBeGreaterThan(0)
    expect(created.some((t) => t.title === "E2E Recurring Nov")).toBeTruthy()
  })

  test("generate-monthly returns 409 when already generated", async ({ request }) => {
    // All recurring entries already generated for MONTH_GENERATE by previous test.
    // No new recurring entries created between the two tests (serial mode).
    const second = await request.post(
      `${API}/cost/generate-monthly?year=${YEAR}&month=${MONTH_GENERATE}`,
    )
    expect(second.status()).toBe(409)
  })
})
