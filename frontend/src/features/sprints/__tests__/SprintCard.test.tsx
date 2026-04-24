import { describe, it, expect } from "vitest"
import { render, screen } from "@testing-library/react"
import { MemoryRouter } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { SprintCard } from "../SprintCard"
import type { Sprint } from "@/api/hooks/sprints"

const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })

function renderCard(sprint: Sprint) {
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <SprintCard sprint={sprint} />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

const BASE_SPRINT: Sprint = {
  id: "abc-123",
  name: "Sprint 1",
  status: "planned",
  start_date: "2026-05-01",
  end_date: "2026-05-14",
  goal: null,
  task_ids: [],
  completion_percent: 0,
  created_at: "2026-04-01T00:00:00Z",
}

describe("SprintCard", () => {
  it("renders sprint name", () => {
    renderCard(BASE_SPRINT)
    expect(screen.getByText("Sprint 1")).toBeInTheDocument()
  })

  it("renders date range", () => {
    renderCard(BASE_SPRINT)
    expect(screen.getByText(/2026-05-01.*2026-05-14/)).toBeInTheDocument()
  })

  it("renders status badge", () => {
    renderCard(BASE_SPRINT)
    expect(screen.getByText("Planned")).toBeInTheDocument()
  })

  it("renders task count", () => {
    renderCard({ ...BASE_SPRINT, task_ids: ["t1", "t2"] })
    expect(screen.getByText("2 tasks")).toBeInTheDocument()
  })

  it("shows Start button for planned sprint", () => {
    renderCard(BASE_SPRINT)
    expect(screen.getByRole("button", { name: "Start" })).toBeInTheDocument()
  })

  it("shows Complete button for active sprint", () => {
    renderCard({ ...BASE_SPRINT, status: "active" })
    expect(screen.getByRole("button", { name: "Complete" })).toBeInTheDocument()
  })
})
