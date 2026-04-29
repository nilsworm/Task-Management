import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, it, expect, vi } from "vitest"
import { CostManagementPage } from "../CostManagementPage"

vi.mock("@/api/hooks/cost", () => ({
  useTransactions: () => ({ data: [], isLoading: false, isError: false }),
  useRecurring: () => ({ data: [], isLoading: false, isError: false }),
  useCostTags: () => ({ data: [] }),
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

  it("switches to Regelmäßig tab", async () => {
    const user = userEvent.setup()
    render(<CostManagementPage />)
    await user.click(screen.getByText("Regelmäßig"))
    expect(screen.getByText("0 Einträge")).toBeInTheDocument()
  })

  it("switches to Analyse tab and shows placeholder", async () => {
    const user = userEvent.setup()
    render(<CostManagementPage />)
    await user.click(screen.getByText("Analyse"))
    expect(screen.getByText(/Analyse-Diagramme folgen/)).toBeInTheDocument()
  })
})
