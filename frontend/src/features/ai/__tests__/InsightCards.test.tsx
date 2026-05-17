import { describe, it, expect } from "vitest"
import { render, screen } from "@testing-library/react"
import { InsightCards } from "@/features/ai/InsightCards"
import type { InsightCard } from "@/api/hooks/ai"

const cards: InsightCard[] = [
  { title: "Ausgaben gestiegen", body: "Deine Ausgaben stiegen um 20%", type: "warning" },
  { title: "Gut gespart", body: "Saldo positiv", type: "tip" },
  { title: "Lastschrift nächsten Monat", body: "3 Abbuchungen kommen", type: "forecast" },
]

describe("InsightCards", () => {
  it("renders all three cards", () => {
    render(<InsightCards cards={cards} isLoading={false} />)
    expect(screen.getByText("Ausgaben gestiegen")).toBeInTheDocument()
    expect(screen.getByText("Gut gespart")).toBeInTheDocument()
    expect(screen.getByText("Lastschrift nächsten Monat")).toBeInTheDocument()
  })

  it("shows skeleton when loading", () => {
    render(<InsightCards cards={[]} isLoading={true} />)
    expect(screen.getAllByTestId("insight-skeleton")).toHaveLength(3)
  })

  it("renders warning card with orange accent", () => {
    render(<InsightCards cards={[cards[0]]} isLoading={false} />)
    const card = screen.getByTestId("insight-card-warning")
    expect(card).toBeInTheDocument()
  })

  it("renders tip card with green accent", () => {
    render(<InsightCards cards={[cards[1]]} isLoading={false} />)
    expect(screen.getByTestId("insight-card-tip")).toBeInTheDocument()
  })

  it("renders forecast card with blue accent", () => {
    render(<InsightCards cards={[cards[2]]} isLoading={false} />)
    expect(screen.getByTestId("insight-card-forecast")).toBeInTheDocument()
  })
})
