import { render, screen } from "@testing-library/react"
import { describe, it, expect } from "vitest"
import { TransactionTypeBadge, formatAmount } from "../TransactionBadge"

describe("TransactionTypeBadge", () => {
  it("renders 'Einnahme' for income", () => {
    render(<TransactionTypeBadge type="income" />)
    expect(screen.getByText("Einnahme")).toBeInTheDocument()
  })

  it("renders 'Ausgabe' for expense", () => {
    render(<TransactionTypeBadge type="expense" />)
    expect(screen.getByText("Ausgabe")).toBeInTheDocument()
  })

  it("applies green class for income", () => {
    const { container } = render(<TransactionTypeBadge type="income" />)
    expect(container.firstChild).toHaveClass("border-green-500")
  })

  it("applies red class for expense", () => {
    const { container } = render(<TransactionTypeBadge type="expense" />)
    expect(container.firstChild).toHaveClass("border-red-500")
  })

  it("renders 'Transfer' for transfer", () => {
    render(<TransactionTypeBadge type="transfer" />)
    expect(screen.getByText("Transfer")).toBeInTheDocument()
  })

  it("applies purple class for transfer", () => {
    const { container } = render(<TransactionTypeBadge type="transfer" />)
    expect(container.firstChild).toHaveClass("border-purple-500")
  })

  it("renders 'Investment' for stock", () => {
    render(<TransactionTypeBadge type="stock" />)
    expect(screen.getByText("Investment")).toBeInTheDocument()
  })

  it("applies amber class for stock", () => {
    const { container } = render(<TransactionTypeBadge type="stock" />)
    expect(container.firstChild).toHaveClass("border-amber-500")
  })
})

describe("formatAmount", () => {
  it("formats number to German EUR format", () => {
    const result = formatAmount(1234.56)
    expect(result).toContain("1.234,56")
    expect(result).toContain("€")
  })

  it("formats string amount", () => {
    const result = formatAmount("800.00")
    expect(result).toContain("800,00")
  })
})
