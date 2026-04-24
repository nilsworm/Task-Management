import { describe, it, expect, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import { MemoryRouter } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { DashboardPage } from "../DashboardPage"

vi.mock("@/api/hooks/dashboard", () => ({
  useDashboard: () => ({
    data: {
      total_tasks: 5,
      task_counts: { backlog: 2, todo: 1, in_progress: 1, review: 0, blocked: 0, done: 1, cancelled: 0 },
      total_goals: 2,
      active_sprint: { id: "s-1", name: "Sprint 1", status: "active", total_tasks: 4, completion_percent: 25 },
    },
    isLoading: false,
  }),
  useMetrics: () => ({
    data: {
      task_counts: { backlog: 2, todo: 1, in_progress: 1, review: 0, blocked: 0, done: 1, cancelled: 0 },
      completion_rate: 20,
    },
    isLoading: false,
  }),
  useBurndown: () => ({
    data: {
      sprint_id: "s-1",
      sprint_name: "Sprint 1",
      start_date: "2026-04-01",
      end_date: "2026-04-14",
      total_points: 20,
      ideal_line: [
        { date: "2026-04-01", remaining_points: 20 },
        { date: "2026-04-14", remaining_points: 0 },
      ],
      actual_remaining: 12,
    },
    isLoading: false,
    isError: false,
  }),
  useVelocity: () => ({
    data: {
      sprints: [{ sprint_id: "s-0", sprint_name: "Sprint 0", completed_points: 15 }],
      average_velocity: 15,
    },
    isLoading: false,
  }),
  useGoalProgress: () => ({
    data: {
      goals: [
        { goal_id: "g-1", goal_title: "Ship v1.0", progress_percent: 50, key_results_count: 2 },
      ],
    },
    isLoading: false,
  }),
}))

const qc = new QueryClient()

function renderPage() {
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe("DashboardPage", () => {
  it("renders the page heading", () => {
    renderPage()
    expect(screen.getByText("Dashboard")).toBeInTheDocument()
  })

  it("renders active sprint name", () => {
    renderPage()
    expect(screen.getAllByText("Sprint 1").length).toBeGreaterThan(0)
  })

  it("renders MetricsWidget title", () => {
    renderPage()
    expect(screen.getByText("Task Metrics")).toBeInTheDocument()
  })

  it("renders BurndownWidget title", () => {
    renderPage()
    expect(screen.getByText("Burndown")).toBeInTheDocument()
  })

  it("renders VelocityWidget title", () => {
    renderPage()
    expect(screen.getByText("Velocity")).toBeInTheDocument()
  })

  it("renders GoalProgressWidget title", () => {
    renderPage()
    expect(screen.getByText("Goal Progress")).toBeInTheDocument()
  })
})
