import { describe, it, expect, vi, beforeEach } from "vitest"
import { renderHook, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { createElement } from "react"
import { useAIInsights } from "@/api/hooks/ai"

vi.mock("@/api/client", () => ({
  apiPost: vi.fn(),
}))

import { apiPost } from "@/api/client"

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return createElement(QueryClientProvider, { client: qc }, children)
}

describe("useAIInsights", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("does not fetch when isOpen is false", () => {
    renderHook(() => useAIInsights(false), { wrapper })
    expect(apiPost).not.toHaveBeenCalled()
  })

  it("fetches insights when isOpen is true", async () => {
    const mockCards = [{ title: "Test", body: "Body", type: "tip" }]
    vi.mocked(apiPost).mockResolvedValue(mockCards)

    const { result } = renderHook(() => useAIInsights(true), { wrapper })

    await waitFor(() => expect(result.current.data).toBeDefined())
    expect(apiPost).toHaveBeenCalledWith("/ai/insights")
    expect(result.current.data).toEqual(mockCards)
  })
})
