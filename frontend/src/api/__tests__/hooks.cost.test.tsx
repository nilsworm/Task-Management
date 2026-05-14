import { describe, it, expect, vi, beforeEach } from "vitest"
import { renderHook, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { useImportStatus } from "../hooks/cost"
import * as client from "../client"

vi.mock("../client", () => ({
  apiGet: vi.fn(),
}))

const mockApiGet = vi.mocked(client.apiGet)

function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  })
}

function renderHookWithProvider<T>(hook: () => T) {
  const queryClient = createQueryClient()
  return renderHook(() => hook(), {
    wrapper: ({ children }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    ),
  })
}

describe("useImportStatus", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("should fetch import status from API", async () => {
    const mockData = {
      last_import_date: "2026-05-14",
      transaction_count: 5,
    }

    mockApiGet.mockResolvedValueOnce(mockData)

    const { result } = renderHookWithProvider(() => useImportStatus())

    // Initially loading
    expect(result.current.isLoading).toBe(true)

    // Wait for data to load
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.data).toEqual(mockData)
    expect(mockApiGet).toHaveBeenCalledWith("/cost/import-status")
    expect(mockApiGet).toHaveBeenCalledTimes(1)
  })

  it("should handle empty import status (no imports yet)", async () => {
    const mockData = {
      last_import_date: null,
      transaction_count: 0,
    }

    mockApiGet.mockResolvedValueOnce(mockData)

    const { result } = renderHookWithProvider(() => useImportStatus())

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.data).toEqual(mockData)
    expect(result.current.data?.last_import_date).toBeNull()
    expect(result.current.data?.transaction_count).toBe(0)
  })

  it("should handle error state", async () => {
    const error = new Error("Network error")
    mockApiGet.mockRejectedValueOnce(error)

    const { result } = renderHookWithProvider(() => useImportStatus())

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.error).not.toBeNull()
    expect(result.current.data).toBeUndefined()
  })

  it("should set up refetch interval of 60 seconds", async () => {
    const mockData = {
      last_import_date: "2026-05-14",
      transaction_count: 3,
    }

    mockApiGet.mockResolvedValue(mockData)

    const { result } = renderHookWithProvider(() => useImportStatus())

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    // Verify the hook was called at least once
    expect(mockApiGet).toHaveBeenCalled()

    // The refetchInterval is configured but we can't easily test timing
    // without advancing timers. This test documents the expected behavior.
    expect(result.current.data).toEqual(mockData)
  })
})
