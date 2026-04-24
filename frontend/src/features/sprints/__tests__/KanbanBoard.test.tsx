import { describe, it, expect } from "vitest"
import { render, screen } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { KanbanBoard } from "../KanbanBoard"

const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })

function renderBoard() {
  return render(
    <QueryClientProvider client={qc}>
      <KanbanBoard tasks={[]} />
    </QueryClientProvider>,
  )
}

describe("KanbanBoard", () => {
  it("renders all 6 columns", () => {
    renderBoard()
    expect(screen.getByText("Backlog")).toBeInTheDocument()
    expect(screen.getByText("To Do")).toBeInTheDocument()
    expect(screen.getByText("In Progress")).toBeInTheDocument()
    expect(screen.getByText("Review")).toBeInTheDocument()
    expect(screen.getByText("Blocked")).toBeInTheDocument()
    expect(screen.getByText("Done")).toBeInTheDocument()
  })

  it("shows task in correct column", () => {
    const task = {
      id: "t1",
      title: "Write tests",
      status: "in_progress",
      priority: "high",
      task_type: "sprint",
      description: "",
      estimation: 3,
      tags: [],
      scheduled_date: null,
      sprint_id: "s1",
      date_range_start: null,
      date_range_end: null,
      due_date: null,
      goal_id: null,
      created_at: "2026-05-01T00:00:00Z",
      updated_at: "2026-05-01T00:00:00Z",
    }
    render(
      <QueryClientProvider client={qc}>
        <KanbanBoard tasks={[task]} />
      </QueryClientProvider>,
    )
    expect(screen.getByText("Write tests")).toBeInTheDocument()
  })
})
