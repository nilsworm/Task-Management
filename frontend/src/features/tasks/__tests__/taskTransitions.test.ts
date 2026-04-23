import { describe, it, expect } from "vitest"
import { TRANSITIONS } from "../taskTransitions"

describe("TRANSITIONS", () => {
  it("backlog can move to todo and cancelled", () => {
    expect(TRANSITIONS.backlog).toContain("todo")
    expect(TRANSITIONS.backlog).toContain("cancelled")
  })

  it("done has no transitions", () => {
    expect(TRANSITIONS.done).toHaveLength(0)
  })

  it("cancelled has no transitions", () => {
    expect(TRANSITIONS.cancelled).toHaveLength(0)
  })

  it("in_progress can move to review, blocked, todo, cancelled", () => {
    expect(TRANSITIONS.in_progress).toContain("review")
    expect(TRANSITIONS.in_progress).toContain("blocked")
    expect(TRANSITIONS.in_progress).toContain("todo")
    expect(TRANSITIONS.in_progress).toContain("cancelled")
  })
})
