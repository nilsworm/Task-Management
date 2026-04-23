import { describe, it, expect } from "vitest"
import { render, screen } from "@testing-library/react"
import { SprintStatusBadge } from "../SprintStatusBadge"

describe("SprintStatusBadge", () => {
  it.each([
    ["planned", "Planned"],
    ["active", "Active"],
    ["completed", "Completed"],
    ["cancelled", "Cancelled"],
  ])("renders label for status %s", (status, label) => {
    render(<SprintStatusBadge status={status} />)
    expect(screen.getByText(label)).toBeInTheDocument()
  })

  it("falls back to raw status for unknown values", () => {
    render(<SprintStatusBadge status="unknown" />)
    expect(screen.getByText("unknown")).toBeInTheDocument()
  })
})
