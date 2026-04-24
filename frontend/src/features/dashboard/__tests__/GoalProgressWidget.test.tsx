import { describe, it, expect } from "vitest"
import { render, screen } from "@testing-library/react"
import { GoalProgressWidget } from "../GoalProgressWidget"
import type { GoalProgressData } from "@/api/hooks/dashboard"

const BASE_DATA: GoalProgressData = {
  goals: [
    { goal_id: "g-1", goal_title: "Ship v1.0", progress_percent: 75, key_results_count: 3 },
    { goal_id: "g-2", goal_title: "Grow audience", progress_percent: 40, key_results_count: 2 },
  ],
}

describe("GoalProgressWidget", () => {
  it("renders widget title", () => {
    render(<GoalProgressWidget goalProgress={BASE_DATA} />)
    expect(screen.getByText("Goal Progress")).toBeInTheDocument()
  })

  it("renders goal titles", () => {
    render(<GoalProgressWidget goalProgress={BASE_DATA} />)
    expect(screen.getByText("Ship v1.0")).toBeInTheDocument()
    expect(screen.getByText("Grow audience")).toBeInTheDocument()
  })

  it("renders progress percentages", () => {
    render(<GoalProgressWidget goalProgress={BASE_DATA} />)
    expect(screen.getByText("75%")).toBeInTheDocument()
    expect(screen.getByText("40%")).toBeInTheDocument()
  })

  it("progressbars have correct aria-valuenow", () => {
    render(<GoalProgressWidget goalProgress={BASE_DATA} />)
    const bars = screen.getAllByRole("progressbar")
    expect(bars[0]).toHaveAttribute("aria-valuenow", "75")
    expect(bars[1]).toHaveAttribute("aria-valuenow", "40")
  })

  it("caps progressbar at 100 when progress_percent > 100", () => {
    const data: GoalProgressData = {
      goals: [{ goal_id: "g-3", goal_title: "Overachiever", progress_percent: 130, key_results_count: 1 }],
    }
    render(<GoalProgressWidget goalProgress={data} />)
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "100")
  })

  it("renders key result counts", () => {
    render(<GoalProgressWidget goalProgress={BASE_DATA} />)
    expect(screen.getByText("3 key results")).toBeInTheDocument()
    expect(screen.getByText("2 key results")).toBeInTheDocument()
  })

  it("shows singular for 1 key result", () => {
    const data: GoalProgressData = {
      goals: [{ goal_id: "g-4", goal_title: "Solo", progress_percent: 50, key_results_count: 1 }],
    }
    render(<GoalProgressWidget goalProgress={data} />)
    expect(screen.getByText("1 key result")).toBeInTheDocument()
  })

  it("shows empty state when no goals", () => {
    render(<GoalProgressWidget goalProgress={{ goals: [] }} />)
    expect(screen.getByText("No goals yet.")).toBeInTheDocument()
  })
})
