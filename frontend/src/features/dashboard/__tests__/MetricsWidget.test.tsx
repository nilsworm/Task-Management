import { describe, it, expect } from "vitest"
import { render, screen } from "@testing-library/react"
import { MetricsWidget } from "../MetricsWidget"
import type { MetricsData } from "@/api/hooks/dashboard"

const BASE_METRICS: MetricsData = {
  task_counts: {
    backlog: 3,
    todo: 2,
    in_progress: 1,
    review: 0,
    blocked: 0,
    done: 4,
    cancelled: 1,
  },
  completion_rate: 36.36,
}

describe("MetricsWidget", () => {
  it("renders widget title", () => {
    render(<MetricsWidget metrics={BASE_METRICS} />)
    expect(screen.getByText("Task Metrics")).toBeInTheDocument()
  })

  it("renders completion rate", () => {
    render(<MetricsWidget metrics={BASE_METRICS} />)
    expect(screen.getByText("36% complete")).toBeInTheDocument()
  })

  it("renders status rows in the table", () => {
    render(<MetricsWidget metrics={BASE_METRICS} />)
    expect(screen.getByText("Backlog")).toBeInTheDocument()
    expect(screen.getByText("Done")).toBeInTheDocument()
  })

  it("renders total count", () => {
    render(<MetricsWidget metrics={BASE_METRICS} />)
    expect(screen.getByText("Total")).toBeInTheDocument()
    expect(screen.getByText("11")).toBeInTheDocument()
  })

  it("shows empty state when no tasks", () => {
    const empty: MetricsData = {
      task_counts: { backlog: 0, todo: 0, in_progress: 0, review: 0, blocked: 0, done: 0, cancelled: 0 },
      completion_rate: 0,
    }
    render(<MetricsWidget metrics={empty} />)
    expect(screen.getByText("No tasks yet.")).toBeInTheDocument()
  })
})
