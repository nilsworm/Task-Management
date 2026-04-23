import { describe, it, expect } from "vitest"
import { render, screen } from "@testing-library/react"
import { TaskStatusBadge } from "../TaskStatusBadge"

describe("TaskStatusBadge", () => {
  it.each([
    ["backlog", "Backlog"],
    ["todo", "Todo"],
    ["in_progress", "In Progress"],
    ["review", "Review"],
    ["blocked", "Blocked"],
    ["done", "Done"],
    ["cancelled", "Cancelled"],
  ])("renders label for status %s", (status, label) => {
    render(<TaskStatusBadge status={status} />)
    expect(screen.getByText(label)).toBeInTheDocument()
  })

  it("falls back to raw status for unknown values", () => {
    render(<TaskStatusBadge status="unknown_status" />)
    expect(screen.getByText("unknown_status")).toBeInTheDocument()
  })
})
