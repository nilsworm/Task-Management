import { describe, it, expect, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { KeyResultItem } from "../KeyResultItem"
import type { KeyResult } from "@/api/hooks/goals"

const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })

function makeKr(overrides: Partial<KeyResult> = {}): KeyResult {
  return {
    id: "kr-1",
    goal_id: "g-1",
    title: "Increase coverage",
    description: "",
    target_value: 100,
    current_value: 50,
    unit: "%",
    progress_percent: 50,
    created_at: "2026-05-01T00:00:00Z",
    updated_at: "2026-05-01T00:00:00Z",
    ...overrides,
  }
}

function renderKr(kr: KeyResult) {
  return render(
    <QueryClientProvider client={qc}>
      <KeyResultItem kr={kr} onEdit={vi.fn()} />
    </QueryClientProvider>,
  )
}

describe("KeyResultItem", () => {
  it("renders the title", () => {
    renderKr(makeKr())
    expect(screen.getByText("Increase coverage")).toBeInTheDocument()
  })

  it("renders current / target with unit", () => {
    renderKr(makeKr())
    expect(screen.getByText(/50 \/ 100 %/)).toBeInTheDocument()
  })

  it("renders progress percent", () => {
    renderKr(makeKr({ progress_percent: 75 }))
    expect(screen.getByText(/75%/)).toBeInTheDocument()
  })

  it("progressbar has correct aria-valuenow", () => {
    renderKr(makeKr({ progress_percent: 60 }))
    const bar = screen.getByRole("progressbar")
    expect(bar).toHaveAttribute("aria-valuenow", "60")
  })

  it("caps progressbar at 100 when progress_percent > 100", () => {
    renderKr(makeKr({ progress_percent: 150 }))
    const bar = screen.getByRole("progressbar")
    expect(bar).toHaveAttribute("aria-valuenow", "100")
  })
})
