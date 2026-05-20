import { describe, it } from "vitest"
import { renderHook, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
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

describe("cost hooks", () => {
  it.todo("add tests for cost hooks here")
})
