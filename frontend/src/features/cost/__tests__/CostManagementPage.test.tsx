import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, it, expect, vi } from "vitest"
import { CostManagementPage } from "../CostManagementPage"

vi.mock("@/api/hooks/cost", () => ({
  useTransactions: () => ({ data: [], isLoading: false, isError: false }),
  useRecurring: () => ({ data: [], isLoading: false, isError: false }),
  useCostTags: () => ({ data: [] }),
  useCostSummary: () => ({
    data: { year: 2026, month: 4, income: "4150.00", expenses: "1420.12", balance: "2729.88" },
    isLoading: false,
  }),
  useCostAnalytics: () => ({
    data: { expenses_by_tag: [], monthly_comparison: [] },
    isLoading: false,
  }),
  useGenerateMonthly: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useCreateTransaction: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useDeleteTransaction: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useCreateRecurring: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useDeleteRecurring: () => ({ mutateAsync: vi.fn(), isPending: false }),
}))

describe("CostManagementPage", () => {
  it("renders heading", () => {
    render(<CostManagementPage />)
    expect(screen.getByText("Cost Management")).toBeInTheDocument()
  })

  it("shows three tabs", () => {
    render(<CostManagementPage />)
    expect(screen.getByText("Übersicht")).toBeInTheDocument()
    expect(screen.getByText("Regelmäßig")).toBeInTheDocument()
    expect(screen.getByText("Analyse")).toBeInTheDocument()
  })

  it("shows transaction list by default (Übersicht tab active)", () => {
    render(<CostManagementPage />)
    expect(screen.getByText("0 Buchungen")).toBeInTheDocument()
  })

  it("shows summary cards on Übersicht tab", () => {
    render(<CostManagementPage />)
    expect(screen.getByText("Einnahmen")).toBeInTheDocument()
    expect(screen.getByText("Ausgaben")).toBeInTheDocument()
    expect(screen.getByText("Saldo")).toBeInTheDocument()
  })

  it("switches to Regelmäßig tab", async () => {
    const user = userEvent.setup()
    render(<CostManagementPage />)
    await user.click(screen.getByText("Regelmäßig"))
    expect(screen.getByText("0 Einträge")).toBeInTheDocument()
  })

  it("switches to Analyse tab and shows analytics content", async () => {
    const user = userEvent.setup()
    render(<CostManagementPage />)
    await user.click(screen.getByText("Analyse"))
    expect(screen.getByText(/Ausgaben nach Tag/)).toBeInTheDocument()
    expect(screen.getByText(/Einnahmen vs. Ausgaben/)).toBeInTheDocument()
  })
})
