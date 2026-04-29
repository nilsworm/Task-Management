import { describe, it, expect, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import { MemoryRouter } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { AppLayout } from "../AppLayout"

// useMetrics is called in the header; stub it to avoid network calls
vi.mock("@/api/hooks/dashboard", () => ({
  useMetrics: () => ({ data: { task_counts: { in_progress: 2, done: 5 }, completion_rate: 0.5 } }),
}))

function renderLayout(path = "/") {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[path]}>
        <AppLayout />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe("AppLayout", () => {
  it("renders the brand name", () => {
    renderLayout()
    expect(screen.getByText("devflow")).toBeInTheDocument()
  })

  it("renders all nav links", () => {
    renderLayout()
    expect(screen.getByText("Dashboard")).toBeInTheDocument()
    expect(screen.getByText("Tasks")).toBeInTheDocument()
    expect(screen.getByText("Sprints")).toBeInTheDocument()
    expect(screen.getByText("Goals")).toBeInTheDocument()
  })

  it("nav links point to correct paths", () => {
    renderLayout()
    expect(screen.getByRole("link", { name: /dashboard/i })).toHaveAttribute("href", "/")
    expect(screen.getByRole("link", { name: /tasks/i })).toHaveAttribute("href", "/tasks")
    expect(screen.getByRole("link", { name: /sprints/i })).toHaveAttribute("href", "/sprints")
    expect(screen.getByRole("link", { name: /goals/i })).toHaveAttribute("href", "/goals")
  })

  it("renders header with theme toggle", () => {
    renderLayout()
    expect(screen.getByLabelText("Toggle theme")).toBeInTheDocument()
  })

  it("renders global stats from metrics", () => {
    renderLayout()
    expect(screen.getByText("2 in progress")).toBeInTheDocument()
    expect(screen.getByText("5 done")).toBeInTheDocument()
  })
})
