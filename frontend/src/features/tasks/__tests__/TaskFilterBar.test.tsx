import { describe, it, expect, vi } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { TaskFilterBar } from "../TaskFilterBar"
import type { TaskFilters } from "../TaskFilterBar"

const DEFAULT: TaskFilters = { search: "", status: "all", priority: "all", taskType: "all", overdue: false }

describe("TaskFilterBar", () => {
  it("renders three filter trigger buttons", () => {
    render(<TaskFilterBar filters={DEFAULT} onChange={vi.fn()} />)
    expect(screen.getByText("All statuses")).toBeInTheDocument()
    expect(screen.getByText("All priorities")).toBeInTheDocument()
    expect(screen.getByText("All types")).toBeInTheDocument()
  })

  it("renders a combobox trigger for each filter", () => {
    render(<TaskFilterBar filters={DEFAULT} onChange={vi.fn()} />)
    const combos = screen.getAllByRole("combobox")
    expect(combos).toHaveLength(3)
  })

  it("opens the status dropdown on trigger click", () => {
    render(<TaskFilterBar filters={DEFAULT} onChange={vi.fn()} />)
    const [statusTrigger] = screen.getAllByRole("combobox")
    fireEvent.click(statusTrigger)
    expect(screen.getByRole("listbox")).toBeInTheDocument()
  })

  it("calls onChange with search value when input changes", () => {
    const onChange = vi.fn()
    render(<TaskFilterBar filters={DEFAULT} onChange={onChange} />)
    const searchInput = screen.getByPlaceholderText("Search tasks…") as HTMLInputElement
    fireEvent.change(searchInput, { target: { value: "backend" } })
    expect(onChange).toHaveBeenCalledWith({ ...DEFAULT, search: "backend" })
  })
})
