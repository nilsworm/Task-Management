import { describe, it, expect } from "vitest"
import { render, screen } from "@testing-library/react"
import { MemoryRouter } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { GoalCard } from "../GoalCard"
import type { Goal } from "@/api/hooks/goals"

const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })

const BASE_GOAL: Goal = {
  id: "g-1",
  title: "Ship v1.0",
  description: "",
  status: "backlog",
  priority: "high",
  tags: [],
  date_range_start: null,
  date_range_end: null,
  created_at: "2026-05-01T00:00:00Z",
  updated_at: "2026-05-01T00:00:00Z",
}

function renderCard(goal: Goal, pct = 0, count = 0) {
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <GoalCard goal={goal} progressPercent={pct} keyResultsCount={count} />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe("GoalCard", () => {
  it("renders goal title", () => {
    renderCard(BASE_GOAL)
    expect(screen.getByText("Ship v1.0")).toBeInTheDocument()
  })

  it("renders KR count", () => {
    renderCard(BASE_GOAL, 0, 3)
    expect(screen.getByText("3 key results")).toBeInTheDocument()
  })

  it("renders singular KR count", () => {
    renderCard(BASE_GOAL, 0, 1)
    expect(screen.getByText("1 key result")).toBeInTheDocument()
  })

  it("renders progress percentage", () => {
    renderCard(BASE_GOAL, 42, 2)
    expect(screen.getByText("42%")).toBeInTheDocument()
  })

  it("progressbar has correct aria-valuenow", () => {
    renderCard(BASE_GOAL, 75)
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "75")
  })
})
