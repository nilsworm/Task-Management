import { describe, it, expect, beforeEach } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { AIFloatingButton } from "@/features/ai/AIFloatingButton"
import { useAIPanelStore } from "@/stores/aiPanelStore"

describe("AIFloatingButton", () => {
  beforeEach(() => {
    useAIPanelStore.setState({ isOpen: false })
  })

  it("renders the button", () => {
    render(<AIFloatingButton />)
    expect(screen.getByRole("button", { name: /ai advisor/i })).toBeInTheDocument()
  })

  it("calls toggle on click", () => {
    render(<AIFloatingButton />)
    fireEvent.click(screen.getByRole("button", { name: /ai advisor/i }))
    expect(useAIPanelStore.getState().isOpen).toBe(true)
  })
})
