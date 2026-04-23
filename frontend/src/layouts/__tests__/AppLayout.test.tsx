import { describe, it, expect } from "vitest"
import { render, screen } from "@testing-library/react"
import { MemoryRouter } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { AppLayout } from "../AppLayout"

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
  it("renders the sidebar with all nav links", () => {
    renderLayout()
    expect(screen.getByText("Dashboard")).toBeInTheDocument()
    expect(screen.getByText("Tasks")).toBeInTheDocument()
    expect(screen.getByText("Sprints")).toBeInTheDocument()
    expect(screen.getByText("Goals")).toBeInTheDocument()
  })

  it("renders the header", () => {
    renderLayout()
    expect(screen.getByText("Task Manager")).toBeInTheDocument()
    expect(screen.getByLabelText("Toggle theme")).toBeInTheDocument()
  })

  it("nav links point to correct paths", () => {
    renderLayout()
    expect(screen.getByRole("link", { name: /dashboard/i })).toHaveAttribute("href", "/")
    expect(screen.getByRole("link", { name: /tasks/i })).toHaveAttribute("href", "/tasks")
    expect(screen.getByRole("link", { name: /sprints/i })).toHaveAttribute("href", "/sprints")
    expect(screen.getByRole("link", { name: /goals/i })).toHaveAttribute("href", "/goals")
  })
})
