import { describe, it, expect, beforeEach } from "vitest"
import { useAIPanelStore } from "@/stores/aiPanelStore"

describe("aiPanelStore", () => {
  beforeEach(() => {
    useAIPanelStore.setState({ isOpen: false })
  })

  it("starts closed", () => {
    expect(useAIPanelStore.getState().isOpen).toBe(false)
  })

  it("toggle opens the panel", () => {
    useAIPanelStore.getState().toggle()
    expect(useAIPanelStore.getState().isOpen).toBe(true)
  })

  it("toggle closes the panel when open", () => {
    useAIPanelStore.setState({ isOpen: true })
    useAIPanelStore.getState().toggle()
    expect(useAIPanelStore.getState().isOpen).toBe(false)
  })
})
