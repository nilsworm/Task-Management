import { describe, it, expect, vi, beforeEach } from "vitest"
import React from "react"
import { renderHook, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { useAIInsights } from "@/api/hooks/ai"

vi.mock("@/api/client", () => ({
  apiPost: vi.fn(),
}))

import { apiPost } from "@/api/client"

function makeWrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return function wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  }
}

describe("useAIInsights", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("does not fetch when isOpen is false", () => {
    renderHook(() => useAIInsights(false), { wrapper: makeWrapper() })
    expect(apiPost).not.toHaveBeenCalled()
  })

  it("fetches insights when isOpen is true", async () => {
    const mockCards = [{ title: "Test", body: "Body", type: "tip" }]
    vi.mocked(apiPost).mockResolvedValue(mockCards)

    const { result } = renderHook(() => useAIInsights(true), { wrapper: makeWrapper() })

    await waitFor(() => expect(result.current.data).toBeDefined())
    expect(apiPost).toHaveBeenCalledWith("/ai/insights")
    expect(result.current.data).toEqual(mockCards)
  })

  it("sets isError when fetch fails", async () => {
    vi.mocked(apiPost).mockRejectedValue(new Error("Network error"))
    const { result } = renderHook(() => useAIInsights(true), { wrapper: makeWrapper() })
    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})
