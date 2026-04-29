import { render, screen } from "@testing-library/react"
import { describe, it, expect } from "vitest"
import { SummaryCards } from "../SummaryCards"
import type { CostSummary } from "@/api/hooks/cost"

const summary: CostSummary = {
  year: 2026,
  month: 4,
  income: "4150.00",
  expenses: "1420.12",
  balance: "2729.88",
}

describe("SummaryCards", () => {
  it("renders three card labels", () => {
    render(<SummaryCards summary={summary} isLoading={false} />)
    expect(screen.getByText("Einnahmen")).toBeInTheDocument()
    expect(screen.getByText("Ausgaben")).toBeInTheDocument()
    expect(screen.getByText("Saldo")).toBeInTheDocument()
  })

  it("formats income in EUR", () => {
    render(<SummaryCards summary={summary} isLoading={false} />)
    expect(screen.getByText(/4\.150,00/)).toBeInTheDocument()
  })

  it("formats expenses in EUR", () => {
    render(<SummaryCards summary={summary} isLoading={false} />)
    expect(screen.getByText(/1\.420,12/)).toBeInTheDocument()
  })

  it("shows positive balance in blue", () => {
    render(<SummaryCards summary={summary} isLoading={false} />)
    const balanceEl = screen.getByText(/2\.729,88/)
    expect(balanceEl).toHaveClass("text-blue-600")
  })

  it("shows negative balance in red", () => {
    const neg: CostSummary = { ...summary, balance: "-100.00" }
    render(<SummaryCards summary={neg} isLoading={false} />)
    const balanceEl = screen.getByText(/100,00/)
    expect(balanceEl).toHaveClass("text-red-600")
  })

  it("shows skeletons while loading", () => {
    const { container } = render(<SummaryCards summary={undefined} isLoading={true} />)
    expect(container.querySelectorAll(".animate-pulse").length).toBeGreaterThan(0)
  })
})
